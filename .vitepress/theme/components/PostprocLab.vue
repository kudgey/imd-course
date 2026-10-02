<script setup lang="ts">
/**
 * Постобробка маски U-Net (лекція 10, розділ «Постобробка: компоненти, дірки, морфологія»).
 * Дані — tools/gen_lec10_postproc.py: для 16 комбінацій кроків (дві найбільші компоненти, заповнення
 * дірок, відкриття диском r = 0…3 px; порядок той самий, що в коді) — середній Dice, середній HD95 і
 * кількість знімків із > 2 компонентами на валідації й тесті JSRT та на Montgomery. Приклад — сира маска
 * одного знімка JSRT і еталон SCR (лише маски, без знімка); кроки повторюються тут у браузері (8-зв’язні
 * компоненти як skimage.measure.label, заповнення через 4-зв’язний фон як binary_fill_holes, відкриття
 * диском x² + y² ≤ r² із фоном за межею кадру як scipy), Dice звіряється з таблицею генератора.
 */
import { ref, computed, watch, onMounted } from 'vue'
import data from '../../data/lec10_postproc.json'

const N = 256
const TABLE = data.table as Record<string, Record<'val' | 'test' | 'mont', number[]>>
const EX = data.ex as Record<string, number[]>

function unpack(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(N * N)
  for (let i = 0; i < out.length; i++) out[i] = (bin.charCodeAt(i >> 3) >> (7 - (i & 7))) & 1
  return out
}
const RAW = unpack(data.raw as string)
const REF = unpack(data.ref as string)

/** 8-зв’язні компоненти: мітки й розміри */
function components(m: Uint8Array): { lab: Int32Array; sizes: number[] } {
  const lab = new Int32Array(N * N)
  const sizes: number[] = [0]
  for (let s = 0; s < N * N; s++) {
    if (!m[s] || lab[s]) continue
    const id = sizes.length
    let count = 0
    const stack = [s]
    lab[s] = id
    while (stack.length) {
      const i = stack.pop()!
      count++
      const y = Math.floor(i / N), x = i % N
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const yy = y + dy, xx = x + dx
        if ((dy || dx) && yy >= 0 && yy < N && xx >= 0 && xx < N) {
          const j = yy * N + xx
          if (m[j] && !lab[j]) { lab[j] = id; stack.push(j) }
        }
      }
    }
    sizes.push(count)
  }
  return { lab, sizes }
}
function keep2(m: Uint8Array): Uint8Array {
  const { lab, sizes } = components(m)
  const order = sizes.map((v, i) => [v, i]).slice(1).sort((a, b) => b[0] - a[0]).slice(0, 2).map(p => p[1])
  return Uint8Array.from(lab, v => (v && order.includes(v) ? 1 : 0))
}
function fillHoles(m: Uint8Array): Uint8Array {
  const outside = new Uint8Array(N * N)
  const stack: number[] = []
  const push = (i: number) => { if (!m[i] && !outside[i]) { outside[i] = 1; stack.push(i) } }
  for (let k = 0; k < N; k++) { push(k); push((N - 1) * N + k); push(k * N); push(k * N + N - 1) }
  while (stack.length) {
    const i = stack.pop()!
    const y = Math.floor(i / N), x = i % N
    if (y > 0) push(i - N)
    if (y < N - 1) push(i + N)
    if (x > 0) push(i - 1)
    if (x < N - 1) push(i + 1)
  }
  return Uint8Array.from(outside, v => 1 - v)
}
/** Ерозія (all = true) або дилатація диском радіуса r; за межею кадру — фон, як у scipy */
function morph(m: Uint8Array, r: number, all: boolean): Uint8Array {
  const W = N + 1
  const pre = new Int32Array(N * W)
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) pre[y * W + x + 1] = pre[y * W + x] + m[y * N + x]
  const half: number[] = []
  for (let dy = -r; dy <= r; dy++) half.push(Math.floor(Math.sqrt(r * r - dy * dy) + 1e-9))
  const out = new Uint8Array(N * N)
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let ok = all
    for (let dy = -r; dy <= r; dy++) {
      const w = half[dy + r], yy = y + dy
      if (all) {
        if (yy < 0 || yy >= N || x - w < 0 || x + w >= N) { ok = false; break }
        if (pre[yy * W + x + w + 1] - pre[yy * W + x - w] !== 2 * w + 1) { ok = false; break }
      } else {
        if (yy < 0 || yy >= N) continue
        const a = Math.max(0, x - w), b = Math.min(N - 1, x + w)
        if (pre[yy * W + b + 1] - pre[yy * W + a] > 0) { ok = true; break }
      }
    }
    out[y * N + x] = ok ? 1 : 0
  }
  return out
}

const k2 = ref(true)
const fh = ref(true)
const r = ref(0)
const key = computed(() => `${k2.value ? 1 : 0}|${fh.value ? 1 : 0}|${r.value}`)
const mask = computed(() => {
  let m = RAW
  if (k2.value) m = keep2(m)
  if (fh.value) m = fillHoles(m)
  if (r.value) m = morph(morph(m, r.value, true), r.value, false)
  return m
})
const live = computed(() => {
  let inter = 0, a = 0, b = 0
  for (let i = 0; i < N * N; i++) { inter += mask.value[i] & REF[i]; a += mask.value[i]; b += REF[i] }
  return { dice: (2 * inter) / (a + b), comps: components(mask.value).sizes.length - 1 }
})
const same = computed(() => Math.abs(live.value.dice - EX[key.value][0]) < 6e-5 && live.value.comps === EX[key.value][2])
const row = computed(() => TABLE[key.value])
const base = TABLE['0|0|0']
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const PARTS = [
  { id: 'val', label: `валідація JSRT (${data.n.val})` },
  { id: 'test', label: `тест JSRT (${data.n.test})` },
  { id: 'mont', label: `Montgomery (${data.n.mont})` },
] as const

