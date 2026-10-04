<script setup lang="ts">
/**
 * Активне навчання на ознаках xrv (лекція 13, розділ «Стратегії запитів проти випадкового вибору на ТБ»).
 * Пул — 510 знімків dev1…dev4 розбиття S1, старт — 5 знімків із ТБ і 5 без ТБ, 15 раундів по 8 запитів,
 * логістична регресія з C = 10⁻³; стратегії «випадковий», «ентропія», «BALD», «core-set»; AUC на валідаційній
 * частині dev0 після кожного раунду для 20 зерен. Праворуч — дві головні компоненти ознак пулу і запити
 * зерна 0. На раунді 15 середні AUC, парна різниця з випадковим вибором і кількість зерен, де стратегія краща,
 * збігаються з таблицею блоку коду (перевіряє tools/gen_lec13_al.py).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec13_al.json'

type Run = { auc: number[]; tb: number }
const S = data.strategies as string[]
const curves = data.curves as Record<string, Run[]>
const order = data.order as Record<string, number[]>
const xy = data.xy as number[][]
const ylab = data.y as number[]
const Q = data.q as number
const R = data.rounds as number
const COLORS: Record<string, string> = { 'випадковий': '#55556A', 'ентропія': '#3D4EC4', 'BALD': '#B4531F', 'core-set': '#1BAF7A' }

const r = ref(5)
const on = ref<Record<string, boolean>>(Object.fromEntries(S.map((s) => [s, true])))
const focus = ref('ентропія')
function toggle(s: string) { on.value = { ...on.value, [s]: !on.value[s] } }
const nLab = (k: number) => 10 + Q * k

const mean = (a: number[]) => a.reduce((s, v) => s + v, 0) / a.length
const stats = computed(() => S.map((s) => {
  const runs = curves[s]
  const pts = [...Array(R + 1).keys()].map((k) => {
    const v = runs.map((x) => x.auc[k])
    return { k, mu: mean(v), lo: Math.min(...v), hi: Math.max(...v) }
  })
  const d = runs.map((x, i) => x.auc[r.value] - curves['випадковий'][i].auc[r.value])
  return { s, pts, cur: pts[r.value], dm: mean(d), wins: d.filter((v) => v > 0).length, area: mean(runs.map((x) => mean(x.auc))) }
}))

const W = 380, H = 230, PL = 38, PR = 10, PT = 10, PB = 32
const yr = computed(() => {
  let lo = 1, hi = 0
  for (const st of stats.value) if (on.value[st.s]) for (const p of st.pts) { lo = Math.min(lo, p.lo); hi = Math.max(hi, p.hi) }
  if (lo > hi) { lo = 0.6; hi = 1 }
  return [Math.floor(lo * 20) / 20, Math.min(1, Math.ceil(hi * 20) / 20)]
})
const X = (k: number) => PL + (k / R) * (W - PL - PR)
const Y = (v: number) => PT + (1 - (v - yr.value[0]) / (yr.value[1] - yr.value[0])) * (H - PT - PB)
const yTicks = computed(() => { const t: number[] = []; for (let v = yr.value[0]; v <= yr.value[1] + 1e-9; v += 0.05) t.push(+v.toFixed(2)); return t })
const line = (pts: { k: number; mu: number }[]) => pts.map((p, i) => `${i ? 'L' : 'M'}${X(p.k).toFixed(1)},${Y(p.mu).toFixed(1)}`).join(' ')
const band = (pts: { k: number; lo: number; hi: number }[]) =>
  pts.map((p, i) => `${i ? 'L' : 'M'}${X(p.k).toFixed(1)},${Y(p.hi).toFixed(1)}`).join(' ') + ' ' +
  [...pts].reverse().map((p) => `L${X(p.k).toFixed(1)},${Y(p.lo).toFixed(1)}`).join(' ') + ' Z'

// проєкція пулу: запити зерна 0 до поточного раунду
const SW = 260, SH = 230, SP = 12
const SX = (v: number) => SP + ((v + 1) / 2) * (SW - 2 * SP)
const SY = (v: number) => SH - SP - ((v + 1) / 2) * (SH - 2 * SP)
const picked = computed(() => order[focus.value].slice(0, nLab(r.value)))
const tbShare = computed(() => {
  const q = picked.value.slice(10)
  return q.length ? q.filter((i) => ylab[i] === 1).length / q.length : NaN
})
const num = (v: number, d = 3) => (Number.isFinite(v) ? v.toFixed(d).replace('.', ',').replace('-', '−') : '—')
const sgn = (v: number) => (v > 0 ? '+' : '') + num(v)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Активне навчання: хто вибирає, що розмітити</div>
        <div class="lab__sub">
          Рухайте номер раунду: після кожного раунду лікар розмічає ще {{ Q }} знімків, які вибрала стратегія. Ліворуч —
          валідаційна AUC (середнє за 20 зернами, смуга — мінімум–максимум), праворуч — куди в просторі ознак пулу
          потрапили запити обраної стратегії для зерна 0.
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>раунд <b>{{ r }}</b> з {{ R }}: мічених <b>{{ nLab(r) }}</b> з {{ ylab.length }}</span>
        <input v-model.number="r" type="range" min="0" :max="R" step="1" aria-label="Раунд активного навчання" />
      </label>
    </div>
    <div class="lab__pills">
      <button v-for="s in S" :key="s" type="button" class="lab__pill" :class="{ 'is-on': on[s] }" @click="toggle(s)">
        <i class="al__sw" :style="{ background: COLORS[s] }" />{{ s }}
      </button>
    </div>

    <div class="al__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" class="al__svg" role="img" aria-label="Валідаційна AUC від кількості мічених для стратегій">
        <g v-for="v in yTicks" :key="'y' + v">
          <line :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" class="al__grid-l" />
          <text :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="al__lbl">{{ num(v, 2) }}</text>
        </g>
        <g v-for="k in [0, 5, 10, 15]" :key="'x' + k">
          <text :x="X(k)" :y="H - PB + 13" text-anchor="middle" class="al__lbl">{{ nLab(k) }}</text>
        </g>
        <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="al__lbl">мічених знімків</text>
        <line :x1="X(r)" :x2="X(r)" :y1="PT" :y2="H - PB" class="al__cur" />
        <g v-for="st in stats" :key="st.s" :opacity="on[st.s] ? 1 : 0">
          <path :d="band(st.pts)" :fill="COLORS[st.s]" opacity="0.08" />
          <path :d="line(st.pts)" fill="none" :stroke="COLORS[st.s]" stroke-width="1.8" />
          <circle :cx="X(r)" :cy="Y(st.cur.mu)" r="3.5" :fill="COLORS[st.s]" />
        </g>
      </svg>
      <div>
        <div class="lab__pills al__focus">
          <span class="al__cap">запити зерна 0:</span>
          <button v-for="s in S" :key="'f' + s" type="button" class="lab__pill" :class="{ 'is-on': focus === s }" @click="focus = s">{{ s }}</button>
        </div>
        <svg :viewBox="`0 0 ${SW} ${SH}`" class="al__svg" role="img" aria-label="Запити стратегії в проєкції ознак пулу">
          <circle v-for="(p, i) in xy" :key="'p' + i" :cx="SX(p[0])" :cy="SY(p[1])" r="1.6" class="al__pool" />
          <g v-for="(i, j) in picked" :key="'q' + i">
            <circle v-if="j >= 10" :cx="SX(xy[i][0])" :cy="SY(xy[i][1])" r="3.4"
                    :fill="ylab[i] ? 'var(--uk-warm)' : 'var(--uk-accent)'" stroke="var(--vp-c-bg)" stroke-width="0.6" />
            <rect v-else :x="SX(xy[i][0]) - 3" :y="SY(xy[i][1]) - 3" width="6" height="6" class="al__start" />
          </g>
          <text :x="SW / 2" :y="SH - 1" text-anchor="middle" class="al__lbl">ГК 1 →; ГК 2 ↑ (знімки не показано)</text>
        </svg>
      </div>
    </div>

    <div class="lab__stats">
      <div v-for="st in stats.filter((x) => on[x.s])" :key="'s' + st.s" class="lab__stat" :class="{ 'is-warm': st.s !== 'випадковий' && st.dm < 0 }">
        <b>{{ num(st.cur.mu) }}</b>
        <span>{{ st.s }}: val AUC<template v-if="st.s !== 'випадковий'">; різниця з випадковим {{ sgn(st.dm) }}, краща в {{ st.wins }} з 20 зерен</template></span>
      </div>
      <div class="lab__stat"><b>{{ Number.isFinite(tbShare) ? num(100 * tbShare, 0) + ' %' : '—' }}</b><span>знімків із ТБ серед запитів «{{ focus }}» (зерно 0; у пулі ≈ половина)</span></div>
    </div>
    <p class="lab__note">
      Квадрати — 10 стартових знімків, кружки — запити: синій — без ТБ, помаранчевий — ТБ. Стратегію вибирає валідаційна
      частина dev0 (128 знімків); тест у цьому експерименті не відкривається. Різниця, менша за ширину смуг, — у межах
      розкиду між зернами.
    </p>
  </div>
</template>

<style scoped>
.al__grid { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 0.8rem; align-items: start; }
@media (max-width: 760px) { .al__grid { grid-template-columns: 1fr; } }
.al__svg { width: 100%; height: auto; display: block; }
.al__grid-l { stroke: var(--uk-line); stroke-width: 0.6; }
.al__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.al__cur { stroke: var(--vp-c-text-2); stroke-dasharray: 3 3; stroke-width: 1; }
.al__pool { fill: var(--vp-c-text-3); opacity: 0.35; }
.al__start { fill: var(--vp-c-text-1); }
.al__sw { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 5px; vertical-align: 0; }
.al__focus { flex-wrap: wrap; margin-bottom: 0.2rem; }
.al__cap { font-size: 0.74rem; color: var(--vp-c-text-3); align-self: center; margin-right: 0.2rem; }
</style>
