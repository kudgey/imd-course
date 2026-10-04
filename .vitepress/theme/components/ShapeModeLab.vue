<script setup lang="ts">
/**
 * Статистична модель форми SCR (лекція 11, розділ «Статистична модель форми: орієнтири, Прокруст,
 * PCA»). Дані — tools/gen_lec11_shape.py: 247 форм × 166 відповідних точок із `landmarks.zip` (SCR,
 * CC BY 4.0), узагальнений Прокруст і PCA, як у блоці коду; середня форма, перші 5 мод (знак кожної
 * зафіксовано: найбільша за модулем координата додатна), √λ і частки дисперсії. Віджет будує
 * x = x̄ + Σ b_i φ_i для перших трьох мод, b_i = c_i · √λ_i, c_i ∈ [−3; 3]. Частки дисперсії генератор
 * звіряє з виводом коду. Координати — у системі середньої форми (сітка 1024 × 1024 SCR після
 * вирівнювання), вісь y — донизу, як на знімку.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec11_shape.json'

const MEAN = data.mean as number[]
const MODES = data.modes as number[][]
const SD = data.sd as number[]
const SHARE = data.share as number[]
const COUNTS = data.counts as number[]
const PARTS = data.parts as string[]
const NEED = data.need as number[]
const COLORS = ['#2A78D6', '#EB6834', '#1BAF7A', '#EDA100', '#E87BA4']

const c = ref([0, 0, 0])
const shape = computed(() => MEAN.map((v, i) => v + c.value.reduce((s, ci, m) => s + ci * SD[m] * MODES[m][i], 0)))
function polys(s: number[]) {
  const out: string[] = []
  let p = 0
  for (const n of COUNTS) {
    const pts: string[] = []
    for (let j = 0; j < n; j++) pts.push(`${s[2 * (p + j)].toFixed(1)},${s[2 * (p + j) + 1].toFixed(1)}`)
    out.push(pts.join(' '))
    p += n
  }
  return out
}
const meanPolys = polys(MEAN)
const curPolys = computed(() => polys(shape.value))
const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const cum = computed(() => SHARE.slice(0, 3).reduce((a, b) => a + b, 0))
function reset() { c.value = [0, 0, 0] }
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Моди форми: як легені, серце й ключиці відрізняються між людьми</div>
        <div class="lab__sub">
          247 форм SCR після узагальненого Прокруста; сірим — середня форма, кольором — x̄ + b₁φ₁ + b₂φ₂ + b₃φ₃.
          Повзунки задають кожен коефіцієнт у стандартних відхиленнях моди: межа ±3√λ — обмеження правдоподібності моделі.
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label v-for="m in 3" :key="m" class="lab__ctl">
        <span>мода {{ m }} ({{ num(SHARE[m - 1]) }} % дисперсії): <b>b{{ m }} = {{ num(c[m - 1]) }}√λ</b></span>
        <input v-model.number="c[m - 1]" type="range" min="-3" max="3" step="0.25" :aria-label="`Коефіцієнт моди ${m}`">
      </label>
    </div>
    <div class="sh__grid">
      <svg viewBox="-570 -400 1080 940" class="sh__svg" role="img" aria-label="Середня форма і форма з вибраними коефіцієнтами мод">
        <polygon v-for="(p, i) in meanPolys" :key="'m' + i" :points="p" fill="none" stroke="#C8C8D4" stroke-width="5" />
        <polygon v-for="(p, i) in curPolys" :key="'c' + i" :points="p" fill="none" :stroke="COLORS[i]" stroke-width="7" stroke-linejoin="round" />
      </svg>
      <div>
        <div class="lab__stats sh__stats">
          <div class="lab__stat"><b>{{ num(cum) }} %</b><span>дисперсії пояснюють перші три моди</span></div>
          <div class="lab__stat is-warm"><b>{{ NEED[1] }}</b><span>мод потрібно для 95 % (для 90 % — {{ NEED[0] }}, для 99 % — {{ NEED[2] }})</span></div>
        </div>
        <div class="sh__legend">
          <span v-for="(p, i) in PARTS" :key="p"><i :style="{ background: COLORS[i] }"></i>{{ p }} ({{ COUNTS[i] }})</span>
        </div>
        <button class="lab__btn" @click="reset">повернути середню форму</button>
      </div>
    </div>
    <p class="lab__note">
      Права легеня пацієнта — ліворуч на рисунку, як на знімку. Кожна мода змінює всі структури разом: модель вивчила
      не окремі контури, а їхню узгоджену мінливість. Форми за межею ±3√λ хоча б однієї моди модель вважає неправдоподібними —
      саме так обмеження форми працює в моделі активної форми.
    </p>
  </div>
</template>

<style scoped>
.sh__grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
@media (max-width: 640px) { .sh__grid { grid-template-columns: 1fr; } }
.sh__svg { width: 100%; max-width: 380px; height: auto; display: block; margin: 0 auto; }
.sh__stats { grid-template-columns: 1fr; margin-top: 0; }
.sh__legend { display: flex; flex-wrap: wrap; gap: 0.7rem; font-size: 0.78rem; color: var(--vp-c-text-2); margin: 0.7rem 0; }
.sh__legend i { display: inline-block; width: 14px; height: 4px; border-radius: 2px; margin-right: 0.35rem; vertical-align: middle; }
</style>
