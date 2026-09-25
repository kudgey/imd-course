<script setup lang="ts">
/**
 * Переглядач серії LIDC-IDRI-0001 (133 зрізи КТ) у трьох площинах з вікном LINEAR стандарту DICOM
 * (PS3.3 C.11.2.1.2.1) — тією самою функцією, що в блоці коду розділу «Вікно відображення».
 * Об’єм: /data/lec03/lidc0001_128x128x133_int16.bin — кожен четвертий рядок і стовпець
 * (роздільність у площині знижено в 4 рази), HU під курсором — значення цих вокселів.
 * Частки чорних і білих вокселів рахуються з точної гістограми еталонного зрізу z = −117,5 мм
 * у повній роздільності 512 × 512, тож на пресетах збігаються з виводом коду: тег серії −600/1600 →
 * 0,0 % і 5,0 %; пара 1 LIDC-IDRI-0957 45/400 → 60,8 % і 4,5 %; пара 2 −400/1750 → 0,0 % і 0,8 %;
 * кісткове 400/1800 → 58,0 % і 0,2 %. Дані пише tools/gen_lec03_window.py.
 */
import { ref, shallowRef, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec03_window.json'

type Preset = { name: string; c: number; w: number; black: number; white: number }
type Plane = 'axial' | 'coronal' | 'sagittal'

const [NZ, NY, NX] = data.shape as number[]
const STEP = data.step as number
const presets = data.presets as Preset[]
const hist = data.hist as number[]
const histLo = data.hist_lo as number
const nFov = data.n_fov as number
const [SY, SX, SZ] = data.spacing as number[]          // мм на піксель зниженої сітки: рядок, стовпець, зріз
const [PR, PC] = data.pixel as number[]               // мм на піксель повної роздільності
const [OX, OY] = data.origin as number[]
const kRef = data.k_ref as number
const NOD = data.nodule as number[]                   // центр вузла (i, j) у повній роздільності

const vol = shallowRef<Int16Array | null>(null)
const status = ref<'loading' | 'ok' | 'error'>('loading')
const plane = ref<Plane>('axial')
const k = ref(kRef)
const j = ref(Math.round(NOD[1] / STEP))
const i = ref(Math.round(NOD[0] / STEP))
const c = ref(-600)
const w = ref(1600)
const canvas = ref<HTMLCanvasElement | null>(null)
const hover = ref<{ hu: number; ii: number; jj: number; kk: number } | null>(null)

const PLANES: { id: Plane; label: string }[] = [
  { id: 'axial', label: 'аксіальна' },
  { id: 'coronal', label: 'корональна' },
  { id: 'sagittal', label: 'сагітальна' },
]

const num = (v: number, d = 0) => v.toFixed(d).replace('.', ',').replace('-', '−')
const pct = (v: number) => num(v * 100, 1) + ' %'
const spaced = (v: number) => String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

const lo = computed(() => c.value - 0.5 - (w.value - 1) / 2)
const hi = computed(() => c.value - 0.5 + (w.value - 1) / 2)

function gray(x: number, cc: number, ww: number): number {
  if (x <= cc - 0.5 - (ww - 1) / 2) return 0
  if (x > cc - 0.5 + (ww - 1) / 2) return 255
  return ((x - (cc - 0.5)) / (ww - 1) + 0.5) * 255
}

/** Частки чорних і білих вокселів еталонного зрізу за гістограмою повної роздільності */
const frac = computed(() => {
  let black = 0
  let white = 0
  for (let n = 0; n < hist.length; n++) {
    const hu = histLo + n
    if (hu <= lo.value) black += hist[n]
    else if (hu > hi.value) white += hist[n]
  }
  return { black: black / nFov, white: white / nFov }
})

/** Розміри поточного перерізу в пікселях сітки і в міліметрах */
const dims = computed(() => {
  if (plane.value === 'axial') return { w: NX, h: NY, mmW: NX * SX, mmH: NY * SY }
  if (plane.value === 'coronal') return { w: NX, h: NZ, mmW: NX * SX, mmH: NZ * SZ }
  return { w: NY, h: NZ, mmW: NY * SY, mmH: NZ * SZ }
})
const aspect = computed(() => `${dims.value.mmW.toFixed(1)} / ${dims.value.mmH.toFixed(1)}`)

/** Номер вокселя (k, рядок, стовпець) для пікселя (x, y) поточного перерізу */
function voxelAt(x: number, y: number): [number, number, number] {
  if (plane.value === 'axial') return [k.value, y, x]
  if (plane.value === 'coronal') return [NZ - 1 - y, j.value, x]
  return [NZ - 1 - y, x, i.value]
}

function draw() {
  const cv = canvas.value
  const v = vol.value
  if (!cv || !v) return
  const { w: W, h: H } = dims.value
  cv.width = W
  cv.height = H
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const lut = new Uint8ClampedArray(data.vmax - data.vmin + 1)
  for (let n = 0; n < lut.length; n++) lut[n] = gray(data.vmin + n, c.value, w.value)
  const img = ctx.createImageData(W, H)
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const [kk, jj, ii] = voxelAt(x, y)
      const g = lut[v[(kk * NY + jj) * NX + ii] - data.vmin]
      const p = 4 * (y * W + x)
      img.data[p] = g
      img.data[p + 1] = g
      img.data[p + 2] = g
      img.data[p + 3] = 255
    }
  }
  ctx.putImageData(img, 0, 0)
}

