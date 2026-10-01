<script setup lang="ts">
/**
 * Гаусове згладжування зрізу КТ: σ у міліметрах проти шуму і ширини краю (лекція 06, розділ
 * «Згладжування: гаусів, медіанний, білатеральний»). Числа (СКО в аорті, ширина краю 10–90 %,
 * профіль рядка 350) порахував tools/gen_lec06_gauss.py на повному зрізі тим самим кодом, що блок
 * коду лекції: при σ = 1 мм — 9,1 HU і 3,8 мм, без фільтра — 15,0 HU і 1,9 мм. Картинка — сирий
 * фрагмент 70 × 70, згладжений тут у браузері (ілюстрація, з дзеркальним краєм, як у scipy).
 */
import { ref, computed, watch, onMounted } from 'vue'
import data from '../../data/lec06_gauss.json'

type Row = { sigma: number; sigma_px: number; noise: number; width: number; x90: number; x10: number; profile: number[] }
const ROWS = data.rows as Row[]
const N = data.crop[2] as number
const RAW = Float64Array.from(data.raw as number[])
const PX = data.pixel as number
const PR = data.profile_row as number
const [PC0, PC1] = data.profile_cols as number[]

const idx = ref(4) // σ = 1 мм
const row = computed(() => ROWS[idx.value])
const raw = ROWS[0]
const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')

/** Сепарабельне гаусове згладжування з дзеркальним краєм (scipy.ndimage, mode='reflect', truncate=4) */
function blur(src: Float64Array, s: number): Float64Array {
  if (s <= 0) return src
  const rad = Math.floor(4 * s + 0.5)
  const k: number[] = []
  let sum = 0
  for (let t = -rad; t <= rad; t++) { const v = Math.exp(-(t * t) / (2 * s * s)); k.push(v); sum += v }
  for (let t = 0; t < k.length; t++) k[t] /= sum
  const refl = (i: number) => { while (i < 0 || i >= N) i = i < 0 ? -i - 1 : 2 * N - i - 1; return i }
  const tmp = new Float64Array(N * N)
  const out = new Float64Array(N * N)
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let acc = 0
    for (let t = -rad; t <= rad; t++) acc += k[t + rad] * src[y * N + refl(x + t)]
    tmp[y * N + x] = acc
  }
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let acc = 0
    for (let t = -rad; t <= rad; t++) acc += k[t + rad] * tmp[refl(y + t) * N + x]
    out[y * N + x] = acc
  }
  return out
}

