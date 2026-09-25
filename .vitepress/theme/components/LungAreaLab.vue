<script setup lang="ts">
/**
 * Площа обох легеневих полів Montgomery (лекція 01, розділ «Кількісний аналіз: площа
 * легеневих полів у квадратних сантиметрах»). Лише числа: кількість пікселів ручних масок,
 * мітка й стать для 138 знімків (tools/gen_lec01_lung.py); жодного знімка чи маски.
 * Площа = пікселі × (0,0875 мм / 10)², як у блоці коду 3; медіани збігаються з виводом:
 * усі 396,0 проти 371,0 см², жінки 334,2 проти 351,7, чоловіки 422,2 проти 443,7.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec01_lung.json'

type Sex = 'all' | 'F' | 'M'
type Img = [number, number, string] // пікселів обох масок, мітка (1 — ТБ), стать F / M / O

const IMGS = data.images as unknown as Img[]
const STEP = (data.spacing_mm as number) / 10
const CM2 = STEP * STEP
const AREAS = IMGS.map(([n, y, s]) => ({ a: n * CM2, y, s }))
const SEXES: { key: Sex; name: string }[] = [
  { key: 'all', name: 'усі' },
  { key: 'F', name: 'жінки' },
  { key: 'M', name: 'чоловіки' },
]
const X0 = 100
const X1 = 650 // см², вісь гістограми не змінюється під час перемикань

const sex = ref<Sex>('all')
const showNorm = ref(true)
const showTb = ref(true)
const binW = ref(25)
const hover = ref<number | null>(null)

const pick = (s: Sex, y: number) =>
  AREAS.filter(r => r.y === y && (s === 'all' || r.s === s)).map(r => r.a).sort((p, q) => p - q)

function median(v: number[]): number {
  const n = v.length
  if (!n) return NaN
  const m = Math.floor(n / 2)
  return n % 2 ? v[m] : (v[m - 1] + v[m]) / 2
}

const stats = computed(() =>
  SEXES.map(({ key, name }) => {
    const norm = pick(key, 0)
    const tb = pick(key, 1)
    return { key, name, n0: norm.length, n1: tb.length, m0: median(norm), m1: median(tb) }
  }),
)
const cur = computed(() => stats.value.find(g => g.key === sex.value)!)

const nBins = computed(() => Math.ceil((X1 - X0) / binW.value))
function counts(s: Sex, y: number): number[] {
  const out = new Array(nBins.value).fill(0)
  for (const a of pick(s, y)) {
    const i = Math.floor((a - X0) / binW.value)
    if (i >= 0 && i < out.length) out[i] += 1
  }
  return out
}
const hist = computed(() => ({ norm: counts(sex.value, 0), tb: counts(sex.value, 1) }))
// вісь Y — за всією вибіркою, щоб перемикання статі не змінювало масштаб
const yMax = computed(() => {
  const m = Math.max(...counts('all', 0), ...counts('all', 1), 1)
  const step = m > 10 ? 5 : 2
  return Math.ceil(m / step) * step
})
const yTicks = computed(() => {
  const step = yMax.value > 10 ? 5 : 2
  return Array.from({ length: yMax.value / step + 1 }, (_, k) => k * step)
})

// гістограма: viewBox 340 × 196
const W = 340, H = 196, L = 30, R = 8, T = 22, B = 30
const sx = (a: number) => L + ((a - X0) / (X1 - X0)) * (W - L - R)
const sy = (c: number) => H - B - (c / yMax.value) * (H - T - B)
const xTicks = [100, 200, 300, 400, 500, 600]

const bars = computed(() => {
  const both = showNorm.value && showTb.value
  const out: { x: number; w: number; y: number; h: number; cls: string }[] = []
  for (let i = 0; i < nBins.value; i++) {
    const x0 = sx(X0 + i * binW.value) + 0.6
    const x1 = sx(Math.min(X0 + (i + 1) * binW.value, X1)) - 0.6
    const half = (x1 - x0) / 2
    const series: [boolean, number, string, number][] = [
      [showNorm.value, hist.value.norm[i], 'la__norm', x0],
      [showTb.value, hist.value.tb[i], 'la__tb', both ? x0 + half : x0],
    ]
    for (const [on, c, cls, x] of series) {
      if (!on || !c) continue
      out.push({ x, w: both ? half : x1 - x0, y: sy(c), h: sy(0) - sy(c), cls })
    }
  }
  return out
})

const medLines = computed(() => {
  const g = cur.value
  const lines = [
    { on: showNorm.value, m: g.m0, cls: 'la__norm', name: 'норма' },
    { on: showTb.value, m: g.m1, cls: 'la__tb', name: 'ТБ' },
  ].filter(l => l.on && Number.isFinite(l.m))
  const lo = Math.min(...lines.map(l => l.m))
  return lines.map(l => ({ ...l, x: sx(l.m), anchor: lines.length > 1 && l.m === lo ? 'end' : 'start' }))
})

// індекс стовпця під курсором; після зміни ширини стовпця старий індекс може бути поза віссю
const hv = computed(() => (hover.value !== null && hover.value < nBins.value ? hover.value : null))
const hoverText = computed(() => {
  if (hv.value === null) return 'Наведіть курсор на стовпець або торкніться його: побачите, скільки знімків у ньому.'
  const i = hv.value
  const a = X0 + i * binW.value
  const b = Math.min(a + binW.value, X1)
  const parts: string[] = []
  if (showNorm.value) parts.push(`норма ${hist.value.norm[i]}`)
  if (showTb.value) parts.push(`ТБ ${hist.value.tb[i]}`)
  return `${a}–${b} см²: ${parts.join(' · ')} (${cur.value.name})`
})

// нижня панель: медіани трьох груп на одній осі
const MX0 = 300, MX1 = 470
const mx = (a: number) => 104 + ((a - MX0) / (MX1 - MX0)) * (332 - 104)
const mTicks = [300, 350, 400, 450]

const men = computed(() => {
  const all = AREAS
  const tb = all.filter(r => r.y === 1)
  const norm = all.filter(r => r.y === 0)
  return {
    tb: tb.filter(r => r.s === 'M').length, nTb: tb.length,
    norm: norm.filter(r => r.s === 'M').length, nNorm: norm.length,
  }
})

const NB = ' '
const dec = (v: number, d = 1) => v.toFixed(d).replace('.', ',')
// різниця медіан, уже заокруглених до 0,1 см², — щоб збігалася з різницею чисел на сторінці
const r1 = (v: number) => Math.round(v * 10) / 10
const diff = (a: number, b: number) => r1(r1(b) - r1(a))
const signed = (v: number) => (v > 0 ? '+' : v < 0 ? '−' : '') + dec(Math.abs(v))
const pct = (a: number, b: number) => dec((100 * a) / b) + NB + '%'

function toggle(which: 'norm' | 'tb') {
  if (which === 'norm' && !(showNorm.value && !showTb.value)) showNorm.value = !showNorm.value
  if (which === 'tb' && !(showTb.value && !showNorm.value)) showTb.value = !showTb.value
}
</script>

<template>
  <div class="lab la">
    <div class="lab__head">
      <div>
        <div class="lab__title">Площа легеневих полів Montgomery: норма і ТБ</div>
        <div class="lab__sub">
          138 знімків, лише числа: пікселі обох ручних масок × (0,0875 мм)². Перемикайте стать і мітку;
          медіани й кількість знімків рахуються так само, як у коді вище. Один запис зі статтю «O»
          входить лише в «усі».
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="g in stats" :key="g.key" type="button" class="lab__pill"
              :class="{ 'is-on': sex === g.key }" @click="sex = g.key">
        {{ g.name }} ({{ g.n0 + g.n1 }})
      </button>
      <span class="la__sep" aria-hidden="true" />
      <button type="button" class="lab__pill la__pnorm" :class="{ 'is-on': showNorm }" @click="toggle('norm')">
        норма ({{ cur.n0 }})
      </button>
      <button type="button" class="lab__pill la__ptb" :class="{ 'is-on': showTb }" @click="toggle('tb')">
        ТБ ({{ cur.n1 }})
      </button>
    </div>

    <label class="lab__ctl la__slider">
      <span>Ширина стовпця = <b>{{ binW }} см²</b></span>
      <input v-model.number="binW" type="range" min="10" max="50" step="5" aria-label="Ширина стовпця" />
    </label>

    <svg class="la__svg" :viewBox="`0 0 ${W} ${H}`" role="img"
         :aria-label="`Гістограма площ: медіана норми ${dec(cur.m0)}, ТБ ${dec(cur.m1)} см²`"
         @pointerleave="hover = null">
      <g v-for="t in yTicks" :key="'y' + t">
        <line :x1="L" :x2="W - R" :y1="sy(t)" :y2="sy(t)" class="la__grid" />
        <text :x="L - 4" :y="sy(t) + 3" text-anchor="end" class="la__tick">{{ t }}</text>
      </g>
      <text :x="L - 4" :y="T - 10" text-anchor="end" class="la__tick">знімків</text>
      <g v-for="t in xTicks" :key="'x' + t">
        <text :x="sx(t)" :y="H - B + 13" text-anchor="middle" class="la__tick">{{ t }}</text>
      </g>
      <text :x="(L + W - R) / 2" :y="H - 3" text-anchor="middle" class="la__lbl">площа обох легеневих полів, см²</text>

      <rect v-if="hv !== null" :x="sx(X0 + hv * binW)" :y="T" :height="H - T - B"
            :width="sx(X0 + binW) - sx(X0)" class="la__hl" />
      <rect v-for="(b, k) in bars" :key="k" :x="b.x" :y="b.y" :width="Math.max(b.w, 0.5)" :height="b.h"
            :class="b.cls" />
      <g v-for="l in medLines" :key="l.name">
        <line :x1="l.x" :x2="l.x" :y1="T - 4" :y2="H - B" :class="[l.cls, 'la__med']" />
        <text :x="l.x + (l.anchor === 'end' ? -3 : 3)" :y="T - 7" :text-anchor="l.anchor"
              :class="[l.cls, 'la__medtxt']">Me {{ dec(l.m) }}</text>
      </g>
      <rect v-for="i in nBins" :key="'h' + i" :x="sx(X0 + (i - 1) * binW)" :y="T"
            :width="sx(X0 + binW) - sx(X0)" :height="H - T - B" class="la__hit"
            @pointerenter="hover = i - 1" @click="hover = i - 1" />
      <line :x1="L" :x2="W - R" :y1="sy(0)" :y2="sy(0)" class="la__axis" />
    </svg>
    <p class="la__hover" aria-live="polite">{{ hoverText }}</p>

    <div class="la__medhead">Медіани груп на одній осі: стрілка веде від норми до ТБ. Натисніть рядок, щоб показати групу вгорі.</div>
    <svg class="la__svg la__svg--med" viewBox="0 0 340 128" role="img"
         aria-label="Медіани площ норми і ТБ для всіх, жінок і чоловіків">
      <defs>
        <marker id="la-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 z" class="la__arrowhead" />
        </marker>
      </defs>
      <g v-for="t in mTicks" :key="'m' + t">
        <line :x1="mx(t)" :x2="mx(t)" y1="6" y2="112" class="la__grid" />
        <text :x="mx(t)" y="124" text-anchor="middle" class="la__tick">{{ t }}</text>
      </g>
      <g v-for="(g, k) in stats" :key="g.key" class="la__row" :class="{ 'is-on': sex === g.key }"
         @click="sex = g.key">
        <rect x="0" :y="8 + k * 35" width="340" height="32" rx="6" class="la__rowbg" />
        <text x="8" :y="22 + k * 35" class="la__rowname">{{ g.name }}</text>
        <text x="8" :y="34 + k * 35" class="la__rown">{{ g.n0 }} / {{ g.n1 }} знімків</text>
        <line :x1="mx(g.m0)" :x2="mx(g.m1) + (g.m1 > g.m0 ? -6 : 6)" :y1="24 + k * 35" :y2="24 + k * 35"
              class="la__arrow" marker-end="url(#la-arrow)" />
        <circle :cx="mx(g.m0)" :cy="24 + k * 35" r="4.5" class="la__norm" />
        <circle :cx="mx(g.m1)" :cy="24 + k * 35" r="4.5" class="la__tb" />
        <text :x="(mx(g.m0) + mx(g.m1)) / 2" :y="17 + k * 35" text-anchor="middle" class="la__diff"
              :class="g.m1 > g.m0 ? 'is-up' : 'is-down'">{{ signed(diff(g.m0, g.m1)) }}</text>
      </g>
    </svg>
    <div class="la__legend">
      <span><i class="la__dot la__norm" />норма</span>
      <span><i class="la__dot la__tb" />ТБ</span>
      <span>число над стрілкою — медіана ТБ мінус медіана норми, см²; під назвою — знімків норми / ТБ</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ dec(cur.m0) }}</b><span>медіана норми, см² ({{ cur.name }}, n = {{ cur.n0 }})</span></div>
      <div class="lab__stat is-warm"><b>{{ dec(cur.m1) }}</b><span>медіана ТБ, см² ({{ cur.name }}, n = {{ cur.n1 }})</span></div>
      <div class="lab__stat"><b>{{ signed(diff(cur.m0, cur.m1)) }}</b><span>ТБ мінус норма, см²</span></div>
      <div class="lab__stat">
        <b>{{ pct(men.tb, men.nTb) }}</b>
        <span>чоловіків серед ТБ ({{ men.tb }} з {{ men.nTb }}); серед норми — {{ pct(men.norm, men.nNorm) }}</span>
      </div>
    </div>

    <p class="lab__note">
      У рядку «усі» стрілка дивиться праворуч: ТБ більша за норму. У жінок і в чоловіків окремо вона
      дивиться ліворуч. Суперечності немає: у чоловіків легеневі поля більші, а серед знімків ТБ чоловіків
      майже дві третини, серед норми — третина. Так виглядає парадокс Сімпсона.
    </p>
  </div>
</template>

<style scoped>
.la__sep { flex: 0 0 0.6rem; }
.la__pnorm.is-on { border-color: var(--uk-accent); color: var(--uk-accent); background: var(--uk-accent-soft); }
.la__ptb.is-on { border-color: var(--uk-warm); color: var(--uk-warm); background: var(--uk-warm-soft); }
.la__slider { display: block; max-width: 22rem; margin-bottom: 0.6rem; }
.la__svg { display: block; width: 100%; max-width: 560px; height: auto; margin: 0 auto; touch-action: manipulation; }
.la__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.la__axis { stroke: var(--vp-c-text-3); stroke-width: 0.8; }
.la__tick { fill: var(--vp-c-text-3); font-size: 9px; }
.la__lbl { fill: var(--vp-c-text-2); font-size: 9.5px; }
rect.la__norm { fill: var(--uk-accent); fill-opacity: 0.7; }
rect.la__tb { fill: var(--uk-warm); fill-opacity: 0.75; }
circle.la__norm { fill: var(--uk-accent); }
circle.la__tb { fill: var(--uk-warm); }
.la__med { stroke-width: 1.3; stroke-dasharray: 4 3; }
line.la__norm { stroke: var(--uk-accent); }
line.la__tb { stroke: var(--uk-warm); }
.la__medtxt { font-size: 9.5px; font-weight: 600; }
text.la__norm { fill: var(--uk-accent); }
text.la__tb { fill: var(--uk-warm); }
.la__hl { fill: var(--uk-fill); }
.la__hit { fill: transparent; cursor: crosshair; }
.la__hover { font-size: 0.8rem; color: var(--vp-c-text-2); text-align: center; min-height: 1.3em; margin: 0.2rem 0 1rem; }
.la__medhead { font-size: 0.8rem; color: var(--vp-c-text-2); margin-bottom: 0.3rem; }
.la__row { cursor: pointer; }
.la__rowbg { fill: transparent; }
.la__row:hover .la__rowbg { fill: var(--uk-fill); }
.la__row.is-on .la__rowbg { fill: var(--uk-accent-soft); }
.la__rowname { font-size: 10.5px; font-weight: 600; fill: var(--vp-c-text-1); }
.la__rown { font-size: 8.5px; fill: var(--vp-c-text-3); }
.la__arrow { stroke: var(--vp-c-text-2); stroke-width: 1.3; }
.la__arrowhead { fill: var(--vp-c-text-2); }
.la__diff { font-size: 9.5px; font-weight: 600; }
.la__diff.is-up { fill: var(--uk-warm); }
.la__diff.is-down { fill: var(--uk-accent); }
.la__legend {
  display: flex; flex-wrap: wrap; gap: 0.3rem 1rem; justify-content: center;
  font-size: 0.75rem; color: var(--vp-c-text-3); margin-top: 0.3rem;
}
.la__dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 0.3rem; vertical-align: -1px; }
.la__dot.la__norm { background: var(--uk-accent); }
.la__dot.la__tb { background: var(--uk-warm); }
@media (max-width: 480px) {
  .lab.la { padding: 1rem 0.8rem; }
  .la__tick { font-size: 10.5px; }
  .la__lbl, .la__medtxt, .la__diff { font-size: 11px; }
  .la__rowname { font-size: 12px; }
  .la__rown { font-size: 10px; }
}
</style>