onMounted(async () => {
  try {
    const res = await fetch(withBase(data.bin as string))
    if (!res.ok) throw new Error(String(res.status))
    const buf = await res.arrayBuffer()
    const little = new Uint8Array(new Uint16Array([1]).buffer)[0] === 1
    let arr = new Int16Array(buf)
    if (!little) {
      const dv = new DataView(buf)
      arr = new Int16Array(buf.byteLength / 2)
      for (let n = 0; n < arr.length; n++) arr[n] = dv.getInt16(2 * n, true)
    }
    vol.value = arr
    status.value = 'ok'
  } catch {
    status.value = 'error'
  }
})
watch([vol, plane, k, j, i, c, w, canvas], draw, { flush: 'post' })

/** Лінії перетину з двома іншими площинами, у відсотках розміру перерізу */
const cross = computed(() => {
  const { w: W, h: H } = dims.value
  if (plane.value === 'axial') return { x: (i.value + 0.5) / W, y: (j.value + 0.5) / H }
  if (plane.value === 'coronal') return { x: (i.value + 0.5) / W, y: (NZ - 1 - k.value + 0.5) / H }
  return { x: (j.value + 0.5) / W, y: (NZ - 1 - k.value + 0.5) / H }
})
const showNodule = computed(() => plane.value === 'axial' && k.value === kRef)

function pixelOf(e: MouseEvent): [number, number] | null {
  const cv = canvas.value
  if (!cv) return null
  const r = cv.getBoundingClientRect()
  const { w: W, h: H } = dims.value
  const x = Math.floor(((e.clientX - r.left) / r.width) * W)
  const y = Math.floor(((e.clientY - r.top) / r.height) * H)
  if (x < 0 || y < 0 || x >= W || y >= H) return null
  return [x, y]
}
function onMove(e: MouseEvent) {
  const v = vol.value
  const p = pixelOf(e)
  if (!v || !p) {
    hover.value = null
    return
  }
  const [kk, jj, ii] = voxelAt(p[0], p[1])
  hover.value = { hu: v[(kk * NY + jj) * NX + ii], ii: ii * STEP, jj: jj * STEP, kk }
}
/** Клік переносить перетин двох інших площин у цю точку */
function onClick(e: MouseEvent) {
  const p = pixelOf(e)
  if (!p) return
  const [kk, jj, ii] = voxelAt(p[0], p[1])
  k.value = kk
  j.value = jj
  i.value = ii
}

