<script setup lang="ts">
/**
 * Чутливість SAM і MedSAM до підказки (лекція 12, розділ «Чутливість до підказки: зсув рамки і точки»).
 * 22 знімки Montgomery з валідаційного фолду dev0, обидві легені (44 маски), сітка 256 px; вхід енкодера
 * 1024 × 1024 (SAM — процесор transformers, MedSAM — min–max до [0, 1]). Підказки: рамка маски +5 px, зсунута
 * на d px у 8 напрямках; та сама рамка, розширена на d px з кожного боку; одна або три позитивні точки
 * всередині маски (найдальші від межі), зсунуті на d px у 8 напрямках. Dice = 2|A∩B| / (|A| + |B|) проти
 * ручної маски. При d = 0 рамка — ті самі Dice, що у виводі блоку коду (там — окремо за половинами знімка). Знімків немає: на схемі — контур
 * однієї ручної маски на нейтральному тлі. Дані: tools/gen_lec12_prompts.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec12_prompts.json'

type Res = Record<string, number[][]>
const D = data.d as number[]
const S = data.scale as number // Dice × S — ціле в JSON
const models = data.models as Record<string, Res>
const ex = data.example as { contour: number[][]; box: number[]; p1: number[]; p3: number[][] }
const TYPES = [
  { key: 'box_shift', label: 'рамка, зсув' },
  { key: 'box_expand', label: 'рамка, розширення' },
  { key: 'point1', label: '1 точка' },
  { key: 'point3', label: '3 точки' },
] as const

const model = ref('MedSAM')
const kind = ref<(typeof TYPES)[number]['key']>('box_shift')
const di = ref(0)

const d = computed(() => D[di.value])
function quart(v: number[]) {
  const s = [...v].sort((a, b) => a - b)
  const q = (p: number) => {
    const x = (s.length - 1) * p, i = Math.floor(x), f = x - i
    return (s[i] + (s[Math.min(i + 1, s.length - 1)] - s[i]) * f) / S
  }
  return [q(0.25), q(0.5), q(0.75)]
}
const cur = computed(() => models[model.value][kind.value][di.value])
const stats = computed(() => {
  const [q1, med, q3] = quart(cur.value)
  const low = cur.value.filter((v) => v < 0.8 * S).length / cur.value.length
  return { q1, med, q3, low, n: cur.value.length }
})
const curves = computed(() => Object.fromEntries(Object.keys(models).map((m) => [m,
  models[m][kind.value].map((v) => quart(v))])))

// графік медіани Dice від d
const W = 320, H = 190, L = 34, R = 8, T = 8, B = 30
const X = (v: number) => L + (v / D[D.length - 1]) * (W - L - R)
const Y = (v: number) => H - B - Math.max(0, v) * (H - T - B)
const line = (m: string, k: number) => curves.value[m].map((q, i) => `${X(D[i])},${Y(q[k])}`).join(' ')
const band = (m: string) => {
  const c = curves.value[m]
  return [...c.map((q, i) => `${X(D[i])},${Y(q[2])}`), ...c.map((q, i) => `${X(D[i])},${Y(q[0])}`).reverse()].join(' ')
}
const dots = computed(() => cur.value.map((v, k) => ({
  x: X(d.value) + ((k * 37) % 17 - 8) * 0.9, y: Y(v / S),
})))

// схема: рамка або точки, зсунуті вправо-вниз на d (у зсуві — один з 8 напрямків)
const cs = computed(() => {
  const s = d.value / Math.SQRT2
  if (kind.value === 'box_shift') return { box: ex.box.map((v) => v + s), pts: [] as number[][] }
  if (kind.value === 'box_expand') return { box: [ex.box[0] - d.value, ex.box[1] - d.value, ex.box[2] + d.value, ex.box[3] + d.value], pts: [] as number[][] }
  const pts = kind.value === 'point1' ? [ex.p1] : ex.p3
  return { box: null, pts: pts.map(([x, y]) => [x + s, y + s]) }
})
const poly = ex.contour.map(([x, y]) => `${x},${y}`).join(' ')
const xs = ex.contour.map((p) => p[0]), ys = ex.contour.map((p) => p[1])
const vb = [Math.min(...xs) - 40, Math.min(...ys) - 40, Math.max(...xs) - Math.min(...xs) + 80, Math.max(...ys) - Math.min(...ys) + 80]
const num = (v: number, k = 3) => v.toFixed(k).replace('.', ',')
const COLORS: Record<string, string> = { SAM: 'var(--uk-accent)', MedSAM: 'var(--uk-warm)' }
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Наскільки маска залежить від підказки</div>
        <div class="lab__sub">
          Оберіть модель і тип підказки, потім рухайте величину збурення d. Графік — медіана Dice за 44 легенями
          (смуга — від Q1 до Q3) для обох моделей; точки — окремі підказки при обраному d.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="m in Object.keys(models)" :key="m" type="button" class="lab__pill" :class="{ 'is-on': model === m }"
              @click="model = m">{{ m }}</button>
      <button v-for="t in TYPES" :key="t.key" type="button" class="lab__pill" :class="{ 'is-on': kind === t.key }"
              @click="kind = t.key">{{ t.label }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>{{ kind === 'box_expand' ? 'розширення кожного боку' : 'зсув' }} d: <b>{{ d }} px</b> знімка 256 px</span>
        <input v-model.number="di" type="range" min="0" :max="D.length - 1" step="1" aria-label="Величина збурення підказки" />
      </label>
    </div>

    <div class="pj__grid">
      <svg :viewBox="vb.join(' ')" class="pj__scheme" role="img" aria-label="Схема підказки на контурі ручної маски">
        <rect :x="vb[0]" :y="vb[1]" :width="vb[2]" :height="vb[3]" class="pj__bg" />
        <polygon :points="poly" class="pj__mask" />
        <rect :x="ex.box[0]" :y="ex.box[1]" :width="ex.box[2] - ex.box[0]" :height="ex.box[3] - ex.box[1]" class="pj__box0" />
        <rect v-if="cs.box" :x="cs.box[0]" :y="cs.box[1]" :width="cs.box[2] - cs.box[0]" :height="cs.box[3] - cs.box[1]" class="pj__box" />
        <circle v-for="(p, k) in cs.pts" :key="k" :cx="p[0]" :cy="p[1]" r="4" class="pj__pt" />
      </svg>
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Медіана Dice від величини збурення">
        <line :x1="L" :x2="W - R" :y1="Y(0)" :y2="Y(0)" class="pj__axis" />
        <line :x1="L" :x2="L" :y1="T" :y2="Y(0)" class="pj__axis" />
        <g v-for="v in [0, 0.25, 0.5, 0.75, 1]" :key="'y' + v">
          <line :x1="L" :x2="W - R" :y1="Y(v)" :y2="Y(v)" class="pj__gl" />
          <text :x="L - 4" :y="Y(v) + 3" text-anchor="end" class="pj__lbl">{{ num(v, 2) }}</text>
        </g>
        <text v-for="v in D" :key="'x' + v" :x="X(v)" :y="Y(0) + 12" text-anchor="middle" class="pj__lbl">{{ v }}</text>
        <text :x="(L + W - R) / 2" :y="H - 3" text-anchor="middle" class="pj__lbl">d, px</text>
        <g v-for="m in Object.keys(models)" :key="m">
          <polygon :points="band(m)" :fill="COLORS[m]" opacity="0.13" />
          <polyline :points="line(m, 1)" fill="none" :stroke="COLORS[m]" stroke-width="2" />
        </g>
        <circle v-for="(p, k) in dots" :key="k" :cx="p.x" :cy="p.y" r="1.6" :fill="COLORS[model]" opacity="0.55" />
        <line :x1="X(d)" :x2="X(d)" :y1="T" :y2="Y(0)" class="pj__cur" />
        <text :x="W - R" :y="T + 10" text-anchor="end" class="pj__lbl" :fill="COLORS.SAM">— SAM</text>
        <text :x="W - R" :y="T + 22" text-anchor="end" class="pj__lbl" :fill="COLORS.MedSAM">— MedSAM</text>
      </svg>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(stats.med) }}</b><span>медіана Dice, {{ model }}</span></div>
      <div class="lab__stat"><b>{{ num(stats.q1) }}–{{ num(stats.q3) }}</b><span>від Q1 до Q3</span></div>
      <div class="lab__stat" :class="{ 'is-warm': stats.low > 0.25 }"><b>{{ num(100 * stats.low, 1) }} %</b><span>підказок із Dice &lt; 0,8 (з {{ stats.n }})</span></div>
    </div>

    <p class="lab__note">
      Рамка без зсуву (d = 0) дає ті самі Dice, що код попереднього розділу; там вони зведені окремо для лівої й правої половини знімка, тут — за обома легенями разом. MedSAM донавчали з рамками,
      кожен бік яких відсунуто назовні на 0–20 px у вході 1024 px (код train_one_gpu.py репозиторію MedSAM), тобто до
      5 px знімка 256 px, — це саме розширення; точкових підказок
      у його донавчанні не було. На схемі — контур однієї ручної маски Montgomery на нейтральному тлі: самого
      знімка сторінка не показує.
    </p>
  </div>
</template>

<style scoped>
.pj__grid { display: grid; grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr); gap: 1rem; align-items: center; }
@media (max-width: 760px) { .pj__grid { grid-template-columns: 1fr; } }
svg { width: 100%; height: auto; display: block; }
.pj__scheme { max-width: 260px; margin: 0 auto; }
.pj__bg { fill: #f0efec; }
.pj__mask { fill: #ffcc33; fill-opacity: 0.35; stroke: #8a6d00; stroke-width: 1.2; }
.pj__box0 { fill: none; stroke: #1b1b27; stroke-width: 1; stroke-dasharray: 3 3; opacity: 0.6; }
.pj__box { fill: none; stroke: #3d4ec4; stroke-width: 2; }
.pj__pt { fill: #3d4ec4; stroke: #fff; stroke-width: 1.2; }
.pj__axis { stroke: var(--uk-line); }
.pj__gl { stroke: var(--uk-line); stroke-dasharray: 2 3; opacity: 0.6; }
.pj__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.pj__cur { stroke: var(--vp-c-text-2); stroke-dasharray: 3 2; }
</style>
