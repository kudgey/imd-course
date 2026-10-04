<script setup lang="ts">
/**
 * Якість від кількості міток (лекція 13, розділ «Рецепт для малого бюджету міток і звітування»).
 * Два набори: PneumoniaMNIST (тест AUC, 624 знімки; CNN з нуля, лінійний зонд на ознаках SimCLR і того
 * самого енкодера до навчання, точки FixMatch-подібного навчання і «лише мічених» при 5 %) і ТБ, 800
 * рентгенограм (val AUC на dev0; чотири заморожені енкодери + логістична регресія). Для кожного бюджету
 * міток — AUC усіх зерен; віджет показує середнє і мінімум–максимум. Дані: tools/gen_lec13_curves.py
 * (звірено з виводом блоків коду розділів про криву міток, перенесення навчання, SimCLR і FixMatch).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec13_curves.json'

type Pt = { n: number; auc: number[]; val?: number[] }
type DSet = { name: string; metric: string; total: number; methods: Record<string, Pt[]> }
const sets = data.sets as DSet[]
const COLORS = ['#3D4EC4', '#B4531F', '#8A8A99', '#1B1B27', '#1BAF7A', '#EDA100']

const si = ref(0)
const set = computed(() => sets[si.value])
const names = computed(() => Object.keys(set.value.methods))
const hidden = ref<Record<string, boolean>>({})
const budgets = computed(() => {
  const all = new Set<number>()
  for (const m of names.value) for (const p of set.value.methods[m]) all.add(p.n)
  return [...all].sort((a, b) => a - b)
})
const bi = ref(2)
const budget = computed(() => budgets.value[Math.min(bi.value, budgets.value.length - 1)])
function pick(i: number) { si.value = i; bi.value = 2; hidden.value = {} }
function toggle(m: string) { hidden.value = { ...hidden.value, [m]: !hidden.value[m] } }

const mean = (a: number[]) => a.reduce((s, v) => s + v, 0) / a.length
const curves = computed(() => names.value.map((m, k) => ({
  m, color: COLORS[k % COLORS.length], on: !hidden.value[m],
  pts: set.value.methods[m].map((p) => ({ n: p.n, mu: mean(p.auc), lo: Math.min(...p.auc), hi: Math.max(...p.auc), k: p.auc.length })),
})))
const rows = computed(() => curves.value.map((c) => ({ ...c, p: c.pts.find((q) => q.n === budget.value) })))

const W = 420, H = 230, PL = 40, PR = 12, PT = 10, PB = 32
const yr = computed(() => {
  let lo = 1, hi = 0
  for (const c of curves.value) for (const p of c.pts) { lo = Math.min(lo, p.lo); hi = Math.max(hi, p.hi) }
  return [Math.floor(lo * 20) / 20, Math.min(1, Math.ceil(hi * 20) / 20)]
})
const lx = computed(() => [Math.log(budgets.value[0]), Math.log(budgets.value[budgets.value.length - 1])])
const X = (n: number) => PL + ((Math.log(n) - lx.value[0]) / (lx.value[1] - lx.value[0])) * (W - PL - PR)
const Y = (v: number) => PT + (1 - (v - yr.value[0]) / (yr.value[1] - yr.value[0])) * (H - PT - PB)
const yTicks = computed(() => { const t: number[] = []; for (let v = yr.value[0]; v <= yr.value[1] + 1e-9; v += 0.05) t.push(+v.toFixed(2)); return t })
const line = (pts: { n: number; mu: number }[]) => pts.map((p, i) => `${i ? 'L' : 'M'}${X(p.n).toFixed(1)},${Y(p.mu).toFixed(1)}`).join(' ')
const band = (pts: { n: number; lo: number; hi: number }[]) =>
  pts.map((p, i) => `${i ? 'L' : 'M'}${X(p.n).toFixed(1)},${Y(p.hi).toFixed(1)}`).join(' ') + ' ' +
  [...pts].reverse().map((p) => `L${X(p.n).toFixed(1)},${Y(p.lo).toFixed(1)}`).join(' ') + ' Z'
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Скільки якості коштує кожна мітка</div>
        <div class="lab__sub">
          Оберіть набір і бюджет міток. Лінія — середня AUC за зернами, смуга — мінімум і максимум. Натискання на назву
          методу ховає або повертає його криву.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(s, i) in sets" :key="s.name" type="button" class="lab__pill" :class="{ 'is-on': si === i }" @click="pick(i)">{{ s.name }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>мічених знімків: <b>{{ budget }}</b> з {{ set.total }} ({{ num((100 * budget) / set.total, 1) }} %)</span>
        <input v-model.number="bi" type="range" min="0" :max="budgets.length - 1" step="1" aria-label="Бюджет міток" />
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="lb__svg" role="img" :aria-label="`AUC від кількості міток: ${set.name}`">
      <g v-for="v in yTicks" :key="'y' + v">
        <line :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" class="lb__grid" />
        <text :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="lb__lbl">{{ num(v, 2) }}</text>
      </g>
      <g v-for="n in budgets" :key="'x' + n">
        <text :x="X(n)" :y="H - PB + 13" text-anchor="middle" class="lb__lbl">{{ n }}</text>
      </g>
      <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="lb__lbl">мічених знімків (логарифмічна шкала)</text>
      <line :x1="X(budget)" :x2="X(budget)" :y1="PT" :y2="H - PB" class="lb__cur" />
      <g v-for="c in curves" :key="c.m" :opacity="c.on ? 1 : 0.08">
        <path v-if="c.pts.length > 1" :d="band(c.pts)" :fill="c.color" opacity="0.13" />
        <path v-if="c.pts.length > 1" :d="line(c.pts)" fill="none" :stroke="c.color" stroke-width="1.8" />
        <g v-for="p in c.pts" :key="p.n">
          <line v-if="c.pts.length === 1" :x1="X(p.n)" :x2="X(p.n)" :y1="Y(p.lo)" :y2="Y(p.hi)" :stroke="c.color" stroke-width="1.5" />
          <circle :cx="X(p.n)" :cy="Y(p.mu)" :r="p.n === budget ? 4 : 2.6" :fill="c.color" />
        </g>
      </g>
    </svg>

    <table class="lb__table">
      <tbody>
        <tr><th>метод</th><th>середня AUC</th><th>мін.–макс.</th><th>зерен</th></tr>
        <tr v-for="r in rows" :key="r.m" :class="{ 'is-off': hidden[r.m] }" @click="toggle(r.m)">
          <td class="lb__m"><i :style="{ background: r.color }" />{{ r.m }}</td>
          <template v-if="r.p">
            <td>{{ num(r.p.mu) }}</td>
            <td>{{ num(r.p.lo) }}–{{ num(r.p.hi) }}</td>
            <td>{{ r.p.k }}</td>
          </template>
          <template v-else><td colspan="3" class="lb__na">немає точки для цього бюджету</td></template>
        </tr>
      </tbody>
    </table>

    <p class="lab__note">
      {{ set.metric }}. На PneumoniaMNIST за тестом нічого не вибирається: кількість кроків фіксована, раннього зупинення
      немає. На ТБ мічені знімки беруться з dev1…dev4, а dev0 у цьому експерименті служить лише для оцінки. Різниця
      методів, менша за ширину смуг, — у межах розкиду між зернами.
    </p>
  </div>
</template>

<style scoped>
.lb__svg { width: 100%; height: auto; display: block; }
.lb__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.lb__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.lb__cur { stroke: var(--vp-c-text-2); stroke-dasharray: 3 3; stroke-width: 1; }
.lb__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; font-size: 0.8rem; margin-top: 0.6rem; }
.lb__table th { font-weight: 500; color: var(--vp-c-text-3); text-align: right; padding: 0.2rem 0.35rem !important; font-size: 0.72rem; }
.lb__table th:first-child { text-align: left; }
.lb__table td { text-align: right; padding: 0.28rem 0.35rem !important; border-top: 1px solid var(--uk-line) !important; font-family: var(--vp-font-family-mono); }
.lb__table td.lb__m { text-align: left; font-family: var(--vp-font-family-base); cursor: pointer; }
.lb__table td.lb__na { text-align: left; color: var(--vp-c-text-3); font-family: var(--vp-font-family-base); }
.lb__m i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.lb__table tr { cursor: pointer; }
.lb__table tr.is-off td { opacity: 0.4; }
</style>
