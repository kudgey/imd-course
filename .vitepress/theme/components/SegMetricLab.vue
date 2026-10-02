<script setup lang="ts">
/**
 * Метрики сегментації на спотвореній масці (лекція 10, розділ «Відстань Гаусдорфа, HD95 і середня
 * поверхнева відстань»). Еталон — маска обох легень пацієнта JPCNN012 (контури SCR, CC BY 4.0),
 * 256 × 256, піксель 1,4 мм; дані — tools/gen_lec10_metrics.py. Спотворення робляться тут так само,
 * як у генераторі й у блоці коду: розширення диском x² + y² ≤ r² (= distance_transform_edt ≤ r),
 * звуження як доповнення розширення фону, зсув униз (np.roll), острівець — диск skimage.draw.disk
 * (x² + y² < R²) у найдальшій від маски точці кадру. Dice та IoU рахуються в браузері й звіряються з
 * таблицею генератора; HD, HD95 і ASSD — з таблиці (ті самі формули, що в коді).
 */
import { ref, computed, watch, onMounted } from 'vue'
import data from '../../data/lec10_metrics.json'

const N = data.n as number
const PX = data.px as number
const TABLE = data.table as Record<string, number[]>
const CENTRE = data.centre as number[]

function unpack(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(N * N)
  for (let i = 0; i < out.length; i++) out[i] = (bin.charCodeAt(i >> 3) >> (7 - (i & 7))) & 1
  return out
}
const REF = unpack(data.ref as string)

/** Розширення диском радіуса r: піксель стає маскою, якщо в диску x² + y² ≤ r² є піксель маски */
function grow(m: Uint8Array, r: number): Uint8Array {
  if (r === 0) return m.slice()
  const W = N + 1
  const pre = new Int32Array(N * W)
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) pre[y * W + x + 1] = pre[y * W + x] + m[y * N + x]
  const half: number[] = []
  for (let dy = -r; dy <= r; dy++) half.push(Math.floor(Math.sqrt(r * r - dy * dy) + 1e-9))
  const out = new Uint8Array(N * N)
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    for (let dy = -r; dy <= r; dy++) {
      const yy = y + dy
      if (yy < 0 || yy >= N) continue
      const w = half[dy + r]
      const a = Math.max(0, x - w), b = Math.min(N - 1, x + w)
      if (pre[yy * W + b + 1] - pre[yy * W + a] > 0) { out[y * N + x] = 1; break }
    }
  }
  return out
}
const invert = (m: Uint8Array) => m.map(v => 1 - v)

const r = ref(0)
const shift = ref(0)
const island = ref(0)
const ISLANDS = data.islands as number[]

const pred = computed(() => {
  let m = r.value > 0 ? grow(REF, r.value) : r.value < 0 ? invert(grow(invert(REF), -r.value)) : REF.slice()
  if (shift.value) {
    const s = shift.value
    const rolled = new Uint8Array(N * N)
    for (let y = 0; y < N; y++) rolled.set(m.subarray(y * N, y * N + N), ((y + s) % N) * N)
    m = rolled
  }
  if (island.value) {
    const R = island.value
    for (let dy = -R; dy <= R; dy++) for (let dx = -R; dx <= R; dx++) {
      const yy = CENTRE[0] + dy, xx = CENTRE[1] + dx
      if (dy * dy + dx * dx < R * R && yy >= 0 && yy < N && xx >= 0 && xx < N) m[yy * N + xx] = 1
    }
  }
  return m
})
const live = computed(() => {
  let inter = 0, a = 0, b = 0
  const p = pred.value
  for (let i = 0; i < p.length; i++) { inter += p[i] & REF[i]; a += p[i]; b += REF[i] }
  return { dice: (2 * inter) / (a + b), iou: inter / (a + b - inter), area: a }
})
const row = computed(() => TABLE[`${r.value}|${shift.value}|${island.value}`])
const same = computed(() => Math.abs(live.value.dice - row.value[0]) < 6e-5 && Math.abs(live.value.iou - row.value[1]) < 6e-5)
const num = (v: number, k = 3) => v.toFixed(k).replace('.', ',')

