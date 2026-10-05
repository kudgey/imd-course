<script setup lang="ts">
/**
 * Тест вилучення (лекція 16, розділ «Вилучення найважливіших пікселів»). Дані —
 * tools/gen_lec16_deletion.py з кривих, які записав блок коду: імовірність ТБ для 49 знімків TP
 * тесту Shenzhen після вилучення частки φ пікселів (0, 5 %, …, 100 %) у порядку Grad-CAM layer3,
 * інтегрованих градієнтів або випадковому; вилучений піксель замінено середнім сірим знімка або
 * розмитим знімком. S_del — площа під кривою за формулою трапецій (середнє за знімками).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec16_deletion.json'

type Curve = { mean: number[]; q1: number[]; q3: number[] }
const FR = data.fr as number[]
const FILLS = data.fills as string[]
const METHODS = data.methods as string[]
const CURVES = data.curves as Record<string, Curve>
const SDEL = data.sdel as Record<string, number[]>
const N = data.n as number
const COLORS = ['var(--uk-accent)', 'var(--uk-warm)', 'var(--vp-c-text-3)']

const fill = ref(FILLS[0])
const step = ref(4)
const band = ref(METHODS[0])

const mean = (a: number[]) => a.reduce((s, v) => s + v, 0) / a.length
const sdel = computed(() => METHODS.map(m => mean(SDEL[`${fill.value}|${m}`])))
const atStep = computed(() => METHODS.map(m => CURVES[`${fill.value}|${m}`].mean[step.value]))

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const W = 380, H = 210, PL = 34, PR = 10, PT = 10, PB = 30
const X = (f: number) => PL + f * (W - PL - PR)
const Y = (v: number) => PT + (1 - v) * (H - PT - PB)
const line = (m: string) => CURVES[`${fill.value}|${m}`].mean.map((v, i) => `${i ? 'L' : 'M'}${X(FR[i]).toFixed(1)},${Y(v).toFixed(1)}`).join(' ')
const area = computed(() => {
  const c = CURVES[`${fill.value}|${band.value}`]
  const up = c.q3.map((v, i) => `${i ? 'L' : 'M'}${X(FR[i]).toFixed(1)},${Y(v).toFixed(1)}`).join(' ')
  const dn = c.q1.map((v, i) => `L${X(FR[FR.length - 1 - i]).toFixed(1)},${Y(c.q1[FR.length - 1 - i]).toFixed(1)}`).join(' ')
  return `${up} ${dn} Z`
})
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Крива вилучення пікселів</div>
        <div class="lab__sub">
          {{ N }} знімків з туберкульозом, які модель S2 знайшла на тесті Shenzhen. Пікселі вилучаються в порядку
          спадання атрибуції; лінія — середня ймовірність туберкульозу, смуга — міжквартильний розмах для вибраного методу.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="f in FILLS" :key="f" type="button" class="lab__pill" :class="{ 'is-on': fill === f }"
              @click="fill = f">заповнення: {{ f }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="m in METHODS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': band === m }"
              @click="band = m">смуга: {{ m }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>вилучено пікселів: <b>{{ Math.round(FR[step] * 100) }} %</b></span>
        <input v-model.number="step" type="range" min="0" :max="FR.length - 1" step="1" aria-label="Частка вилучених пікселів">
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="dl__svg" role="img" aria-label="Криві вилучення">
      <line v-for="v in [0, 0.25, 0.5, 0.75, 1]" :key="'g' + v" :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" class="dl__grid" />
      <text v-for="v in [0, 0.5, 1]" :key="'y' + v" :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="dl__lbl">{{ num(v, 1) }}</text>
      <text v-for="f in [0, 0.25, 0.5, 0.75, 1]" :key="'x' + f" :x="X(f)" :y="H - 14" text-anchor="middle" class="dl__lbl">{{ f * 100 }} %</text>
      <path :d="area" :fill="COLORS[METHODS.indexOf(band)]" opacity="0.15" />
      <path v-for="(m, i) in METHODS" :key="m" :d="line(m)" fill="none" :stroke="COLORS[i]" stroke-width="2"
            :stroke-dasharray="i === 2 ? '4 3' : ''" />
      <line :x1="X(FR[step])" :x2="X(FR[step])" :y1="PT" :y2="H - PB" class="dl__mark" />
      <text :x="W - PR" :y="H - 2" text-anchor="end" class="dl__lbl">частка вилучених пікселів φ</text>
    </svg>

    <div class="lab__stats">
      <div v-for="(m, i) in METHODS" :key="m" class="lab__stat">
        <b :style="{ color: COLORS[i] }">{{ num(atStep[i]) }}</b>
        <span>{{ m }}: середня p при {{ Math.round(FR[step] * 100) }} %; S_del {{ num(sdel[i]) }}</span>
      </div>
    </div>

    <p class="lab__note">
      Менше S_del — швидше падає оцінка, але одне число ховає форму кривої. З сірим заповненням площі майже
      рівні, хоча криві різні: Grad-CAM падає найшвидше на перших 20 %, а після половини йде вище за дві інші.
      Праву точку кривої задає сама заміна: кадр без жодного пікселя знімка модель усе одно оцінює вище порогу.
      З розмитим заповненням випадкова крива спершу піднімається, і Grad-CAM опиняється далеко під нею.
    </p>
  </div>
</template>

<style scoped>
.dl__svg { width: 100%; max-width: 540px; height: auto; display: block; margin: 0.4rem 0; }
.dl__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.dl__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
.dl__mark { stroke: var(--vp-c-text-2); stroke-width: 1; stroke-dasharray: 3 3; }
</style>
