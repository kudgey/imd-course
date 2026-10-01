<script setup lang="ts">
/**
 * Нормалізація інтенсивностей КТ на серії LIDC-IDRI-0001: п’ять методів із блоку коду розділу
 * «Нормалізація інтенсивностей КТ: min–max, z-score, перцентилі» плюс вікно −1000…400 HU з конвеєра MONAI.
 * Дані — точні гістограми HU (кошик 1 HU) усіх вокселів серії і вокселів під мітками маски LUNA16
 * (tools/gen_lec05_normalize.py). Мінімум, максимум, середні, СКО і перцентилі (лінійна інтерполяція, як
 * numpy.percentile) рахуються тут із гістограм, тож при перцентилях 0,5 і 99,5 межі nnU-Net −988…214 HU,
 * середнє −824 і СКО 174 HU, 4,4 % обрізаних вокселів і всі значення шести тканин збігаються з виводом коду
 * (генератор звіряє це з --check).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec05_normalize.json'

const hist = data.hist as number[]
const hLo = data.hist_lo as number
const fg = data.fg_hist as number[]
const fLo = data.fg_lo as number
const nAll = data.n_all as number
const nPad = data.n_pad as number
const PAD = data.pad as number
const MIN = data.min as number
const MAX = data.max as number
const PROBE = data.probe as number[]
const NAMES = ['повітря', 'легеня', 'жир', 'м’яз', 'контраст', 'кістка']
const nBody = hist.reduce((a, b) => a + b, 0)

function moments(lo: number, h: number[], extraV = 0, extraN = 0) {
  let n = extraN
  let s = extraV * extraN
  for (let i = 0; i < h.length; i++) { n += h[i]; s += (lo + i) * h[i] }
  const mu = s / n
  let q = extraN * (extraV - mu) ** 2
  for (let i = 0; i < h.length; i++) q += h[i] * (lo + i - mu) ** 2
  return { mu, sd: Math.sqrt(q / n) }
}
/** Перцентиль за гістограмою цілих значень — як numpy.percentile (лінійна інтерполяція) */
function percentile(lo: number, h: number[], q: number) {
  const n = h.reduce((a, b) => a + b, 0)
  const r = (q / 100) * (n - 1)
  const k = Math.floor(r)
  const frac = r - k
  const at = (rank: number) => {
    let c = 0
    for (let i = 0; i < h.length; i++) { c += h[i]; if (c > rank) return lo + i }
    return lo + h.length - 1
  }
  const a = at(k)
  const b = at(Math.min(k + 1, n - 1))
  return a + frac * (b - a)
}

const all = moments(hLo, hist, PAD, nPad)
const histAir = hist.slice()
histAir[-1024 - hLo] += nPad
const air = moments(hLo, histAir)
const fgm = moments(fLo, fg)

const METHODS = [
  { key: 'mmPad', name: 'min–max із заповнювачем' },
  { key: 'mmAir', name: 'min–max, заповнювач → −1024' },
  { key: 'zAll', name: 'z-score за всім об’ємом' },
  { key: 'zAir', name: 'z-score без заповнювача' },
  { key: 'nn', name: 'nnU-Net CT (передній план)' },
  { key: 'win', name: 'вікно −1000…400 → [0, 1]' },
]
const method = ref('nn')
const pLo = ref(0.5)
const pHi = ref(99.5)
const bounds = computed(() => ({ lo: percentile(fLo, fg, pLo.value), hi: percentile(fLo, fg, pHi.value) }))

/** Параметри поточного методу: зсув a, масштаб s, межі обрізання lo…hi */
const par = computed(() => {
  const inf = Infinity
  switch (method.value) {
    case 'mmPad': return { a: MIN, s: MAX - MIN, lo: -inf, hi: inf }
    case 'mmAir': return { a: Math.min(hLo, -1024), s: MAX - Math.min(hLo, -1024), lo: -inf, hi: inf }
    case 'zAll': return { a: all.mu, s: all.sd, lo: -inf, hi: inf }
    case 'zAir': return { a: air.mu, s: air.sd, lo: -inf, hi: inf }
    case 'nn': return { a: fgm.mu, s: fgm.sd, lo: bounds.value.lo, hi: bounds.value.hi }
    default: return { a: -1000, s: 1400, lo: -1000, hi: 400 }
  }
})
const f = (x: number) => (Math.min(Math.max(x, par.value.lo), par.value.hi) - par.value.a) / par.value.s
const probeOut = computed(() => PROBE.map(f))
const clipped = computed(() => {
  let below = 0
  let above = 0
  for (let i = 0; i < hist.length; i++) {
    const v = hLo + i
    if (v < par.value.lo) below += hist[i]
    else if (v > par.value.hi) above += hist[i]
  }
  return { below: below / nBody, above: above / nBody }
})

