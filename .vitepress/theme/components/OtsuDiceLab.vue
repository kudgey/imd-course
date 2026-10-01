<script setup lang="ts">
/**
 * Поріг Оцу на об’ємі LIDC-IDRI-0001 і Dice маски «HU ≤ t» з маскою легень LUNA16 (лекція 06,
 * розділ «Поріг Оцу: розділити гістограму на два класи»). Дані — гістограми з кроком 1 HU від
 * tools/gen_lec06_otsu.py: вокселі легень і решта, окремо всередині тіла і поза ним. σ²_B(t)
 * рахується тут так само, як skimage.filters.threshold_otsu для цілих значень; максимум — −469 HU,
 * Dice при ньому — 0,332 у всьому полі і 0,959 усередині тіла, як у виводі блоку коду.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec06_otsu.json'

const LO = data.lo as number
const LB = data.lung_body as number[]
const OB = data.other_body as number[]
const LOUT = data.lung_out as number[]
const OOUT = data.other_out as number[]
const NL = data.n_lungs as number
const NB = LB.length

const FOV = LB.map((v, i) => v + OB[i] + LOUT[i] + OOUT[i])
const cum = (a: number[]) => { const o = new Float64Array(a.length); let s = 0; for (let i = 0; i < a.length; i++) { s += a[i]; o[i] = s } return o }
const cN = cum(FOV)
const cX = cum(FOV.map((v, i) => v * (i + LO)))
const cLB = cum(LB), cOB = cum(OB), cLO = cum(LOUT), cOO = cum(OOUT)
const NTOT = cN[NB - 1], XTOT = cX[NB - 1]

/** σ²_B для порогу t (клас 0 — значення ≤ t) у частках вокселів, HU² */
function stats(t: number) {
  const i = t - LO
  const n0 = cN[i], n1 = NTOT - n0
  const m0 = cX[i] / n0, m1 = (XTOT - cX[i]) / n1
  const w0 = n0 / NTOT
  return { w0, w1: 1 - w0, m0, m1, sb: w0 * (1 - w0) * (m0 - m1) ** 2 }
}
/** Поріг Оцу, як у skimage: argmax w1·w2·(μ1 − μ2)² за кошиками-значеннями */
const OTSU = (() => {
  let best = -1, arg = 0
  for (let i = 0; i < NB - 1; i++) {
    const n0 = cN[i], n1 = NTOT - n0
    if (n0 === 0 || n1 === 0) continue
    const v = n0 * n1 * (cX[i] / n0 - (XTOT - cX[i]) / n1) ** 2
    if (v > best) { best = v; arg = i }
  }
  return arg + LO
})()
const diceBody = (t: number) => { const i = t - LO; return (2 * cLB[i]) / (cLB[i] + cOB[i] + NL) }
const diceFov = (t: number) => { const i = t - LO; return (2 * (cLB[i] + cLO[i])) / (cLB[i] + cOB[i] + cLO[i] + cOO[i] + NL) }

const T0 = -1000, T1 = 400
const t = ref(OTSU)
const cur = computed(() => ({ ...stats(t.value), db: diceBody(t.value), df: diceFov(t.value) }))
const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const big = (v: number) => Math.round(v).toLocaleString('uk-UA').replace(/ /g, ' ')

