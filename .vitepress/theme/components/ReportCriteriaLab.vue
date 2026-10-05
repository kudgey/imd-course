<script setup lang="ts">
/**
 * Критерій успіху звіту (лекція 18, розділ «Звіт, зібраний кодом»). Чутливість і специфічність
 * моделі S2 за порогом t з валідації на трьох частинах — з 95 % ДІ (бутстреп за пацієнтами,
 * B = 2000), як у виводі блоку «Звіт із артефактів»; дані — tools/gen_lec18_report.py, його --check
 * звіряє кожне число з виводом. Перемикачі: цілі TPP WHO (мінімальні або бажані, строгі «>») і
 * правило перевірки (точкова оцінка чи нижня межа ДІ).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec18_report.json'

type Part = { key: string; name: string; set: string; images: number; patients: number; tb: number; se: number; se_lo: number; se_hi: number; sp: number; sp_lo: number; sp_hi: number; ppv: number; npv: number }
type Target = { name: string; se: number; sp: number }
const PARTS = data.parts as Part[]
const TARGETS = data.targets as Record<string, Target>

const target = ref<'min' | 'opt'>('min')
const rule = ref<'point' | 'lower'>('point')
const tg = computed(() => TARGETS[target.value])

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const pct = (v: number) => `${Math.round(v * 100)} %`
const lo = (p: Part, m: 'se' | 'sp') => (m === 'se' ? p.se_lo : p.sp_lo)
const hi = (p: Part, m: 'se' | 'sp') => (m === 'se' ? p.se_hi : p.sp_hi)
const value = (p: Part, m: 'se' | 'sp') => (rule.value === 'point' ? p[m] : lo(p, m))
const passes = (p: Part, m: 'se' | 'sp') => value(p, m) > tg.value[m]
const verdict = (p: Part) => passes(p, 'se') && passes(p, 'sp')

// шкала 0,2…1,0 для обох метрик
const W = 360, PL = 112, PR = 12, ROW = 22, TOP = 18
const X = (v: number) => PL + ((v - 0.2) / 0.8) * (W - PL - PR)
const H = TOP + PARTS.length * 2 * ROW + PARTS.length * 8 + 22
const rows = computed(() => {
  const out: { y: number; p: Part; m: 'se' | 'sp'; label: string }[] = []
  let y = TOP
  for (const p of PARTS) {
    out.push({ y, p, m: 'se', label: `${p.name}: чутл.` })
    out.push({ y: y + ROW, p, m: 'sp', label: 'специфічн.' })
    y += 2 * ROW + 8
  }
  return out
})
const ticks = [0.2, 0.4, 0.6, 0.8, 1.0]
const ext = PARTS[PARTS.length - 1]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Чи досягнуто критерію успіху, записаного до запуску</div>
        <div class="lab__sub">
          Поріг t = {{ num(data.t, 4) }} вибрано на валідаційній частині й заморожено. Точка — оцінка, відрізок — 95 % ДІ
          (бутстреп за пацієнтами, {{ data.B }} повторів), вертикаль — ціль TPP.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': target === 'min' }" @click="target = 'min'">мінімальні цілі TPP: &gt; 90 % і &gt; 70 %</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': target === 'opt' }" @click="target = 'opt'">бажані цілі TPP: &gt; 95 % і &gt; 80 %</button>
    </div>
    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': rule === 'point' }" @click="rule = 'point'">перевіряти точкову оцінку</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': rule === 'lower' }" @click="rule = 'lower'">перевіряти нижню межу 95 % ДІ</button>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="rc__svg" role="img" aria-label="Чутливість і специфічність на трьох частинах даних з інтервалами і цілями TPP">
      <g v-for="v in ticks" :key="'t' + v">
        <line :x1="X(v)" :x2="X(v)" :y1="TOP - 8" :y2="H - 18" class="rc__grid" />
        <text :x="X(v)" :y="H - 6" text-anchor="middle" class="rc__lbl">{{ num(v, 1) }}</text>
      </g>
      <g v-for="r in rows" :key="r.p.key + r.m">
        <text :x="PL - 6" :y="r.y + 4" text-anchor="end" class="rc__lbl">{{ r.label }}</text>
        <line :x1="X(tg[r.m])" :x2="X(tg[r.m])" :y1="r.y - 8" :y2="r.y + 8" class="rc__target" />
        <line :x1="X(lo(r.p, r.m))" :x2="X(hi(r.p, r.m))" :y1="r.y" :y2="r.y"
              :class="passes(r.p, r.m) ? 'rc__ci is-ok' : 'rc__ci is-no'" />
        <circle :cx="X(r.p[r.m])" :cy="r.y" r="4" :class="passes(r.p, r.m) ? 'rc__dot is-ok' : 'rc__dot is-no'" />
      </g>
    </svg>

    <div class="rc__wrap">
      <table class="rc__table">
        <thead><tr><th>частина</th><th>пацієнтів</th><th>чутливість</th><th>специфічність</th><th>ціль досягнуто</th></tr></thead>
        <tbody>
          <tr v-for="p in PARTS" :key="p.key">
            <td>{{ p.name }} ({{ p.set }})</td>
            <td>{{ p.patients }}</td>
            <td>{{ num(p.se) }} [{{ num(p.se_lo) }}; {{ num(p.se_hi) }}]</td>
            <td>{{ num(p.sp) }} [{{ num(p.sp_lo) }}; {{ num(p.sp_hi) }}]</td>
            <td :class="verdict(p) ? 'rc__yes' : 'rc__no'">{{ verdict(p) ? 'так' : 'ні' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(ext.ppv) }}</b><span>PPV зовнішнього тесту за поширеності {{ num(data.prev * 100, 1) }} %</span></div>
      <div class="lab__stat"><b>{{ num(ext.npv) }}</b><span>NPV зовнішнього тесту</span></div>
      <div class="lab__stat"><b>{{ pct(tg.se) }} / {{ pct(tg.sp) }}</b><span>{{ tg.name }}: чутливість / специфічність, строго більше</span></div>
    </div>

    <p class="lab__note">
      Валідаційна частина лише описує вибір: поріг узято так, щоб чутливість на ній дорівнювала 0,9, тож строгу ціль
      «більше 90 %» вона не проходить за побудовою. Нижня межа інтервалу — суворіше правило: воно вимагає, щоб ціль
      лишалася досягнутою навіть за невдалої вибірки пацієнтів.
    </p>
  </div>
</template>

<style scoped>
.rc__svg { width: 100%; height: auto; display: block; margin: 0.2rem 0 0.6rem; }
.rc__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.rc__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.rc__target { stroke: var(--vp-c-text-1); stroke-width: 1.4; stroke-dasharray: 3 2; }
.rc__ci { stroke-width: 3; stroke-linecap: round; }
.rc__ci.is-ok, .rc__dot.is-ok { stroke: var(--uk-green); fill: var(--uk-green); }
.rc__ci.is-no, .rc__dot.is-no { stroke: var(--uk-warm); fill: var(--uk-warm); }
.rc__wrap { width: 100%; overflow-x: auto; }
.rc__table { width: 100%; border-collapse: collapse; font-size: 0.8rem; min-width: 320px; }
.rc__table th, .rc__table td { border: none; border-bottom: 1px solid var(--uk-line); padding: 0.28rem 0.35rem; text-align: left; background: none; }
.rc__table th { font-weight: 500; color: var(--vp-c-text-3); font-size: 0.74rem; }
.rc__yes { color: var(--uk-green); font-weight: 600; }
.rc__no { color: var(--uk-warm); font-weight: 600; }
</style>