const num = (v: number, d = 2) => (Object.is(Math.round(v * 10 ** d), -0) ? 0 : v).toFixed(d).replace('.', ',').replace('-', '−')
const pct = (v: number) => num(100 * v, 1) + ' %'

/* Гістограма (кошики 20 HU, логарифм висоти) і крива відображення */
const X0 = -1100
const X1 = 1600
const BIN = 20
const SW = 380
const SH = 180
const PL = 10
const PR = 34
const PB = 22
const sx = (hu: number) => PL + ((Math.min(Math.max(hu, X0), X1) - X0) / (X1 - X0)) * (SW - PL - PR)
function bins(lo: number, h: number[]) {
  const n = (X1 - X0) / BIN
  const arr = new Array(n).fill(0)
  for (let i = 0; i < h.length; i++) {
    const v = lo + i
    if (v >= X0 && v < X1) arr[Math.floor((v - X0) / BIN)] += h[i]
  }
  return arr
}
const bAll = bins(hLo, hist)
const bFg = bins(fLo, fg)
const top = Math.log10(Math.max(...bAll) + 1)
const bh = (c: number) => (Math.log10(c + 1) / top) * (SH - PB - 8)
const barW = ((SW - PL - PR) * BIN) / (X1 - X0)
const yRange = computed(() => {
  const ys = [f(X0), f(X1), ...probeOut.value]
  const lo = Math.min(...ys)
  const hi = Math.max(...ys)
  return { lo, hi: hi > lo ? hi : lo + 1 }
})
const sy = (y: number) => SH - PB - ((y - yRange.value.lo) / (yRange.value.hi - yRange.value.lo)) * (SH - PB - 8)
const curve = computed(() => {
  const pts: string[] = []
  for (let hu = X0; hu <= X1; hu += 10) pts.push(`${sx(hu).toFixed(1)},${sy(f(hu)).toFixed(1)}`)
  return pts.join(' ')
})
const TICKS = [-1000, -500, 0, 500, 1000, 1500]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Шкала HU → вхід мережі: шість способів нормалізації</div>
        <div class="lab__sub">
          Гістограма всіх вокселів серії LIDC-IDRI-0001 у полі реконструкції (світла) і під мітками маски легень
          LUNA16 (темна), висота — логарифм кількості. Помаранчева крива — значення, яке отримує кожне HU після
          вибраної нормалізації (права вісь).
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="m in METHODS" :key="m.key" class="lab__pill" type="button" :class="{ 'is-on': method === m.key }"
              @click="method = m.key">{{ m.name }}</button>
    </div>

    <div v-if="method === 'nn'" class="lab__controls">
      <label class="lab__ctl">
        <span>нижній перцентиль переднього плану: <b>{{ num(pLo, 1) }}</b> → {{ num(bounds.lo, 1) }} HU</span>
        <input type="range" min="0" max="5" step="0.1" v-model.number="pLo" />
      </label>
      <label class="lab__ctl">
        <span>верхній перцентиль: <b>{{ num(pHi, 1) }}</b> → {{ num(bounds.hi, 1) }} HU</span>
        <input type="range" min="95" max="100" step="0.1" v-model.number="pHi" />
      </label>
    </div>

    <svg :viewBox="`0 0 ${SW} ${SH}`" class="nl__svg" role="img" aria-label="Гістограма HU і крива нормалізації">
      <rect v-if="par.lo > X0 && Number.isFinite(par.lo)" :x="PL" y="4" :width="Math.max(sx(par.lo) - PL, 0)"
            :height="SH - PB - 4" class="nl__clip" />
      <rect v-if="par.hi < X1 && Number.isFinite(par.hi)" :x="sx(par.hi)" y="4" :width="Math.max(SW - PR - sx(par.hi), 0)"
            :height="SH - PB - 4" class="nl__clip" />
      <rect v-for="(c, k) in bAll" :key="'a' + k" :x="PL + k * barW" :y="SH - PB - bh(c)" :width="barW" :height="bh(c)" class="nl__all" />
      <rect v-for="(c, k) in bFg" :key="'f' + k" :x="PL + k * barW" :y="SH - PB - bh(c)" :width="barW" :height="bh(c)" class="nl__fg" />
      <polyline :points="curve" class="nl__curve" />
      <g v-for="(p, k) in PROBE" :key="'p' + k">
        <circle :cx="sx(p)" :cy="sy(probeOut[k])" r="2.6" class="nl__dot" />
      </g>
      <line :x1="PL" :x2="SW - PR" :y1="SH - PB" :y2="SH - PB" class="nl__axis" />
      <g v-for="t in TICKS" :key="t">
        <line :x1="sx(t)" :x2="sx(t)" :y1="SH - PB" :y2="SH - PB + 4" class="nl__axis" />
        <text :x="sx(t)" :y="SH - 6" text-anchor="middle" class="nl__lbl">{{ num(t, 0) }}</text>
      </g>
      <text :x="SW - PR + 4" :y="sy(yRange.hi) + 4" class="nl__lbl nl__r">{{ num(yRange.hi) }}</text>
      <text :x="SW - PR + 4" :y="sy(yRange.lo)" class="nl__lbl nl__r">{{ num(yRange.lo) }}</text>
    </svg>
    <div class="nl__cap">HU (вісь унизу); заштриховано значення, які метод обрізає. Заповнювач {{ num(PAD, 0) }} HU
      ({{ pct(nPad / nAll) }} вокселів серії) лежить лівіше осі, але входить у статистики перших методів.</div>

    <div class="nl__table">
      <div class="nl__row nl__head"><span>тканина</span><span>HU</span><span>після нормалізації</span></div>
      <div v-for="(p, k) in PROBE" :key="p" class="nl__row">
        <span>{{ NAMES[k] }}</span><span>{{ num(p, 0) }}</span><span><b>{{ num(probeOut[k]) }}</b></span>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(par.a, 0) }}</b><span>зсув, HU (мінімум або середнє)</span></div>
      <div class="lab__stat"><b>{{ num(par.s, 0) }}</b><span>масштаб, HU (розмах або СКО)</span></div>
      <div class="lab__stat is-warm"><b>{{ pct(clipped.above) }}</b><span>вокселів поля обрізано зверху</span></div>
      <div class="lab__stat is-green"><b>{{ pct(clipped.below) }}</b><span>обрізано знизу</span></div>
    </div>

    <p class="lab__note">
      Порівняйте «min–max із заповнювачем» і «min–max, заповнювач → −1024»: легеня (−850 HU) переїжджає з 0,23 на 0,04,
      хоча самі воксели легені не змінилися. У nnU-Net зсуньте верхній перцентиль від 99,5 до 100 — межа обрізання
      біжить до максимуму маски, а кістка і контраст знову отримують різні значення; поверніть 99,5 — і вони злипаються
      в одне число.
    </p>
  </div>
</template>

<style scoped>
.nl__svg { width: 100%; max-width: 620px; height: auto; display: block; }
.nl__all { fill: var(--uk-accent); opacity: 0.25; }
.nl__fg { fill: var(--uk-accent); opacity: 0.75; }
.nl__clip { fill: var(--uk-warm); opacity: 0.1; }
.nl__curve { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.nl__dot { fill: var(--uk-warm); stroke: var(--vp-c-bg); stroke-width: 1; }
.nl__axis { stroke: var(--uk-line); stroke-width: 1; }
.nl__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.nl__r { fill: var(--uk-warm); }
.nl__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.3rem 0 0.7rem; line-height: 1.4; max-width: 620px; }
.nl__table { display: grid; gap: 0.15rem; max-width: 420px; font-size: 0.82rem; }
.nl__row { display: grid; grid-template-columns: 1.2fr 0.8fr 1.4fr; gap: 0.5rem; padding: 0.15rem 0.3rem; border-bottom: 1px dashed var(--uk-line); }
.nl__head { color: var(--vp-c-text-3); font-size: 0.75rem; }
.nl__row b { font-family: var(--vp-font-family-mono); color: var(--uk-accent); font-weight: 500; }
</style>
