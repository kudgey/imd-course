<script setup lang="ts">
/**
 * Псевдомітки на ознаках xrv (лекція 13, розділ «Псевдорозмітка і зміщення підтвердження»).
 * SelfTrainingClassifier з логістичною регресією (C = 10⁻³) на пулі dev1…dev4 розбиття S1: n мічених
 * (порівну ТБ і без ТБ), частка перевернутих міток серед них, поріг упевненості τ. Для кожної клітинки —
 * 10 зерен: скільки знімків пулу отримали псевдомітку, скільки з них правильних і AUC на валідаційній частині
 * dev0. Рядки таблиці коду (32 мічені без шуму; 128 мічених при τ = 0,9 і «лише мічені» для всіх часток шуму)
 * збігаються з віджетом — це перевіряє tools/gen_lec13_pseudo.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec13_pseudo.json'

type Cell = { n: number; noise: number; tau: number | null; acc: number[]; right: number[]; auc: number[] }
const cells = data.cells as Cell[]
const TAUS = data.taus as number[]
const NOISES = data.noises as number[]
const n = ref(32)
const ni = ref(0)
const ti = ref(TAUS.indexOf(0.9))
const get = (tau: number | null, nn = n.value, nz = NOISES[ni.value]) =>
  cells.find((c) => c.n === nn && c.noise === nz && c.tau === tau)!
const mean = (a: number[]) => a.reduce((s, v) => s + v, 0) / a.length
const sd = (a: number[]) => { const m = mean(a); return Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / a.length) }
const stat = (c: Cell) => {
  const acc = c.acc.reduce((s, v) => s + v, 0)
  return { acc: acc / c.acc.length, prec: acc ? c.right.reduce((s, v) => s + v, 0) / acc : NaN, auc: mean(c.auc), sd: sd(c.auc) }
}
const base = computed(() => stat(get(null)))
const cur = computed(() => stat(get(TAUS[ti.value])))
const diff = computed(() => {
  const a = get(TAUS[ti.value]).auc, b = get(null).auc
  const d = a.map((v, i) => v - b[i])
  return { m: mean(d), wins: d.filter((v) => v > 0).length, lo: Math.min(...d), hi: Math.max(...d) }
})
const series = computed(() => TAUS.map((t) => ({ t, ...stat(get(t)) })))
const pool = computed(() => data.pool - n.value)

const W = 420, H = 210, PL = 40, PR = 40, PT = 10, PB = 30
const X = (i: number) => PL + (i / (TAUS.length - 1)) * (W - PL - PR)
const aucR = computed(() => {
  const v = [...series.value.map((s) => s.auc), base.value.auc]
  return [Math.floor(Math.min(...v) * 100 - 1) / 100, Math.ceil(Math.max(...v) * 100 + 1) / 100]
})
const YA = (v: number) => PT + (1 - (v - aucR.value[0]) / (aucR.value[1] - aucR.value[0])) * (H - PT - PB)
const YB = (v: number) => H - PB - (v / pool.value) * (H - PT - PB)
const path = computed(() => series.value.map((s, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${YA(s.auc).toFixed(1)}`).join(' '))
const num = (v: number, d = 3) => (Number.isFinite(v) ? v.toFixed(d).replace('.', ',').replace('-', '−') : '—')
const sgn = (v: number) => (v >= 0 ? '+' : '') + num(v)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Псевдомітки: поріг упевненості і шум у мітках</div>
        <div class="lab__sub">
          Модель, навчена на n мічених, ставить мітки знімкам пулу з упевненістю ≥ τ і донавчається на них, доки нових
          не залишиться. Стовпчики — скільки знімків пулу отримали мітку (темна частина — правильні), лінія — val AUC,
          пунктир — «лише мічені».
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="k in [32, 128]" :key="k" type="button" class="lab__pill" :class="{ 'is-on': n === k }" @click="n = k">{{ k }} мічених</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поріг τ: <b>{{ num(TAUS[ti], 2) }}</b></span>
        <input v-model.number="ti" type="range" min="0" :max="TAUS.length - 1" step="1" aria-label="Поріг упевненості" />
      </label>
      <label class="lab__ctl">
        <span>перевернутих міток серед мічених: <b>{{ NOISES[ni] }} %</b></span>
        <input v-model.number="ni" type="range" min="0" :max="NOISES.length - 1" step="1" aria-label="Частка перевернутих міток" />
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="pl__svg" role="img" aria-label="Прийняті псевдомітки і val AUC від порогу">
      <g v-for="(s, i) in series" :key="'b' + i">
        <rect :x="X(i) - 8" :y="YB(s.acc)" width="16" :height="H - PB - YB(s.acc)" class="pl__acc" :class="{ 'is-cur': i === ti }" />
        <rect :x="X(i) - 8" :y="YB(s.acc * (Number.isFinite(s.prec) ? s.prec : 0))" width="16"
              :height="H - PB - YB(s.acc * (Number.isFinite(s.prec) ? s.prec : 0))" class="pl__ok" />
        <text :x="X(i)" :y="H - PB + 12" text-anchor="middle" class="pl__lbl">{{ num(s.t, 2) }}</text>
      </g>
      <line :x1="PL" :x2="W - PR" :y1="YA(base.auc)" :y2="YA(base.auc)" class="pl__base" />
      <path :d="path" class="pl__line" />
      <circle v-for="(s, i) in series" :key="'c' + i" :cx="X(i)" :cy="YA(s.auc)" :r="i === ti ? 4 : 2.5" class="pl__dot" />
      <text :x="PL - 4" :y="YA(aucR[1]) + 4" text-anchor="end" class="pl__lbl">{{ num(aucR[1], 2) }}</text>
      <text :x="PL - 4" :y="YA(aucR[0])" text-anchor="end" class="pl__lbl">{{ num(aucR[0], 2) }}</text>
      <text :x="W - PR + 4" :y="YB(pool) + 8" class="pl__lbl">{{ pool }}</text>
      <text :x="W - PR + 4" :y="H - PB" class="pl__lbl">0</text>
      <text :x="(PL + W - PR) / 2" :y="H - 4" text-anchor="middle" class="pl__lbl">поріг τ (ліва вісь — val AUC, права — знімків пулу)</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(cur.acc, 1) }}</b><span>з {{ pool }} знімків пулу отримали псевдомітку</span></div>
      <div class="lab__stat" :class="{ 'is-warm': cur.prec < 0.85 }"><b>{{ num(cur.prec) }}</b><span>частка правильних псевдоміток</span></div>
      <div class="lab__stat"><b>{{ num(cur.auc) }} ± {{ num(cur.sd) }}</b><span>val AUC з псевдомітками</span></div>
      <div class="lab__stat"><b>{{ num(base.auc) }}</b><span>val AUC «лише мічені»</span></div>
      <div class="lab__stat" :class="{ 'is-warm': diff.m < 0 }"><b>{{ sgn(diff.m) }}</b><span>парна різниця; краще в {{ diff.wins }} з 10 зерен</span></div>
    </div>
    <p class="lab__note">
      Середнє за 10 зернами; частка правильних — сума правильних псевдоміток, поділена на суму прийнятих. Логістична
      регресія тут із C = 10⁻³ (вибір крос-валідації в темі про CNN): при слабшій регуляризації модель упевненіша, і той
      самий поріг пропускає набагато більше знімків. Поріг тут рухається на валідаційній частині для ілюстрації; у роботі
      його вибирають на ній один раз, а підсумкове число дає тест, якого цей експеримент не відкриває.
    </p>
  </div>
</template>

<style scoped>
.pl__svg { width: 100%; height: auto; display: block; }
.pl__acc { fill: var(--uk-warm-soft); }
.pl__acc.is-cur { stroke: var(--uk-warm); stroke-width: 1.2; }
.pl__ok { fill: var(--uk-warm); opacity: 0.55; }
.pl__line { fill: none; stroke: var(--uk-accent); stroke-width: 1.8; }
.pl__dot { fill: var(--uk-accent); }
.pl__base { stroke: var(--vp-c-text-2); stroke-dasharray: 4 3; stroke-width: 1.2; }
.pl__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
</style>
