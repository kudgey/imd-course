<script setup lang="ts">
/**
 * Криві навчання для п’яти функцій втрат (лекція 10, розділ «Порівняння функцій втрат на одному
 * наборі»). Дані — tools/gen_lec10_losses.py: середній Dice на валідаційній частині JSRT після кожної
 * епохи (записує сам блок коду) і підсумкова таблиця з виводу того самого блоку. Нічого не
 * перераховується: віджет лише показує вибрані криві й значення під курсором.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec10_losses.json'

const CURVES = data.val_dice as Record<string, number[]>
const TABLE = data.table as Record<string, number[]>
const NAMES = Object.keys(CURVES)
const COLORS = ['#2A78D6', '#EB6834', '#1BAF7A', '#EDA100', '#E87BA4']
const EP = data.epochs as number
const on = ref<Record<string, boolean>>(Object.fromEntries(NAMES.map(n => [n, true])))
const hover = ref(EP)

const W = 600, H = 260, L = 52, R = 14, T = 14, B = 34
const firstShown = 3 // перші епохи далеко внизу шкали — вісь Y від третьої епохи
const vals = NAMES.flatMap(n => CURVES[n].slice(firstShown - 1))
const yMin = Math.floor(Math.min(...vals) * 100) / 100, yMax = Math.ceil(Math.max(...vals) * 100) / 100
const xs = (e: number) => L + ((e - firstShown) / (EP - firstShown)) * (W - L - R)
const ys = (v: number) => T + (1 - (Math.max(v, yMin) - yMin) / (yMax - yMin)) * (H - T - B)
const lines = computed(() => NAMES.map((n, i) => ({
  n, color: COLORS[i], shown: on.value[n],
  d: CURVES[n].map((v, e) => (e + 1 < firstShown ? '' : `${e + 1 === firstShown ? 'M' : 'L'}${xs(e + 1).toFixed(1)},${ys(v).toFixed(1)}`)).join(' '),
})))
const yTicks = Array.from({ length: 5 }, (_, i) => yMin + (i * (yMax - yMin)) / 4)
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')

const svg = ref<SVGSVGElement | null>(null)
function move(ev: MouseEvent | TouchEvent) {
  const el = svg.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const cx = 'touches' in ev ? ev.touches[0].clientX : ev.clientX
  const x = ((cx - rect.left) / rect.width) * W
  const e = Math.round(firstShown + ((x - L) / (W - L - R)) * (EP - firstShown))
  hover.value = Math.min(EP, Math.max(firstShown, e))
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">П’ять функцій втрат: Dice на валідації після кожної епохи</div>
        <div class="lab__sub">
          U-Net 2D на знімках 128 × 128, однакові ініціалізація, порядок батчів і {{ EP }} епох; Dice — середнє по {{ data.n_val }}
          знімках валідації при порозі 0,5. Наведіть курсор на графік, щоб побачити значення в епосі.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="(n, i) in NAMES" :key="n" type="button" class="lab__pill" :class="{ 'is-on': on[n] }"
              :style="on[n] ? { borderColor: COLORS[i] } : {}" @click="on[n] = !on[n]">{{ n }}</button>
    </div>
    <svg ref="svg" :viewBox="`0 0 ${W} ${H}`" class="lc__svg" role="img" aria-label="Dice на валідації за епохами"
         @mousemove="move" @touchmove.passive="move">
      <g v-for="v in yTicks" :key="v">
        <line :x1="L" :x2="W - R" :y1="ys(v)" :y2="ys(v)" stroke="var(--vp-c-divider)" />
        <text :x="L - 6" :y="ys(v) + 4" text-anchor="end" class="lc__tick">{{ num(v, 2) }}</text>
      </g>
      <g v-for="e in EP" :key="'x' + e">
        <text v-if="e >= firstShown && e % 2 === 0" :x="xs(e)" :y="H - B + 16" text-anchor="middle" class="lc__tick">{{ e }}</text>
      </g>
      <text :x="(L + W - R) / 2" :y="H - 4" text-anchor="middle" class="lc__tick">епоха</text>
      <line :x1="xs(hover)" :x2="xs(hover)" :y1="T" :y2="H - B" stroke="var(--vp-c-text-2)" stroke-dasharray="4 3" />
      <path v-for="l in lines" v-show="l.shown" :key="l.n" :d="l.d" fill="none" :stroke="l.color" stroke-width="2" />
    </svg>
    <div class="lc__wrap">
    <table class="lc__table">
      <thead><tr><th>втрата</th><th>Dice, епоха {{ hover }}</th><th>Dice, епоха {{ EP }}</th><th>HD95, мм</th><th>&gt; 2 компоненти</th><th>час, с</th></tr></thead>
      <tbody>
        <tr v-for="(n, i) in NAMES" :key="n" :style="{ opacity: on[n] ? 1 : 0.45 }">
          <td><i class="lc__dot" :style="{ background: COLORS[i] }"></i>{{ n }}</td>
          <td>{{ num(CURVES[n][hover - 1]) }}</td>
          <td>{{ num(TABLE[n][0]) }}</td>
          <td>{{ num(TABLE[n][1], 1) }}</td>
          <td>{{ TABLE[n][2] }}</td>
          <td>{{ TABLE[n][3] }}</td>
        </tr>
      </tbody>
    </table>
    </div>
    <p class="lab__note">
      Криві розходяться в перших епохах і сходяться до кінця: для великої структури, як легені, вибір втрати
      впливає більше на швидкість, ніж на підсумок. Один прогін на кожну втрату не дає оцінки розкиду, тому
      різниця в третьому знаку — не рейтинг.
    </p>
  </div>
</template>

<style scoped>
.lc__svg { width: 100%; height: auto; display: block; touch-action: pan-y; }
.lc__wrap { overflow-x: auto; }
.lc__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.lc__table th { font-weight: 500; font-size: 0.72rem; color: var(--vp-c-text-2); text-align: right; padding: 0.3rem 0.45rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; }
.lc__table th:first-child, .lc__table td:first-child { text-align: left; }
.lc__table td { font-size: 0.82rem; text-align: right; white-space: nowrap; padding: 0.3rem 0.45rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; }
.lc__tick { font-size: 11px; fill: var(--vp-c-text-2); }
.lc__dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 0.4rem; vertical-align: middle; }
</style>
