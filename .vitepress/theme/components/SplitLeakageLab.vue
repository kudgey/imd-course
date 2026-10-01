<script setup lang="ts">
/**
 * Витік при розбитті ChestX-ray14 (лекція 04, розділ «Витік при розбитті по знімках: вимірюємо на
 * ChestX-ray14»). Дані — гістограма «знімків на пацієнта» (30 805 пацієнтів, 112 120 знімків) і
 * результати справжніх розбиттів scikit-learn (ShuffleSplit за знімками, GroupShuffleSplit за
 * Patient ID) для тесту 10–30 % і seed 0–4. Очікування витоку віджет рахує сам — тією самою
 * формулою, що блок коду: P(усі c знімків у тесті) = Π (m − i) / (N − i). При 20 % формула дає
 * 82,65 % і 7983 пацієнти, середнє п’яти seed — 82,79 ± 0,14 % і 8024 ± 37, як у виводі коду.
 * Дані пише tools/gen_lec04_leakage.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec04_leakage.json'

type Row = { f: number; m: number; formula: number[]; image: number[][]; patient: number[][] }
type Unit = 'image' | 'patient'

const N = data.n_images as number
const P = data.n_patients as number
const HIST = data.hist as number[][]
const ROWS = data.rows as Row[]

const unit = ref<Unit>('image')
const fi = ref(2)
const seed = ref(0)
const hover = ref<number | null>(null)

const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',')
const spaced = (v: number) => String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

/** Точне очікування для m тестових знімків із N (той самий алгоритм, що tools/gen_lec04_leakage.py) */
function expected(m: number) {
  let leak = 0
  let both = 0
  for (const [c, k] of HIST) {
    let pTest = 1
    let pTrain = 1
    for (let i = 0; i < c; i++) {
      pTest *= (m - i) / (N - i)
      pTrain *= (N - m - i) / (N - i)
    }
    leak += k * c * (m / N - pTest)
    both += k * (1 - pTest - pTrain)
  }
  return { leak: (100 * leak) / m, both }
}

const row = computed(() => ROWS[fi.value])
const run = computed(() => row.value[unit.value][seed.value])     // [тест, витік %, з обох боків]
const exp = computed(() => (unit.value === 'image' ? expected(row.value.m) : { leak: 0, both: 0 }))

/* Крива очікуваного витоку від частки тесту 5–50 % і точки п’яти seed для кожної частки */
const W = 340
const H = 170
const L = 40
const R = 10
const T = 12
const B = 30
const fx = (f: number) => L + ((f - 0.05) / 0.45) * (W - L - R)
const fy = (v: number) => T + (1 - (v - 75) / 15) * (H - T - B)
const curve = computed(() => {
  const pts: string[] = []
  for (let f = 0.05; f <= 0.5001; f += 0.01) {
    const v = expected(Math.ceil(f * N)).leak
    pts.push(`${fx(f).toFixed(1)},${fy(v).toFixed(1)}`)
  }
  return pts.join(' ')
})
const Y_TICKS = [75, 80, 85, 90]
const X_TICKS = [0.1, 0.2, 0.3, 0.4, 0.5]