const slice = computed({
  get: () => (plane.value === 'axial' ? k.value : plane.value === 'coronal' ? j.value : i.value),
  set: (v: number) => {
    if (plane.value === 'axial') k.value = v
    else if (plane.value === 'coronal') j.value = v
    else i.value = v
  },
})
const sliceMax = computed(() => (plane.value === 'axial' ? NZ - 1 : plane.value === 'coronal' ? NY - 1 : NX - 1))
const sliceLabel = computed(() => {
  if (plane.value === 'axial') return `зріз k = ${k.value}, z = ${num(data.z0 + k.value * SZ, 1)} мм`
  if (plane.value === 'coronal') return `рядок j = ${j.value * STEP}, y = ${num(OY + j.value * STEP * PR, 1)} мм`
  return `стовпець i = ${i.value * STEP}, x = ${num(OX + i.value * STEP * PC, 1)} мм`
})
function stepSlice(d: number) {
  slice.value = Math.min(sliceMax.value, Math.max(0, slice.value + d))
}
const LABELS: Record<Plane, [string, string, string, string]> = {
  axial: ['A', 'P', 'R', 'L'],
  coronal: ['S', 'I', 'R', 'L'],
  sagittal: ['S', 'I', 'A', 'P'],
}
function toReference() {
  plane.value = 'axial'
  k.value = kRef
  i.value = Math.round(NOD[0] / STEP)
  j.value = Math.round(NOD[1] / STEP)
}
function setPreset(p: Preset) {
  c.value = p.c
  w.value = p.w
}

