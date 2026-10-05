<script setup lang="ts">
/**
 * Контрольовані збурення і стійкість (лекція 17, розділ «Контрольовані збурення і стійкість»).
 * Дані — tools/gen_lec17_robust.py: AUC, чутливість і специфічність моделі S2 на 99 знімках тестової
 * частини Shenzhen за замороженим порогом t для п’яти збурень по три рівні (рівень 0 — без збурення),
 * парний бутстреп-інтервал ΔAUC третього рівня — ті самі числа, що у виводі коду. Кадр для показу —
 * рентгенограма NIH ChestX-ray14 00000511_000, спотворена тими самими функціями (WebP 256 × 256,
 * вантажиться лише вибраний кадр). Знімків Shenzhen не показано.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec17_robust.json'

type Kind = { name: string; slug: string; levels: number[]; rows: number[][]; d3: number[] }
const KINDS = data.kinds as Kind[]
const CLEAN = data.clean as number[]
const ki = ref(0)
const lv = ref(2)
const kind = computed(() => KINDS[ki.value])
const row = computed(() => (lv.value === 0 ? CLEAN : kind.value.rows[lv.value - 1]))
const src = computed(() => withBase(lv.value === 0 ? '/data/lec17/nih_clean.webp' : `/data/lec17/nih_${kind.value.slug}_${lv.value}.webp`))
const levelText = computed(() => (lv.value === 0 ? 'без збурення' : `${kind.value.name.split(',')[0]}: ${String(kind.value.levels[lv.value - 1]).replace('.', ',')}${kind.value.name.includes(',') ? ' (' + kind.value.name.split(', ')[1] + ')' : ''}`))

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const sgn = (v: number) => (v >= 0 ? '+' : '−') + num(Math.abs(v))
const W = 300, H = 170, L = 34, R = 10, T0 = 10, B = 26
const X = (i: number) => L + (i / 3) * (W - L - R)
const Y = (v: number) => T0 + (1 - v) * (H - T0 - B)
const series = computed(() => {
  const all = [CLEAN, ...kind.value.rows]
  const path = (j: number) => all.map((r, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${Y(r[j]).toFixed(1)}`).join(' ')
  return [
    { id: 'auc', label: 'AUC', color: 'var(--uk-accent)', d: path(0), pts: all.map((r) => r[0]) },
    { id: 'spec', label: 'специфічність', color: 'var(--uk-warm)', d: path(2), pts: all.map((r) => r[2]) },
    { id: 'sens', label: 'чутливість', color: '#1BAF7A', d: path(1), pts: all.map((r) => r[1]) },
  ]
})
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Збурення знімка: ранжування проти порогу</div>
        <div class="lab__sub">
          Оберіть збурення і рівень. Ліворуч — те саме збурення на рентгенограмі NIH ChestX-ray14; праворуч — AUC,
          чутливість і специфічність моделі на {{ data.n }} знімках тестової частини Shenzhen за замороженим порогом
          t = {{ num(data.t as number, 4) }}.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="(k, i) in KINDS" :key="k.slug" type="button" class="lab__pill" :class="{ 'is-on': ki === i }" @click="ki = i">{{ k.name.split(',')[0] }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>рівень: <b>{{ lv }}</b> — {{ levelText }}</span>
        <input v-model.number="lv" type="range" min="0" max="3" step="1" aria-label="Рівень збурення" />
      </label>
    </div>
    <div class="pr__grid">
      <figure class="pr__img">
        <img :src="src" width="256" height="256" alt="Рентгенограма NIH ChestX-ray14 00000511_000 з вибраним збуренням" loading="lazy" />
        <figcaption>NIH ChestX-ray14 00000511_000 (Wang et al., 2017), 256 × 256</figcaption>
      </figure>
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Метрики залежно від рівня збурення">
        <line v-for="v in [0, 0.5, 1]" :key="'g' + v" :x1="L" :x2="W - R" :y1="Y(v)" :y2="Y(v)" class="pr__gl" />
        <text v-for="v in [0, 0.5, 1]" :key="'t' + v" :x="L - 5" :y="Y(v) + 3" text-anchor="end" class="pr__lbl">{{ num(v, 1) }}</text>
        <text v-for="i in [0, 1, 2, 3]" :key="'x' + i" :x="X(i)" :y="H - B + 14" text-anchor="middle" class="pr__lbl">{{ i }}</text>
        <text :x="(L + W - R) / 2" :y="H - 2" text-anchor="middle" class="pr__lbl">рівень збурення</text>
        <line :x1="X(lv)" :x2="X(lv)" :y1="T0" :y2="H - B" class="pr__cur" />
        <path v-for="s in series" :key="s.id" :d="s.d" fill="none" :stroke="s.color" stroke-width="2" />
        <g v-for="s in series" :key="'p' + s.id">
          <circle v-for="(v, i) in s.pts" :key="i" :cx="X(i)" :cy="Y(v)" :r="i === lv ? 4 : 2.5" :fill="s.color" />
        </g>
      </svg>
    </div>
    <div class="pr__legend">
      <span v-for="s in series" :key="s.id"><i :style="{ background: s.color }" />{{ s.label }}</span>
    </div>
    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(row[0]) }}</b><span>AUC</span></div>
      <div class="lab__stat is-green"><b>{{ num(row[1]) }}</b><span>чутливість за t</span></div>
      <div class="lab__stat is-warm"><b>{{ num(row[2]) }}</b><span>специфічність за t</span></div>
      <div class="lab__stat"><b>{{ sgn(kind.d3[0]) }}</b><span>ΔAUC рівня 3: [{{ sgn(kind.d3[1]) }}; {{ sgn(kind.d3[2]) }}]</span></div>
    </div>
    <p class="lab__note">
      Інтервал ΔAUC — парний бутстреп на тих самих пацієнтах (2000 вибірок). Збурення зсувають скори вгору: поріг t,
      вибраний на чистих знімках, перестає відділяти норму раніше, ніж падає ранжування. Кадр NIH лише ілюструє
      збурення: числа пораховано на знімках Shenzhen, яких сторінка не показує.
    </p>
  </div>
</template>

<style scoped>
.pr__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.3fr); gap: 1rem; align-items: center; }
@media (max-width: 680px) { .pr__grid { grid-template-columns: 1fr; } }
.pr__img { margin: 0; }
.pr__img img { width: 100%; max-width: 256px; height: auto; display: block; border-radius: 6px; background: #000; image-rendering: auto; }
.pr__img figcaption { font-size: 0.72rem; color: var(--vp-c-text-3); margin-top: 0.25rem; }
svg { width: 100%; height: auto; display: block; }
.pr__gl { stroke: var(--vp-c-divider); }
.pr__cur { stroke: var(--vp-c-text-3); stroke-dasharray: 3 3; }
.pr__lbl { fill: var(--vp-c-text-2); font-size: 10px; }
.pr__legend { display: flex; flex-wrap: wrap; gap: 0.9rem; font-size: 0.8rem; color: var(--vp-c-text-2); margin: 0.4rem 0; }
.pr__legend i { display: inline-block; width: 14px; height: 4px; border-radius: 2px; margin-right: 0.35rem; vertical-align: middle; }
</style>
