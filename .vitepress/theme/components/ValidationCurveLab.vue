<script setup lang="ts">
/**
 * Крива валідації градієнтного бустингу (лекція 07, розділ «Перенавчання і крива валідації»).
 * Дані — tools/gen_lec07_valcurve.py: LightGBM (крок 0,1, min_child_samples = 5) на 66 ознаках,
 * dev-частина S1, п’ять фолдів курсу dev0…dev4; для 6 значень кількості листків і 13 значень
 * кількості дерев — середні AUC і log-loss на навчальних і валідаційному фолдах. Точки мінімуму
 * log-loss збігаються з таблицею у виводі блоку коду (перевіряє --check генератора).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec07_valcurve.json'

type Curve = { auc_train: number[]; auc_val: number[]; ll_train: number[]; ll_val: number[] }
const TREES = data.trees as number[]
const LEAVES = data.leaves as number[]
const CURVES = data.curves as Record<string, Curve>
const leaves = ref(8)
const ti = ref(TREES.length - 1)
const metric = ref<'auc' | 'll'>('ll')
const c = computed(() => CURVES[String(leaves.value)])
const bestI = computed(() => { const v = c.value.ll_val; return v.indexOf(Math.min(...v)) })
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')

const W = 380, H = 200, PL = 38, PR = 12, PT = 10, PB = 30
const range = computed(() => (metric.value === 'auc' ? [0.75, 1.0] : [0, 1.1]))
const X = (i: number) => PL + (i / (TREES.length - 1)) * (W - PL - PR)
const Y = (v: number) => { const [a, b] = range.value; return PT + (1 - (Math.min(Math.max(v, a), b) - a) / (b - a)) * (H - PT - PB) }
const tr = computed(() => (metric.value === 'auc' ? 'auc_train' : 'll_train') as keyof Curve)
const va = computed(() => (metric.value === 'auc' ? 'auc_val' : 'll_val') as keyof Curve)
const trPath = computed(() => c.value[tr.value].map((v, i) => `${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' '))
const vaPath = computed(() => c.value[va.value].map((v, i) => `${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' '))
const yTicks = computed(() => (metric.value === 'auc' ? [0.75, 0.8, 0.85, 0.9, 0.95, 1.0] : [0, 0.2, 0.4, 0.6, 0.8, 1.0]))
const xTickIdx = [0, 2, 4, 6, 8, 10, 12]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Крива валідації LightGBM: складність дерева і кількість дерев</div>
        <div class="lab__sub">
          Середнє за п’ятьма фолдами курсу dev0…dev4; крок навчання 0,1. Вертикальна риска — вибрана кількість дерев, зелена
          точка — мінімум log-loss на валідаційних фолдах.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <div class="lab__ctl">
        <span>листків у дереві</span>
        <div class="lab__pills">
          <button v-for="L in LEAVES" :key="L" type="button" class="lab__pill" :class="{ 'is-on': leaves === L }" @click="leaves = L">{{ L }}</button>
        </div>
      </div>
      <label class="lab__ctl">
        <span>дерев: <b>{{ TREES[ti] }}</b></span>
        <input v-model.number="ti" type="range" min="0" :max="TREES.length - 1" step="1" aria-label="Кількість дерев">
      </label>
      <div class="lab__ctl">
        <span>міра на графіку</span>
        <div class="lab__pills">
          <button type="button" class="lab__pill" :class="{ 'is-on': metric === 'll' }" @click="metric = 'll'">log-loss</button>
          <button type="button" class="lab__pill" :class="{ 'is-on': metric === 'auc' }" @click="metric = 'auc'">AUC</button>
        </div>
      </div>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="vc__svg" role="img" aria-label="Міра якості на навчальних і валідаційних фолдах залежно від кількості дерев">
      <g v-for="v in yTicks" :key="'y' + v">
        <line :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" class="vc__grid" />
        <text :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="vc__lbl">{{ num(v, metric === 'auc' ? 2 : 1) }}</text>
      </g>
      <text v-for="i in xTickIdx" :key="'x' + i" :x="X(i)" :y="H - PB + 13" text-anchor="middle" class="vc__lbl">{{ TREES[i] }}</text>
      <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="vc__lbl">кількість дерев (логарифмічна шкала)</text>
      <polyline :points="trPath" class="vc__train" />
      <polyline :points="vaPath" class="vc__val" />
      <line :x1="X(ti)" :x2="X(ti)" :y1="PT" :y2="H - PB" class="vc__cur" />
      <circle :cx="X(bestI)" :cy="Y(c[va][bestI])" r="4" class="vc__best" />
    </svg>
    <div class="vc__legend">
      <span><i class="vc__k vc__k--t"></i>навчальні фолди</span>
      <span><i class="vc__k vc__k--v"></i>валідаційний фолд</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(c.auc_train[ti]) }} / {{ num(c.auc_val[ti]) }}</b><span>AUC навч. / валід.</span></div>
      <div class="lab__stat is-warm"><b>{{ num(c.ll_val[ti]) }}</b><span>log-loss на валідаційному фолді</span></div>
      <div class="lab__stat"><b>{{ num(c.auc_train[ti] - c.auc_val[ti]) }}</b><span>розрив AUC навч. − валід.</span></div>
      <div class="lab__stat is-green"><b>{{ TREES[bestI] }} дерев</b><span>мінімум log-loss: {{ num(c.ll_val[bestI]) }}</span></div>
    </div>
    <p class="lab__note">
      Перемкніть міру. На log-loss валідаційна крива має виразний мінімум, після якого росте, хоча навчальна падає до нуля;
      на AUC та сама модель після мінімуму ще трохи покращується або стоїть на місці. Ранжування знімків псується пізніше,
      ніж імовірності: модель стає надто впевненою раніше, ніж починає плутати порядок.
    </p>
  </div>
</template>

<style scoped>
.vc__svg { width: 100%; height: auto; display: block; }
.vc__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.vc__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.vc__train { fill: none; stroke: var(--uk-accent); stroke-width: 1.6; stroke-dasharray: 5 3; }
.vc__val { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.vc__cur { stroke: var(--vp-c-text-1); stroke-width: 1.2; }
.vc__best { fill: var(--uk-green); }
.vc__legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.3rem; }
.vc__k { display: inline-block; width: 18px; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 0.35rem; }
.vc__k--t { border-top: 2px dashed var(--uk-accent); }
.vc__k--v { border-color: var(--uk-warm); }
</style>
