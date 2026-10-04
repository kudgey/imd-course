<script setup lang="ts">
/**
 * Поріг імовірності для U-Net 2D (лекція 10, розділ «Поріг імовірності: вибір на валідації»).
 * Дані — tools/gen_lec10_threshold.py: середній Dice і медіана HD95 при порогах 0,10…0,90 на
 * валідаційній і тестовій частинах JSRT та на Montgomery (ті самі пороги й метрики, що в коді);
 * приклад — карта ймовірностей одного знімка валідації (PNG 256 × 256, значення round(255 · p)) і
 * його еталон SCR. Маска прикладу будується тут за правилом q / 255 ≥ t, Dice рахується в браузері
 * і звіряється з таблицею генератора. Знімок не показується — лише карта ймовірностей і маски.
 */
import { ref, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec10_threshold.json'

const N = 256
const TS = data.ts as number[]
const K_STAR = TS.indexOf(data.t_star as number)
const k = ref(K_STAR)
const t = computed(() => TS[k.value])
const SERIES = [
  { id: 'val', label: `валідація JSRT (${data.n.val})`, color: '#1BAF7A' },
  { id: 'test', label: `тест JSRT (${data.n.test})`, color: '#EDA100' },
  { id: 'mont', label: `Montgomery (${data.n.mont})`, color: '#EB6834' },
] as const
type Sid = typeof SERIES[number]['id']
const D = data as unknown as Record<Sid, { dice: number[]; hd95: number[] }>

function unpack(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(N * N)
  for (let i = 0; i < out.length; i++) out[i] = (bin.charCodeAt(i >> 3) >> (7 - (i & 7))) & 1
  return out
}
const REF = unpack(data.ref as string)
const prob = ref<Uint8Array | null>(null)

// графік
const W = 600, H = 250, L = 52, R = 14, T = 14, B = 34
const all = SERIES.flatMap(s => D[s.id].dice)
const yMin = Math.floor(Math.min(...all) * 100) / 100, yMax = Math.ceil(Math.max(...all) * 1000) / 1000
const xs = (v: number) => L + ((v - TS[0]) / (TS[TS.length - 1] - TS[0])) * (W - L - R)
const ys = (v: number) => T + (1 - (v - yMin) / (yMax - yMin)) * (H - T - B)
const paths = SERIES.map(s => ({ ...s, d: D[s.id].dice.map((v, i) => `${i ? 'L' : 'M'}${xs(TS[i]).toFixed(1)},${ys(v).toFixed(1)}`).join(' ') }))
const yTicks = Array.from({ length: 5 }, (_, i) => yMin + (i * (yMax - yMin)) / 4)
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')

const example = computed(() => {
  const q = prob.value
  if (!q) return null
  let inter = 0, a = 0, b = 0
  for (let i = 0; i < N * N; i++) {
    const m = q[i] / 255 >= t.value ? 1 : 0
    inter += m & REF[i]; a += m; b += REF[i]
  }
  return (2 * inter) / (a + b)
})
const same = computed(() => example.value !== null && Math.abs(example.value - (data.ex_dice as number[])[k.value]) < 6e-5)

const canvas = ref<HTMLCanvasElement | null>(null)
function draw() {
  const cv = canvas.value, q = prob.value
  if (!cv || !q) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(N, N)
  for (let i = 0; i < N * N; i++) {
    const y = Math.floor(i / N), x = i % N
    const m = q[i] / 255 >= t.value
    const edge = REF[i] && ((y > 0 && !REF[i - N]) || (y < N - 1 && !REF[i + N]) || (x > 0 && !REF[i - 1]) || (x < N - 1 && !REF[i + 1]))
    const g = 240 - Math.round((q[i] / 255) * 90) // ймовірність — відтінок нейтрального тла
    let c = [g, g, g]
    if (m && REF[i]) c = [193, 199, 238]
    else if (m) c = [255, 79, 163]
    else if (REF[i]) c = [180, 83, 31]
    if (edge) c = [27, 27, 39]
    const p = 4 * i
    img.data[p] = c[0]; img.data[p + 1] = c[1]; img.data[p + 2] = c[2]; img.data[p + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
}
onMounted(() => {
  const im = new Image()
  im.onload = () => {
    const off = document.createElement('canvas')
    off.width = N; off.height = N
    const c2 = off.getContext('2d')
    if (!c2) return
    c2.drawImage(im, 0, 0)
    const px = c2.getImageData(0, 0, N, N).data
    const q = new Uint8Array(N * N)
    for (let i = 0; i < N * N; i++) q[i] = px[4 * i]
    prob.value = q
  }
  im.src = withBase(data.png as string)
})
watch([t, prob, canvas], draw, { flush: 'post' })
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Поріг імовірності: де Dice найбільший і хто вибирає</div>
        <div class="lab__sub">
          U-Net 2D, епоха {{ data.epoch }}. Криві — середній Dice по знімках при кожному порозі; поріг t* = {{ num(data.t_star as number, 2) }}
          вибрано лише за валідаційною частиною. Праворуч — карта ймовірностей моделі (вихід моделі, а не знімок; сирих знімків miniJSRT на сторінці не
          публікуємо) для знімка {{ data.example }} з валідації (темніше — вища ймовірність) і маска при вибраному порозі.
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поріг t: <b>{{ num(t, 2) }}</b>{{ k === K_STAR ? ' (t*, вибраний на валідації)' : '' }}</span>
        <input v-model.number="k" type="range" min="0" :max="TS.length - 1" step="1" aria-label="Поріг імовірності">
      </label>
    </div>
    <div class="th__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" class="th__svg" role="img" aria-label="Середній Dice залежно від порогу">
        <g v-for="v in yTicks" :key="v">
          <line :x1="L" :x2="W - R" :y1="ys(v)" :y2="ys(v)" stroke="var(--vp-c-divider)" stroke-width="1" />
          <text :x="L - 6" :y="ys(v) + 4" text-anchor="end" class="th__tick">{{ num(v, 3) }}</text>
        </g>
        <g v-for="(v, i) in TS" :key="'x' + i">
          <text v-if="i % 2 === 0" :x="xs(v)" :y="H - B + 16" text-anchor="middle" class="th__tick">{{ num(v, 1) }}</text>
        </g>
        <text :x="(L + W - R) / 2" :y="H - 4" text-anchor="middle" class="th__tick">поріг t</text>
        <line :x1="xs(t)" :x2="xs(t)" :y1="T" :y2="H - B" stroke="var(--vp-c-text-2)" stroke-dasharray="4 3" />
        <path v-for="s in paths" :key="s.id" :d="s.d" fill="none" :stroke="s.color" stroke-width="2.2" />
        <circle v-for="s in paths" :key="'c' + s.id" :cx="xs(t)" :cy="ys(D[s.id].dice[k])" r="4" :fill="s.color" />
      </svg>
      <div class="th__frame">
        <canvas ref="canvas" :width="N" :height="N" aria-label="Карта ймовірностей і маска при порозі"></canvas>
        <div v-if="!prob" class="th__wait">завантаження карти (≈ 20 КБ)…</div>
      </div>
    </div>
    <div class="th__legend">
      <span v-for="s in SERIES" :key="s.id"><i :style="{ background: s.color }"></i>{{ s.label }}</span>
    </div>
    <div class="th__wrap">
    <table class="th__table">
      <thead><tr><th>частина</th><th>Dice, середнє</th><th>HD95, медіана, мм</th></tr></thead>
      <tbody>
        <tr v-for="s in SERIES" :key="s.id">
          <td>{{ s.label }}</td><td>{{ num(D[s.id].dice[k], 4) }}</td><td>{{ num(D[s.id].hd95[k], 2) }}</td>
        </tr>
      </tbody>
    </table>
    </div>
    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ example === null ? '…' : num(example, 4) }}</b><span>Dice прикладу {{ data.example }}</span></div>
      <div class="lab__stat" :class="same ? 'is-green' : 'is-warm'"><b>{{ same ? 'так' : '…' }}</b><span>збігається з таблицею генератора</span></div>
    </div>
    <p class="lab__note">
      Валідаційна крива пласка біля максимуму: пороги в середині діапазону дають майже однаковий Dice, а
      помітні втрати — лише на краях. Крива Montgomery має свій максимум, але брати поріг за нею — те саме,
      що підбирати його на тесті: тестові й зовнішні криві показано лише для того, щоб побачити, як поводиться
      вибір, зроблений на валідації.
    </p>
  </div>
</template>

<style scoped>
.th__grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 680px) { .th__grid { grid-template-columns: 1fr; } }
.th__svg { width: 100%; height: auto; display: block; }
.th__wrap { overflow-x: auto; margin-top: 0.4rem; }
.th__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.th__table th { font-weight: 500; font-size: 0.75rem; color: var(--vp-c-text-2); text-align: right; padding: 0.3rem 0.5rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; }
.th__table th:first-child, .th__table td:first-child { text-align: left; }
.th__table td { font-size: 0.85rem; text-align: right; padding: 0.3rem 0.5rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; }
.th__tick { font-size: 11px; fill: var(--vp-c-text-2); }
.th__frame { position: relative; width: 100%; max-width: 320px; aspect-ratio: 1 / 1; }
.th__frame canvas { width: 100%; height: 100%; image-rendering: pixelated; border-radius: 6px; display: block; background: #f0efec; }
.th__wait { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; color: var(--vp-c-text-2); }
.th__legend { display: flex; flex-wrap: wrap; gap: 0.9rem; font-size: 0.8rem; color: var(--vp-c-text-2); margin: 0.4rem 0; }
.th__legend i { display: inline-block; width: 14px; height: 4px; border-radius: 2px; margin-right: 0.35rem; vertical-align: middle; }
</style>
