<script setup lang="ts">
/**
 * Воксель → міліметри за матрицею affine з тегів DICOM (IOP, PixelSpacing, IPP, крок між зрізами).
 * Дві серії: LIDC-IDRI-0001 (осьова КТ) і Prostate-3T 01-0019 (коса МРТ). Координати показано
 * в LPS (DICOM, ITK) і RAS (NIfTI, nibabel): RAS = (−x, −y, z) від LPS.
 * Звірка з кодом: центр вузла (314, 365, 89) → LPS (54,78; 84,94; −117,5) мм,
 * RAS (−54,78; −84,94; −117,5) мм. Дані пише tools/gen_lec03_affine.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec03_affine.json'

type Pt = { label: string; ijk: number[] }
type Series = { name: string; dims: number[]; affine: number[][]; points: Pt[] }

const series = data.series as Series[]
const si = ref(0)
const i = ref(series[0].points[0].ijk[0])
const j = ref(series[0].points[0].ijk[1])
const k = ref(series[0].points[0].ijk[2])

const cur = computed(() => series[si.value])
const A = computed(() => cur.value.affine)

function clampInt(v: number, max: number): number {
  if (!Number.isFinite(v)) return 0
  return Math.min(max, Math.max(0, Math.round(v)))
}
const ijk = computed(() => [
  clampInt(i.value, cur.value.dims[0] - 1),
  clampInt(j.value, cur.value.dims[1] - 1),
  clampInt(k.value, cur.value.dims[2] - 1),
])

const lps = computed(() => {
  const m = A.value
  const v = [...ijk.value, 1]
  return [0, 1, 2].map(r => m[r][0] * v[0] + m[r][1] * v[1] + m[r][2] * v[2] + m[r][3] * v[3])
})
const ras = computed(() => [-lps.value[0], -lps.value[1], lps.value[2]])

const f = (v: number, d = 2) => {
  const s = (Math.abs(v) < 0.5 * Math.pow(10, -d) ? 0 : v).toFixed(d).replace('.', ',')
  return s.startsWith('-') ? '−' + s.slice(1) : s
}

function pickSeries(n: number) {
  si.value = n
  setPoint(series[n].points[0])
}
function setPoint(p: Pt) {
  i.value = p.ijk[0]
  j.value = p.ijk[1]
  k.value = p.ijk[2]
}
const isPoint = (p: Pt) => p.ijk[0] === ijk.value[0] && p.ijk[1] === ijk.value[1] && p.ijk[2] === ijk.value[2]

const COLS = ['i (стовпець)', 'j (рядок)', 'k (зріз)', 'зсув']
const ROWS = ['x', 'y', 'z']
/** Що змінює крок k → k + 1: третій стовпець матриці */
const kStep = computed(() => [0, 1, 2].map(r => A.value[r][2]))
const kLen = computed(() => Math.hypot(...kStep.value))
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Воксель → міліметри: LPS і RAS</div>
        <div class="lab__sub">
          Матриця affine зібрана з тегів серії так само, як у коді лекції. Змініть індекси вокселя —
          координати в обох системах перераховуються за тією самою матрицею.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(s, n) in series" :key="s.name" class="lab__pill" :class="{ 'is-on': si === n }"
              @click="pickSeries(n)">{{ s.name }}</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>i — стовпець, 0…{{ cur.dims[0] - 1 }}</span>
        <input type="number" min="0" :max="cur.dims[0] - 1" step="1" v-model.number="i" />
      </label>
      <label class="lab__ctl">
        <span>j — рядок, 0…{{ cur.dims[1] - 1 }}</span>
        <input type="number" min="0" :max="cur.dims[1] - 1" step="1" v-model.number="j" />
      </label>
      <label class="lab__ctl">
        <span>k — зріз, 0…{{ cur.dims[2] - 1 }}</span>
        <input type="number" min="0" :max="cur.dims[2] - 1" step="1" v-model.number="k" />
      </label>
    </div>

    <div class="lab__pills">
      <button v-for="p in cur.points" :key="p.label" class="lab__pill" :class="{ 'is-on': isPoint(p) }"
              @click="setPoint(p)">{{ p.label }}: ({{ p.ijk.join(', ') }})</button>
    </div>

    <div class="vm__grid">
      <div>
        <div class="vm__cap">Матриця affine у LPS, мм (стовпці: крок за i, за j, за k і положення першого вокселя)</div>
        <div class="vm__scroll">
        <table class="vm__mat">
          <tbody>
            <tr>
              <th></th>
              <th v-for="(h, c) in COLS" :key="c" :class="{ 'is-k': c === 2 }">{{ h }}</th>
            </tr>
            <tr v-for="(row, r) in A.slice(0, 3)" :key="r">
              <th>{{ ROWS[r] }}</th>
              <td v-for="(v, c) in row" :key="c" :class="{ 'is-k': c === 2, 'is-hot': c === 2 && Math.abs(v) > 1e-6 }">
                {{ f(v, 4) }}
              </td>
            </tr>
          </tbody>
        </table>
        </div>
        <div class="vm__cap">
          Крок k → k + 1 зсуває точку на ({{ f(kStep[0]) }}; {{ f(kStep[1]) }}; {{ f(kStep[2]) }}) мм,
          довжина кроку {{ f(kLen) }} мм.
          <template v-if="Math.abs(kStep[1]) > 1e-3">
            Змінюються одночасно y і z: площина зрізу нахилена, «крок по z» ({{ f(kStep[2]) }} мм) не дорівнює
            кроку між зрізами.
          </template>
          <template v-else>Змінюється лише z: осьова серія.</template>
        </div>
      </div>
      <div>
        <div class="lab__stats vm__stats">
          <div class="lab__stat"><b>({{ f(lps[0]) }}; {{ f(lps[1]) }}; {{ f(lps[2]) }})</b>
            <span>LPS, мм: x — до лівого боку, y — до спини, z — до голови (DICOM, ITK, SimpleITK)</span></div>
          <div class="lab__stat is-warm"><b>({{ f(ras[0]) }}; {{ f(ras[1]) }}; {{ f(ras[2]) }})</b>
            <span>RAS, мм: x — до правого боку, y — до грудей, z — до голови (NIfTI, nibabel)</span></div>
        </div>
      </div>
    </div>

    <p class="lab__note">
      Центр вузла LIDC-IDRI-0001 — воксель (314, 365, 89) — лежить у точці (54,78; 84,94; −117,5) мм у LPS
      і (−54,78; −84,94; −117,5) мм у RAS. Це та сама точка тіла: знаки x і y протилежні, бо осі
      спрямовані протилежно. Додатне x у LPS означає лівий бік пацієнта — вузол у лівій легені.
      Перемкніться на Prostate-3T і збільште k на одиницю: точка зсувається на 4 мм уздовж нормалі,
      з яких лише 3,62 мм припадає на z. Якби програма множила k на «крок по z», вона б помилилася
      і в положенні, і в розмірі.
    </p>
  </div>
