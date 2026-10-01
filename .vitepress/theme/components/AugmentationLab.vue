<script setup lang="ts">
/**
 * Аугментації рентгенограми SCR/JSRT JPCNN010 (256 × 256, CC BY 4.0) разом із контурами правої легені, лівої
 * легені й серця з points.zip (координати 1024 × 1024). Геометрія: поворот і масштаб навколо центру кадру, зсув,
 * віддзеркалення — одна афінна матриця для знімка (canvas) і для контурів (SVG). Інтенсивність: яскравість,
 * контраст, гамма, гауссів шум (фіксоване зерно генератора, щоб кадр не мерехтів).
 * Центр серця — середнє індексів пікселів заливки контуру heart на сітці 1024 (tools/gen_lec05_aug.py), перенесене
 * тією самою матрицею: без перетворень x = 584,3, після віддзеркалення 438,7 (x → 1023 − x) — як у виводі блоку
 * коду розділу про набір SCR.
 */
import { ref, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec05_aug.json'

const S = data.size as number                 // 256
const G = data.grid as number                 // 1024
const MID = data.mid as number                // 511,5
const contours = data.contours as Record<string, number[][]>
const heart = data.heart as number[]

const rot = ref(0)
const scale = ref(1)
const tx = ref(0)
const ty = ref(0)
const bright = ref(0)
const contrast = ref(1)
const gamma = ref(1)
const noise = ref(0)
const flip = ref(false)
const canvas = ref<HTMLCanvasElement | null>(null)
let img: HTMLImageElement | null = null      // створюється лише в браузері (onMounted), не під час SSR
const ready = ref(false)

/** Афінна матриця в координатах полотна 256 × 256: p' = A·p + b */
const M = computed(() => {
  const th = (rot.value * Math.PI) / 180
  const c = Math.cos(th) * scale.value
  const s = Math.sin(th) * scale.value
  const cx = S / 2
  // поворот і масштаб навколо центру, потім зсув
  let a11 = c, a12 = -s, a21 = s, a22 = c
  let b1 = cx + tx.value - (c * cx - s * cx)
  let b2 = cx + ty.value - (s * cx + c * cx)
  if (flip.value) { a11 = -a11; a12 = -a12; b1 = S - b1 }
  return { a11, a12, a21, a22, b1, b2 }
})
/** Індекс сітки 1024 → полотно 256 → перетворення → назад в індекс 1024 */
function mapIdx(x: number, y: number) {
  const u = (x + 0.5) * (S / G)
  const v = (y + 0.5) * (S / G)
  const m = M.value
  const u2 = m.a11 * u + m.a12 * v + m.b1
  const v2 = m.a21 * u + m.a22 * v + m.b2
  return [u2 * (G / S) - 0.5, v2 * (G / S) - 0.5]
}
const paths = computed(() => {
  const out: Record<string, string> = {}
  for (const [k, pts] of Object.entries(contours)) {
    out[k] = pts.map(([x, y]) => mapIdx(x, y)).map(([x, y]) => `${((x + 0.5) * S / G).toFixed(2)},${((y + 0.5) * S / G).toFixed(2)}`).join(' ')
  }
  return out
})
const hc = computed(() => mapIdx(heart[0], heart[1]))
const side = computed(() => {
  if (flip.value) return 'з іншого боку: анатомія віддзеркалена, так виглядає декстрокардія'
  return hc.value[0] > MID ? 'праворуч від середини кадру, з лівого боку пацієнта' : 'ліворуч від середини кадру лише через зсув — анатомія та сама'
})

function mulberry32(seed: number) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
function draw() {
  const cv = canvas.value
  if (!cv || !ready.value || !img) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.fillStyle = '#000'
  ctx.fillRect(0, 0, S, S)
  const m = M.value
  ctx.imageSmoothingEnabled = true
  ctx.setTransform(m.a11, m.a21, m.a12, m.a22, m.b1, m.b2)
  ctx.drawImage(img, 0, 0, S, S)
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  const id = ctx.getImageData(0, 0, S, S)
  const rnd = mulberry32(1)
  const lut = new Float32Array(256)
  for (let g = 0; g < 256; g++) {
    const x = Math.min(Math.max((g / 255 - 0.5) * contrast.value + 0.5 + bright.value, 0), 1)
    lut[g] = Math.pow(x, gamma.value)
  }
  for (let p = 0; p < S * S; p++) {
    let y = lut[id.data[4 * p]]
    if (noise.value > 0) {
      const u1 = Math.max(rnd(), 1e-12)
      const u2 = rnd()
      y += noise.value * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
    }
    const g = Math.round(255 * Math.min(Math.max(y, 0), 1))
    id.data[4 * p] = id.data[4 * p + 1] = id.data[4 * p + 2] = g
  }
  ctx.putImageData(id, 0, 0)
}
onMounted(() => {
  const im = new Image()
  im.onload = () => { img = im; ready.value = true; draw() }
  im.src = withBase(data.png as string)
})
watch([rot, scale, tx, ty, bright, contrast, gamma, noise, flip, canvas], draw, { flush: 'post' })

function randomize() {
  const u = (a: number, b: number) => a + Math.random() * (b - a)
  rot.value = Math.round(u(-15, 15))
  scale.value = Math.round(u(0.9, 1.1) * 100) / 100
  tx.value = Math.round(u(-12, 12))
  ty.value = Math.round(u(-12, 12))
  bright.value = Math.round(u(-0.1, 0.1) * 100) / 100
  contrast.value = Math.round(u(0.85, 1.15) * 100) / 100
  gamma.value = Math.round(u(0.8, 1.25) * 100) / 100
  noise.value = Math.round(u(0, 0.03) * 1000) / 1000
}
function reset() {
  rot.value = 0; scale.value = 1; tx.value = 0; ty.value = 0
  bright.value = 0; contrast.value = 1; gamma.value = 1; noise.value = 0; flip.value = false
}
const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const COL: Record<string, string> = { 'right lung': '#FFCC33', 'left lung': '#FFCC33', heart: '#33C3FF' }
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Аугментації рентгенограми разом із контурами</div>
        <div class="lab__sub">
          Знімок SCR із намальованими контурами розмітки (JPCNN010, Zenodo 7056076, CC BY 4.0). Жовті контури легень і
          блакитний контур серця з points.zip проходять через ту саму матрицю, що й знімок, тож мають лягати на
          чорно-білі лінії розмітки, впечатані у файл. Порожні кути після повороту заповнено чорним.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl"><span>поворот <b>{{ num(rot, 0) }}°</b></span>
        <input type="range" min="-15" max="15" step="1" v-model.number="rot" /></label>
      <label class="lab__ctl"><span>масштаб <b>{{ num(scale, 2) }}</b></span>
        <input type="range" min="0.85" max="1.15" step="0.01" v-model.number="scale" /></label>
      <label class="lab__ctl"><span>зсув x <b>{{ num(tx, 0) }}</b> px</span>
        <input type="range" min="-20" max="20" step="1" v-model.number="tx" /></label>
      <label class="lab__ctl"><span>зсув y <b>{{ num(ty, 0) }}</b> px</span>
        <input type="range" min="-20" max="20" step="1" v-model.number="ty" /></label>
      <label class="lab__ctl"><span>яскравість <b>{{ num(bright, 2) }}</b></span>
        <input type="range" min="-0.2" max="0.2" step="0.01" v-model.number="bright" /></label>
      <label class="lab__ctl"><span>контраст <b>{{ num(contrast, 2) }}</b></span>
        <input type="range" min="0.7" max="1.3" step="0.01" v-model.number="contrast" /></label>
      <label class="lab__ctl"><span>гамма <b>{{ num(gamma, 2) }}</b></span>
        <input type="range" min="0.6" max="1.6" step="0.01" v-model.number="gamma" /></label>
      <label class="lab__ctl"><span>шум σ <b>{{ num(noise, 3) }}</b></span>
        <input type="range" min="0" max="0.08" step="0.002" v-model.number="noise" /></label>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" type="button" :class="{ 'is-on': flip }" @click="flip = !flip">
        горизонтальне віддзеркалення: {{ flip ? 'увімкнено' : 'вимкнено' }}</button>
      <button class="lab__pill" type="button" @click="randomize">випадкова аугментація без віддзеркалення</button>
      <button class="lab__pill" type="button" @click="reset">скинути</button>
    </div>

    <div class="ag__grid">
      <div class="ag__frame">
        <canvas ref="canvas" :width="S" :height="S" aria-label="Знімок після аугментації"></canvas>
        <svg :viewBox="`0 0 ${S} ${S}`" class="ag__ov" aria-hidden="true">
          <line :x1="S / 2" :x2="S / 2" y1="0" :y2="S" class="ag__mid" />
          <polygon v-for="(p, k) in paths" :key="k" :points="p" :style="{ stroke: COL[k] }" class="ag__ct" />
          <circle :cx="(hc[0] + 0.5) * S / G" :cy="(hc[1] + 0.5) * S / G" r="3.2" class="ag__hc" />
        </svg>
        <div v-if="!ready" class="ag__status">завантаження знімка…</div>
      </div>
      <div>
        <div class="lab__stats ag__stats">
          <div class="lab__stat" :class="{ 'is-warm': flip }"><b>{{ num(hc[0]) }}</b>
            <span>x центру серця, px із {{ G }} (середина кадру — {{ num(MID) }})</span></div>
          <div class="lab__stat"><b>{{ num(hc[1]) }}</b><span>y центру серця, px</span></div>
        </div>
        <p class="ag__side" :class="{ 'is-bad': flip }">Серце {{ side }}.</p>
        <p class="ag__hint">Пунктир — середина кадру. Поворот і масштаб лишають серце праворуч; великий зсув уліво може
          перетягнути центр через пунктир, але серце лишається з лівого боку тіла. Віддзеркалення змінює саму анатомію.</p>
      </div>
    </div>

    <p class="lab__note">
      Без перетворень центр серця лежить при x = {{ num(data.heart[0]) }}, праворуч від середини кадру, як у 99,2 % знімків
      SCR. Увімкніть віддзеркалення — x стає {{ num(data.heart_flip_x) }}: знімок показує анатомію, якої в клініці майже
      не буває. Кнопка «випадкова аугментація» тягне параметри з діапазонів, у яких мітка «туберкульоз чи ні» лишається
      правильною.
    </p>
  </div>
</template>

<style scoped>
.ag__grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 1.1rem; align-items: start; }
@media (max-width: 720px) { .ag__grid { grid-template-columns: 1fr; } }
.ag__frame { position: relative; width: 100%; max-width: 420px; aspect-ratio: 1 / 1; background: #000; border-radius: 6px; overflow: hidden; }
.ag__frame canvas, .ag__ov { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.ag__ct { fill: none; stroke-width: 1.1; opacity: 0.9; }
.ag__mid { stroke: rgba(255, 255, 255, 0.55); stroke-dasharray: 3 3; stroke-width: 0.8; }
.ag__hc { fill: #33c3ff; stroke: #000; stroke-width: 0.8; }
.ag__status { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #ddd; font-size: 0.8rem; }
.ag__stats { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 0; }
.ag__side { font-size: 0.86rem; margin: 0.7rem 0 0.3rem; color: var(--vp-c-text-1); }
.ag__side.is-bad { color: var(--uk-warm); font-weight: 600; }
.ag__hint { font-size: 0.78rem; color: var(--vp-c-text-3); line-height: 1.45; margin: 0; }
</style>