const canvas = ref<HTMLCanvasElement | null>(null)
function draw() {
  const cv = canvas.value
  if (!cv) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(N, N)
  const p = pred.value
  for (let i = 0; i < N * N; i++) {
    const y = Math.floor(i / N), x = i % N
    const edge = REF[i] && ((y > 0 && !REF[i - N]) || (y < N - 1 && !REF[i + N]) || (x > 0 && !REF[i - 1]) || (x < N - 1 && !REF[i + 1]))
    let c = [240, 239, 236]
    if (p[i] && REF[i]) c = [193, 199, 238]
    else if (p[i]) c = [255, 79, 163]
    else if (REF[i]) c = [180, 83, 31]
    if (edge) c = [27, 27, 39]
    const q = 4 * i
    img.data[q] = c[0]; img.data[q + 1] = c[1]; img.data[q + 2] = c[2]; img.data[q + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
}
onMounted(draw)
watch([pred, canvas], draw, { flush: 'post' })
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Одна маска — п’ять метрик: Dice, IoU, HD, HD95, ASSD</div>
        <div class="lab__sub">
          Еталон — обидві легені пацієнта {{ data.name }} (контури SCR, {{ data.area }} пікселів 256 × 256, піксель
          {{ num(PX, 1) }} мм). «Прогноз» — той самий еталон зі спотвореннями; острівець стоїть за {{ num(data.far_mm as number, 0) }} мм від маски.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>межа: <b>{{ r > 0 ? `розширення на ${r} px` : r < 0 ? `звуження на ${-r} px` : 'без змін' }}</b></span>
        <input v-model.number="r" type="range" min="-5" max="5" step="1" aria-label="Розширення або звуження межі">
      </label>
      <label class="lab__ctl">
        <span>зсув униз: <b>{{ shift }} px ({{ num(shift * PX, 1) }} мм)</b></span>
        <input v-model.number="shift" type="range" min="0" max="10" step="1" aria-label="Зсув униз">
      </label>
    </div>
    <div class="lab__pills">
      <span class="sm__lbl">острівець:</span>
      <button v-for="R in ISLANDS" :key="R" type="button" class="lab__pill" :class="{ 'is-on': island === R }"
              @click="island = R">{{ R ? `радіус ${R} px` : 'немає' }}</button>
    </div>

    <div class="sm__grid">
      <div class="sm__frame">
        <canvas ref="canvas" :width="N" :height="N" aria-label="Еталон і спотворена маска на нейтральному тлі"></canvas>
      </div>
      <div class="sm__side">
        <div class="sm__legend">
          <span><i style="background:#c1c7ee"></i>спільна площа</span>
          <span><i style="background:#ff4fa3"></i>зайве в прогнозі (FP)</span>
          <span><i style="background:#b4531f"></i>пропущене (FN)</span>
          <span><i style="background:#1b1b27"></i>межа еталона</span>
        </div>
        <div class="lab__stats">
          <div class="lab__stat is-warm"><b>{{ num(live.dice) }}</b><span>Dice</span></div>
          <div class="lab__stat"><b>{{ num(live.iou) }}</b><span>IoU</span></div>
          <div class="lab__stat is-warm"><b>{{ num(row[2], 1) }}</b><span>HD, мм</span></div>
          <div class="lab__stat"><b>{{ num(row[3], 1) }}</b><span>HD95, мм</span></div>
          <div class="lab__stat"><b>{{ num(row[4], 2) }}</b><span>ASSD, мм</span></div>
          <div class="lab__stat" :class="same ? 'is-green' : 'is-warm'"><b>{{ same ? 'так' : 'ні' }}</b>
            <span>Dice та IoU збігаються з таблицею генератора</span></div>
        </div>
      </div>
    </div>

    <p class="lab__note">
      Розширення на r px зсуває HD95 рівно на r пікселів, а Dice при 1–2 px майже не змінюється. Звуження б’є по HD
      сильніше, ніж розширення: тонкі кути легень зникають цілком. Острівець будь-якого радіуса підкидає HD до
      відстані до острівця, а HD95 лишає нулем — точок межі острівця менше за 5 % усіх точок межі. Додайте до
      острівця зсув: HD95 тепер показує зсув, а HD — острівець.
    </p>
  </div>
</template>

<style scoped>
.sm__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 680px) { .sm__grid { grid-template-columns: 1fr; } }
.sm__frame { width: 100%; max-width: 400px; aspect-ratio: 1 / 1; }
.sm__frame canvas { width: 100%; height: 100%; image-rendering: pixelated; border-radius: 6px; display: block; }
.sm__lbl { font-size: 0.85rem; color: var(--vp-c-text-2); align-self: center; margin-right: 0.3rem; }
.sm__legend { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem; color: var(--vp-c-text-2); }
.sm__legend i { display: inline-block; width: 14px; height: 10px; border-radius: 2px; margin-right: 0.4rem; vertical-align: middle; }
.sm__side .lab__stats { margin-top: 0.8rem; }
</style>