const canvas = ref<HTMLCanvasElement | null>(null)
function draw() {
  const cv = canvas.value
  if (!cv) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(N, N)
  const m = mask.value
  for (let i = 0; i < N * N; i++) {
    const y = Math.floor(i / N), x = i % N
    const edge = REF[i] && ((y > 0 && !REF[i - N]) || (y < N - 1 && !REF[i + N]) || (x > 0 && !REF[i - 1]) || (x < N - 1 && !REF[i + 1]))
    let c = [240, 239, 236]
    if (m[i] && REF[i]) c = [193, 199, 238]
    else if (m[i]) c = [255, 79, 163]
    else if (RAW[i]) c = [190, 190, 196]
    if (edge) c = [27, 27, 39]
    const p = 4 * i
    img.data[p] = c[0]; img.data[p + 1] = c[1]; img.data[p + 2] = c[2]; img.data[p + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
}
onMounted(draw)
watch([mask, canvas], draw, { flush: 'post' })
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Постобробка маски: що змінює кожен крок</div>
        <div class="lab__sub">
          Маска U-Net після порогу t* = {{ num(data.t_star as number, 2) }}, далі кроки в порядку з коду. Таблиця — середні по знімках
          трьох частин; праворуч — знімок {{ data.example }}, у якого після порогу найбільше компонент (лише маски).
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl pp__check"><input v-model="k2" type="checkbox"><span>лишити дві найбільші компоненти</span></label>
      <label class="lab__ctl pp__check"><input v-model="fh" type="checkbox"><span>заповнити дірки</span></label>
      <label class="lab__ctl">
        <span>відкриття диском: <b>{{ r ? `r = ${r} px` : 'вимкнено' }}</b></span>
        <input v-model.number="r" type="range" min="0" max="3" step="1" aria-label="Радіус відкриття">
      </label>
    </div>
    <div class="pp__grid">
      <div class="pp__wrap">
        <table class="pp__table">
          <thead><tr><th>частина</th><th>Dice</th><th>HD95, мм</th><th>&gt; 2 компонент</th></tr></thead>
          <tbody>
            <tr v-for="p in PARTS" :key="p.id">
              <td>{{ p.label }}</td>
              <td class="pp__num">{{ num(row[p.id][0]) }}</td>
              <td class="pp__num">{{ num(row[p.id][1], 2) }}<span class="pp__was">без кроків {{ num(base[p.id][1], 2) }}</span></td>
              <td class="pp__num">{{ row[p.id][2] }}<span class="pp__was">без кроків {{ base[p.id][2] }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pp__side">
        <div class="pp__frame"><canvas ref="canvas" :width="N" :height="N" aria-label="Маска після постобробки на нейтральному тлі"></canvas></div>
        <div class="pp__legend">
          <span><i style="background:#c1c7ee"></i>маска ∩ еталон</span>
          <span><i style="background:#ff4fa3"></i>зайве (FP)</span>
          <span><i style="background:#bebec4"></i>прибрано кроками</span>
          <span><i style="background:#1b1b27"></i>межа еталона</span>
        </div>
      </div>
    </div>
    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(live.dice) }}</b><span>Dice прикладу</span></div>
      <div class="lab__stat"><b>{{ live.comps }}</b><span>компонент у масці прикладу</span></div>
      <div class="lab__stat" :class="same ? 'is-green' : 'is-warm'"><b>{{ same ? 'так' : 'ні' }}</b><span>збігається з таблицею генератора</span></div>
    </div>
    <p class="lab__note">
      Dice майже не реагує на жоден крок: острівці займають сотні пікселів проти десятків тисяч у легенях. HD95
      реагує сильно, особливо на Montgomery, де острівців найбільше. Якщо дві компоненти вже лишено, відкриття з
      більшим радіусом різатиме тонкі кути легень, і середній HD95 знову росте; без цього кроку на Montgomery
      відкриття трохи допомагає. Рішення приймають за валідацією; тест і Montgomery тут лише для звіту.
    </p>
  </div>
</template>

<style scoped>
.pp__grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 680px) { .pp__grid { grid-template-columns: 1fr; } }
.pp__wrap { overflow-x: auto; }
.pp__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.pp__table th { font-weight: 500; font-size: 0.75rem; color: var(--vp-c-text-2); text-align: left; padding: 0.3rem 0.5rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; }
.pp__table td { font-size: 0.85rem; padding: 0.35rem 0.5rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; vertical-align: top; }
.pp__num { text-align: right; white-space: nowrap; }
.pp__was { display: block; font-size: 0.72rem; color: var(--vp-c-text-3); }
.pp__check { display: flex; gap: 0.5rem; align-items: center; }
.pp__check > span { margin: 0; }
.pp__frame { width: 100%; max-width: 300px; aspect-ratio: 1 / 1; }
.pp__frame canvas { width: 100%; height: 100%; image-rendering: pixelated; border-radius: 6px; display: block; }
.pp__legend { display: flex; flex-wrap: wrap; gap: 0.5rem 0.9rem; font-size: 0.8rem; color: var(--vp-c-text-2); margin-top: 0.4rem; }
.pp__legend i { display: inline-block; width: 14px; height: 10px; border-radius: 2px; margin-right: 0.35rem; vertical-align: middle; }
</style>