/* Гістограма еталонного зрізу кошиками по 20 HU від −1100 до 1600, логарифмічна висота */
const H_LO = -1100
const H_HI = 1600
const BIN = 20
const SW = 360
const SH = 150
const PADL = 8
const bins = computed(() => {
  const n = (H_HI - H_LO) / BIN
  const arr = new Array(n).fill(0)
  for (let m = 0; m < hist.length; m++) {
    const hu = histLo + m
    if (hu < H_LO || hu >= H_HI) continue
    arr[Math.floor((hu - H_LO) / BIN)] += hist[m]
  }
  const top = Math.log10(Math.max(...arr) + 1)
  return arr.map((v, m) => ({ x: PADL + (m / n) * (SW - 2 * PADL), h: (Math.log10(v + 1) / top) * (SH - 36) }))
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
        <div class="lab__title">Серія КТ у трьох площинах: вікно, HU і міліметри</div>
        <div class="lab__sub">
          LIDC-IDRI-0001, 133 зрізи, одиниці Гаунсфілда за тегами Rescale, вікно — функція LINEAR стандарту
          DICOM. Роздільність у площині зрізу знижено в {{ STEP }} рази (кожен {{ STEP }}-й рядок і стовпець),
          тому HU під курсором — значення вокселя зниженої сітки. Пропорції перерізів — за розміром пікселя
          {{ num(PR, 6) }} мм і кроком між зрізами {{ num(SZ, 1) }} мм.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="p in presets" :key="p.name" class="lab__pill" type="button"
              :class="{ 'is-on': c === p.c && w === p.w }" @click="setPreset(p)">
        {{ p.name }}: {{ num(p.c) }}/{{ p.w }}
      </button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>центр c = <b>{{ num(c) }}</b> HU</span>
        <input type="range" min="-1200" max="1200" step="1" v-model.number="c" />
      </label>
      <label class="lab__ctl">
        <span>ширина w = <b>{{ w }}</b> HU</span>
        <input type="range" min="1" max="2500" step="1" v-model.number="w" />
      </label>
    </div>

    <div class="cw__grid">
      <div class="cw__view">
        <div class="lab__pills cw__planes">
          <button v-for="p in PLANES" :key="p.id" class="lab__pill" type="button"
                  :class="{ 'is-on': plane === p.id }" @click="plane = p.id">{{ p.label }}</button>
          <button class="lab__pill" type="button" @click="toReference">еталонний зріз</button>
        </div>
        <div class="cw__frame" :style="{ aspectRatio: aspect }">
          <canvas ref="canvas" :width="dims.w" :height="dims.h" @mousemove="onMove" @mouseleave="hover = null"
                  @click="onClick" aria-label="Переріз КТ у вибраному вікні"></canvas>
          <div class="cw__line cw__line--v" :style="{ left: `${cross.x * 100}%` }"></div>
          <div class="cw__line cw__line--h" :style="{ top: `${cross.y * 100}%` }"></div>
          <div v-if="showNodule" class="cw__nodule"
               :style="{ left: `${((NOD[0] + 0.5) / (NX * STEP)) * 100}%`, top: `${((NOD[1] + 0.5) / (NY * STEP)) * 100}%` }"
               title="центр вузла (314, 365, 89)"></div>
          <span class="cw__lab cw__lab--t">{{ LABELS[plane][0] }}</span>
          <span class="cw__lab cw__lab--b">{{ LABELS[plane][1] }}</span>
          <span class="cw__lab cw__lab--l">{{ LABELS[plane][2] }}</span>
          <span class="cw__lab cw__lab--r">{{ LABELS[plane][3] }}</span>
          <div v-if="status !== 'ok'" class="cw__status">
            {{ status === 'loading' ? 'завантаження об’єму (4,4 МБ)…' : 'не вдалося завантажити об’єм' }}
          </div>
        </div>
        <div class="cw__slice">
          <button class="lab__btn" type="button" aria-label="попередній" @click="stepSlice(-1)">−</button>
          <input type="range" min="0" :max="sliceMax" step="1" v-model.number="slice" aria-label="номер перерізу" />
          <button class="lab__btn" type="button" aria-label="наступний" @click="stepSlice(1)">+</button>
        </div>
        <div class="cw__probe">
          <div>{{ sliceLabel }}</div>
          <template v-if="hover">
            <div>
              <b>{{ num(hover.hu) }} HU</b> → рівень сірого <b>{{ Math.round(gray(hover.hu, c, w)) }}</b>;
              воксель (i, j, k) = ({{ hover.ii }}, {{ hover.jj }}, {{ hover.kk }})
            </div>
            <div>
              LPS ({{ num(OX + hover.ii * PC, 1) }}; {{ num(OY + hover.jj * PR, 1) }}; {{ num(data.z0 + hover.kk * SZ, 1) }}) мм
            </div>
          </template>
          <div v-else class="cw__hint">наведіть курсор на переріз — з’являться HU і координати; клік переносить перетин площин</div>
        </div>
      </div>

      <div class="cw__side">
        <div class="cw__cap">Гістограма еталонного зрізу z = −117,5 мм (висота — логарифм числа вокселів) і функція вікна</div>
        <svg :viewBox="`0 0 ${SW} ${SH}`" role="img" aria-label="Гістограма HU з функцією вікна">
          <rect :x="sx(lo)" y="6" :width="Math.max(sx(hi) - sx(lo), 1)" :height="SH - 26" class="cw__band" />
          <rect v-for="(b, m) in bins" :key="m" :x="b.x" :y="SH - 20 - b.h" :width="barW" :height="b.h" class="cw__bar" />
          <polyline :points="curve" class="cw__curve" />
          <line :x1="PADL" :x2="SW - PADL" :y1="SH - 20" :y2="SH - 20" class="cw__axis" />
          <g v-for="t in TICKS" :key="t">
            <line :x1="sx(t)" :x2="sx(t)" :y1="SH - 20" :y2="SH - 16" class="cw__axis" />
            <text :x="sx(t)" :y="SH - 5" text-anchor="middle" class="cw__lbl">{{ num(t) }}</text>
          </g>
        </svg>
        <div class="cw__cap">Смуга — HU, що отримують проміжні рівні сірого: від {{ num(lo, 1) }} (не включно)
          до {{ num(hi, 1) }} HU.</div>
        <div class="lab__stats cw__stats">
          <div class="lab__stat"><b>{{ pct(frac.black) }}</b><span>чорні (HU ≤ {{ num(lo, 1) }})</span></div>
          <div class="lab__stat is-warm"><b>{{ pct(frac.white) }}</b><span>білі (HU &gt; {{ num(hi, 1) }})</span></div>
          <div class="lab__stat is-green"><b>{{ pct(1 - frac.black - frac.white) }}</b><span>проміжний сірий</span></div>
          <div class="lab__stat"><b>{{ Math.round(gray(-872, c, w)) }}</b><span>сірий для легені (−872 HU)</span></div>
        </div>
        <div class="cw__cap">Частки — для {{ spaced(nFov) }} вокселів еталонного зрізу в полі реконструкції,
          у повній роздільності 512 × 512.</div>
      </div>
    </div>

    <p class="lab__note">
      На тезі серії (−600/1600) чорних вокселів у полі реконструкції немає: навіть повітря з медіаною −1012 HU
      отримує темно-сірий рівень, бо нижня межа вікна — −1400 HU. Перемкніться на пару 1 з LIDC-IDRI-0957
      (45/400) — легеня стає чорною (60,8 % вокселів еталонного зрізу), зате в м’яких тканинах з’являються
      відтінки. Гортайте корональні й сагітальні перерізи: з кроком 2,5 мм і пікселем 0,703125 мм тіло має
      правильні пропорції лише тоді, коли переглядач враховує обидва розміри вокселя. Вузол у лівій легені
      (на екрані праворуч) позначено колом на еталонному зрізі.
    </p>
  </div>
</template>

<style scoped>
.cw__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 1.1rem;
  align-items: start;
}
@media (max-width: 760px) { .cw__grid { grid-template-columns: 1fr; } }
.cw__planes { margin-bottom: 0.55rem; }
.cw__frame {
  position: relative;
  width: 100%;
  max-width: 440px;
  background: #000;
  border-radius: 6px;
  overflow: hidden;
}
.cw__frame canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  cursor: crosshair;
}
.cw__line { position: absolute; pointer-events: none; background: rgba(151, 162, 238, 0.55); }
.cw__line--v { top: 0; bottom: 0; width: 1px; }
.cw__line--h { left: 0; right: 0; height: 1px; }
.cw__nodule {
  position: absolute;
  width: 26px;
  height: 26px;
  margin: -13px 0 0 -13px;
  border: 2px solid #f2c94c;
  border-radius: 50%;
  pointer-events: none;
}
.cw__lab {
  position: absolute;
  font-size: 0.7rem;
  font-weight: 600;
  color: #f2c94c;
  pointer-events: none;
  text-shadow: 0 0 3px #000;
}
.cw__lab--t { top: 3px; left: 50%; transform: translateX(-50%); }
.cw__lab--b { bottom: 3px; left: 50%; transform: translateX(-50%); }
.cw__lab--l { left: 5px; top: 50%; transform: translateY(-50%); }
.cw__lab--r { right: 5px; top: 50%; transform: translateY(-50%); }
.cw__status {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ddd;
  font-size: 0.8rem;
  text-align: center;
  padding: 1rem;
}
.cw__slice {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  max-width: 440px;
  margin-top: 0.5rem;
}
.cw__slice input { flex: 1; min-width: 0; accent-color: var(--uk-accent); }
.cw__probe {
  font-size: 0.78rem;
  color: var(--vp-c-text-2);
  margin-top: 0.35rem;
  min-height: 3.6em;
  line-height: 1.45;
}
.cw__probe b { font-family: var(--vp-font-family-mono); color: var(--uk-accent); font-weight: 500; }
.cw__hint { color: var(--vp-c-text-3); }
.cw__side svg { width: 100%; height: auto; display: block; }
.cw__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.35rem; line-height: 1.4; }
.cw__stats { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 0.5rem; }
.cw__band { fill: var(--uk-accent-soft); }
.cw__bar { fill: var(--uk-accent); opacity: 0.55; }
.cw__curve { fill: none; stroke: var(--uk-warm); stroke-width: 1.8; }
.cw__axis { stroke: var(--uk-line); stroke-width: 1; }
.cw__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
</style>
