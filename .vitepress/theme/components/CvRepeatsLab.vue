<script setup lang="ts">
/**
 * Розкид оцінки крос-валідації (лекція 07, розділ «Розкид оцінки між фолдами і повторами»).
 * Дані — tools/gen_lec07_repeats.py: логістична регресія (C = 1) на 66 ознаках, dev-частина S1,
 * StratifiedGroupKFold(5) за пацієнтами для 20 зерен; для кожного зерна — AUC п’яти валідаційних
 * фолдів. Зерна 0…4 дають той самий рядок «лог. регресія», що й вивід блоку коду (перевіряє
 * --check генератора).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec07_repeats.json'

const F = data.folds as number[][]
const NS = F.length
const seed = ref(0)
const reps = ref(5)
const mean = (a: number[]) => a.reduce((s, v) => s + v, 0) / a.length
const sd = (a: number[]) => { const m = mean(a); return Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / (a.length - 1)) }
const seedMeans = F.map(mean)
const cur = computed(() => ({ folds: F[seed.value], m: seedMeans[seed.value], lo: Math.min(...F[seed.value]), hi: Math.max(...F[seed.value]) }))
const pooled = computed(() => {
  const all = F.slice(0, reps.value).flat()
  const ms = seedMeans.slice(0, reps.value)
  return { m: mean(all), sd: sd(all), n: all.length, mlo: Math.min(...ms), mhi: Math.max(...ms) }
})
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')

const W = 380, H = 200, PL = 36, PR = 10, PT = 10, PB = 28
const Y0 = 0.75, Y1 = 0.95
const X = (i: number) => PL + ((i + 0.5) / NS) * (W - PL - PR)
const Y = (v: number) => PT + (1 - (Math.min(Math.max(v, Y0), Y1) - Y0) / (Y1 - Y0)) * (H - PT - PB)
const yTicks = [0.75, 0.8, 0.85, 0.9, 0.95]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Одна крос-валідація чи кілька: розкид AUC логістичної регресії</div>
        <div class="lab__sub">
          Кожне зерно — нове розбиття dev-частини на 5 фолдів за пацієнтами. Точки — AUC на валідаційних фолдах, риски —
          середнє одного повтору, смуга — середнє ± SD за вибраною кількістю повторів.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>зерно одного повтору: <b>{{ seed }}</b></span>
        <input v-model.number="seed" type="range" min="0" :max="NS - 1" step="1" aria-label="Зерно повтору">
      </label>
      <label class="lab__ctl">
        <span>повторів у середньому: <b>{{ reps }}</b> ({{ pooled.n }} навчань)</span>
        <input v-model.number="reps" type="range" min="1" :max="NS" step="1" aria-label="Кількість повторів">
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="cr__svg" role="img" aria-label="AUC валідаційних фолдів для 20 зерен">
      <rect :x="PL" :width="W - PL - PR" :y="Y(pooled.m + pooled.sd)" :height="Y(pooled.m - pooled.sd) - Y(pooled.m + pooled.sd)" class="cr__band" />
      <line :x1="PL" :x2="W - PR" :y1="Y(pooled.m)" :y2="Y(pooled.m)" class="cr__pooled" />
      <g v-for="v in yTicks" :key="'y' + v">
        <line :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" class="cr__grid" />
        <text :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="cr__lbl">{{ num(v, 2) }}</text>
      </g>
      <g v-for="(fs, i) in F" :key="'s' + i" :class="{ 'is-off': i >= reps }">
        <circle v-for="(a, k) in fs" :key="k" :cx="X(i) + (k - 2) * 1.6" :cy="Y(a)" r="2" :class="i === seed ? 'cr__dot is-cur' : 'cr__dot'" />
        <line :x1="X(i) - 6" :x2="X(i) + 6" :y1="Y(seedMeans[i])" :y2="Y(seedMeans[i])" :class="i === seed ? 'cr__mean is-cur' : 'cr__mean'" />
      </g>
      <text v-for="i in [0, 4, 9, 14, 19]" :key="'x' + i" :x="X(i)" :y="H - PB + 13" text-anchor="middle" class="cr__lbl">{{ i }}</text>
      <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="cr__lbl">зерно розбиття</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(cur.m) }}</b><span>середня AUC повтору {{ seed }}</span></div>
      <div class="lab__stat"><b>{{ num(cur.lo) }}…{{ num(cur.hi) }}</b><span>найгірший і найкращий фолд повтору</span></div>
      <div class="lab__stat is-warm"><b>{{ num(pooled.m) }} ± {{ num(pooled.sd) }}</b><span>середнє ± SD за {{ pooled.n }} навчаннями</span></div>
      <div class="lab__stat"><b>{{ num(pooled.mlo) }}…{{ num(pooled.mhi) }}</b><span>середні окремих повторів</span></div>
    </div>
    <p class="lab__note">
      При 5 повторах смуга збігається з рядком «лог. регресія» у виводі коду. Посуньте перший повзунок: середнє одного
      повтору змінюється від зерна до зерна менше, ніж окремі фолди, але саме одне число й потрапило б у статтю, якби
      розбиття було одне. Другий повзунок показує, що від п’яти повторів SD за навчаннями майже не змінюється: це розкид
      окремого фолду, а не похибка середнього.
    </p>
  </div>
</template>

<style scoped>
.cr__svg { width: 100%; height: auto; display: block; }
.cr__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.cr__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.cr__band { fill: var(--uk-warm-soft); }
.cr__pooled { stroke: var(--uk-warm); stroke-width: 1.4; }
.cr__dot { fill: var(--uk-accent); opacity: 0.55; }
.cr__dot.is-cur { fill: var(--uk-warm); opacity: 1; }
.cr__mean { stroke: var(--vp-c-text-2); stroke-width: 1.6; }
.cr__mean.is-cur { stroke: var(--uk-warm); stroke-width: 2.4; }
.is-off { opacity: 0.25; }
</style>
