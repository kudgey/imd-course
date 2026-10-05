<script setup lang="ts">
/**
 * Інтервал Вілсона для чутливості залежно від кількості хворих у тесті (лекція 15, розділ «Розмір
 * тестової вибірки обмежує висновки»). Для x знайдених з n хворих:
 * (x + z²/2)/(n + z²) ± z/(n + z²)·√(x(n − x)/n + z²/4), z = 1,96. Пресети — тестова частина Shenzhen
 * і Montgomery при порозі t. Дані: tools/gen_lec15_ci.py (звірено з виводом блоку коду).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec15_ci.json'

type Preset = { label: string; x: number; n: number }
const Z = data.z as number
const PRESETS = data.presets as Preset[]
const TARGET = data.target as number

const n = ref<number>(PRESETS[0].n)
const q = ref<number>(PRESETS[0].x / PRESETS[0].n)
const x = computed(() => Math.round(q.value * n.value))

function wilson(xx: number, nn: number) {
  const mid = (xx + (Z * Z) / 2) / (nn + Z * Z)
  const half = (Z * Math.sqrt((xx * (nn - xx)) / nn + (Z * Z) / 4)) / (nn + Z * Z)
  return { lo: mid - half, hi: mid + half }
}
const ci = computed(() => wilson(x.value, n.value))
const active = computed(() => PRESETS.find(p => p.n === n.value && p.x === x.value) ?? null)
function setPreset(p: Preset) { n.value = p.n; q.value = p.x / p.n }

// ширина інтервалу від кількості хворих при поточній частці
const W = 360
const H = 190
const L = 38
const R = 10
const T = 10
const Bm = 32
const N_MIN = 10
const N_MAX = 500
const XN = (v: number) => L + ((Math.log(v) - Math.log(N_MIN)) / (Math.log(N_MAX) - Math.log(N_MIN))) * (W - L - R)
const YH = (v: number) => T + (1 - v / 0.25) * (H - T - Bm)
const widthPath = computed(() => {
  const pts: string[] = []
  for (let k = 0; k <= 120; k++) {
    const nn = N_MIN * Math.pow(N_MAX / N_MIN, k / 120)
    const xx = q.value * nn
    const w = wilson(xx, nn)
    pts.push(`${k ? 'L' : 'M'}${XN(nn).toFixed(1)},${YH(Math.min(0.25, (w.hi - w.lo) / 2)).toFixed(1)}`)
  }
  return pts.join(' ')
})
// шкала частки для смуги інтервалу
const BX = (v: number) => 12 + ((v - 0.5) / 0.5) * (W - 24)

const dec = (v: number, d: number) => v.toFixed(d).replace('.', ',')
</script>

<template>
  <div class="lab ts">
    <div class="lab__head">
      <div>
        <div class="lab__title">Скільки хворих має бути в тесті</div>
        <div class="lab__sub">
          Задайте кількість хворих n і спостережену чутливість: смуга показує 95-відсотковий інтервал Вілсона,
          графік — його півширину для будь-якого n при тій самій частці.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="p in PRESETS" :key="p.label" type="button" class="lab__pill" :class="{ 'is-on': active?.label === p.label }"
              @click="setPreset(p)">{{ p.label }}: {{ p.x }} з {{ p.n }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>хворих у тесті n = <b>{{ n }}</b></span>
        <input v-model.number="n" type="range" :min="N_MIN" :max="N_MAX" step="1" aria-label="Кількість хворих" />
      </label>
      <label class="lab__ctl">
        <span>спостережена чутливість ≈ <b>{{ dec(q, 2) }}</b> (знайдено x = {{ x }})</span>
        <input v-model.number="q" type="range" min="0.5" max="1" step="0.01" aria-label="Чутливість" />
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} 54`" role="img" aria-label="Інтервал Вілсона">
      <line :x1="BX(0.5)" :x2="BX(1)" y1="30" y2="30" class="ts__axis" />
      <line v-for="v in [0.5, 0.6, 0.7, 0.8, 0.9, 1]" :key="'t' + v" :x1="BX(v)" :x2="BX(v)" y1="27" y2="33" class="ts__axis" />
      <text v-for="v in [0.5, 0.6, 0.7, 0.8, 0.9, 1]" :key="'l' + v" :x="BX(v)" y="46" text-anchor="middle" class="ts__lbl">{{ dec(v, 1) }}</text>
      <line :x1="BX(TARGET)" :x2="BX(TARGET)" y1="8" y2="36" class="ts__target" />
      <rect :x="BX(Math.max(0.5, ci.lo))" y="21" :width="Math.max(1, BX(ci.hi) - BX(Math.max(0.5, ci.lo)))" height="18" rx="3" class="ts__ci" />
      <circle :cx="BX(Math.max(0.5, x / n))" cy="30" r="4.5" class="ts__pt" />
    </svg>

    <div class="ts__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Півширина інтервалу від кількості хворих">
        <line v-for="v in [0, 0.05, 0.1, 0.15, 0.2, 0.25]" :key="'g' + v" :x1="L" :x2="W - R" :y1="YH(v)" :y2="YH(v)" class="ts__grid-l" />
        <text v-for="v in [0, 0.05, 0.1, 0.15, 0.2, 0.25]" :key="'y' + v" :x="L - 4" :y="YH(v) + 3" text-anchor="end" class="ts__lbl">{{ dec(v, 2) }}</text>
        <text v-for="v in [10, 20, 50, 100, 200, 500]" :key="'x' + v" :x="XN(v)" :y="H - Bm + 14" text-anchor="middle" class="ts__lbl">{{ v }}</text>
        <text :x="(L + W - R) / 2" :y="H - 4" text-anchor="middle" class="ts__lbl">хворих у тесті (лог. шкала)</text>
        <path :d="widthPath" class="ts__curve" />
        <circle :cx="XN(n)" :cy="YH(Math.min(0.25, (ci.hi - ci.lo) / 2))" r="4" class="ts__pt" />
      </svg>
      <div class="lab__stats ts__stats">
        <div class="lab__stat"><b>{{ dec(x / n, 3) }}</b><span>чутливість {{ x }} / {{ n }}</span></div>
        <div class="lab__stat" :class="{ 'is-warm': ci.lo < TARGET }"><b>{{ dec(ci.lo, 3) }}</b><span>нижня межа 95 %</span></div>
        <div class="lab__stat"><b>{{ dec(ci.hi, 3) }}</b><span>верхня межа 95 %</span></div>
        <div class="lab__stat"><b>±{{ dec((ci.hi - ci.lo) / 2, 3) }}</b><span>півширина</span></div>
      </div>
    </div>
    <p class="lab__note">Вертикаль на смузі — ціль 0,90. Нижня межа, нижча за ціль, підсвічена: на такому тесті не можна стверджувати,
      що модель досягає цілі, навіть якщо точкова оцінка вища.</p>
  </div>
</template>

<style scoped>
svg { width: 100%; max-width: 560px; height: auto; display: block; }
.ts__grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 1rem; align-items: center; margin-top: 0.6rem; }
@media (max-width: 760px) { .ts__grid { grid-template-columns: 1fr; } }
.ts__stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.ts__axis { stroke: var(--uk-line); stroke-width: 1; }
.ts__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
.ts__target { stroke: var(--uk-warm); stroke-width: 1.4; stroke-dasharray: 3 2; }
.ts__ci { fill: var(--uk-accent); opacity: 0.35; }
.ts__pt { fill: var(--uk-accent); stroke: var(--vp-c-bg); stroke-width: 1; }
.ts__grid-l { stroke: var(--uk-line); stroke-width: 0.6; }
.ts__curve { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
</style>
