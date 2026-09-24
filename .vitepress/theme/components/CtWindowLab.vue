<script setup lang="ts">
/**
 * Вікно КТ на справжньому зрізі LIDC-IDRI-0001 (z = −117,5 мм, зріз із найбільшим контуром вузла).
 * Формула — функція LINEAR стандарту DICOM (PS3.3 C.11.2.1.2.1), та сама, що в блоці коду лекції.
 * Частки «чорних» і «білих» рахуються з точної гістограми всього зрізу 512×512 у полі
 * реконструкції, тому на пресетах збігаються з виводом коду: тег серії −600/1600 → 0,0 % і 5,0 %;
 * пара 1 LIDC-IDRI-0957 45/400 → 60,8 % і 4,5 %; пара 2 −400/1750 → 0,0 % і 0,8 %;
 * кісткове 400/1800 → 58,0 % і 0,2 %. Дані пише tools/gen_lec03_window.py.
 */
import { ref, computed, watch, onMounted } from 'vue'
import data from '../../data/lec03_window.json'

type Preset = { name: string; c: number; w: number; black: number; white: number }

const presets = data.presets as Preset[]
const hist = data.hist as number[]
const histLo = data.hist_lo as number
const nFov = data.n_fov as number
const size = data.size as number
const nFovText = String(nFov).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

const c = ref(-600)
const w = ref(1600)
const canvas = ref<HTMLCanvasElement | null>(null)
const pixels = ref<Int16Array | null>(null)
const hover = ref<{ hu: number; i: number; j: number } | null>(null)

const lo = computed(() => c.value - 0.5 - (w.value - 1) / 2)
const hi = computed(() => c.value - 0.5 + (w.value - 1) / 2)

function gray(x: number, cc: number, ww: number): number {
  if (x <= cc - 0.5 - (ww - 1) / 2) return 0
  if (x > cc - 0.5 + (ww - 1) / 2) return 255
  return ((x - (cc - 0.5)) / (ww - 1) + 0.5) * 255
}

const frac = computed(() => {
  let black = 0
  let white = 0
  for (let k = 0; k < hist.length; k++) {
    const hu = histLo + k
    if (hu <= lo.value) black += hist[k]
    else if (hu > hi.value) white += hist[k]
  }
  return { black: black / nFov, white: white / nFov }
})

const pct = (v: number) => (v * 100).toFixed(1).replace('.', ',') + ' %'
const num = (v: number, d = 0) => v.toFixed(d).replace('.', ',').replace('-', '−')

function decode(): Int16Array {
  const bin = atob(data.img as string)
  const buf = new ArrayBuffer(bin.length)
  const u8 = new Uint8Array(buf)
  for (let k = 0; k < bin.length; k++) u8[k] = bin.charCodeAt(k)
  const view = new DataView(buf)
  const out = new Int16Array(bin.length / 2)
  for (let k = 0; k < out.length; k++) out[k] = view.getInt16(2 * k, true)
  return out
}

