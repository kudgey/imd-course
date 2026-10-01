<script setup lang="ts">
/**
 * Матриця суміжності рівнів сірого для двох фрагментів зрізу КТ (лекція 06, розділ «Текстура: матриця
 * суміжності рівнів сірого»). Фрагменти в HU — від tools/gen_lec06_glcm.py; рівні — L рівних кошиків на
 * −1000…200 HU. GLCM рахується тут зі зсувами IBSI: 0° → (0, d), 45° → (d, d), 90° → (d, 0), 135° →
 * (d, −d) (рядок, стовпець), symmetric, normed; ознаки — за формулами graycoprops (енергія = √ΣP²).
 * Генератор перевірив ту саму реалізацію проти graycomatrix (по діагоналі — відстань d·√2) на всіх 48
 * комбінаціях і поклав очікувані значення. Для фрагмента 4 × 4 при L = 4, d = 1, θ = 0°: контраст 0,5833,
 * однорідність 0,7083, енергія 0,3584, кореляція 0,5614.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec06_glcm.json'

type Frag = { name: string; rows: number[]; cols: number[]; hu: number[][] }
const FRAGS = data.frags as Frag[]
const EXPECT = data.expect as Record<string, number[]>
const LO = data.lo as number
const HI = data.hi as number

const fi = ref(0)
const L = ref(4)
const d = ref(1)
const ang = ref(0)

const levels = computed(() => {
  const w = (HI - LO) / L.value
  return FRAGS[fi.value].hu.map(row => row.map(v => Math.min(L.value - 1, Math.max(0, Math.floor((v - LO) / w)))))
})
/** Пари (i, j) зі зсувом IBSI d · (напрямок θ), симетрично */
const counts = computed(() => {
  const q = levels.value
  const n = q.length, m = q[0].length
  const [ur, uc] = DIR[ang.value]
  const dr = ur * d.value
  const dc = uc * d.value
  const P = Array.from({ length: L.value }, () => new Array(L.value).fill(0))
  for (let r = 0; r < n; r++) for (let c = 0; c < m; c++) {
    const rr = r + dr, cc = c + dc
    if (rr >= 0 && rr < n && cc >= 0 && cc < m) { P[q[r][c]][q[rr][cc]] += 1; P[q[rr][cc]][q[r][c]] += 1 }
  }
  return P
})
const total = computed(() => counts.value.flat().reduce((a, b) => a + b, 0))
const props = computed(() => {
  const P = counts.value.map(row => row.map(v => v / (total.value || 1)))
  let con = 0, hom = 0, asm = 0, mu = 0
  P.forEach((row, i) => row.forEach((p, j) => { con += p * (i - j) ** 2; hom += p / (1 + (i - j) ** 2); asm += p * p; mu += i * p }))
  let vr = 0, cov = 0
  P.forEach((row, i) => row.forEach((p, j) => { vr += p * (i - mu) ** 2; cov += p * (i - mu) * (j - mu) }))
  return [con, hom, Math.sqrt(asm), vr < 1e-15 ? 1 : cov / vr]
})
const expected = computed(() => EXPECT[`${fi.value}-${L.value}-${d.value}-${ang.value}`])
const same = computed(() => props.value.every((v, k) => Math.abs(v - expected.value[k]) < 1e-5))
const NAMES = ['контраст', 'однорідність', 'енергія', 'кореляція']
const num = (v: number, k = 4) => v.toFixed(k).replace('.', ',').replace('-', '−')
const maxCount = computed(() => Math.max(1, ...counts.value.flat()))
const cellColor = (v: number, mx: number) => `rgba(61, 78, 196, ${(0.08 + 0.8 * (v / mx)).toFixed(3)})`
const levelColor = (k: number) => {
  const g = Math.round(30 + (200 * k) / Math.max(1, L.value - 1))
  return `rgb(${g}, ${g}, ${g})`
}
const ARROW: Record<number, string> = { 0: '→', 45: '↘', 90: '↓', 135: '↙' } // рядки — донизу, як у масиві
const DIR: Record<number, [number, number]> = { 0: [0, 1], 45: [1, 1], 90: [1, 0], 135: [1, -1] } // IBSI
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Матриця суміжності: фрагмент, зсув, кут, рівні</div>
        <div class="lab__sub">
          Фрагменти зрізу z = −117,5 мм LIDC-IDRI-0001; рівні — {{ L }} кошики по {{ num((HI - LO) / L, 0) }} HU
          від −1000 до 200 HU. Матриця симетрична: кожна пара враховується в обидва боки.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(f, k) in FRAGS" :key="f.name" type="button" class="lab__pill" :class="{ 'is-on': fi === k }"
              @click="fi = k">{{ f.name }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="l in data.levels" :key="'L' + l" type="button" class="lab__pill" :class="{ 'is-on': L === l }"
              @click="L = l">{{ l }} рівні{{ l > 4 ? 'в' : '' }}</button>
      <button v-for="k in data.dists" :key="'d' + k" type="button" class="lab__pill" :class="{ 'is-on': d === k }"
              @click="d = k">d = {{ k }}</button>
      <button v-for="a in data.angles" :key="'a' + a" type="button" class="lab__pill" :class="{ 'is-on': ang === a }"
              @click="ang = a">θ = {{ a }}° {{ ARROW[a] }}</button>
    </div>

    <div class="gl__grid">
      <div>
        <div class="gl__cap">Фрагмент (рядки {{ FRAGS[fi].rows.join('–') }}, стовпці {{ FRAGS[fi].cols.join('–') }}):
          число — рівень, наведіть, щоб побачити HU</div>
        <table class="gl__frag">
          <tbody>
            <tr v-for="(row, r) in levels" :key="r">
              <td v-for="(v, c) in row" :key="c" :title="`${num(FRAGS[fi].hu[r][c], 0)} HU`"
                  :style="{ background: levelColor(v), color: v > (L - 1) / 2 ? '#1b1b27' : '#fff' }">{{ v }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div>
        <div class="gl__cap">Кількість пар (рядок — рівень i, стовпець — рівень сусіда j), усього {{ total }}</div>
        <table class="gl__mat">
          <tbody>
            <tr><th></th><th v-for="j in L" :key="'h' + j">{{ j - 1 }}</th></tr>
            <tr v-for="(row, i) in counts" :key="i">
              <th>{{ i }}</th>
              <td v-for="(v, j) in row" :key="j" :style="{ background: cellColor(v, maxCount) }">{{ v }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="lab__stats">
      <div v-for="(v, k) in props" :key="NAMES[k]" class="lab__stat"><b>{{ num(v) }}</b><span>{{ NAMES[k] }}</span></div>
      <div class="lab__stat" :class="same ? 'is-green' : 'is-warm'"><b>{{ same ? 'так' : 'ні' }}</b><span>збігається з graycoprops (зсув IBSI)</span></div>
    </div>

    <p class="lab__note">
      Контраст зважує пари квадратом різниці рівнів, тому для того самого фрагмента 4 × 4 при d = 1, θ = 0° він
      дорівнює 0,5833 при 4 рівнях і 1,5000 при 8: ознака описує текстуру разом із дискретизацією. Кут теж важить:
      край вузла на цьому фрагменті йде навскіс, і вздовж нього (θ = 135°) контраст 0,1111, а поперек (θ = 45°) —
      1,3333. Збільшення d рахує пари далі одна від одної, і на маленькому фрагменті їх лишається мало: на 4 × 4 при
      d = 3 і θ = 0° матриця містить лише 8 записів — 4 пари, кожну в обидва боки. Діагональний зсув тут — як в IBSI,
      (d, d); graycomatrix із цілою відстанню d рахує його як round(d · sin 45°) і для d = 2 дає (1, 1), тобто ту саму
      матрицю, що для d = 1.
    </p>
  </div>
</template>

<style scoped>
.gl__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 640px) { .gl__grid { grid-template-columns: 1fr; } }
.gl__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin-bottom: 0.4rem; line-height: 1.4; }
.gl__frag, .gl__mat { border-collapse: separate; border-spacing: 2px; font-variant-numeric: tabular-nums; }
.gl__frag td {
  width: 1.9rem; height: 1.9rem; text-align: center; font-family: var(--vp-font-family-mono);
  font-size: 0.8rem; border-radius: 3px; padding: 0 !important;
}
.gl__mat td, .gl__mat th {
  min-width: 1.9rem; height: 1.7rem; text-align: center; font-family: var(--vp-font-family-mono);
  font-size: 0.78rem; padding: 0 0.2rem !important; border-radius: 3px;
}
.gl__mat th { color: var(--vp-c-text-3); font-weight: 500; }
</style>
