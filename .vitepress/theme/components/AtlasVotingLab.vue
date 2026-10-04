<script setup lang="ts">
/**
 * Злиття міток мультиатласної сегментації (лекція 11, розділ «Злиття міток: більшість голосів, зважене
 * голосування, STAPLE»). Дані — tools/gen_lec11_atlas.py з ckpt/lec11_atlas.npz, який пише блок коду:
 * 22 цілі Montgomery (S1 dev0), для кожної 9 масок атласів (dev1–dev4), перенесених афінним + demons.
 * Таблиця — медіана, Q1, Q3 Dice і медіана HD95 по 22 цілях для k = 1…9 і трьох правил (ті самі
 * функції, що в коді; рядки k = 1, 3, 5, 7, 9 генератор звіряє з виводом). Приклад — ціль із медіанним
 * Dice (k = 9, більшість): 9 перенесених масок, ручна маска й злиті маски «зважене» та STAPLE у вигляді
 * довжин серій. Більшість голосів і Dice прикладу рахуються тут і звіряються з генератором.
 * Знімків Montgomery у віджеті немає — лише маски й контури.
 */
import { ref, computed, watch } from 'vue'
import data from '../../data/lec11_atlas.json'

type Rule = 'більшість' | 'зважене' | 'STAPLE'
const RULES = data.rules as Rule[]
const KS = data.ks as number[]
const TABLE = data.table as Record<string, { dice: number[]; hd95: number }>
const EX = data.example as { index: number; h: number; w: number; ref: number[]; atlases: number[][]; fused: Record<string, number[]>; dice: Record<string, number> }
const H = EX.h, W = EX.w

function unrle(runs: number[]): Uint8Array {
  const out = new Uint8Array(H * W)
  let p = 0, v = 0
  for (const n of runs) { if (v) out.fill(1, p, p + n); p += n; v = 1 - v }
  return out
}
const REF = unrle(EX.ref)
const ATL = EX.atlases.map(unrle)

const k = ref(9)
const rule = ref<Rule>('більшість')
const COLORS: Record<Rule, string> = { 'більшість': '#2A78D6', 'зважене': '#1BAF7A', STAPLE: '#EB6834' }

const votes = computed(() => {
  const v = new Uint8Array(H * W)
  for (let j = 0; j < k.value; j++) { const a = ATL[j]; for (let i = 0; i < v.length; i++) v[i] += a[i] }
  return v
})
const fused = computed(() => {
  if (rule.value === 'більшість') return votes.value.map(c => (c > k.value / 2 ? 1 : 0))
  return unrle(EX.fused[`${k.value}|${rule.value}`])
})
const dice = computed(() => {
  let inter = 0, a = 0, b = 0
  const f = fused.value
  for (let i = 0; i < f.length; i++) { inter += f[i] & REF[i]; a += f[i]; b += REF[i] }
  return (2 * inter) / (a + b)
})
const same = computed(() => Math.abs(dice.value - EX.dice[`${k.value}|${rule.value}`]) < 6e-5)
const row = computed(() => TABLE[`${k.value}|${rule.value}`])
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')

// графік медіанного Dice за k
const CW = 360, CH = 200, L = 44, R = 10, T = 10, B = 30
const all = RULES.flatMap(r => KS.flatMap(kk => TABLE[`${kk}|${r}`].dice))
const y0 = Math.floor(Math.min(...all) * 100) / 100, y1 = Math.ceil(Math.max(...all) * 100) / 100
const cx = (kk: number) => L + ((kk - 1) / (KS.length - 1)) * (CW - L - R)
const cy = (v: number) => T + (1 - (v - y0) / (y1 - y0)) * (CH - T - B)
const lines = RULES.map(r => ({ r, d: KS.map((kk, i) => `${i ? 'L' : 'M'}${cx(kk).toFixed(1)},${cy(TABLE[`${kk}|${r}`].dice[0]).toFixed(1)}`).join(' ') }))
const band = computed(() => {
  const up = KS.map(kk => `${cx(kk).toFixed(1)},${cy(TABLE[`${kk}|${rule.value}`].dice[2]).toFixed(1)}`)
  const lo = KS.map(kk => `${cx(kk).toFixed(1)},${cy(TABLE[`${kk}|${rule.value}`].dice[1]).toFixed(1)}`).reverse()
  return [...up, ...lo].join(' ')
})
const yTicks = [y0, (y0 + y1) / 2, y1]

