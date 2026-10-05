<script setup lang="ts">
/**
 * PPV і NPV моделі курсу залежно від поширеності (лекція 15, розділ «PPV і NPV залежать від поширеності»).
 * Чутливість і специфічність — ResNet-18 схеми S2 на тестовій частині при порозі t (правило курсу на
 * валідаційній частині) або при порозі 0,5. PPV = чутл.·π / (чутл.·π + (1 − спец.)(1 − π)),
 * NPV = спец.(1 − π) / (спец.(1 − π) + (1 − чутл.)π), кількості — на 1000 обстежених.
 * Дані й пресети: tools/gen_lec15_ppv.py (звірено з виводом блоку коду).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec15_ppv.json'

type Op = { key: string; label: string; thr: number; se: number; sp: number }
type Preset = { key: string; p: number; label: string; note: string }
const OPS = data.ops as Op[]
const PRESETS = data.presets as Preset[]
const P_MIN = 0.001
const P_MAX = 0.6

const opKey = ref<string>('t')
const prev = ref<number>(0.01)
const op = computed(() => OPS.find(o => o.key === opKey.value) as Op)

const pos = computed<number>({
  get: () => Math.round((1000 * Math.log(prev.value / P_MIN)) / Math.log(P_MAX / P_MIN)),
  set: (v: number) => { prev.value = P_MIN * Math.pow(P_MAX / P_MIN, v / 1000) },
})
const preset = computed(() => PRESETS.find(p => Math.abs(p.p - prev.value) < 1e-12) ?? null)

function bayes(se: number, sp: number, p: number) {
  const ppv = (se * p) / (se * p + (1 - sp) * (1 - p))
  const npv = (sp * (1 - p)) / (sp * (1 - p) + (1 - se) * p)
  return { ppv, npv, tp: 1000 * p * se, fp: 1000 * (1 - p) * (1 - sp), fn: 1000 * p * (1 - se) }
}
const res = computed(() => bayes(op.value.se, op.value.sp, prev.value))

const W = 360
const H = 210
const L = 38
const R = 10
const T = 10
const Bm = 34
const X = (p: number) => L + ((Math.log10(p) - Math.log10(P_MIN)) / (Math.log10(P_MAX) - Math.log10(P_MIN))) * (W - L - R)
const Y = (v: number) => T + (1 - v) * (H - T - Bm)
const GRID = Array.from({ length: 121 }, (_, i) => P_MIN * Math.pow(P_MAX / P_MIN, i / 120))
const path = (key: 'ppv' | 'npv') => GRID.map((p, i) => `${i ? 'L' : 'M'}${X(p).toFixed(1)},${Y(bayes(op.value.se, op.value.sp, p)[key]).toFixed(1)}`).join(' ')
const XT = [0.001, 0.01, 0.1, 0.6]

const NB = ' '
const dec = (v: number, d: number) => v.toFixed(d).replace('.', ',')
const pct = (v: number) => dec(100 * v, v < 0.01 ? 3 : v < 0.1 ? 2 : 1) + NB + '%'
const xLab = (p: number) => (p < 0.01 ? dec(100 * p, 1) : String(Math.round(100 * p))) + NB + '%'
</script>

<template>
  <div class="lab pp">
    <div class="lab__head">
      <div>
        <div class="lab__title">Та сама модель за різної поширеності</div>
        <div class="lab__sub">
          Чутливість і специфічність виміряно на тестовій частині (99 знімків, 50 з ТБ) і не змінюються.
          Рухайте поширеність π: PPV і NPV перераховуються за теоремою Баєса, кількості — на 1000 обстежених.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="o in OPS" :key="o.key" type="button" class="lab__pill" :class="{ 'is-on': opKey === o.key }"
              @click="opKey = o.key">{{ o.label }}: {{ dec(o.se, 3) }} / {{ dec(o.sp, 3) }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="p in PRESETS" :key="p.key" type="button" class="lab__pill"
              :class="{ 'is-on': preset?.key === p.key }" @click="prev = p.p">{{ p.label }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поширеність π (логарифмічна шкала 0,1–60 %) = <b>{{ pct(prev) }}</b></span>
        <input v-model.number="pos" type="range" min="0" max="1000" step="1" aria-label="Поширеність" />
      </label>
    </div>
    <p v-if="preset" class="lab__note pp__note">{{ preset.label }} — {{ preset.note }}.</p>

    <div class="pp__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="PPV і NPV залежно від поширеності">
        <line v-for="v in [0, 0.25, 0.5, 0.75, 1]" :key="'g' + v" :x1="L" :x2="W - R" :y1="Y(v)" :y2="Y(v)" class="pp__grid-l" />
        <text v-for="v in [0, 0.5, 1]" :key="'y' + v" :x="L - 5" :y="Y(v) + 3" text-anchor="end" class="pp__lbl">{{ dec(v, 1) }}</text>
        <text v-for="p in XT" :key="'x' + p" :x="X(p)" :y="H - Bm + 14" text-anchor="middle" class="pp__lbl">{{ xLab(p) }}</text>
        <text :x="(L + W - R) / 2" :y="H - 4" text-anchor="middle" class="pp__lbl">поширеність π</text>
        <line v-for="p in PRESETS" :key="'p' + p.key" :x1="X(p.p)" :x2="X(p.p)" :y1="Y(0)" :y2="Y(0) - 5" class="pp__tick" />
        <path :d="path('npv')" class="pp__npv" />
        <path :d="path('ppv')" class="pp__ppv" />
        <line :x1="X(prev)" :x2="X(prev)" :y1="Y(1)" :y2="Y(0)" class="pp__cur" />
        <circle :cx="X(prev)" :cy="Y(res.ppv)" r="4" class="pp__dot-ppv" />
        <circle :cx="X(prev)" :cy="Y(res.npv)" r="4" class="pp__dot-npv" />
      </svg>
      <div class="pp__legend">
        <p><span class="pp__sw pp__sw--ppv" /> PPV — частка хворих серед позитивних результатів.</p>
        <p><span class="pp__sw pp__sw--npv" /> NPV — частка здорових серед негативних.</p>
        <p>Риски внизу — пресети. Що нижча поширеність, то більша частка позитивних результатів припадає на
          хибні тривоги, а NPV наближається до одиниці.</p>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat" :class="{ 'is-warm': res.ppv < 0.1 }"><b>{{ dec(res.ppv, 4) }}</b><span>PPV</span></div>
      <div class="lab__stat"><b>{{ dec(res.npv, 4) }}</b><span>NPV</span></div>
      <div class="lab__stat"><b>{{ dec(res.tp, 1) }}</b><span>знайдено хворих на 1000 (TP)</span></div>
      <div class="lab__stat"><b>{{ dec(res.fp, 0) }}</b><span>хибних тривог на 1000 (FP)</span></div>
      <div class="lab__stat"><b>{{ dec(res.fn, 2) }}</b><span>пропусків на 1000 (FN)</span></div>
      <div class="lab__stat" :class="{ 'is-warm': res.fp / res.tp > 10 }"><b>{{ dec(res.fp / res.tp, 1) }}</b><span>хибних тривог на одного знайденого</span></div>
    </div>
  </div>
</template>

<style scoped>
.pp__grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
@media (max-width: 760px) { .pp__grid { grid-template-columns: 1fr; } }
svg { width: 100%; max-width: 420px; height: auto; display: block; }
.pp__note { margin-top: 0.2rem; }
.pp__grid-l { stroke: var(--uk-line); stroke-width: 0.6; }
.pp__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
.pp__tick { stroke: var(--vp-c-text-2); stroke-width: 1.2; }
.pp__ppv { fill: none; stroke: var(--uk-accent); stroke-width: 2.2; }
.pp__npv { fill: none; stroke: var(--uk-warm); stroke-width: 2; stroke-dasharray: 5 3; }
.pp__cur { stroke: var(--vp-c-text-2); stroke-width: 1; stroke-dasharray: 2 2; }
.pp__dot-ppv { fill: var(--uk-accent); stroke: var(--vp-c-bg); stroke-width: 1; }
.pp__dot-npv { fill: var(--uk-warm); stroke: var(--vp-c-bg); stroke-width: 1; }
.pp__legend { font-size: 0.8rem; color: var(--vp-c-text-2); line-height: 1.5; }
.pp__legend p { margin: 0.3rem 0; }
.pp__sw { display: inline-block; width: 16px; height: 3px; margin-right: 5px; vertical-align: 3px; }
.pp__sw--ppv { background: var(--uk-accent); }
.pp__sw--npv { background: var(--uk-warm); }
</style>
