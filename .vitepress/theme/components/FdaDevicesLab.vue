<script setup lang="ts">
/**
 * Перелік FDA «AI-Enabled Medical Devices» за роками рішення (лекція 01, розділ «Дозволені
 * системи ШІ: що показує перелік FDA»). Дані — таблиця «провідна панель × рік» зі знімка CSV
 * (tools/gen_lec01_fda.py). За замовчуванням — усі панелі й усі роки: 1 614 пристроїв,
 * Radiology 1 230 (76,2 %), 18 рішень у 2016 і 335 у 2025 році — як у виводі блоку коду 6.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec01_fda.json'

type Mode = 'all' | 'rad' | 'other'

const YEARS = data.years as number[]
const PANELS = data.panels as string[]
const COUNTS = data.counts as number[][]
const RAD = PANELS.indexOf('Radiology')
const Y_FIRST = YEARS[0]
const Y_LAST = YEARS[YEARS.length - 1]
const snapshot = (data.snapshot as string).split('-').reverse().join('.')
const lastDecision = data.last_decision as string

const PER_YEAR = YEARS.map((year, i) => {
  const all = COUNTS.reduce((s, row) => s + row[i], 0)
  const rad = COUNTS[RAD][i]
  return { year, i, all, rad, other: all - rad }
})

const mode = ref<Mode>('all')
const lo = ref<number>(Y_FIRST)
const hi = ref<number>(Y_LAST)
const hover = ref<number | null>(null) // рік під курсором

// повзунки «від» і «до» не розминаються: той, що рухають, тягне інший за собою
const loModel = computed<number>({
  get: () => lo.value,
  set: v => {
    lo.value = v
    if (v > hi.value) hi.value = v
  },
})
const hiModel = computed<number>({
  get: () => hi.value,
  set: v => {
    hi.value = v
    if (v < lo.value) lo.value = v
  },
})

const shown = computed(() => PER_YEAR.filter(r => r.year >= lo.value && r.year <= hi.value))
const value = (r: { all: number; rad: number; other: number }) =>
  mode.value === 'all' ? r.all : mode.value === 'rad' ? r.rad : r.other

const totals = computed(() => {
  const s = shown.value
  const all = s.reduce((a, r) => a + r.all, 0)
  const rad = s.reduce((a, r) => a + r.rad, 0)
  const peak = s.reduce((best, r) => (value(r) > value(best) ? r : best), s[0])
  return { all, rad, other: all - rad, sel: s.reduce((a, r) => a + value(r), 0), peak }
})

function plural(n: number): string {
  const d = n % 10
  const dd = n % 100
  if (d === 1 && dd !== 11) return 'панель'
  if (d >= 2 && d <= 4 && (dd < 12 || dd > 14)) return 'панелі'
  return 'панелей'
}

const panelsInRange = computed(() => {
  const idx = shown.value.map(r => r.i)
  // список панелей іде за фільтром: «лише Radiology» — один рядок, «усі, крім Radiology» — без неї
  const rows = PANELS.map((name, p) => ({ name, n: idx.reduce((a, i) => a + COUNTS[p][i], 0) }))
    .filter(r => r.n > 0 && (mode.value === 'all' || (mode.value === 'rad') === (r.name === 'Radiology')))
    .sort((a, b) => b.n - a.n)
  const top = rows.slice(0, 5)
  const rest = rows.slice(5)
  if (rest.length) top.push({ name: `інші ${rest.length} ${plural(rest.length)}`, n: rest.reduce((a, r) => a + r.n, 0) })
  return top
})
const panelMax = computed(() => Math.max(1, ...panelsInRange.value.map(r => r.n)))

// діаграма: viewBox 340 × 206
const W = 340, H = 206, L = 34, R = 8, T = 14, B = 34
const yMax = computed(() => {
  const m = Math.max(1, ...shown.value.map(value))
  const step = m > 200 ? 100 : m > 100 ? 50 : m > 40 ? 20 : m > 10 ? 5 : 2
  return Math.ceil(m / step) * step
})
const yTicks = computed(() => {
  const m = yMax.value
  const step = m > 200 ? 100 : m > 100 ? 50 : m > 40 ? 20 : m > 10 ? 5 : 2
  return Array.from({ length: m / step + 1 }, (_, k) => k * step)
})
const slot = computed(() => (W - L - R) / shown.value.length)
const sy = (c: number) => H - B - (c / yMax.value) * (H - T - B)
const bx = (k: number) => L + k * slot.value + slot.value * 0.12
const bw = computed(() => slot.value * 0.76)
const labelStep = computed(() => {
  const n = shown.value.length
  return n <= 8 ? 1 : n <= 16 ? 2 : 5
})

const hoverRow = computed(() => shown.value.find(r => r.year === hover.value) ?? null)

const NB = ' '
const int = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, NB)
const pct = (a: number, b: number) => (b ? ((100 * a) / b).toFixed(1).replace('.', ',') + NB + '%' : '—')

const hoverText = computed(() => {
  const r = hoverRow.value
  if (!r) return 'Наведіть курсор на стовпець або торкніться його: рік, кількість рішень і частка радіології.'
  const tail = r.year === Y_LAST ? ` (рік неповний: рішення до ${lastDecision})` : ''
  if (mode.value === 'other') return `${r.year}: інших панелей ${int(r.other)} із ${int(r.all)} рішень${tail}`
  return `${r.year}: ${int(r.all)} рішень, із них Radiology ${int(r.rad)} (${pct(r.rad, r.all)})${tail}`
})
const selLabel = computed(() =>
  mode.value === 'all' ? 'пристроїв у вибраних роках' : mode.value === 'rad' ? 'пристроїв із панеллю Radiology' : 'пристроїв інших панелей')

function setRange(a: number, b: number) {
  lo.value = a
  hi.value = b
}
</script>

<template>
  <div class="lab fd">
    <div class="lab__head">
      <div>
        <div class="lab__title">Перелік FDA: дозволені пристрої з ШІ за роками</div>
        <div class="lab__sub">
          Знімок переліку {{ snapshot }}, рішення {{ Y_FIRST }}–{{ lastDecision }}. Оберіть провідну панель
          і діапазон років; наведіть курсор на стовпець, щоб побачити рік, кількість рішень і частку
          радіології.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': mode === 'all' }" @click="mode = 'all'">усі панелі</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': mode === 'rad' }" @click="mode = 'rad'">лише Radiology</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': mode === 'other' }" @click="mode = 'other'">усі, крім Radiology</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Від року <b>{{ lo }}</b></span>
        <input v-model.number="loModel" type="range" :min="Y_FIRST" :max="Y_LAST" step="1" aria-label="Від року" />
      </label>
      <label class="lab__ctl">
        <span>До року <b>{{ hi }}</b></span>
        <input v-model.number="hiModel" type="range" :min="Y_FIRST" :max="Y_LAST" step="1" aria-label="До року" />
      </label>
    </div>
    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': lo === Y_FIRST && hi === Y_LAST }"
              @click="setRange(Y_FIRST, Y_LAST)">увесь перелік</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': lo === 2016 && hi === 2025 }"
              @click="setRange(2016, 2025)">2016–2025, повні роки</button>
    </div>

    <svg class="fd__svg" :viewBox="`0 0 ${W} ${H}`" role="img"
         :aria-label="`Рішення FDA за роками ${lo}–${hi}: ${totals.sel} пристроїв`" @pointerleave="hover = null">
      <g v-for="t in yTicks" :key="'y' + t">
        <line :x1="L" :x2="W - R" :y1="sy(t)" :y2="sy(t)" class="fd__grid" />
        <text :x="L - 4" :y="sy(t) + 3" text-anchor="end" class="fd__tick">{{ t }}</text>
      </g>
      <g v-for="(r, k) in shown" :key="r.year">
        <rect v-if="hover === r.year" :x="L + k * slot" :y="T" :width="slot" :height="H - T - B" class="fd__hl" />
        <template v-if="mode === 'all'">
          <rect :x="bx(k)" :y="sy(r.rad)" :width="bw" :height="sy(0) - sy(r.rad)" class="fd__rad"
                :class="{ 'is-partial': r.year === Y_LAST }" />
          <rect :x="bx(k)" :y="sy(r.all)" :width="bw" :height="sy(r.rad) - sy(r.all)" class="fd__other"
                :class="{ 'is-partial': r.year === Y_LAST }" />
        </template>
        <rect v-else :x="bx(k)" :y="sy(value(r))" :width="bw" :height="sy(0) - sy(value(r))"
              :class="[mode === 'rad' ? 'fd__rad' : 'fd__other', { 'is-partial': r.year === Y_LAST }]" />
        <text v-if="r.year % labelStep === 0 || shown.length === 1" :x="L + (k + 0.5) * slot" :y="H - B + 13"
              text-anchor="middle" class="fd__tick">{{ r.year }}</text>
        <rect :x="L + k * slot" :y="T" :width="slot" :height="H - T - B" class="fd__hit"
              @pointerenter="hover = r.year" @click="hover = r.year" />
      </g>
      <line :x1="L" :x2="W - R" :y1="sy(0)" :y2="sy(0)" class="fd__axis" />
      <text :x="(L + W - R) / 2" :y="H - 3" text-anchor="middle" class="fd__lbl">рік рішення FDA</text>
    </svg>
    <p class="fd__hover" aria-live="polite">{{ hoverText }}</p>
    <div class="fd__legend">
      <span v-if="mode !== 'other'"><i class="fd__sw fd__rad" />провідна панель Radiology</span>
      <span v-if="mode !== 'rad'"><i class="fd__sw fd__other" />інші панелі</span>
      <span v-if="hi === Y_LAST"><i class="fd__sw fd__rad is-partial" />{{ Y_LAST }} — рішення до {{ lastDecision }}</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ int(totals.sel) }}</b><span>{{ selLabel }}, {{ lo }}–{{ hi }}</span></div>
      <div class="lab__stat is-warm"><b>{{ pct(totals.rad, totals.all) }}</b><span>частка Radiology серед {{ int(totals.all) }} пристроїв цих років</span></div>
      <div class="lab__stat"><b>{{ int(value(totals.peak)) }}</b><span>найбільше за рік: {{ totals.peak.year }}</span></div>
    </div>

    <div class="fd__panels">
      <div class="fd__phead">Провідні панелі в {{ lo }}–{{ hi }} роках</div>
      <div v-for="p in panelsInRange" :key="p.name" class="lab__row fd__prow"
           :class="{ 'is-rad': p.name === 'Radiology' }">
        <span class="lab__label fd__pname" :title="p.name">{{ p.name }}</span>
        <span class="lab__bar"><i :style="{ width: (100 * p.n) / panelMax + '%' }" /></span>
        <span class="lab__num">{{ int(p.n) }}</span>
      </div>
    </div>

    <p class="lab__note">
      Присутність у переліку — це дозвіл на ринок США, а не доказ користі для пацієнтів. Звузьте роки до
      2016–2025 і наведіть курсор на крайні стовпці: 18 рішень у 2016 році проти 335 у 2025-му, і більшість
      щороку — радіологія. Перемкніть «усі, крім Radiology», щоб побачити, які панелі ростуть поза нею.
    </p>
  </div>
</template>

<style scoped>
.fd__svg { display: block; width: 100%; max-width: 580px; height: auto; margin: 0.3rem auto 0; touch-action: manipulation; }
.fd__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.fd__axis { stroke: var(--vp-c-text-3); stroke-width: 0.8; }
.fd__tick { fill: var(--vp-c-text-3); font-size: 9px; }
.fd__lbl { fill: var(--vp-c-text-2); font-size: 9.5px; }
.fd__rad { fill: var(--uk-accent); }
.fd__other { fill: var(--uk-accent); fill-opacity: 0.32; }
rect.is-partial { fill-opacity: 0.45; stroke: var(--uk-accent); stroke-width: 0.8; stroke-dasharray: 2 1.5; }
rect.fd__other.is-partial { fill-opacity: 0.16; }
.fd__hl { fill: var(--uk-fill); }
.fd__hit { fill: transparent; cursor: crosshair; }
.fd__hover { font-size: 0.8rem; color: var(--vp-c-text-2); text-align: center; min-height: 1.3em; margin: 0.2rem 0 0.2rem; }
.fd__legend {
  display: flex; flex-wrap: wrap; gap: 0.3rem 1rem; justify-content: center;
  font-size: 0.75rem; color: var(--vp-c-text-3); margin-bottom: 0.4rem;
}
.fd__sw { display: inline-block; width: 11px; height: 9px; margin-right: 0.3rem; vertical-align: -1px; }
.fd__sw.fd__rad { background: var(--uk-accent); }
.fd__sw.fd__other { background: var(--uk-accent); opacity: 0.32; }
.fd__sw.is-partial { opacity: 0.45; outline: 1px dashed var(--uk-accent); }
.fd__panels { margin-top: 1rem; }
.fd__phead { font-size: 0.8rem; color: var(--vp-c-text-2); margin-bottom: 0.3rem; }
.fd__pname { flex: 0 0 11.5rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fd__prow .lab__num { flex: 0 0 3rem; }
.fd__prow.is-rad .lab__bar i { background: var(--uk-accent); }
.fd__prow:not(.is-rad) .lab__bar i { background: var(--uk-accent); opacity: 0.4; }
@media (max-width: 480px) {
  .lab.fd { padding: 1rem 0.8rem; }
  .fd__tick { font-size: 10.5px; }
  .fd__lbl { font-size: 11px; }
  .fd__pname { flex-basis: 8.5rem; }
}
</style>
