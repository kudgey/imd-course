<script setup lang="ts">
/**
 * Морфологія маски легень на зрізі КТ (лекція 06, розділ «Морфологія: ерозія, дилатація, відкриття,
 * закриття»). Еталонний зріз z = −117,5 мм LIDC-IDRI-0001, маска кроку 2 («HU ≤ −469 усередині тіла»)
 * і маска легень LUNA16 на тому самому зрізі — від tools/gen_lec06_morph.py. Операції рахуються тут,
 * у браузері, з диском x² + y² ≤ r² і фоном за межею кадру — як scipy.ndimage з
 * skimage.morphology.disk; «повний рецепт» додає дві найбільші 8-зв’язні компоненти і заповнення
 * дірок. Генератор поклав таблицю Dice для всіх комбінацій; віджет показує, чи збігся з нею власний
 * результат. Без операцій Dice 0,953 — те саме число, що крок 2 на зрізі 89 у виводі блоку коду.
 */
import { ref, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec06_morph.json'

type Op = 'erosion' | 'dilation' | 'opening' | 'closing' | 'fill'
const N = data.w as number // зріз квадратний: 512 × 512
const PX = data.pixel as number
const OPS: { id: Op; label: string }[] = [
  { id: 'erosion', label: 'ерозія' },
  { id: 'dilation', label: 'дилатація' },
  { id: 'opening', label: 'відкриття' },
  { id: 'closing', label: 'закриття' },
  { id: 'fill', label: 'заповнення дірок' },
]
const TABLE = data.table as Record<string, number[]>

function unpack(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(N * N)
  for (let i = 0; i < out.length; i++) out[i] = (bin.charCodeAt(i >> 3) >> (7 - (i & 7))) & 1
  return out
}
const LUNG = unpack(data.mask as string)
const REF = unpack(data.ref as string)

/** Ерозія (all = true) або дилатація диском радіуса r; за межею кадру — фон, як у scipy */
function morph(m: Uint8Array, r: number, all: boolean): Uint8Array {
  const pre = new Int32Array(N * (N + 1))
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) pre[y * (N + 1) + x + 1] = pre[y * (N + 1) + x] + m[y * N + x]
  const half: number[] = []
  for (let dy = -r; dy <= r; dy++) half.push(Math.floor(Math.sqrt(r * r - dy * dy) + 1e-9))
  const out = new Uint8Array(N * N)
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let ok = all
    for (let dy = -r; dy <= r; dy++) {
      const w = half[dy + r]
      const yy = y + dy
      if (all) {
        if (yy < 0 || yy >= N || x - w < 0 || x + w >= N) { ok = false; break }
        if (pre[yy * (N + 1) + x + w + 1] - pre[yy * (N + 1) + x - w] !== 2 * w + 1) { ok = false; break }
      } else {
        if (yy < 0 || yy >= N) continue
        const a = Math.max(0, x - w), b = Math.min(N - 1, x + w)
        if (pre[yy * (N + 1) + b + 1] - pre[yy * (N + 1) + a] > 0) { ok = true; break }
      }
    }
    out[y * N + x] = ok ? 1 : 0
  }
  return out
}

/** Заповнення дірок: фон, не з’єднаний 4-зв’язно з краєм кадру, стає маскою (як binary_fill_holes) */
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
  const out = new Uint8Array(N * N)
  for (let i = 0; i < out.length; i++) out[i] = outside[i] ? 0 : 1
  return out
}

/** Дві найбільші 8-зв’язні компоненти (як skimage.measure.label) і заповнення дірок */
function recipe(m: Uint8Array): Uint8Array {
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
  const order = sizes.map((v, i) => [v, i]).slice(1).sort((a, b) => b[0] - a[0]).slice(0, 2).map(p => p[1])
  const keep = new Uint8Array(N * N)
  for (let i = 0; i < keep.length; i++) keep[i] = order.includes(lab[i]) ? 1 : 0
  return fillHoles(keep)
}

function dice(a: Uint8Array, b: Uint8Array): number {
  let inter = 0, sa = 0, sb = 0
  for (let i = 0; i < a.length; i++) { inter += a[i] & b[i]; sa += a[i]; sb += b[i] }
  return (2 * inter) / (sa + sb)
}

const op = ref<Op>('opening')
const r = ref(3)
const full = ref(true)
const result = computed(() => {
  let m: Uint8Array
  if (op.value === 'erosion') m = morph(LUNG, r.value, true)
  else if (op.value === 'dilation') m = morph(LUNG, r.value, false)
  else if (op.value === 'opening') m = morph(morph(LUNG, r.value, true), r.value, false)
  else if (op.value === 'closing') m = morph(morph(LUNG, r.value, false), r.value, true)
  else m = fillHoles(LUNG)
  return full.value ? recipe(m) : m
})
const d = computed(() => dice(result.value, REF))
const expected = computed(() => TABLE[`${op.value}-${r.value}`][full.value ? 1 : 0])
const same = computed(() => Math.abs(d.value - expected.value) < 1e-5)
const num = (v: number, k = 3) => v.toFixed(k).replace('.', ',')