/* Гістограма: пацієнти за кількістю знімків, групи 1, 2, 3, 4–5, 6–10, 11–20, 21–50, 51–184 */
const GROUPS = [[1, 1], [2, 2], [3, 3], [4, 5], [6, 10], [11, 20], [21, 50], [51, 184]]
const groups = computed(() =>
  GROUPS.map(([a, b]) => {
    let pats = 0
    let imgs = 0
    for (const [c, k] of HIST) if (c >= a && c <= b) { pats += k; imgs += c * k }
    return { label: a === b ? `${a}` : `${a}–${b}`, pats, imgs }
  }),
)
const GW = 340
const GH = 150
const gMax = computed(() => Math.max(...groups.value.map(g => Math.max(g.pats / P, g.imgs / N))))
const gh = (v: number) => (v / gMax.value) * (GH - 40)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Витік при розбитті ChestX-ray14: знімки чи пацієнти</div>
        <div class="lab__sub">
          {{ spaced(N) }} знімків, {{ spaced(P) }} пацієнтів. Емпіричні числа — справжні розбиття scikit-learn
          (як у коді); очікування для розбиття за знімками віджет рахує за точною формулою з гістограми «знімків
          на пацієнта».
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': unit === 'image' }" @click="unit = 'image'">
        розбиття за знімками (ShuffleSplit)</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': unit === 'patient' }" @click="unit = 'patient'">
        розбиття за пацієнтами (GroupShuffleSplit)</button>
    </div>
    <div class="lab__pills">
      <span class="sl__lbl">тест:</span>
      <button v-for="(r, i) in ROWS" :key="r.f" type="button" class="lab__pill" :class="{ 'is-on': fi === i }"
              @click="fi = i">{{ Math.round(r.f * 100) }} %</button>
      <span class="sl__lbl">seed:</span>
      <button v-for="s in data.seeds" :key="s" type="button" class="lab__pill" :class="{ 'is-on': seed === s }"
              @click="seed = s">{{ s }}</button>
    </div>

    <div class="lab__stats">
      <div class="lab__stat" :class="{ 'is-warm': run[1] > 0, 'is-green': run[1] === 0 }">
        <b>{{ num(run[1], 2) }} %</b><span>тестових знімків, чий пацієнт є в навчальній частині</span>
      </div>
      <div class="lab__stat"><b>{{ spaced(run[2]) }}</b><span>пацієнтів і в навчальній, і в тестовій частині</span></div>
      <div class="lab__stat"><b>{{ spaced(run[0]) }}</b><span>знімків у тесті</span></div>
      <div class="lab__stat">
        <b>{{ unit === 'image' ? num(exp.leak, 2) + ' %' : '0' }}</b>
        <span>{{ unit === 'image' ? `очікування за формулою; з обох боків ${spaced(exp.both)}` : 'за побудовою: пацієнт лише в одній частині' }}</span>
      </div>
    </div>

    <div class="sl__grid">
      <div>
        <div class="sl__cap">Очікуваний витік при розбитті за знімками залежно від частки тесту (лінія) і п’ять
          справжніх розбиттів (точки)</div>
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Витік залежно від частки тесту">
          <g v-for="t in Y_TICKS" :key="'y' + t">
            <line :x1="L" :x2="W - R" :y1="fy(t)" :y2="fy(t)" class="sl__grid-line" />
            <text :x="L - 4" :y="fy(t) + 3" text-anchor="end" class="sl__t">{{ t }} %</text>
          </g>
          <g v-for="t in X_TICKS" :key="'x' + t">
            <text :x="fx(t)" :y="H - B + 14" text-anchor="middle" class="sl__t">{{ Math.round(t * 100) }} %</text>
          </g>
          <polyline :points="curve" class="sl__curve" />
          <g v-for="(r, i) in ROWS" :key="r.f">
            <circle v-for="(p, s) in r.image" :key="s" :cx="fx(r.f)" :cy="fy(p[1])" :r="i === fi && s === seed ? 4 : 2.3"
                    :class="['sl__pt', { 'is-on': i === fi && s === seed && unit === 'image' }]" />
          </g>
          <text :x="(L + W - R) / 2" :y="H - 3" text-anchor="middle" class="sl__t">частка знімків у тесті</text>
        </svg>
      </div>
      <div>
        <div class="sl__cap">Пацієнти за кількістю знімків: частка пацієнтів (світлі) і частка знімків (темні);
          наведіть курсор на групу</div>
        <svg :viewBox="`0 0 ${GW} ${GH}`" role="img" aria-label="Розподіл знімків на пацієнта">
          <g v-for="(g, i) in groups" :key="g.label" @mouseenter="hover = i" @mouseleave="hover = null">
            <rect :x="14 + i * 40" :y="GH - 22 - gh(g.pats / P)" width="16" :height="gh(g.pats / P)" class="sl__bp" />
            <rect :x="31 + i * 40" :y="GH - 22 - gh(g.imgs / N)" width="16" :height="gh(g.imgs / N)" class="sl__bi" />
            <text :x="30 + i * 40" :y="GH - 8" text-anchor="middle" class="sl__t">{{ g.label }}</text>
            <rect :x="12 + i * 40" y="0" width="38" :height="GH - 20" fill="transparent" />
          </g>
        </svg>
        <div class="sl__probe">
          <template v-if="hover !== null">
            {{ groups[hover].label }} знімків на пацієнта: {{ spaced(groups[hover].pats) }} пацієнтів
            ({{ num((100 * groups[hover].pats) / P, 1) }} %), {{ spaced(groups[hover].imgs) }} знімків
            ({{ num((100 * groups[hover].imgs) / N, 1) }} %)
          </template>
          <template v-else>Пацієнти з одним знімком — більшість людей, але менша частина знімків.</template>
        </div>
      </div>
    </div>

    <p class="lab__note">
      При тесті 20 % і seed 0 за знімками витік становить {{ num(ROWS[2].image[0][1], 2) }} %, а п’ять seed дають
      82,79 ± 0,14 %; формула — 82,65 %. Частка тесту майже не змінює картини: за формулою витік — 83,59 % при
      тесті 10 % і 81,51 % при 30 %, а пацієнтів з обох боків стає більше — від 5419 до 9440. Перемкніться на
      розбиття за пацієнтами:
      витоку немає за будь-якої частки і seed, а кількість знімків у тесті трохи коливається, бо відбирають
      пацієнтів, а не знімки.
    </p>
  </div>
</template>

<style scoped>
.sl__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1.1rem;
  margin-top: 1rem;
}
@media (max-width: 760px) { .sl__grid { grid-template-columns: 1fr; } }
.sl__lbl { font-size: 0.78rem; color: var(--vp-c-text-3); align-self: center; margin: 0 0.15rem 0 0.4rem; }
.sl__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin-bottom: 0.4rem; line-height: 1.4; }
.sl__grid-line { stroke: var(--uk-line); stroke-width: 0.6; }
.sl__t { fill: var(--vp-c-text-3); font-size: 9px; }
.sl__curve { fill: none; stroke: var(--uk-warm); stroke-width: 1.8; }
.sl__pt { fill: var(--uk-accent); opacity: 0.6; }
.sl__pt.is-on { opacity: 1; stroke: var(--vp-c-bg); stroke-width: 1; }
.sl__bp { fill: var(--uk-accent); opacity: 0.35; }
.sl__bi { fill: var(--uk-accent); }
.sl__probe { font-size: 0.78rem; color: var(--vp-c-text-2); margin-top: 0.3rem; min-height: 2.4em; }
svg { width: 100%; height: auto; display: block; }
</style>
