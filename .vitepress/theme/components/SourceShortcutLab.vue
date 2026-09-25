<script setup lang="ts">
/**
 * «Джерело знімка»: що можна передбачити лише з розміру кадру, не бачачи жодного пікселя.
 * Дані — заголовки IHDR 800 PNG Montgomery і Shenzhen (ширина, висота, набір, мітка);
 * генератор tools/gen_lec01_source.py, звірка з виводом блоку коду 5 лекції.
 * За замовчуванням: лише Shenzhen, поріг — медіана площі кадру → ті самі числа, що в розділі.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec01_source.json'

type Frame = [number, number, number, number]   // ширина, висота, набір (0 — Montgomery, 1 — Shenzhen), мітка (1 — ТБ)
const ALL = data.frames as unknown as Frame[]
const MEDIAN = data.median_mpx as number

const scope = ref<'sz' | 'all'>('sz')
const thr = ref<number>(MEDIAN)

const rows = computed(() => (scope.value === 'sz' ? ALL.filter(f => f[2] === 1) : ALL))

const res = computed(() => {
  let nS = 0, tbS = 0, nL = 0, tbL = 0, hits = 0, tb = 0, mcLarge = 0, mcAll = 0
  const t = thr.value * 1e6
  for (const [w, h, s, y] of rows.value) {
    const small = w * h < t
    if (small) { nS++; tbS += y } else { nL++; tbL += y; if (s === 0) mcLarge++ }
    if (small === (y === 1)) hits++
    tb += y
    if (s === 0) mcAll++
  }
  const n = rows.value.length
  return {
    n, nS, nL,
    tbS: nS ? tbS / nS : NaN,
    tbL: nL ? tbL / nL : NaN,
    acc: hits / n,
    majority: Math.max(tb, n - tb) / n,
    mcLarge, mcAll, szLarge: nL - mcLarge,
  }
})

// Montgomery має лише два розміри кадру — підписуємо, скільки знімків у кожній точці
const mcSpots = computed(() => {
  const m = new Map<string, number>()
  for (const [w, h, s] of ALL) if (s === 0) m.set(`${w}×${h}`, (m.get(`${w}×${h}`) || 0) + 1)
  return [...m.entries()].map(([k, c]) => {
    const [w, h] = k.split('×').map(Number)
    return { w, h, c }
  })
})

const W = 360, H = 300, L = 46, R = 12, T = 12, B = 40, MAX = 5200
const sx = (v: number) => L + (v / MAX) * (W - L - R)
const sy = (v: number) => H - B - (v / MAX) * (H - T - B)
const ticks = [0, 1000, 2000, 3000, 4000, 5000]

const curve = computed(() => {
  const t = thr.value * 1e6
  const pts: string[] = []
  const w0 = Math.max(t / MAX, 200)
  for (let k = 0; k <= 60; k++) {
    const w = w0 + ((MAX - w0) * k) / 60
    const h = t / w
    if (h <= MAX) pts.push(`${sx(w).toFixed(1)},${sy(h).toFixed(1)}`)
  }
  return pts.join(' ')
})

const shown = computed(() => (scope.value === 'sz' ? ALL.filter(f => f[2] === 1) : ALL))

const pct = (v: number) => (Number.isFinite(v) ? (v * 100).toFixed(1).replace('.', ',') + ' %' : '—')
const num2 = (v: number) => v.toFixed(2).replace('.', ',')
const isMedian = computed(() => Math.abs(thr.value - MEDIAN) < 1e-9)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Джерело знімка: що видає розмір кадру</div>
        <div class="lab__sub">
          800 рентгенограм Montgomery і Shenzhen, але без жодного пікселя: лише ширина й висота кадру
          із заголовка PNG, набір і мітка з імені файлу. Правило одне: кадр, менший за поріг площі, —
          «ТБ», решта — «норма».
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" :class="{ 'is-on': scope === 'sz' }" @click="scope = 'sz'">лише Shenzhen (662)</button>
      <button class="lab__pill" :class="{ 'is-on': scope === 'all' }" @click="scope = 'all'">усі 800 знімків</button>
    </div>

    <label class="lab__ctl ss__slider">
      <span>Поріг площі кадру = <b>{{ num2(thr) }} Мпікс</b></span>
      <input type="range" min="1" max="20" step="0.01" v-model.number="thr" />
    </label>

    <div class="lab__pills">
      <button class="lab__pill" :class="{ 'is-on': isMedian }" @click="thr = MEDIAN">
        медіана площі кадру Shenzhen: {{ num2(MEDIAN) }} Мпікс
      </button>
      <button class="lab__pill" :class="{ 'is-on': Math.abs(thr - 15) < 1e-9 }" @click="thr = 15">
        між наборами: 15 Мпікс
      </button>
    </div>

    <div class="ss__plot">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Ширина і висота кадру 800 рентгенограм">
        <g v-for="t in ticks" :key="'t' + t">
          <line :x1="sx(t)" :y1="sy(0)" :x2="sx(t)" :y2="sy(MAX)" class="ss__grid" />
          <line :x1="sx(0)" :y1="sy(t)" :x2="sx(MAX)" :y2="sy(t)" class="ss__grid" />
          <text :x="sx(t)" :y="H - B + 14" text-anchor="middle" class="ss__tick">{{ t }}</text>
          <text :x="L - 5" :y="sy(t) + 3" text-anchor="end" class="ss__tick">{{ t }}</text>
        </g>
        <text :x="(L + W - R) / 2" :y="H - 6" text-anchor="middle" class="ss__lbl">ширина кадру, px</text>
        <text :x="12" :y="(T + H - B) / 2" text-anchor="middle" class="ss__lbl"
              :transform="`rotate(-90 12 ${(T + H - B) / 2})`">висота кадру, px</text>

        <polyline :points="curve" class="ss__curve" />

        <template v-for="(f, i) in shown" :key="i">
          <circle v-if="f[2] === 1" :cx="sx(f[0])" :cy="sy(f[1])" r="2.3"
                  :class="f[3] === 1 ? 'ss__tb' : 'ss__norm'" />
          <rect v-else :x="sx(f[0]) - 4" :y="sy(f[1]) - 4" width="8" height="8"
                :class="f[3] === 1 ? 'ss__tb' : 'ss__norm'" />
        </template>
        <template v-if="scope === 'all'">
          <text v-for="m in mcSpots" :key="m.w" :x="sx(m.w) - 8" :y="sy(m.h) + (m.h > m.w ? -8 : 16)"
                text-anchor="end" class="ss__tick">Montgomery: {{ m.c }}</text>
        </template>
      </svg>
      <div class="ss__legend">
        <span><i class="ss__dot ss__norm"></i>норма</span>
        <span><i class="ss__dot ss__tb"></i>ТБ</span>
        <span>кружок — Shenzhen, квадрат — Montgomery</span>
        <span><i class="ss__line"></i>площа кадру = поріг</span>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ res.nS }}</b><span>кадрів менші за поріг; ТБ серед них {{ pct(res.tbS) }}</span></div>
      <div class="lab__stat"><b>{{ res.nL }}</b><span>кадрів не менші; ТБ серед них {{ pct(res.tbL) }}</span></div>
      <div class="lab__stat" :class="res.acc > res.majority ? 'is-warm' : ''">
        <b>{{ pct(res.acc) }}</b><span>влучань правила «менший кадр → ТБ»</span>
      </div>
      <div class="lab__stat"><b>{{ pct(res.majority) }}</b><span>частка більшого класу — стільки дає вгадування</span></div>
      <div v-if="scope === 'all'" class="lab__stat">
        <b>{{ res.mcLarge }} з {{ res.mcAll }}</b>
        <span>знімків Montgomery не менші за поріг; Shenzhen серед них — {{ res.szLarge }}</span>
      </div>
    </div>

    <p class="lab__note">
      Поріг за замовчуванням — медіана площі кадру в Shenzhen: його не підбирали під мітки, він
      лише ділить набір навпіл. Зсуньте його — частки ТБ по обидва боки зміняться, але правило
      й далі влучає частіше, ніж вгадування, хоча не бачить ні легень, ні уражень. Перемкніться на
      всі 800 знімків і поставте поріг 15 Мпікс: розмір кадру відокремлює Montgomery від Shenzhen
      без жодної помилки. Мережа, що бачить увесь кадр, отримує ці підказки разом зі знімком.
    </p>
  </div>
</template>

<style scoped>
.ss__slider { display: block; margin-bottom: 0.9rem; }
.ss__plot svg { width: 100%; max-width: 560px; height: auto; display: block; margin: 0 auto; }
.ss__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.ss__tick { fill: var(--vp-c-text-3); font-size: 8.5px; }
.ss__lbl { fill: var(--vp-c-text-2); font-size: 9.5px; }
.ss__curve { fill: none; stroke: var(--uk-ink); stroke-width: 1.4; stroke-dasharray: 4 3; }
.ss__norm { fill: var(--uk-accent); fill-opacity: 0.55; }
.ss__tb { fill: var(--uk-warm); fill-opacity: 0.55; }
rect.ss__norm, rect.ss__tb { fill-opacity: 0.8; }
.ss__legend {
  display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; justify-content: center;
  font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.3rem;
}
.ss__dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 0.3rem; vertical-align: -1px; }
.ss__dot.ss__norm { background: var(--uk-accent); }
.ss__dot.ss__tb { background: var(--uk-warm); }
.ss__line { display: inline-block; width: 18px; border-top: 1.5px dashed var(--uk-ink); margin-right: 0.3rem; vertical-align: 3px; }
.lab__pill { text-align: left; }
/* 375 px: SVG стискається приблизно до 0,8 — підписи осей більші, поля віджета вужчі */
@media (max-width: 480px) {
  .lab { padding: 1rem 0.8rem; }
  .ss__tick { font-size: 11px; }
  .ss__lbl { font-size: 11.5px; }
}
</style>
