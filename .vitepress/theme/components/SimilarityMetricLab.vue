<script setup lang="ts">
/**
 * Метрики схожості на зрізі шаблону MNI (лекція 11, розділ «Метрики схожості: SSD, NCC і взаємна
 * інформація»). Дані — tools/gen_lec11_metrics.py: для пар «T1 → T1» і «псевдо-Т2 → T1» таблиці
 * SSD (середній квадрат різниці), NCC і MI (спільна гістограма 32 × 32, нати) на сітці кут −15…15° ×
 * зсув −20…20 мм (крок 1) — ті самі функції й параметри, що в блоці коду; рядки виводу коду
 * генератор звіряє з таблицею. Накладання зрізів малюється тут: рухомий PNG повертається навколо
 * центру й зсувається в canvas (як scipy.ndimage.rotate + shift); числа беруться лише з таблиці.
 * Шаблон ICBM 2009a: Copyright (C) 1993–2004 Louis Collins, McConnell Brain Imaging Centre, Montreal
 * Neurological Institute, McGill University (дозвіл на використання й поширення зі збереженням копірайту).
 */
import { ref, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec11_metrics.json'

type Key = 'ssd' | 'ncc' | 'mi'
type Pair = 'mono' | 'multi'
const SHIFTS = data.shifts as number[]
const ANGLES = data.angles as number[]
const P = data.pairs as Record<Pair, Record<Key, number[][]>>
const W = data.w as number, H = data.h as number

const pair = ref<Pair>('multi')
const si = ref(SHIFTS.indexOf(0))
const ai = ref(ANGLES.indexOf(0))
const axis = ref<'shift' | 'angle'>('angle')

const METRICS: { key: Key; label: string; best: 'min' | 'max'; dec: number; color: string }[] = [
  { key: 'ssd', label: 'SSD (менше — краще)', best: 'min', dec: 4, color: '#EB6834' },
  { key: 'ncc', label: 'NCC (більше — краще)', best: 'max', dec: 3, color: '#1BAF7A' },
  { key: 'mi', label: 'MI, нат (більше — краще)', best: 'max', dec: 3, color: '#3D4EC4' },
]
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const val = (k: Key) => P[pair.value][k][ai.value][si.value]
const series = (k: Key) => axis.value === 'shift' ? P[pair.value][k][ai.value] : ANGLES.map((_, i) => P[pair.value][k][i][si.value])
const xs = computed(() => (axis.value === 'shift' ? SHIFTS : ANGLES))
const cur = computed(() => (axis.value === 'shift' ? si.value : ai.value))
function bestIdx(k: Key, best: 'min' | 'max') {
  const s = series(k)
  let b = 0
  for (let i = 1; i < s.length; i++) if (best === 'min' ? s[i] < s[b] : s[i] > s[b]) b = i
  return b
}

// міні-графіки
const CW = 300, CH = 150, L = 46, R = 8, T = 10, B = 26
function chart(k: Key) {
  const s = series(k)
  const lo = Math.min(...s), hi = Math.max(...s)
  const pad = (hi - lo) * 0.08 || 0.01
  const y0 = lo - pad, y1 = hi + pad
  const x = (i: number) => L + (i / (s.length - 1)) * (CW - L - R)
  const y = (v: number) => T + (1 - (v - y0) / (y1 - y0)) * (CH - T - B)
  const d = s.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const ticks = [y0 + pad, (y0 + y1) / 2, y1 - pad]
  return { d, x, y, ticks, s }
}
const charts = computed(() => METRICS.map(m => ({ ...m, ...chart(m.key), b: bestIdx(m.key, m.best) })))

// накладання зрізів
const canvas = ref<HTMLCanvasElement | null>(null)
const imgs: Record<string, HTMLImageElement> = {}
const loaded = ref(0)
let fixedPx: Uint8ClampedArray | null = null
onMounted(() => {
  for (const [k, src] of Object.entries(data.png as Record<string, string>)) {
    const im = new Image()
    im.onload = () => { loaded.value++ }
    im.src = withBase(src)
    imgs[k] = im
  }
})
function draw() {
  const cv = canvas.value
  if (!cv || loaded.value < 2) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  if (!fixedPx) {
    ctx.clearRect(0, 0, W, H)
    ctx.drawImage(imgs.t1, 0, 0)
    fixedPx = ctx.getImageData(0, 0, W, H).data
  }
  const off = document.createElement('canvas')
  off.width = W; off.height = H
  const c2 = off.getContext('2d')
  if (!c2) return
  c2.fillStyle = '#000'
  c2.fillRect(0, 0, W, H)
  c2.save()
  c2.translate((W - 1) / 2 + SHIFTS[si.value], (H - 1) / 2)
  c2.rotate((-ANGLES[ai.value] * Math.PI) / 180) // ndimage.rotate: додатний кут — проти годинникової стрілки
  c2.drawImage(pair.value === 'mono' ? imgs.t1 : imgs.t2, -(W - 1) / 2, -(H - 1) / 2)
  c2.restore()
  const mv = c2.getImageData(0, 0, W, H).data
  const out = ctx.createImageData(W, H)
  for (let i = 0; i < W * H; i++) {
    const p = 4 * i
    out.data[p] = mv[p]            // рухоме — пурпурове (червоний + синій)
    out.data[p + 1] = fixedPx[p]   // фіксоване — зелене
    out.data[p + 2] = mv[p]
    out.data[p + 3] = 255
  }
  ctx.putImageData(out, 0, 0)
}
watch([si, ai, pair, loaded, canvas], draw, { flush: 'post' })
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Метрики схожості: посуньте й поверніть рухомий зріз</div>
        <div class="lab__sub">
          Фіксоване — аксіальний зріз T1 шаблону MNI (зелений), рухоме — той самий зріз або «псевдо-Т2» (пурпуровий);
          де зображення збігаються за яскравістю, накладання сіре. Числа — з таблиці генератора, звіреної з виводом коду.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button class="lab__pill" :class="{ 'is-on': pair === 'mono' }" @click="pair = 'mono'">T1 → T1 (одна модальність)</button>
      <button class="lab__pill" :class="{ 'is-on': pair === 'multi' }" @click="pair = 'multi'">«псевдо-Т2» → T1</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>зсув по горизонталі: <b>{{ num(SHIFTS[si], 0) }} мм</b></span>
        <input v-model.number="si" type="range" min="0" :max="SHIFTS.length - 1" step="1" aria-label="Зсув, мм">
      </label>
      <label class="lab__ctl">
        <span>поворот: <b>{{ num(ANGLES[ai], 0) }}°</b></span>
        <input v-model.number="ai" type="range" min="0" :max="ANGLES.length - 1" step="1" aria-label="Кут, градуси">
      </label>
    </div>
    <div class="sm__grid">
      <div class="sm__frame">
        <div class="sm__canvas">
          <canvas ref="canvas" :width="W" :height="H" aria-label="Накладання фіксованого й рухомого зрізів"></canvas>
          <div v-if="loaded < 2" class="sm__wait">завантаження зрізів (≈ 30 КБ)…</div>
        </div>
        <div class="sm__credit">Шаблон ICBM 2009a (копія nilearn). Copyright (C) 1993–2004 Louis Collins, McConnell Brain Imaging Centre, Montreal Neurological Institute, McGill University.</div>
      </div>
      <div class="lab__stats sm__stats">
        <div v-for="m in METRICS" :key="m.key" class="lab__stat">
          <b :style="{ color: m.color }">{{ num(val(m.key), m.dec) }}</b><span>{{ m.label }}</span>
        </div>
      </div>
    </div>
    <div class="lab__pills sm__axis">
      <span class="sm__axislabel">графіки за віссю:</span>
      <button class="lab__pill" :class="{ 'is-on': axis === 'angle' }" @click="axis = 'angle'">кут (при поточному зсуві)</button>
      <button class="lab__pill" :class="{ 'is-on': axis === 'shift' }" @click="axis = 'shift'">зсув (при поточному куті)</button>
    </div>
    <div class="sm__charts">
      <figure v-for="c in charts" :key="c.key" class="sm__chart">
        <svg :viewBox="`0 0 ${CW} ${CH}`" role="img" :aria-label="c.label">
          <g v-for="v in c.ticks" :key="v">
            <line :x1="L" :x2="CW - R" :y1="c.y(v)" :y2="c.y(v)" stroke="var(--vp-c-divider)" />
            <text :x="L - 4" :y="c.y(v) + 4" text-anchor="end" class="sm__tick">{{ num(v, c.dec) }}</text>
          </g>
          <text :x="L" :y="CH - 8" class="sm__tick">{{ num(xs[0], 0) }}</text>
          <text :x="CW - R" :y="CH - 8" text-anchor="end" class="sm__tick">{{ num(xs[xs.length - 1], 0) }}</text>
          <text :x="(L + CW - R) / 2" :y="CH - 8" text-anchor="middle" class="sm__tick">{{ axis === 'shift' ? 'зсув, мм' : 'кут, °' }}</text>
          <line :x1="c.x(xs.indexOf(0))" :x2="c.x(xs.indexOf(0))" :y1="T" :y2="CH - B" stroke="var(--vp-c-text-3)" stroke-dasharray="2 3" />
          <path :d="c.d" fill="none" :stroke="c.color" stroke-width="2" />
          <circle :cx="c.x(c.b)" :cy="c.y(c.s[c.b])" r="5" fill="none" :stroke="c.color" stroke-width="1.6" />
          <circle :cx="c.x(cur)" :cy="c.y(c.s[cur])" r="3.5" :fill="c.color" />
        </svg>
        <figcaption>{{ c.label }}: екстремум при {{ num(xs[c.b], 0) }}{{ axis === 'shift' ? ' мм' : '°' }}</figcaption>
      </figure>
    </div>
    <p class="lab__note">
      Для однієї модальності всі три криві мають екстремум у нулі. Для «псевдо-Т2» SSD і NCC при суміщенні далекі від
      ідеалу, а за віссю кута найкращі не в нулі; MI знову найбільша в нулі. Порожнє кільце на графіку — екстремум,
      заповнена точка — поточне положення.
    </p>
  </div>
</template>

<style scoped>
.sm__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
@media (max-width: 640px) { .sm__grid { grid-template-columns: 1fr; } }
.sm__frame { position: relative; width: 100%; max-width: 300px; margin: 0 auto; }
.sm__frame canvas { width: 100%; height: auto; aspect-ratio: 197 / 233; image-rendering: pixelated; border-radius: 6px; display: block; background: #000; }
.sm__canvas { position: relative; }
.sm__credit { font-size: 0.68rem; line-height: 1.35; color: var(--vp-c-text-3); margin-top: 0.3rem; }
.sm__wait { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; color: #ddd; }
.sm__stats { grid-template-columns: 1fr; margin-top: 0; }
.sm__axis { margin-top: 0.8rem; align-items: center; }
.sm__axislabel { font-size: 0.78rem; color: var(--vp-c-text-2); }
.sm__charts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.6rem; }
@media (max-width: 720px) { .sm__charts { grid-template-columns: 1fr; } }
.sm__chart { margin: 0; }
.sm__chart svg { width: 100%; height: auto; display: block; }
.sm__chart figcaption { font-size: 0.75rem; color: var(--vp-c-text-2); text-align: center; }
.sm__tick { font-size: 10px; fill: var(--vp-c-text-2); }
</style>
