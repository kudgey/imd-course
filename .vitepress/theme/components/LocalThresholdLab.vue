<script setup lang="ts">
/**
 * Локальне перекалібрування порогу (лекція 17, розділ «Розклад падіння якості на ранжування і поріг»).
 * Дані — tools/gen_lec17_threshold.py: для кожної частки калібрувальної частини Montgomery (10…50 %)
 * 200 поділів за пацієнтами, на кожному — локальний поріг за правилом теми про валідацію і чутливість та
 * специфічність замороженого й локального порогу на оцінювальній частині. Частка 30 % — та сама, що в
 * блоці коду. Знімків не показано, лише числа.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec17_threshold.json'

type By = { n_cal: number; n_cal_range: number[]; rows: number[][]; summary: Record<string, number[] | number> }
const FR = data.fracs as number[]
const BY = data.by as Record<string, By>
const k = ref(FR.indexOf(0.3))
const frac = computed(() => FR[k.value])
const cur = computed(() => BY[String(frac.value)])

function q(a: number[], p: number) { // лінійна інтерполяція, як numpy.quantile
  const s = [...a].sort((x, y) => x - y)
  const i = (s.length - 1) * p
  const lo = Math.floor(i), hi = Math.ceil(i)
  return s[lo] + (s[hi] - s[lo]) * (i - lo)
}
const stats = computed(() => {
  const r = cur.value.rows
  const col = (j: number) => r.map((x) => x[j])
  const se1 = col(3)
  return {
    tloc: [q(col(0), 0.5), q(col(0), 0.025), q(col(0), 0.975)],
    sp0: q(col(2), 0.5), sp1: [q(col(4), 0.5), q(col(4), 0.025), q(col(4), 0.975)],
    se0: q(col(1), 0.5), se1: q(se1, 0.5),
    below: se1.filter((v) => v < 0.9).length / se1.length,
  }
})

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const pct = (v: number) => `${Math.round(100 * v)} %`
const W = 320, H = 260, L = 40, B = 34, T0 = 10, R = 10
const X = (v: number) => L + v * (W - L - R) // специфічність 0…1
const Y = (v: number) => T0 + (1 - (v - 0.5) / 0.5) * (H - T0 - B) // чутливість 0,5…1
const jit = (i: number, a: number) => ((Math.sin(i * 12.9898 + a) * 43758.5453) % 1) * 0.006
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Локальний поріг: скільки знімків треба розмітити</div>
        <div class="lab__sub">
          Montgomery ділять за пацієнтами на калібрувальну й оцінювальну частини 200 разів. Сірі точки —
          поріг t = {{ num(data.t as number, 4) }} з валідації Shenzhen, сині — поріг, вибраний на калібрувальній частині
          за тим самим правилом; обидва оцінено на оцінювальній частині.
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>калібрувальна частина: <b>{{ pct(frac) }}</b> ({{ cur.n_cal_range[0] }}–{{ cur.n_cal_range[1] }} знімків з {{ data.n_mont }})</span>
        <input v-model.number="k" type="range" min="0" :max="FR.length - 1" step="1" aria-label="Частка калібрувальної частини" />
      </label>
    </div>
    <div class="lt__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Чутливість проти специфічності для 200 поділів">
        <line v-for="v in [0, 0.25, 0.5, 0.75, 1]" :key="'gx' + v" :x1="X(v)" :x2="X(v)" :y1="T0" :y2="H - B" class="lt__grid-l" />
        <line v-for="v in [0.5, 0.75, 1]" :key="'gy' + v" :x1="L" :x2="W - R" :y1="Y(v)" :y2="Y(v)" class="lt__grid-l" />
        <line :x1="L" :x2="W - R" :y1="Y(0.9)" :y2="Y(0.9)" class="lt__target" />
        <text :x="W - R - 2" :y="Y(0.9) - 4" text-anchor="end" class="lt__lbl">ціль 0,90</text>
        <circle v-for="(r, i) in cur.rows" :key="'f' + i" :cx="X(r[2] + jit(i, 1))" :cy="Y(r[1] + jit(i, 2))" r="2.4" class="lt__frozen" />
        <circle v-for="(r, i) in cur.rows" :key="'l' + i" :cx="X(r[4] + jit(i, 3))" :cy="Y(Math.max(0.5, r[3]) + jit(i, 4))" r="2.4" class="lt__local" />
        <text v-for="v in [0, 0.5, 1]" :key="'xl' + v" :x="X(v)" :y="H - B + 14" text-anchor="middle" class="lt__lbl">{{ num(v, 1) }}</text>
        <text v-for="v in [0.5, 0.75, 1]" :key="'yl' + v" :x="L - 5" :y="Y(v) + 3" text-anchor="end" class="lt__lbl">{{ num(v, 2) }}</text>
        <text :x="(L + W - R) / 2" :y="H - 4" text-anchor="middle" class="lt__lbl">специфічність на оцінювальній частині</text>
        <text :x="10" :y="(T0 + H - B) / 2" text-anchor="middle" class="lt__lbl" :transform="`rotate(-90 10 ${(T0 + H - B) / 2})`">чутливість</text>
      </svg>
      <div class="lt__legend">
        <p><span class="lt__sw lt__sw--f" /> заморожений поріг з валідації Shenzhen</p>
        <p><span class="lt__sw lt__sw--l" /> локальний поріг з калібрувальної частини</p>
        <p>Точки з чутливістю нижче 0,5 притиснуто до нижньої межі графіка. Кожна точка — один поділ Montgomery.</p>
      </div>
    </div>
    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(stats.sp0) }}</b><span>специфічність, заморожений t (медіана)</span></div>
      <div class="lab__stat"><b>{{ num(stats.sp1[0]) }}</b><span>специфічність, локальний t: [{{ num(stats.sp1[1]) }}; {{ num(stats.sp1[2]) }}]</span></div>
      <div class="lab__stat"><b>{{ num(stats.tloc[0]) }}</b><span>локальний поріг: [{{ num(stats.tloc[1]) }}; {{ num(stats.tloc[2]) }}]</span></div>
      <div class="lab__stat is-warm"><b>{{ pct(stats.below) }}</b><span>поділів, де чутливість з локальним t &lt; 0,90</span></div>
    </div>
    <p class="lab__note">
      Квадратні дужки — 2,5 і 97,5 перцентилі за 200 поділами. За частки 30 % числа збігаються з виводом коду в розділі.
      Розкид локального порогу звужується приблизно до частки 30 %, далі майже ні: кожен знімок, відданий на
      калібрування, забирають з оцінки. Частка поділів із чутливістю нижче цілі не зникає за жодної частки —
      правило ставить поріг упритул до цілі, і рятує лише запас.
    </p>
  </div>
</template>

<style scoped>
.lt__grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
@media (max-width: 700px) { .lt__grid { grid-template-columns: 1fr; } }
svg { width: 100%; max-width: 420px; height: auto; display: block; }
.lt__grid-l { stroke: var(--vp-c-divider); stroke-width: 1; }
.lt__target { stroke: var(--vp-c-text-2); stroke-dasharray: 4 3; }
.lt__lbl { fill: var(--vp-c-text-2); font-size: 10px; }
.lt__frozen { fill: #9a9aa8; opacity: 0.55; }
.lt__local { fill: var(--uk-accent); opacity: 0.6; }
.lt__legend { font-size: 0.8rem; color: var(--vp-c-text-2); line-height: 1.5; }
.lt__legend p { margin: 0.3rem 0; }
.lt__sw { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: -1px; }
.lt__sw--f { background: #9a9aa8; }
.lt__sw--l { background: var(--uk-accent); }
</style>