function draw() {
  const cv = canvas.value
  const px = pixels.value
  if (!cv || !px) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(size, size)
  for (let k = 0; k < px.length; k++) {
    const g = gray(px[k], c.value, w.value)
    img.data[4 * k] = g
    img.data[4 * k + 1] = g
    img.data[4 * k + 2] = g
    img.data[4 * k + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
}

onMounted(() => {
  pixels.value = decode()
  draw()
})
watch([c, w], draw)

function onMove(e: MouseEvent) {
  const cv = canvas.value
  const px = pixels.value
  if (!cv || !px) return
  const r = cv.getBoundingClientRect()
  const i = Math.min(size - 1, Math.max(0, Math.floor(((e.clientX - r.left) / r.width) * size)))
  const j = Math.min(size - 1, Math.max(0, Math.floor(((e.clientY - r.top) / r.height) * size)))
  hover.value = { hu: px[j * size + i], i: i * data.step, j: j * data.step }
}

function setPreset(p: Preset) {
  c.value = p.c
  w.value = p.w
}

/* Гістограма зрізу кошиками по 20 HU від −1100 до 1600, логарифмічна висота */
const H_LO = -1100
const H_HI = 1600
const BIN = 20
const SW = 360
const SH = 150
const PADL = 8
const bins = computed(() => {
  const n = (H_HI - H_LO) / BIN
  const arr = new Array(n).fill(0)
  for (let k = 0; k < hist.length; k++) {
    const hu = histLo + k
    if (hu < H_LO || hu >= H_HI) continue
    arr[Math.floor((hu - H_LO) / BIN)] += hist[k]
  }
  const top = Math.log10(Math.max(...arr) + 1)
  return arr.map((v, k) => ({ x: PADL + (k / n) * (SW - 2 * PADL), h: (Math.log10(v + 1) / top) * (SH - 36) }))
})
const sx = (hu: number) => PADL + ((Math.min(Math.max(hu, H_LO), H_HI) - H_LO) / (H_HI - H_LO)) * (SW - 2 * PADL)
const barW = ((SW - 2 * PADL) * BIN) / (H_HI - H_LO)
const curve = computed(() => {
  const pts: string[] = []
  for (let hu = H_LO; hu <= H_HI; hu += 10) {
    pts.push(`${sx(hu).toFixed(1)},${(SH - 20 - (gray(hu, c.value, w.value) / 255) * (SH - 36)).toFixed(1)}`)
  }
  return pts.join(' ')
})
const TICKS = [-1000, -500, 0, 500, 1000, 1500]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Вікно КТ: центр і ширина на справжньому зрізі</div>
        <div class="lab__sub">
          LIDC-IDRI-0001, зріз k = {{ data.k }} (z = −117,5 мм), значення в одиницях Гаунсфілда за тегами Rescale.
          Відображення — функція LINEAR зі стандарту DICOM. Частки рахуються для всіх
          {{ nFovText }} вокселів зрізу в полі реконструкції.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="p in presets" :key="p.name" class="lab__pill"
              :class="{ 'is-on': c === p.c && w === p.w }" @click="setPreset(p)">
        {{ p.name }}: {{ num(p.c) }}/{{ p.w }}
      </button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>центр c = <b>{{ num(c) }}</b> HU</span>
        <input type="range" min="-1200" max="400" step="1" v-model.number="c" />
      </label>
      <label class="lab__ctl">
        <span>ширина w = <b>{{ w }}</b> HU</span>
        <input type="range" min="1" max="2500" step="1" v-model.number="w" />
      </label>
    </div>

    <div class="cw__grid">
      <div class="cw__img">
        <canvas ref="canvas" :width="size" :height="size" @mousemove="onMove" @mouseleave="hover = null"
                aria-label="Зріз КТ у вибраному вікні"></canvas>
        <div class="cw__probe">
          <template v-if="hover">
            піксель (i = {{ hover.i }}, j = {{ hover.j }}): <b>{{ num(hover.hu) }} HU</b> → рівень сірого
            <b>{{ Math.round(gray(hover.hu, c, w)) }}</b>
          </template>
          <template v-else>наведіть курсор на зріз, щоб побачити HU вокселя і його рівень сірого</template>
        </div>
      </div>
      <div class="cw__hist">
        <div class="cw__cap">Гістограма зрізу (висота — логарифм числа вокселів) і функція вікна</div>
        <svg :viewBox="`0 0 ${SW} ${SH}`" role="img" aria-label="Гістограма HU з функцією вікна">
          <rect :x="sx(lo)" y="6" :width="Math.max(sx(hi) - sx(lo), 1)" :height="SH - 26" class="cw__band" />
          <rect v-for="(b, k) in bins" :key="k" :x="b.x" :y="SH - 20 - b.h" :width="barW" :height="b.h"
                class="cw__bar" />
          <polyline :points="curve" class="cw__curve" />
          <line :x1="PADL" :x2="SW - PADL" :y1="SH - 20" :y2="SH - 20" class="cw__axis" />
          <g v-for="t in TICKS" :key="t">
            <line :x1="sx(t)" :x2="sx(t)" :y1="SH - 20" :y2="SH - 16" class="cw__axis" />
            <text :x="sx(t)" :y="SH - 5" text-anchor="middle" class="cw__lbl">{{ num(t) }}</text>
          </g>
        </svg>
        <div class="cw__cap">Смуга — діапазон HU, що отримує проміжні рівні сірого:
          від {{ num(lo, 1) }} (не включно) до {{ num(hi, 1) }} HU.</div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ pct(frac.black) }}</b><span>вокселів чорні (HU ≤ {{ num(lo, 1) }})</span></div>
      <div class="lab__stat is-warm"><b>{{ pct(frac.white) }}</b><span>вокселів білі (HU &gt; {{ num(hi, 1) }})</span></div>
      <div class="lab__stat is-green"><b>{{ pct(1 - frac.black - frac.white) }}</b><span>отримують проміжний сірий</span></div>
      <div class="lab__stat"><b>{{ Math.round(gray(-872, c, w)) }}</b><span>рівень сірого для легені (медіана −872 HU)</span></div>
    </div>

    <p class="lab__note">
      На тезі серії (−600/1600) чорних вокселів у полі реконструкції немає зовсім: навіть повітря
      з медіаною −1012 HU отримує темно-сірий рівень, бо нижня межа вікна — −1400 HU. Білими стають
      5,0 % вокселів — кістки, аорта з контрастом і все, що вище 199 HU. Перемкніться на пару 1 з
      LIDC-IDRI-0957 (45/400): легеня вся стає чорною (60,8 % вокселів), а в м’яких тканинах
      з’являються відтінки, яких у легеневому вікні не видно. Вузол у лівій легені добре видно
      в обох вікнах, але його межу з легенею — лише в легеневому. Числа не змінюються, змінюється
      тільки те, що побачить око, — і що побачить модель, якщо їй подати вже «вікнований» знімок.
    </p>
  </div>
</template>

<style scoped>
.cw__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  gap: 1.1rem;
  align-items: start;
}
@media (max-width: 700px) { .cw__grid { grid-template-columns: 1fr; } }
.cw__img canvas {
  width: 100%;
  max-width: 420px;
  aspect-ratio: 1 / 1;
  image-rendering: pixelated;
  border-radius: 6px;
  background: #000;
  display: block;
  cursor: crosshair;
}
.cw__probe {
  font-size: 0.78rem;
  color: var(--vp-c-text-2);
  margin-top: 0.4rem;
  min-height: 2.4em;
  line-height: 1.4;
}
.cw__probe b { font-family: var(--vp-font-family-mono); color: var(--uk-accent); font-weight: 500; }
.cw__hist svg { width: 100%; height: auto; }
.cw__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.35rem; line-height: 1.4; }
.cw__band { fill: var(--uk-accent-soft); }
.cw__bar { fill: var(--uk-accent); opacity: 0.55; }
.cw__curve { fill: none; stroke: var(--uk-warm); stroke-width: 1.8; }
.cw__axis { stroke: var(--uk-line); stroke-width: 1; }
.cw__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
</style>
