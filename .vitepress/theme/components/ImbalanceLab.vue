<script setup lang="ts">
/**
 * Дисбаланс класів і його компенсація (лекція 08, розділ «Зважена функція втрат і зважений семплінг»).
 * Ознаки xrv DenseNet-121 + логістична регресія (C = 0,001); у навчальній частині S1 лишається частка ТБ
 * 49 % (усі знімки) або 30…5 % (10 випадкових підвибірок знімків ТБ); способи: без ваг, зважена втрата
 * w₊ = N₋/N₊, дублювання знімків ТБ до рівних часток. Тест S1 (162 знімки, 50 % ТБ) не змінюється.
 * Віджет рахує чутливість і специфічність за обраним порогом з імовірностей кожної підвибірки й
 * усереднює; при порозі 0,5 числа збігаються з таблицею блоку коду. Дані: tools/gen_lec08_imbalance.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec08_imbalance.json'

type Run = { auc: number; p: number[] }
type Cell = { pct: number; n_pos: number; n_neg: number; w: number; runs: Record<string, Run[]> }
const cells = data.cells as Cell[]
const y = data.y as number[]
const SCALE = data.scale as number
const METHODS = ['без ваг', 'зважена втрата', 'дублювання ТБ']

const ci = ref(cells.findIndex((c) => c.pct === 10))
const method = ref('без ваг')
const thr = ref(0.5)
const cell = computed(() => cells[ci.value])

function stats(c: Cell, m: string, t: number) {
  const runs = c.runs[m]
  let auc = 0, sens = 0, spec = 0, mean = 0
  for (const r of runs) {
    let tp = 0, pos = 0, tn = 0, neg = 0, s = 0
    r.p.forEach((v, i) => {
      const p = v / SCALE
      s += p
      if (y[i] === 1) { pos++; if (p >= t) tp++ } else { neg++; if (p < t) tn++ }
    })
    auc += r.auc; sens += tp / pos; spec += tn / neg; mean += s / r.p.length
  }
  const k = runs.length
  return { auc: auc / k, sens: sens / k, spec: spec / k, mean: mean / k, k }
}
const cur = computed(() => stats(cell.value, method.value, thr.value))
const all = computed(() => METHODS.map((m) => ({ m, ...stats(cell.value, m, thr.value) })))

// гістограма p для ТБ і норми, усі підвибірки разом, 20 кошиків
const NB = 20
const hist = computed(() => {
  const tb = new Array(NB).fill(0)
  const no = new Array(NB).fill(0)
  for (const r of cell.value.runs[method.value]) {
    r.p.forEach((v, i) => {
      const b = Math.min(NB - 1, Math.floor((v / SCALE) * NB))
      if (y[i] === 1) tb[b]++
      else no[b]++
    })
  }
  const k = cell.value.runs[method.value].length
  return { tb: tb.map((v) => v / k), no: no.map((v) => v / k) }
})
const hmax = computed(() => Math.max(...hist.value.tb, ...hist.value.no, 1))
const W = 340
const H = 140
const bw = (W - 20) / NB
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Дисбаланс у навчанні: що робить вага класу</div>
        <div class="lab__sub">
          Зменшуйте частку ТБ у навчальній частині і перемикайте спосіб компенсації. Тест не змінюється
          (162 знімки, половина — ТБ). Поріг рішення можна рухати: при 0,5 числа збігаються з таблицею коду.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="m in METHODS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': method === m }"
              @click="method = m">{{ m }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>частка ТБ у навчанні: <b>{{ cell.pct }} %</b> (ТБ {{ cell.n_pos }}, норма {{ cell.n_neg }})</span>
        <input v-model.number="ci" type="range" min="0" :max="cells.length - 1" step="1" aria-label="Частка ТБ у навчанні" />
      </label>
      <label class="lab__ctl">
        <span>поріг: <b>{{ num(thr, 2) }}</b></span>
        <input v-model.number="thr" type="range" min="0.05" max="0.95" step="0.01" aria-label="Поріг рішення" />
      </label>
    </div>

    <div class="im__grid">
      <div>
        <div class="im__cap">Імовірності «ТБ» на тесті: <span class="im__k im__k--tb">ТБ</span> <span class="im__k im__k--no">норма</span></div>
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Гістограма ймовірностей на тесті">
          <g v-for="(v, b) in hist.no" :key="'n' + b">
            <rect :x="10 + b * bw" :y="H - 18 - (v / hmax) * (H - 28)" :width="bw - 1" :height="(v / hmax) * (H - 28)" class="im__no" />
          </g>
          <g v-for="(v, b) in hist.tb" :key="'t' + b">
            <rect :x="10 + b * bw + bw * 0.25" :y="H - 18 - (v / hmax) * (H - 28)" :width="bw * 0.5" :height="(v / hmax) * (H - 28)" class="im__tb" />
          </g>
          <line :x1="10 + thr * (W - 20)" :x2="10 + thr * (W - 20)" y1="6" :y2="H - 18" class="im__thr" />
          <line x1="10" :x2="W - 10" :y1="H - 18" :y2="H - 18" class="im__axis" />
          <text x="10" :y="H - 5" class="im__lbl">0</text>
          <text :x="10 + 0.5 * (W - 20)" :y="H - 5" text-anchor="middle" class="im__lbl">0,5</text>
          <text :x="W - 10" :y="H - 5" text-anchor="end" class="im__lbl">1</text>
        </svg>
      </div>
      <table class="im__table">
        <tbody>
          <tr><th>спосіб</th><th>AUC</th><th>чутл.</th><th>спец.</th><th>сер. p</th></tr>
          <tr v-for="r in all" :key="r.m" :class="{ 'is-on': r.m === method }">
            <td class="im__m">{{ r.m }}</td><td>{{ num(r.auc) }}</td><td>{{ num(r.sens) }}</td><td>{{ num(r.spec) }}</td><td>{{ num(r.mean) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(cell.w, 2) }}</b><span>w₊ = N₋ / N₊ для зваженої втрати</span></div>
      <div class="lab__stat"><b>{{ num(cur.auc) }}</b><span>AUC (від порогу не залежить)</span></div>
      <div class="lab__stat" :class="{ 'is-warm': cur.sens < 0.5 }"><b>{{ num(cur.sens) }}</b><span>чутливість при порозі</span></div>
      <div class="lab__stat"><b>{{ num(cur.spec) }}</b><span>специфічність при порозі</span></div>
      <div class="lab__stat"><b>{{ num(cur.mean) }}</b><span>середня p на тесті (частка ТБ 0,5)</span></div>
    </div>

    <p class="lab__note">
      Середнє за {{ cur.k }} {{ cur.k === 1 ? 'навчанням (усі знімки ТБ)' : 'випадковими підвибірками знімків ТБ' }}.
      Без ваг модель при малій частці ТБ зсуває ймовірності донизу і майже нікого не називає хворим за порогом 0,5;
      вага або дублювання повертають чутливість, а AUC при цьому не покращується (при 5 % — падає). Те саме зрушення
      чутливості дає і зсув порогу вниз для моделі «без ваг». Поріг тут рухається на тесті лише для ілюстрації:
      у роботі його вибирають на валідаційній частині, а тест лишають для остаточної оцінки.
    </p>
  </div>
</template>

<style scoped>
.im__grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr); gap: 1rem; align-items: center; }
@media (max-width: 760px) { .im__grid { grid-template-columns: 1fr; } }
svg { width: 100%; height: auto; display: block; }
.im__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin-bottom: 0.25rem; }
.im__k { white-space: nowrap; margin-right: 0.5rem; }
.im__k::before { content: ''; display: inline-block; width: 10px; height: 10px; margin-right: 4px; vertical-align: -1px; border-radius: 2px; }
.im__k--tb::before { background: var(--uk-warm); }
.im__k--no::before { background: var(--uk-accent); opacity: 0.45; }
.im__no { fill: var(--uk-accent); opacity: 0.4; }
.im__tb { fill: var(--uk-warm); }
.im__thr { stroke: var(--vp-c-text-1); stroke-width: 1.5; stroke-dasharray: 4 3; }
.im__axis { stroke: var(--uk-line); }
.im__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
.im__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; font-size: 0.8rem; }
.im__table th { font-weight: 500; color: var(--vp-c-text-3); text-align: right; padding: 0.2rem 0.3rem !important; font-size: 0.72rem; }
.im__table td { text-align: right; padding: 0.28rem 0.3rem !important; border-top: 1px solid var(--uk-line) !important; font-family: var(--vp-font-family-mono); }
.im__table td.im__m, .im__table th:first-child { text-align: left; font-family: var(--vp-font-family-base); }
.im__table tr.is-on td { color: var(--uk-accent); font-weight: 600; }
</style>
