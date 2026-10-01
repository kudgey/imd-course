<script setup lang="ts">
/**
 * Каппа Коена для двох експертів і двох класів (лекція 04, розділ «Згода як число: каппа Коена
 * і Фляйса»). Повзунки задають чотири клітинки таблиці 2×2; p_o, p_e і κ = (p_o − p_e) / (1 − p_e)
 * рахуються тією самою формулою, що в блоці коду. Пресети — рядки виводу: Jaeger et al., 2014,
 * Table IV (69 / 15 / 6 / 48 → p_o 0,848, p_e 0,509, κ 0,690) і та сама згода при майже відсутніх
 * «нормах» (112 / 15 / 6 / 5 → κ 0,245). Дані пише tools/gen_lec04_kappa.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec04_kappa.json'

type Preset = { name: string; note: string; cells: number[]; p_o: number; p_e: number; kappa: number }
const PRESETS = data.presets as Preset[]
const MAX = data.max_cell as number

const cells = ref<number[]>([...PRESETS[0].cells])
const NAMES = ['обидва «ТБ»', 'лише A «ТБ»', 'лише B «ТБ»', 'обидва «норма»']

const num = (v: number, d = 3) => (Number.isFinite(v) ? v.toFixed(d).replace('.', ',').replace('-', '−') : '—')
const res = computed(() => {
  const [a, b, c, d] = cells.value
  const n = a + b + c + d
  if (!n) return { n, po: NaN, pe: NaN, k: NaN, pa: NaN, pb: NaN }
  const po = (a + d) / n
  const pa = (a + b) / n
  const pb = (a + c) / n
  const pe = pa * pb + (1 - pa) * (1 - pb)
  return { n, po, pe, k: pe < 1 ? (po - pe) / (1 - pe) : NaN, pa, pb }
})
const active = computed(() => PRESETS.findIndex(p => p.cells.every((v, i) => v === cells.value[i])))
function set(i: number, v: number) {
  const c = [...cells.value]
  c[i] = v
  cells.value = c
}

// смуга 0…1: p_e — випадкова згода, p_o — спостережена; κ — частка відстані від p_e до 1
const W = 340
const H = 70
const X = (v: number) => 12 + v * (W - 24)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Каппа Коена: згода понад випадкову</div>
        <div class="lab__sub">
          Два експерти, два класи. Змінюйте кількість знімків у клітинках таблиці 2×2 — p_o, p_e і каппа
          перераховуються тією самою формулою, що в коді.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(p, i) in PRESETS" :key="p.name" type="button" class="lab__pill" :class="{ 'is-on': active === i }"
              @click="cells = [...p.cells]">{{ p.name }}: {{ p.note }}</button>
    </div>

    <div class="lab__controls">
      <label v-for="(name, i) in NAMES" :key="name" class="lab__ctl">
        <span>{{ name }}: <b>{{ cells[i] }}</b></span>
        <input type="range" min="0" :max="MAX" step="1" :value="cells[i]" :aria-label="name"
               @input="set(i, Number(($event.target as HTMLInputElement).value))" />
      </label>
    </div>

    <div class="ka__grid">
      <table class="ka__table">
        <tbody>
          <tr><th></th><th>B: «ТБ»</th><th>B: «норма»</th><th>разом</th></tr>
          <tr><th>A: «ТБ»</th><td class="is-agree">{{ cells[0] }}</td><td>{{ cells[1] }}</td><td>{{ cells[0] + cells[1] }}</td></tr>
          <tr><th>A: «норма»</th><td>{{ cells[2] }}</td><td class="is-agree">{{ cells[3] }}</td><td>{{ cells[2] + cells[3] }}</td></tr>
          <tr><th>разом</th><td>{{ cells[0] + cells[2] }}</td><td>{{ cells[1] + cells[3] }}</td><td>{{ res.n }}</td></tr>
        </tbody>
      </table>
      <div>
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Спостережена і випадкова згода на шкалі від 0 до 1">
          <line :x1="X(0)" :x2="X(1)" y1="34" y2="34" class="ka__axis" />
          <rect v-if="Number.isFinite(res.pe)" :x="X(res.pe)" y="26" :width="Math.max(X(1) - X(res.pe), 0)" height="16" class="ka__band" />
          <rect v-if="Number.isFinite(res.po) && res.po > res.pe" :x="X(res.pe)" y="26" :width="X(res.po) - X(res.pe)" height="16" class="ka__fill" />
          <g v-if="Number.isFinite(res.pe)">
            <line :x1="X(res.pe)" :x2="X(res.pe)" y1="20" y2="48" class="ka__tick" />
            <text :x="X(res.pe)" y="14" text-anchor="middle" class="ka__lbl">p_e = {{ num(res.pe) }}</text>
          </g>
          <g v-if="Number.isFinite(res.po)">
            <line :x1="X(res.po)" :x2="X(res.po)" y1="20" y2="48" class="ka__tick is-po" />
            <text :x="X(res.po)" y="62" text-anchor="middle" class="ka__lbl">p_o = {{ num(res.po) }}</text>
          </g>
          <text :x="X(0)" y="62" text-anchor="start" class="ka__lbl">0</text>
          <text :x="X(1)" y="62" text-anchor="end" class="ka__lbl">1</text>
        </svg>
        <div class="ka__cap">Сіра смуга — шлях від випадкової згоди p_e до повної; синя частина — скільки з нього
          пройдено. Каппа — саме ця частка.</div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(res.po) }}</b><span>p_o — спостережена частка збігів</span></div>
      <div class="lab__stat"><b>{{ num(res.pe) }}</b><span>p_e — збіг за випадковості</span></div>
      <div class="lab__stat" :class="{ 'is-warm': res.k < 0.4, 'is-green': res.k >= 0.6 }">
        <b>{{ num(res.k) }}</b><span>каппа Коена</span>
      </div>
      <div class="lab__stat"><b>{{ num(res.pa, 2) }} / {{ num(res.pb, 2) }}</b><span>частка «ТБ» в A / в B</span></div>
    </div>

    <p class="lab__note">
      Пресет Jaeger 2014 відтворює статтю: p_o = 0,848, κ = 0,690. Другий пресет має ту саму кількість збігів
      (117 із 138), але майже всі знімки там «ТБ», тому випадкова згода зростає до 0,798, а каппа падає до 0,245.
      Спробуйте зменшити обидві «нормальні» клітинки за незмінних 117 збігів — каппа реагує на баланс класів,
      а не лише на згоду.
    </p>
  </div>
</template>

<style scoped>
.ka__grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 1.1rem;
  align-items: center;
}
@media (max-width: 760px) { .ka__grid { grid-template-columns: 1fr; } }
.ka__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.ka__table th { font-weight: 500; font-size: 0.74rem; color: var(--vp-c-text-3); text-align: right; padding: 0.25rem 0.4rem !important; }
.ka__table td {
  font-family: var(--vp-font-family-mono);
  font-size: 0.85rem;
  text-align: right;
  padding: 0.3rem 0.4rem !important;
  border-top: 1px solid var(--uk-line) !important;
}
.ka__table td.is-agree { color: var(--uk-accent); font-weight: 600; }
.ka__axis { stroke: var(--uk-line); stroke-width: 1; }
.ka__band { fill: var(--uk-fill); stroke: var(--uk-line); stroke-width: 0.6; }
.ka__fill { fill: var(--uk-accent); opacity: 0.55; }
.ka__tick { stroke: var(--vp-c-text-3); stroke-width: 1.2; }
.ka__tick.is-po { stroke: var(--uk-accent); stroke-width: 2; }
.ka__lbl { fill: var(--vp-c-text-2); font-size: 10px; }
.ka__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.3rem; line-height: 1.4; }
svg { width: 100%; height: auto; display: block; }
</style>
