<script setup lang="ts">
/**
 * Частковий об’єм: товстий зріз = середнє n сусідніх зрізів LIDC-IDRI-0001 по 2,5 мм (2,5…15 мм) навколо
 * дрібного вузла (позначений однією точкою, z = −150 мм) і великого (центр — воксель 315, 366, z = −117,5 мм).
 * Максимум у вікні 5 × 5 біля центру, медіана легені в кільці, контраст і профілі — з tools/gen_lec02_partial.py,
 * який повторює блок коду розділу «Товщина зрізу і частковий об’єм»: контраст дрібного вузла 351 → 153 HU
 * на 10 мм, великого — 896…922 HU. Вирізки (≈ 23 КБ разом) вантажаться одразу, вікно −1000…−200 HU.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec02_partial.json'

type Key = 'small' | 'big'
const T = data.thickness_mm as number[]
const STATS = data.stats as Record<Key, number[][]>
const PROF = data.profiles as Record<Key, number[][]>
const RINGS = data.rings as Record<Key, number[]>
const HALF = data.half as Record<Key, number>
const PNG = data.png as Record<Key, string>
const PX = data.px_mm as number

const ti = ref(0)
const KEYS: { k: Key; name: string }[] = [
  { k: 'small', name: 'дрібний вузол (позначений точкою, < 3 мм)' },
  { k: 'big', name: 'великий вузол (24,2 мм)' },
]

const num = (v: number, d = 0) => v.toFixed(d).replace('.', ',').replace('-', '−')
const pct = (v: number) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v * 100).toFixed(0) + ' %'
const stat = (k: Key) => STATS[k][ti.value]
const change = (k: Key) => STATS[k][ti.value][2] / STATS[k][0][2] - 1
const tileStyle = (k: Key) => ({
  backgroundImage: `url(${withBase(PNG[k])})`,
  backgroundSize: `${T.length * 100}% 100%`,
  backgroundPosition: `${(ti.value / (T.length - 1)) * 100}% 0%`,
})

/* Профіль HU через центр вузла: поточна товщина і 2,5 мм для порівняння */
const PW = 260
const PH = 120
const PL = 36
const PR = 6
const PT = 8
const PB = 22
const LO = -1000
const HI = 200
const py = (v: number) => PT + (1 - (Math.min(Math.max(v, LO), HI) - LO) / (HI - LO)) * (PH - PT - PB)
const path = (k: Key, t: number) => {
  const p = PROF[k][t]
  return p.map((v, i) => `${(PL + (i / (p.length - 1)) * (PW - PL - PR)).toFixed(1)},${py(v).toFixed(1)}`).join(' ')
}
const mmTicks = (k: Key) => {
  const h = HALF[k]
  const span = h * PX
  const step = span > 20 ? 10 : 5
  const out: { x: number; t: string }[] = []
  for (let mm = -Math.floor(span / step) * step; mm <= span; mm += step) {
    out.push({ x: PL + ((mm / PX + h) / (2 * h)) * (PW - PL - PR), t: num(mm) })
  }
  return out
}
const YT = [-1000, -600, -200, 200]
/** «1 зріз», «2 зрізи», «5 зрізів» */
const slicesLabel = () => {
  const n = ti.value + 1
  return `${n} ${n === 1 ? 'зріз' : n >= 5 ? 'зрізів' : 'зрізи'}`
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Товщина зрізу і частковий об’єм на двох вузлах LIDC-IDRI-0001</div>
        <div class="lab__sub">
          Товстий зріз змодельовано як середнє сусідніх зрізів по 2,5 мм. Вирізки у вікні −1000…−200 HU;
          жовтий квадрат — вікно 5 × 5 пікселів, де шукається максимум, пунктирні кола — кільце легені.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>товщина зрізу: <b>{{ num(T[ti], 1) }}</b> мм ({{ slicesLabel() }} по 2,5 мм)</span>
        <input type="range" min="0" :max="T.length - 1" step="1" v-model.number="ti" />
      </label>
    </div>

    <div class="pv__grid">
      <div v-for="it in KEYS" :key="it.k" class="pv__col">
        <div class="pv__cap">{{ it.name }}</div>
        <div class="pv__tile" :style="tileStyle(it.k)">
          <svg :viewBox="`0 0 ${2 * HALF[it.k] + 1} ${2 * HALF[it.k] + 1}`" aria-hidden="true">
            <rect :x="HALF[it.k] - 2" :y="HALF[it.k] - 2" width="5" height="5" class="pv__win" />
            <circle :cx="HALF[it.k] + 0.5" :cy="HALF[it.k] + 0.5" :r="RINGS[it.k][0]" class="pv__ring" />
            <circle :cx="HALF[it.k] + 0.5" :cy="HALF[it.k] + 0.5" :r="RINGS[it.k][1]" class="pv__ring" />
          </svg>
        </div>
        <div class="pv__stats">
          <div><span>максимум</span><b>{{ num(stat(it.k)[0]) }} HU</b></div>
          <div><span>легеня</span><b>{{ num(stat(it.k)[1]) }} HU</b></div>
          <div><span>контраст</span><b :class="it.k === 'small' ? 'pv__warm' : ''">{{ num(stat(it.k)[2]) }} HU</b></div>
          <div><span>проти 2,5 мм</span><b>{{ ti === 0 ? '—' : pct(change(it.k)) }}</b></div>
        </div>
        <div class="pv__cap">Профіль HU через центр (горизонтально): суцільна — {{ num(T[ti], 1) }} мм, пунктир — 2,5 мм</div>
        <svg :viewBox="`0 0 ${PW} ${PH}`" role="img" :aria-label="`Профіль HU, ${it.name}`">
          <g v-for="t in YT" :key="t">
            <line :x1="PL" :x2="PW - PR" :y1="py(t)" :y2="py(t)" class="pv__grid-line" />
            <text :x="PL - 3" :y="py(t) + 3" text-anchor="end" class="pv__lbl">{{ num(t) }}</text>
          </g>
          <g v-for="m in mmTicks(it.k)" :key="m.t">
            <text :x="m.x" :y="PH - PB + 12" text-anchor="middle" class="pv__lbl">{{ m.t }}</text>
          </g>
          <polyline :points="path(it.k, 0)" class="pv__base" />
          <polyline :points="path(it.k, ti)" class="pv__now" />
          <text :x="PW - PR" :y="PH - 2" text-anchor="end" class="pv__lbl">мм від центру</text>
        </svg>
      </div>
    </div>

    <p class="lab__note">
      На 2,5 мм дрібний вузол — світла крапка в центрі лівої вирізки. Пересувайте повзунок і стежте за контрастом
      і профілем: крапка тьмяніє і на товстих зрізах стає схожою на переріз судини, а судини, що йдуть уздовж
      осі z, не зникають. Профіль великого вузла майже не змінюється — він займає весь воксель на будь-якій
      товщині.
    </p>
  </div>
</template>

<style scoped>
.pv__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.2rem;
  align-items: start;
}
.pv__col { min-width: 0; }
.pv__col svg { width: 100%; height: auto; display: block; }
.pv__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.4rem; line-height: 1.4; }
.pv__tile {
  position: relative;
  width: 100%;
  max-width: 260px;
  aspect-ratio: 1 / 1;
  background-repeat: no-repeat;
  background-color: #000;
  image-rendering: pixelated;
  border-radius: 6px;
}
.pv__tile svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.pv__win { fill: none; stroke: #f2c94c; stroke-width: 0.5; }
.pv__ring { fill: none; stroke: #33c3ff; stroke-width: 0.4; stroke-dasharray: 1.2 1; }
.pv__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.25rem 0.8rem;
  margin: 0.6rem 0 0.4rem;
  max-width: 260px;
  font-size: 0.8rem;
}
.pv__stats div { display: flex; justify-content: space-between; gap: 0.4rem; border-top: 1px solid var(--uk-line); padding-top: 0.2rem; }
.pv__stats span { color: var(--vp-c-text-3); }
.pv__stats b { font-family: var(--vp-font-family-mono); font-weight: 500; color: var(--uk-accent); }
.pv__stats b.pv__warm { color: var(--uk-warm); }
.pv__grid-line { stroke: var(--uk-line); stroke-width: 0.6; }
.pv__lbl { fill: var(--vp-c-text-3); font-size: 8.5px; }
.pv__base { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 3 2; }
.pv__now { fill: none; stroke: var(--uk-warm); stroke-width: 1.8; }
</style>
