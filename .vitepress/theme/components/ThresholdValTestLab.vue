<script setup lang="ts">
/**
 * Поріг на валідаційній і тестовій частинах одночасно (лекція 15, розділ «Поріг обирають на
 * валідаційній вибірці»). Оцінки ResNet-18 схеми S2: валідаційна частина (99 знімків, 50 з ТБ) і
 * тестова (99, 50). Позитив — оцінка ≥ поріг; чутливість = частка знімків ТБ з оцінкою ≥ поріг,
 * специфічність = частка знімків без ТБ з оцінкою < поріг. Позначки: правило курсу на валідаційній
 * частині (t), індекс Юдена на ній, те саме правило на тесті (помилка протоколу), 0,5.
 * Дані: tools/gen_lec15_threshold.py (звірено з виводом блоку коду).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec15_threshold.json'

type Part = { s: number[]; y: number[] }
const VAL = data.val as Part
const TEST = data.test as Part
const M = data.marks as Record<string, number>
const MARKS = [
  { key: 'rule_val', label: 't — правило курсу на валідаційній', cls: 'is-t' },
  { key: 'youden', label: 'індекс Юдена на валідаційній', cls: 'is-y' },
  { key: 'rule_test', label: 'правило «за тестом» (помилка)', cls: 'is-x' },
  { key: 'half', label: '0,5', cls: 'is-h' },
]

const LO = Math.log(0.002 / 0.998)
const HI = Math.log(0.998 / 0.002)
const lg = (p: number) => Math.log(p / (1 - p))
const sig = (z: number) => 1 / (1 + Math.exp(-z))

const z = ref<number>(lg(M.rule_val))
// точне значення позначки: sig(lg(x)) може відрізнятися від x в останньому знаку і «загубити» знімок на порозі
const exact = ref<string | null>('rule_val')
const thr = computed(() => (exact.value ? M[exact.value] : sig(z.value)))
function setMark(key: string) { exact.value = key; z.value = lg(M[key]) }

function rates(p: Part, t: number) {
  let tp = 0, n1 = 0, tn = 0, n0 = 0
  p.s.forEach((v, i) => {
    if (p.y[i] === 1) { n1++; if (v >= t) tp++ } else { n0++; if (v < t) tn++ }
  })
  return { se: tp / n1, sp: tn / n0 }
}
const now = computed(() => ({ val: rates(VAL, thr.value), test: rates(TEST, thr.value) }))
const activeMark = computed(() => MARKS.find(m => m.key === exact.value) ?? null)

const W = 380
const H = 220
const L = 34
const R = 10
const T = 10
const Bm = 34
const X = (zz: number) => L + ((zz - LO) / (HI - LO)) * (W - L - R)
const Y = (v: number) => T + (1 - v) * (H - T - Bm)
const GRID = Array.from({ length: 241 }, (_, i) => LO + ((HI - LO) * i) / 240)
const curve = (p: Part, key: 'se' | 'sp') =>
  GRID.map((zz, i) => `${i ? 'L' : 'M'}${X(zz).toFixed(1)},${Y(rates(p, sig(zz))[key]).toFixed(1)}`).join(' ')
const CURVES = [
  { d: curve(VAL, 'se'), cls: 'tv__val' }, { d: curve(VAL, 'sp'), cls: 'tv__val tv__dash' },
  { d: curve(TEST, 'se'), cls: 'tv__test' }, { d: curve(TEST, 'sp'), cls: 'tv__test tv__dash' },
]
const XT = [0.01, 0.05, 0.2, 0.5, 0.8, 0.95, 0.99]

const dec = (v: number, d: number) => v.toFixed(d).replace('.', ',')
const thrText = computed(() => dec(thr.value, thr.value < 0.1 || thr.value > 0.9 ? 4 : 3))
</script>

<template>
  <div class="lab tv">
    <div class="lab__head">
      <div>
        <div class="lab__title">Поріг на валідаційній і тестовій частинах</div>
        <div class="lab__sub">
          Суцільні лінії — чутливість, пунктир — специфічність; зелене — валідаційна частина, жовте — тестова.
          Рухайте поріг або натискайте позначки: поріг вибирають за валідаційними кривими, тестові лише перевіряють вибір.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="m in MARKS" :key="m.key" type="button" class="lab__pill" :class="{ 'is-on': activeMark?.key === m.key }"
              @click="setMark(m.key)">{{ m.label }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поріг оцінки (вісь у логітах) = <b>{{ thrText }}</b></span>
        <input v-model.number="z" type="range" :min="LO" :max="HI" step="0.01" aria-label="Поріг" @input="exact = null" />
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Чутливість і специфічність залежно від порогу">
      <line v-for="v in [0, 0.25, 0.5, 0.75, 1]" :key="'g' + v" :x1="L" :x2="W - R" :y1="Y(v)" :y2="Y(v)" class="tv__grid" />
      <line :x1="L" :x2="W - R" :y1="Y(0.9)" :y2="Y(0.9)" class="tv__target" />
      <text :x="W - R" :y="Y(0.9) - 3" text-anchor="end" class="tv__lbl tv__lbl--warm">0,90</text>
      <text v-for="v in [0, 0.5, 1]" :key="'y' + v" :x="L - 4" :y="Y(v) + 3" text-anchor="end" class="tv__lbl">{{ dec(v, 1) }}</text>
      <text v-for="p in XT" :key="'x' + p" :x="X(lg(p))" :y="H - Bm + 14" text-anchor="middle" class="tv__lbl">{{ dec(p, 2) }}</text>
      <text :x="(L + W - R) / 2" :y="H - 4" text-anchor="middle" class="tv__lbl">поріг оцінки</text>
      <path v-for="(c, k) in CURVES" :key="k" :d="c.d" :class="c.cls" />
      <line v-for="m in MARKS" :key="'m' + m.key" :x1="X(lg(M[m.key]))" :x2="X(lg(M[m.key]))" :y1="Y(1)" :y2="Y(0)"
            class="tv__mark" :class="m.cls" />
      <line :x1="X(z)" :x2="X(z)" :y1="Y(1.02)" :y2="Y(0)" class="tv__cur" />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat" :class="{ 'is-warm': now.val.se < 0.9 }"><b>{{ dec(now.val.se, 3) }}</b><span>чутливість, валідаційна</span></div>
      <div class="lab__stat"><b>{{ dec(now.val.sp, 3) }}</b><span>специфічність, валідаційна</span></div>
      <div class="lab__stat" :class="{ 'is-warm': now.test.se < 0.9 }"><b>{{ dec(now.test.se, 3) }}</b><span>чутливість, тестова</span></div>
      <div class="lab__stat"><b>{{ dec(now.test.sp, 3) }}</b><span>специфічність, тестова</span></div>
    </div>
    <p class="lab__note">Вертикалі: t (суцільна), індекс Юдена (штрих), «за тестом» (червона), 0,5 (точки). Чутливість нижче
      цілі 0,90 підсвічено.</p>
  </div>
</template>

<style scoped>
svg { width: 100%; max-width: 560px; height: auto; display: block; }
.tv__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.tv__target { stroke: var(--uk-warm); stroke-width: 1; stroke-dasharray: 3 3; }
.tv__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
.tv__lbl--warm { fill: var(--uk-warm); }
.tv__val { fill: none; stroke: #1baf7a; stroke-width: 2; }
.tv__test { fill: none; stroke: #eda100; stroke-width: 2; }
.tv__dash { stroke-dasharray: 5 3; stroke-width: 1.6; }
.tv__mark { stroke: var(--vp-c-text-2); stroke-width: 1; opacity: 0.7; }
.tv__mark.is-y { stroke-dasharray: 6 3; }
.tv__mark.is-x { stroke: var(--uk-warm); }
.tv__mark.is-h { stroke-dasharray: 1 3; }
.tv__cur { stroke: var(--vp-c-text-1); stroke-width: 1.6; }
</style>
