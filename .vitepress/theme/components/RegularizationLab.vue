<script setup lang="ts">
/**
 * Регуляризація логістичної регресії (лекція 07, розділ «Логістична регресія як перша модель»).
 * Дані — tools/gen_lec07_logreg.py: для 21 значення C (10^−3…10^2) і штрафів L2/L1 — середні за
 * п’ятьма фолдами курсу dev0…dev4 AUC на навчальних фолдах і на валідаційному фолді, кількість
 * ненульових ваг і середні ваги 66 стандартизованих ознак. Точки C = 0,001; 0,01; 0,1; 1; 10; 100
 * збігаються з таблицею у виводі блоку коду (перевіряє --check генератора).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec07_logreg.json'

type Pt = { train: number; val: number; nonzero: number; w: number[] }
const CS = data.C as number[]
const FEAT = data.features as string[]
const PATH: Record<'l2' | 'l1', Pt[]> = { l2: data.l2 as Pt[], l1: data.l1 as Pt[] }

const pen = ref<'l2' | 'l1'>('l2')
const idx = ref(CS.findIndex(c => Math.abs(c - 1) < 1e-9))
const cur = computed(() => PATH[pen.value][idx.value])
const best = computed(() => {
  const p = PATH[pen.value]
  let b = 0
  p.forEach((q, i) => { if (q.val > p[b].val) b = i })
  return b
})
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const cLabel = (c: number) => String(Number(c.toPrecision(2))).replace('.', ',')

/* графік AUC від lg C */
const W = 380, H = 190, PL = 36, PR = 12, PT = 10, PB = 30
const Y0 = 0.45, Y1 = 0.95
const X = (i: number) => PL + (i / (CS.length - 1)) * (W - PL - PR)
const Y = (v: number) => PT + (1 - (v - Y0) / (Y1 - Y0)) * (H - PT - PB)
const line = (key: 'train' | 'val') => computed(() => PATH[pen.value].map((q, i) => `${X(i).toFixed(1)},${Y(q[key]).toFixed(1)}`).join(' '))
const trainPath = line('train')
const valPath = line('val')
const yTicks = [0.5, 0.6, 0.7, 0.8, 0.9]
const xTicks = [-3, -2, -1, 0, 1, 2]