// карта голосів і контури
const canvas = ref<HTMLCanvasElement | null>(null)
function edge(m: Uint8Array, i: number) {
  if (!m[i]) return false
  const y = Math.floor(i / W), x = i % W
  return (y === 0 || !m[i - W]) || (y === H - 1 || !m[i + W]) || (x === 0 || !m[i - 1]) || (x === W - 1 || !m[i + 1])
}
function draw() {
  const cv = canvas.value
  if (!cv) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(W, H)
  const v = votes.value, f = fused.value, kk = k.value
  const fc = COLORS[rule.value]
  const rgb = [parseInt(fc.slice(1, 3), 16), parseInt(fc.slice(3, 5), 16), parseInt(fc.slice(5, 7), 16)]
  for (let i = 0; i < W * H; i++) {
    const t = v[i] / kk
    let c = [240 - 150 * t, 239 - 120 * t, 236 - 40 * t]  // частка голосів «легеня» — відтінок синього на нейтральному тлі
    if (edge(f, i)) c = rgb
    if (edge(REF, i)) c = [27, 27, 39]
    const p = 4 * i
    img.data[p] = c[0]; img.data[p + 1] = c[1]; img.data[p + 2] = c[2]; img.data[p + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
}
watch([votes, fused, canvas], draw, { flush: 'post' })
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Злиття міток: скільки атласів і за яким правилом</div>
        <div class="lab__sub">
          22 цілі Montgomery (фолд dev0), атласи — фолди dev1–dev4, k найсхожіших за рангом відбору. Таблиця й графік — по всіх
          22 цілях; карта — ціль із медіанним Dice: синім — частка атласів, що голосують «легеня», чорне — ручна маска,
          кольорове — злита маска. Знімків Montgomery тут немає, лише маски.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="r in RULES" :key="r" class="lab__pill" :class="{ 'is-on': rule === r }" @click="rule = r">{{ r }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>кількість атласів k: <b>{{ k }}</b></span>
        <input v-model.number="k" type="range" min="1" max="9" step="1" aria-label="Кількість атласів">
      </label>
    </div>
    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(row.dice[0]) }}</b><span>Dice, медіана по 22 цілях [{{ num(row.dice[1]) }}; {{ num(row.dice[2]) }}]</span></div>
      <div class="lab__stat is-warm"><b>{{ num(row.hd95, 1) }}</b><span>HD95, мм, медіана</span></div>
      <div class="lab__stat"><b>{{ num(dice, 4) }}</b><span>Dice цілі на карті (рахує віджет)</span></div>
      <div class="lab__stat" :class="same ? 'is-green' : 'is-warm'"><b>{{ same ? 'так' : '…' }}</b><span>збігається з генератором</span></div>
    </div>
    <div class="av__grid">
      <div class="av__frame" :style="{ aspectRatio: `${W} / ${H}` }">
        <canvas ref="canvas" :width="W" :height="H" aria-label="Карта голосів атласів і контури масок"></canvas>
      </div>
      <figure class="av__chart">
        <svg :viewBox="`0 0 ${CW} ${CH}`" role="img" aria-label="Медіанний Dice залежно від кількості атласів">
          <g v-for="v in yTicks" :key="v">
            <line :x1="L" :x2="CW - R" :y1="cy(v)" :y2="cy(v)" stroke="var(--vp-c-divider)" />
            <text :x="L - 4" :y="cy(v) + 4" text-anchor="end" class="av__tick">{{ num(v, 2) }}</text>
          </g>
          <text v-for="kk in KS" :key="kk" :x="cx(kk)" :y="CH - 14" text-anchor="middle" class="av__tick">{{ kk }}</text>
          <text :x="(L + CW - R) / 2" :y="CH - 1" text-anchor="middle" class="av__tick">k — кількість атласів</text>
          <polygon :points="band" :fill="COLORS[rule]" fill-opacity="0.12" />
          <path v-for="l in lines" :key="l.r" :d="l.d" fill="none" :stroke="COLORS[l.r]" :stroke-width="l.r === rule ? 2.4 : 1.2" />
          <circle :cx="cx(k)" :cy="cy(row.dice[0])" r="4.5" :fill="COLORS[rule]" />
        </svg>
        <figcaption>медіанний Dice по 22 цілях; смуга — від Q1 до Q3 для вибраного правила</figcaption>
      </figure>
    </div>
    <p class="lab__note">
      При k = 1 усі три правила однакові — це один атлас. Зі зростанням k медіана повільно росте, а розкид між цілями
      лишається: атласи розходяться біля діафрагми, уздовж бічних стінок і на межі лівої легені з серцем. При парних k більшість голосів
      вимагає строго більше половини, тож нічия віддається фону.
    </p>
  </div>
</template>

<style scoped>
.av__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr); gap: 1rem; align-items: center; margin-top: 0.9rem; }
@media (max-width: 640px) { .av__grid { grid-template-columns: 1fr; } }
.av__frame { position: relative; width: 100%; max-width: 260px; margin: 0 auto; }
.av__frame canvas { width: 100%; height: 100%; image-rendering: pixelated; border-radius: 6px; display: block; background: #f0efec; }
.av__chart { margin: 0; }
.av__chart svg { width: 100%; height: auto; display: block; }
.av__chart figcaption { font-size: 0.75rem; color: var(--vp-c-text-2); text-align: center; }
.av__tick { font-size: 10px; fill: var(--vp-c-text-2); }
</style>