/* Графік: гістограма (лог), σ²_B / max і Dice на одній шкалі 0…1 */
const W = 380, H = 220, PL = 34, PR = 34, PT = 10, PB = 30
const X = (hu: number) => PL + ((hu - T0) / (T1 - T0)) * (W - PL - PR)
const Yr = (v: number) => PT + (1 - v) * (H - PT - PB)
const STEP = 8
const histPath = (() => {
  const pts: string[] = []
  let mx = 0
  const vals: [number, number][] = []
  for (let h = T0; h < T1; h += STEP) {
    let s = 0
    for (let k = h; k < h + STEP; k++) s += FOV[k - LO] ?? 0
    const v = Math.log10(s + 1)
    vals.push([h, v]); mx = Math.max(mx, v)
  }
  for (const [h, v] of vals) pts.push(`${X(h).toFixed(1)},${Yr(v / mx).toFixed(1)}`, `${X(h + STEP).toFixed(1)},${Yr(v / mx).toFixed(1)}`)
  return `${X(T0)},${Yr(0)} ${pts.join(' ')} ${X(T1)},${Yr(0)}`
})()
const curve = (fn: (t: number) => number, norm = 1) => {
  const pts: string[] = []
  for (let h = T0; h <= T1; h += 4) pts.push(`${X(h).toFixed(1)},${Yr(fn(h) / norm).toFixed(1)}`)
  return pts.join(' ')
}
const SBMAX = stats(OTSU).sb
const sbPath = curve(h => stats(h).sb, SBMAX)
const dbPath = curve(diceBody)
const dfPath = curve(diceFov)
const xTicks = [-1000, -800, -600, -400, -200, 0, 200, 400]
const yTicks = [0, 0.25, 0.5, 0.75, 1]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Поріг Оцу на КТ: σ²_B(t) і Dice з маскою LUNA16</div>
        <div class="lab__sub">
          Гістограма HU поля реконструкції LIDC-IDRI-0001 (увесь об’єм, без заповнювача −2048). Маска — вокселі HU ≤ t,
          еталон — легені LUNA16 (мітки 3 і 4).
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поріг t: <b>{{ num(t, 0) }} HU</b></span>
        <input v-model.number="t" type="range" :min="T0" :max="T1" step="1" aria-label="Поріг у HU">
      </label>
      <div class="lab__ctl ot__btns">
        <span>швидкий вибір</span>
        <button type="button" class="lab__btn" @click="t = OTSU">поріг Оцу ({{ num(OTSU, 0) }} HU)</button>
        <button type="button" class="lab__btn" @click="t = -200">−200 HU</button>
        <button type="button" class="lab__btn" @click="t = -800">−800 HU</button>
      </div>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="ot__svg" role="img" aria-label="Гістограма HU, крива міжкласової дисперсії і Dice залежно від порогу">
      <g v-for="v in yTicks" :key="'y' + v">
        <line :x1="PL" :x2="W - PR" :y1="Yr(v)" :y2="Yr(v)" class="ot__grid" />
        <text :x="W - PR + 4" :y="Yr(v) + 3" class="ot__lbl">{{ num(v, 2) }}</text>
      </g>
      <polygon :points="histPath" class="ot__hist" />
      <polyline :points="sbPath" class="ot__sb" />
      <polyline :points="dfPath" class="ot__df" />
      <polyline :points="dbPath" class="ot__db" />
      <line :x1="X(OTSU)" :x2="X(OTSU)" :y1="PT" :y2="H - PB" class="ot__otsu" />
      <line :x1="X(t)" :x2="X(t)" :y1="PT" :y2="H - PB" class="ot__t" />
      <text v-for="h in xTicks" :key="'x' + h" :x="X(h)" :y="H - PB + 13" text-anchor="middle" class="ot__lbl">{{ num(h, 0) }}</text>
      <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="ot__lbl">HU</text>
      <text :x="PL - 4" :y="PT + 8" text-anchor="end" class="ot__lbl">лог</text>
    </svg>
    <div class="ot__legend">
      <span><i class="ot__k ot__k--hist"></i>гістограма (лог. шкала)</span>
      <span><i class="ot__k ot__k--sb"></i>σ²_B(t) / максимум</span>
      <span><i class="ot__k ot__k--db"></i>Dice усередині тіла</span>
      <span><i class="ot__k ot__k--df"></i>Dice у всьому полі</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(cur.w0, 3) }} / {{ num(cur.w1, 3) }}</b><span>ω₀ / ω₁ — частки класів</span></div>
      <div class="lab__stat"><b>{{ num(cur.m0, 1) }} / {{ num(cur.m1, 1) }}</b><span>μ₀ / μ₁, HU</span></div>
      <div class="lab__stat" :class="{ 'is-green': t === OTSU }"><b>{{ big(cur.sb) }}</b><span>σ²_B(t), HU²{{ t === OTSU ? ' — максимум' : '' }}</span></div>
      <div class="lab__stat is-warm"><b>{{ num(cur.db, 3) }}</b><span>Dice усередині тіла</span></div>
      <div class="lab__stat"><b>{{ num(cur.df, 3) }}</b><span>Dice у всьому полі</span></div>
    </div>

    <p class="lab__note">
      Максимум σ²_B стоїть на −469 HU — у провалі гістограми між горбом повітря й легень і горбом м’яких тканин.
      Усередині тіла Dice тримається біля максимуму в широкому діапазоні порогів, бо в провалі мало вокселів: зсув
      порогу на сотню HU переводить у маску лише межові вокселі. У всьому полі Dice не піднімається вище третини за
      будь-якого порогу — повітря навколо пацієнта темніше за поріг так само, як легені, і поріг сам по собі його не відокремить.
    </p>
  </div>
</template>

<style scoped>
.ot__btns { display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center; }
.ot__btns > span { width: 100%; }
.ot__svg { width: 100%; height: auto; display: block; }
.ot__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.ot__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.ot__hist { fill: var(--uk-fill); stroke: none; }
.ot__sb { fill: none; stroke: var(--vp-c-text-2); stroke-width: 1.4; stroke-dasharray: 5 3; }
.ot__db { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.ot__df { fill: none; stroke: var(--uk-accent); stroke-width: 1.6; }
.ot__otsu { stroke: var(--uk-green); stroke-width: 1; stroke-dasharray: 2 2; }
.ot__t { stroke: var(--vp-c-text-1); stroke-width: 1.3; }
.ot__legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.3rem; }
.ot__k { display: inline-block; width: 18px; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 0.35rem; }
.ot__k--hist { border-top: 8px solid var(--uk-fill); }
.ot__k--sb { border-top: 2px dashed var(--vp-c-text-2); }
.ot__k--db { border-color: var(--uk-warm); }
.ot__k--df { border-color: var(--uk-accent); }
</style>