</template>

<style scoped>
.vm__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);
  gap: 1.1rem;
  align-items: start;
}
@media (max-width: 760px) { .vm__grid { grid-template-columns: 1fr; } }
.vm__cap { font-size: 0.78rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.45rem; line-height: 1.45; }
.vm__scroll { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.vm__mat { width: 100%; min-width: 300px; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.vm__mat th {
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--vp-c-text-3);
  text-align: right;
  padding: 0.2rem 0.35rem !important;
}
.vm__mat td {
  font-family: var(--vp-font-family-mono);
  font-size: 0.8rem;
  text-align: right;
  padding: 0.25rem 0.35rem !important;
  border-top: 1px solid var(--uk-line) !important;
}
.vm__mat .is-k { background: var(--uk-fill) !important; }
.vm__mat td.is-hot { color: var(--uk-warm); font-weight: 600; }
.vm__stats { grid-template-columns: 1fr; margin-top: 0; }
.vm__stats b { font-size: 1.05rem; }
@media (max-width: 480px) {
  .vm__mat th { font-size: 0.64rem; padding: 0.15rem 0.2rem !important; }
  .vm__mat td { font-size: 0.7rem; padding: 0.2rem 0.2rem !important; }
  .vm__stats b { font-size: 0.95rem; }
}
</style>
