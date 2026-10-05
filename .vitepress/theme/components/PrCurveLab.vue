<script setup lang="ts">
/**
 * ROC- і PR-крива тієї самої моделі за різної поширеності (лекція 15, розділ «PR-крива і середня
 * влучність (AP)»). Оцінки ResNet-18 схеми S2 на 99 знімках тестової частини; знімки без ТБ
 * перезважено до поширеності π вагою w = (1 − π)/π · n₊/n₋. AUC — площа під зваженою ROC-кривою
 * (трапеції, нічиї — навпіл), AP = Σ (R_k − R_{k−1})·P_k — як roc_auc_score і average_precision_score
 * зі sample_weight. Дані: tools/gen_lec15_pr.py (звірено зі scikit-learn і з виводом блоку коду).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec15_pr.json'

const S = data.s as number[]
const Yl = data.y as number[]
const TT = data.t as number
const NPOS = Yl.reduce((a, v) => a + v, 0)
const NNEG = Yl.length - NPOS
const PI0 = NPOS / Yl.length
const P_MIN = 0.005
const P_MAX = 0.6
const PRESETS = [
  { label: 'тестова частина, 50,5 %', p: PI0 },
  { label: 'triage, 15,3 %', p: 0.153 },
  { label: 'сценарій 1 %', p: 0.01 },
]

const prev = ref<number>(PI0)
const pos = computed<number>({
  get: () => Math.round((1000 * Math.log(prev.value / P_MIN)) / Math.log(P_MAX / P_MIN)),
  set: (v: number) => { prev.value = P_MIN * Math.pow(P_MAX / P_MIN, v / 1000) },
})

const order = S.map((_, i) => i).sort((a, b) => S[b] - S[a] || a - b)

const res = computed(() => {
  const p = prev.value
  const wNeg = ((1 - p) / p) * (NPOS / NNEG)
  const P = NPOS
  const N = NNEG * wNeg
  let tp = 0, fp = 0, auc = 0, ap = 0, rPrev = 0
  const roc: [number, number][] = [[0, 0]]
  const pr: [number, number][] = []
  let atT: { fpr: number; tpr: number; prec: number } | null = null
  let i = 0
  while (i < order.length) {
    let j = i
    let dtp = 0, dfp = 0
    while (j < order.length && S[order[j]] === S[order[i]]) {
      if (Yl[order[j]] === 1) dtp += 1
      else dfp += wNeg
      j++
    }
    auc += (dfp / N) * (tp + dtp / 2) / P
    tp += dtp; fp += dfp
    const rec = tp / P
    const prec = tp / (tp + fp)
    ap += (rec - rPrev) * prec
    rPrev = rec
    roc.push([fp / N, tp / P]); pr.push([rec, prec])
    if (S[order[i]] >= TT) atT = { fpr: fp / N, tpr: tp / P, prec }
    i = j
  }
  return { auc, ap, roc, pr, atT: atT as { fpr: number; tpr: number; prec: number } }
})

const SZ = 200
const PAD = 30
const X = (v: number) => PAD + v * (SZ - PAD - 8)
const Y = (v: number) => SZ - PAD + 4 - v * (SZ - PAD - 4)
const line = (pts: [number, number][], step: boolean) => pts.map(([x, y], k) => {
  if (k === 0) return `M${X(x).toFixed(1)},${Y(y).toFixed(1)}`
  return step ? `H${X(x).toFixed(1)}V${Y(y).toFixed(1)}` : `L${X(x).toFixed(1)},${Y(y).toFixed(1)}`
}).join(' ')
const prPath = computed(() => line([[0, res.value.pr[0][1]], ...res.value.pr], true))

const NB = ' '
const dec = (v: number, d: number) => v.toFixed(d).replace('.', ',')
const pct = (v: number) => dec(100 * v, v < 0.1 ? 2 : 1) + NB + '%'
</script>

<template>
  <div class="lab prc">
    <div class="lab__head">
      <div>
        <div class="lab__title">ROC проти PR: що змінює поширеність</div>
        <div class="lab__sub">
          Ті самі 99 оцінок тестової частини; знімки без ТБ перезважено так, ніби хворих серед обстежених — π.
          ROC-крива рахується окремо серед хворих і серед здорових, тож від π не залежить; PR-крива — залежить.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="p in PRESETS" :key="p.label" type="button" class="lab__pill"
              :class="{ 'is-on': Math.abs(prev - p.p) < 1e-12 }" @click="prev = p.p">{{ p.label }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поширеність π (логарифмічна шкала 0,5–60 %) = <b>{{ pct(prev) }}</b></span>
        <input v-model.number="pos" type="range" min="0" max="1000" step="1" aria-label="Поширеність" />
      </label>
    </div>

    <div class="prc__grid">
      <figure class="prc__fig">
        <svg :viewBox="`0 0 ${SZ} ${SZ}`" role="img" aria-label="ROC-крива">
          <line :x1="X(0)" :y1="Y(0)" :x2="X(1)" :y2="Y(1)" class="prc__diag" />
          <path :d="line(res.roc, false)" class="prc__curve" />
          <circle :cx="X(res.atT.fpr)" :cy="Y(res.atT.tpr)" r="3.5" class="prc__pt" />
          <line :x1="X(0)" :x2="X(1)" :y1="Y(0)" :y2="Y(0)" class="prc__axis" />
          <line :x1="X(0)" :x2="X(0)" :y1="Y(0)" :y2="Y(1)" class="prc__axis" />
          <text v-for="v in [0, 0.5, 1]" :key="'rx' + v" :x="X(v)" :y="SZ - 14" text-anchor="middle" class="prc__lbl">{{ dec(v, 1) }}</text>
          <text v-for="v in [0.5, 1]" :key="'ry' + v" :x="PAD - 4" :y="Y(v) + 3" text-anchor="end" class="prc__lbl">{{ dec(v, 1) }}</text>
          <text :x="X(0.5)" :y="SZ - 2" text-anchor="middle" class="prc__lbl">1 − специфічність</text>
        </svg>
        <figcaption>ROC: AUC {{ dec(res.auc, 4) }}</figcaption>
      </figure>
      <figure class="prc__fig">
        <svg :viewBox="`0 0 ${SZ} ${SZ}`" role="img" aria-label="PR-крива">
          <line :x1="X(0)" :x2="X(1)" :y1="Y(prev)" :y2="Y(prev)" class="prc__diag" />
          <path :d="prPath" class="prc__curve prc__curve--pr" />
          <circle :cx="X(res.atT.tpr)" :cy="Y(res.atT.prec)" r="3.5" class="prc__pt" />
          <line :x1="X(0)" :x2="X(1)" :y1="Y(0)" :y2="Y(0)" class="prc__axis" />
          <line :x1="X(0)" :x2="X(0)" :y1="Y(0)" :y2="Y(1)" class="prc__axis" />
          <text v-for="v in [0, 0.5, 1]" :key="'px' + v" :x="X(v)" :y="SZ - 14" text-anchor="middle" class="prc__lbl">{{ dec(v, 1) }}</text>
          <text v-for="v in [0.5, 1]" :key="'py' + v" :x="PAD - 4" :y="Y(v) + 3" text-anchor="end" class="prc__lbl">{{ dec(v, 1) }}</text>
          <text :x="X(0.5)" :y="SZ - 2" text-anchor="middle" class="prc__lbl">повнота (чутливість)</text>
        </svg>
        <figcaption>PR: AP {{ dec(res.ap, 4) }}; пунктир — базова лінія π</figcaption>
      </figure>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ dec(res.auc, 4) }}</b><span>AUC (не залежить від π)</span></div>
      <div class="lab__stat" :class="{ 'is-warm': res.ap < 0.5 }"><b>{{ dec(res.ap, 4) }}</b><span>AP</span></div>
      <div class="lab__stat"><b>{{ dec(res.atT.prec, 4) }}</b><span>влучність (PPV) при порозі t</span></div>
      <div class="lab__stat"><b>{{ dec(res.atT.tpr, 3) }}</b><span>повнота при порозі t</span></div>
    </div>
    <p class="lab__note">Кружок — поріг t = {{ dec(TT, 4) }}. Числа при π нижче кількох відсотків грубі: у тесті лише {{ NNEG }} знімків
      без ТБ, і кожен після перезважування представляє близько 2 % усіх здорових.</p>
  </div>
</template>

<style scoped>
.prc__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; }
@media (max-width: 560px) { .prc__grid { grid-template-columns: 1fr; } }
.prc__fig { margin: 0; }
.prc__fig figcaption { font-size: 0.8rem; color: var(--vp-c-text-2); text-align: center; }
svg { width: 100%; max-width: 300px; height: auto; display: block; margin: 0 auto; }
.prc__diag { stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 4 3; }
.prc__curve { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
.prc__curve--pr { stroke: var(--uk-warm); }
.prc__pt { fill: var(--vp-c-bg); stroke: var(--vp-c-text-1); stroke-width: 1.6; }
.prc__axis { stroke: var(--uk-line); }
.prc__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
</style>