const canvas = ref<HTMLCanvasElement | null>(null)
function draw() {
  const cv = canvas.value
  if (!cv) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(N, N)
  const sm = blur(RAW, row.value.sigma_px)
  const lo = 40 - 200
  for (let p = 0; p < N * N; p++) {
    const g = Math.max(0, Math.min(255, Math.round(((sm[p] - lo) / 400) * 255)))
    img.data[4 * p] = g; img.data[4 * p + 1] = g; img.data[4 * p + 2] = g; img.data[4 * p + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
}
onMounted(draw)
watch([idx, canvas], draw, { flush: 'post' })

/* Графік профілю: x — мм уздовж рядка, y — HU */
const W = 360, H = 200, PL = 46, PRt = 10, PT = 10, PB = 32
const XMAX = (PC1 - PC0 - 1) * PX
const Y0 = -950, Y1 = 250
const X = (mm: number) => PL + (mm / XMAX) * (W - PL - PRt)
const Y = (hu: number) => PT + (1 - (hu - Y0) / (Y1 - Y0)) * (H - PT - PB)
const path = (p: number[]) => p.map((v, i) => `${X(i * PX).toFixed(1)},${Y(v).toFixed(1)}`).join(' ')
const yTicks = [-800, -600, -400, -200, 0, 200]
const xTicks = [0, 5, 10, 15, 20, 25]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Гаусів фільтр: σ у міліметрах, шум і ширина краю</div>
        <div class="lab__sub">
          Зріз z = −117,5 мм LIDC-IDRI-0001. Числа пораховано на повному зрізі 512 × 512, як у блоці коду;
          картинка — фрагмент біля межі «грудна стінка — легеня», вікно 40/400.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>σ гаусіани: <b>{{ num(row.sigma, 2) }} мм</b> = {{ num(row.sigma_px, 2) }} px</span>
        <input v-model.number="idx" type="range" min="0" :max="ROWS.length - 1" step="1" aria-label="σ гаусіани">
      </label>
    </div>

    <div class="ge__grid">
      <div class="ge__imgwrap">
        <canvas ref="canvas" :width="N" :height="N" aria-label="Фрагмент зрізу після згладжування"></canvas>
        <svg class="ge__over" :viewBox="`0 0 ${N} ${N}`" aria-hidden="true">
          <line :x1="PC0" :x2="PC1 - 1" :y1="PR + 0.5" :y2="PR + 0.5" class="ge__prof" />
        </svg>
        <div class="ge__cap">Лінія — профіль рядка 350; квадрат аорти для СКО (рядки 312–327, стовпці 260–275) лежить поза фрагментом.</div>
      </div>
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Профіль HU через межу при вибраному σ">
        <g v-for="t in yTicks" :key="'y' + t">
          <line :x1="PL" :x2="W - PRt" :y1="Y(t)" :y2="Y(t)" class="ge__grid-line" />
          <text :x="PL - 4" :y="Y(t) + 3" text-anchor="end" class="ge__lbl">{{ num(t, 0) }}</text>
        </g>
        <text v-for="t in xTicks" :key="'x' + t" :x="X(t)" :y="H - PB + 13" text-anchor="middle" class="ge__lbl">{{ t }}</text>
        <polyline :points="path(raw.profile)" class="ge__raw" />
        <polyline :points="path(row.profile)" class="ge__cur" />
        <line :x1="X(row.x90)" :x2="X(row.x90)" :y1="PT" :y2="H - PB" class="ge__mark" />
        <line :x1="X(row.x10)" :x2="X(row.x10)" :y1="PT" :y2="H - PB" class="ge__mark" />
        <text :x="(PL + W - PRt) / 2" :y="H - 3" text-anchor="middle" class="ge__lbl">відстань уздовж рядка 350, мм</text>
        <text x="10" :y="(PT + H - PB) / 2" text-anchor="middle" class="ge__lbl"
              :transform="`rotate(-90 10 ${(PT + H - PB) / 2})`">HU</text>
      </svg>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(row.noise, 1) }} HU</b><span>СКО в аорті (без фільтра {{ num(raw.noise, 1) }})</span></div>
      <div class="lab__stat is-warm"><b>{{ num(row.width, 1) }} мм</b><span>край 10–90 % (без фільтра {{ num(raw.width, 1) }})</span></div>
      <div class="lab__stat"><b>{{ num(row.sigma_px, 2) }} px</b><span>той самий σ у пікселях 0,703125 мм</span></div>
    </div>

    <p class="lab__note">
      Сіра штрихова лінія — профіль без фільтра, кольорова — після згладжування; вертикальні лінії — рівні 90 % і 10 %
      перепаду. Ширина краю росте з σ майже лінійно, а СКО в квадраті 16 × 16 пікселів аорти падає лише до σ ≈ 1,5 мм:
      далі гаусіана захоплює стінку аорти, і розкид дає вже не шум, а розмитий край. Згладжувати сильніше, ніж розмір
      структури, яку треба виміряти, означає вимірювати фільтр, а не тканину.
    </p>
  </div>
</template>

<style scoped>
.ge__grid {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.3fr);
  gap: 1rem;
  align-items: start;
}
@media (max-width: 680px) { .ge__grid { grid-template-columns: 1fr; } }
.ge__grid svg { width: 100%; height: auto; display: block; }
.ge__imgwrap { position: relative; max-width: 260px; width: 100%; }
.ge__imgwrap canvas { width: 100%; height: auto; display: block; image-rendering: pixelated; border-radius: 6px; }
.ge__over { position: absolute; left: 0; top: 0; width: 100%; height: auto; aspect-ratio: 1 / 1; }
.ge__prof { stroke: var(--uk-accent); stroke-width: 1; }
.ge__cap { font-size: 0.75rem; color: var(--vp-c-text-3); margin-top: 0.3rem; line-height: 1.4; }
.ge__grid-line { stroke: var(--uk-line); stroke-width: 0.6; }
.ge__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.ge__raw { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1.2; stroke-dasharray: 4 3; }
.ge__cur { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
.ge__mark { stroke: var(--uk-warm); stroke-width: 1; stroke-dasharray: 3 3; }
</style>