/* ваги: 12 найбільших за модулем при поточному C */
const bars = computed(() => {
  const w = cur.value.w
  const order = w.map((v, i) => i).filter(i => w[i] !== 0).sort((a, b) => Math.abs(w[b]) - Math.abs(w[a])).slice(0, 12)
  const m = Math.max(1e-6, ...PATH.l2[PATH.l2.length - 1].w.map(Math.abs), ...PATH.l1[PATH.l1.length - 1].w.map(Math.abs))
  return order.map(i => ({ name: FEAT[i], v: w[i], frac: Math.abs(w[i]) / m }))
})
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Логістична регресія: сила регуляризації C і штраф</div>
        <div class="lab__sub">
          66 ознак, dev-частина S1, середнє за п’ятьма фолдами курсу dev0…dev4. Мале C — сильний штраф і прості ваги,
          велике C — слабкий штраф.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>C = <b>{{ cLabel(CS[idx]) }}</b> (lg C = {{ num(Math.log10(CS[idx]), 2) }})</span>
        <input v-model.number="idx" type="range" min="0" :max="CS.length - 1" step="1" aria-label="Індекс значення C">
      </label>
      <div class="lab__ctl">
        <span>штраф</span>
        <div class="lab__pills">
          <button type="button" class="lab__pill" :class="{ 'is-on': pen === 'l2' }" @click="pen = 'l2'">L2 (ridge)</button>
          <button type="button" class="lab__pill" :class="{ 'is-on': pen === 'l1' }" @click="pen = 'l1'">L1 (lasso)</button>
        </div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(cur.train) }}</b><span>AUC на навчальних фолдах</span></div>
      <div class="lab__stat is-warm"><b>{{ num(cur.val) }}</b><span>AUC на валідаційному фолді</span></div>
      <div class="lab__stat"><b>{{ num(cur.train - cur.val) }}</b><span>розрив навчання − валідація</span></div>
      <div class="lab__stat is-green"><b>{{ num(cur.nonzero, 1) }}</b><span>ненульових ваг із 66</span></div>
    </div>

    <div class="rg__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" class="rg__svg" role="img" aria-label="AUC залежно від lg C">
        <g v-for="v in yTicks" :key="'y' + v">
          <line :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" class="rg__grid-l" />
          <text :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="rg__lbl">{{ num(v, 1) }}</text>
        </g>
        <text v-for="e in xTicks" :key="'x' + e" :x="X((e + 3) * 4)" :y="H - PB + 13" text-anchor="middle" class="rg__lbl">{{ e }}</text>
        <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="rg__lbl">lg C</text>
        <polyline :points="trainPath" class="rg__train" />
        <polyline :points="valPath" class="rg__val" />
        <line :x1="X(best)" :x2="X(best)" :y1="PT" :y2="H - PB" class="rg__best" />
        <line :x1="X(idx)" :x2="X(idx)" :y1="PT" :y2="H - PB" class="rg__cur" />
        <circle :cx="X(idx)" :cy="Y(cur.val)" r="3.5" class="rg__dot" />
      </svg>
      <div class="rg__bars">
        <div class="rg__bars-h">12 найбільших за модулем ваг (середнє за фолдами)</div>
        <div v-for="b in bars" :key="b.name" class="rg__bar">
          <code>{{ b.name }}</code>
          <span class="rg__track"><i :class="b.v > 0 ? 'is-pos' : 'is-neg'" :style="{ width: (100 * b.frac).toFixed(1) + '%' }"></i></span>
          <span class="rg__v">{{ num(b.v, 2) }}</span>
        </div>
        <div v-if="!bars.length" class="rg__empty">усі 66 ваг нульові</div>
      </div>
    </div>
    <div class="rg__legend">
      <span><i class="rg__k rg__k--train"></i>AUC навч.</span>
      <span><i class="rg__k rg__k--val"></i>AUC валід.</span>
      <span><i class="rg__k rg__k--best"></i>максимум AUC валід. (C = {{ cLabel(CS[best]) }})</span>
    </div>
    <p class="lab__note">
      Помаранчеві смуги — ваги, що піднімають імовірність ТБ, сині — ті, що знижують. Із L1 при C = 0,01 лишаються одиниці
      ненульових ваг, з L2 ненульові всі 66 при будь-якому C, лише менші за модулем. Валідаційна AUC майже не змінюється на
      двох декадах C, а навчальна росте весь час — розрив між ними і є мірою підгонки під навчальні фолди.
    </p>
  </div>
</template>

<style scoped>
.rg__grid { display: flex; flex-wrap: wrap; gap: 0.8rem; align-items: flex-start; }
.rg__svg { flex: 1 1 300px; width: 100%; max-width: 420px; height: auto; display: block; }
.rg__grid-l { stroke: var(--uk-line); stroke-width: 0.6; }
.rg__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.rg__train { fill: none; stroke: var(--uk-accent); stroke-width: 1.6; stroke-dasharray: 5 3; }
.rg__val { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.rg__best { stroke: var(--uk-green); stroke-width: 1; stroke-dasharray: 2 2; }
.rg__cur { stroke: var(--vp-c-text-1); stroke-width: 1.2; }
.rg__dot { fill: var(--uk-warm); }
.rg__bars { flex: 1 1 260px; min-width: 0; font-size: 0.78rem; }
.rg__bars-h { color: var(--vp-c-text-3); margin-bottom: 0.3rem; }
.rg__bar { display: grid; grid-template-columns: minmax(0, 11rem) 1fr 3rem; gap: 0.4rem; align-items: center; margin: 0.12rem 0; }
.rg__bar code { font-size: 0.72rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rg__track { height: 0.6rem; background: var(--uk-fill); border-radius: 3px; overflow: hidden; }
.rg__track i { display: block; height: 100%; }
.rg__track i.is-pos { background: var(--uk-warm); }
.rg__track i.is-neg { background: var(--uk-accent); }
.rg__v { text-align: right; font-variant-numeric: tabular-nums; }
.rg__empty { color: var(--vp-c-text-3); }
.rg__legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.3rem; }
.rg__k { display: inline-block; width: 18px; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 0.35rem; }
.rg__k--train { border-top: 2px dashed var(--uk-accent); }
.rg__k--val { border-color: var(--uk-warm); }
.rg__k--best { border-top: 1px dashed var(--uk-green); }
</style>