const canvas = ref<HTMLCanvasElement | null>(null)
function draw() {
  const cv = canvas.value
  if (!cv) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(N, N)
  const m = result.value
  for (let i = 0; i < N * N; i++) {
    const y = Math.floor(i / N), x = i % N
    const edge = REF[i] && ((y > 0 && !REF[i - N]) || (y < N - 1 && !REF[i + N]) || (x > 0 && !REF[i - 1]) || (x < N - 1 && !REF[i + 1]))
    const p = 4 * i
    if (edge) { img.data[p] = 255; img.data[p + 1] = 204; img.data[p + 2] = 51; img.data[p + 3] = 255 }
    else if (m[i]) { img.data[p] = 51; img.data[p + 1] = 195; img.data[p + 2] = 255; img.data[p + 3] = 110 }
    else if (LUNG[i] && !m[i]) { img.data[p] = 255; img.data[p + 1] = 79; img.data[p + 2] = 163; img.data[p + 3] = 90 }
  }
  ctx.putImageData(img, 0, 0)
}
onMounted(draw)
watch([result, canvas], draw, { flush: 'post' })
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Морфологія маски легень: операція, радіус, Dice</div>
        <div class="lab__sub">
          Зріз z = −117,5 мм LIDC-IDRI-0001 (512 × 512, піксель 0,703 мм), легеневе вікно −600/1600. Маска — вокселі
          HU ≤ {{ data.threshold }} усередині тіла (крок 2 конвеєра); Dice рахується з маскою легень LUNA16 на цьому зрізі.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="o in OPS" :key="o.id" type="button" class="lab__pill" :class="{ 'is-on': op === o.id }"
              @click="op = o.id">{{ o.label }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>радіус диска: <b>{{ op === 'fill' ? '—' : r + ' px' }}</b>{{ op === 'fill' ? '' : ` (${num(r * PX, 1)} мм)` }}</span>
        <input v-model.number="r" type="range" min="1" max="10" step="1" :disabled="op === 'fill'" aria-label="Радіус диска">
      </label>
      <label class="lab__ctl mo__check">
        <input v-model="full" type="checkbox">
        <span>повний рецепт: + дві найбільші компоненти і заповнення дірок</span>
      </label>
    </div>

    <div class="mo__grid">
      <div class="mo__frame">
        <img :src="withBase(data.png as string)" alt="Зріз КТ LIDC-IDRI-0001 у легеневому вікні" width="512" height="512" loading="lazy">
        <canvas ref="canvas" :width="N" :height="N" aria-label="Маска після операції поверх знімка"></canvas>
      </div>
      <div class="mo__side">
        <div class="mo__legend">
          <span><i style="background:#33c3ff"></i>маска після операції</span>
          <span><i style="background:#ff4fa3"></i>прибрано з вихідної маски</span>
          <span><i style="background:#ffcc33"></i>межа маски легень LUNA16</span>
        </div>
        <div class="lab__stats">
          <div class="lab__stat is-warm"><b>{{ num(d) }}</b><span>Dice з маскою LUNA16</span></div>
          <div class="lab__stat"><b>{{ num(data.base as number) }}</b><span>Dice маски без операцій</span></div>
          <div class="lab__stat" :class="same ? 'is-green' : 'is-warm'"><b>{{ same ? 'так' : 'ні' }}</b>
            <span>збігається з таблицею scipy ({{ num(expected) }})</span></div>
        </div>
      </div>
    </div>

    <p class="lab__note">
      Ерозія відрізає поодинокі пікселі біля шкіри, але стоншує й легені — Dice падає з радіусом. Дилатація
      заливає судини всередині легень і водночас розширює межу назовні. Відкриття прибирає дрібні острівці, не
      змінюючи великих областей. Закриття заповнює просвіти судин і бронхів, а з повним рецептом при r = 10 px дає
      найбільший Dice — бо еталон LUNA16 включає судини в легеню. Заповнення дірок не має радіуса: воно закриває
      лише замкнені порожнини.
    </p>
  </div>
</template>

<style scoped>
.mo__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 680px) { .mo__grid { grid-template-columns: 1fr; } }
.mo__frame { position: relative; width: 100%; max-width: 420px; aspect-ratio: 1 / 1; }
.mo__frame img, .mo__frame canvas { position: absolute; inset: 0; width: 100%; height: 100%; image-rendering: pixelated; border-radius: 6px; }
.mo__check { display: flex; gap: 0.5rem; align-items: center; }
.mo__check > span { margin: 0; }
.mo__legend { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem; color: var(--vp-c-text-2); }
.mo__legend i { display: inline-block; width: 14px; height: 10px; border-radius: 2px; margin-right: 0.4rem; vertical-align: middle; }
.mo__side .lab__stats { margin-top: 0.8rem; }
</style>
