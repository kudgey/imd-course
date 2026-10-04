<script setup lang="ts">
/**
 * Злиття знімка з віком і статтю (лекція 14, розділ «Експеримент: знімок + вік + стать для скринінгу ТБ»).
 * Дані — tools/gen_lec14_fusion.py: dev-частина S1 (638 знімків), 1024 заморожені ознаки xrv DenseNet-121,
 * вік і стать із ClinicalReadings, 10 повторів StratifiedGroupKFold(5) за пацієнтами. Способи злиття:
 * «пізнє: середнє» (середнє ймовірностей двох моделей, без навчання), «стекінг», «ознаки + LR», «PCA + GBDT»
 * (три останні — раннє злиття типу II за Huang et al., 2020). Для кожного набору
 * входів, способу злиття і частки прихованого віку (0 / 30 / 60 % валідаційних знімків; медіана + індикатор,
 * модальнісний dropout у навчанні) — AUC (середнє ± SD за повторами), AUC у Montgomery і Shenzhen, різниця
 * з «лише знімок». Рядки без пропусків збігаються з таблицею виводу блоку коду (перевіряє --check).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec14_fusion.json'

type Cfg = { auc: number; sd: number; mont: number; shz: number; delta: number; pos: number; seeds: number[] }
const CFG = data.configs as Record<string, Cfg>
const FUSIONS = data.fusions as string[]
const MISSING = data.missing as number[]

const img = ref(true)
const age = ref(true)
const sex = ref(true)
const fusion = ref('стекінг')
const miss = ref(0)

const tname = computed(() => [age.value ? 'вік' : '', sex.value ? 'стать' : ''].filter(Boolean).join(' + '))
const hasTab = computed(() => tname.value !== '')
const pct = computed(() => (age.value ? miss.value : 0))
const key = computed(() => {
  if (img.value && hasTab.value) return `знімок + ${tname.value}|${fusion.value}|${pct.value}`
  if (img.value) return 'знімок||0'
  if (hasTab.value) return `${tname.value}||${pct.value}`
  return ''
})
const cur = computed(() => (key.value ? CFG[key.value] : null))
const base = CFG['знімок||0']
const label = computed(() => {
  if (!key.value) return 'оберіть хоча б один вхід'
  if (img.value && hasTab.value) return `знімок + ${tname.value}: ${fusion.value}`
  return img.value ? 'лише знімок' : `лише таблиця: ${tname.value}`
})
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const sign = (v: number) => (v > 0 ? '+' : '') + num(v)

const W = 360, H = 118, PL = 92, PR = 44, PT = 6, BH = 13
const X0 = 0.5, X1 = 1.0
const X = (v: number) => PL + ((Math.max(X0, Math.min(X1, v)) - X0) / (X1 - X0)) * (W - PL - PR)
const bars = computed(() => {
  if (!cur.value) return []
  return [
    { name: 'усі знімки', v: cur.value.auc, b: base.auc },
    { name: 'Montgomery', v: cur.value.mont, b: base.mont },
    { name: 'Shenzhen', v: cur.value.shz, b: base.shz },
  ]
})
const xTicks = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Знімок, вік і стать: що дає злиття на скринінгу ТБ</div>
        <div class="lab__sub">
          638 dev-знімків S1, 10 повторів п’ятифолдової крос-валідації за пацієнтами; тест S1 не відкривається. Знімок —
          1024 заморожені ознаки xrv DenseNet-121.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <div class="lab__ctl">
        <span>входи</span>
        <div class="lab__pills">
          <button type="button" class="lab__pill" :class="{ 'is-on': img }" @click="img = !img">знімок</button>
          <button type="button" class="lab__pill" :class="{ 'is-on': age }" @click="age = !age">вік</button>
          <button type="button" class="lab__pill" :class="{ 'is-on': sex }" @click="sex = !sex">стать</button>
        </div>
      </div>
      <div class="lab__ctl">
        <span>спосіб злиття</span>
        <div class="lab__pills">
          <button v-for="f in FUSIONS" :key="f" type="button" class="lab__pill" :class="{ 'is-on': fusion === f }"
            :disabled="!(img && hasTab)" @click="fusion = f">{{ f }}</button>
        </div>
      </div>
      <div class="lab__ctl">
        <span>вік прихований у валідації</span>
        <div class="lab__pills">
          <button v-for="m in MISSING" :key="m" type="button" class="lab__pill" :class="{ 'is-on': miss === m }"
            :disabled="!age" @click="miss = m">{{ m }} %</button>
        </div>
      </div>
    </div>

    <div class="fu__label">{{ label }}</div>
    <div v-if="cur" class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(cur.auc) }} ± {{ num(cur.sd) }}</b><span>AUC, середнє ± sd за 10 повторами</span></div>
      <div class="lab__stat"><b>{{ sign(cur.delta) }}</b><span>різниця з «лише знімок» ({{ num(base.auc) }})</span></div>
      <div class="lab__stat"><b>{{ cur.pos }} / 10</b><span>повторів, де різниця > 0</span></div>
    </div>

    <svg v-if="cur" :viewBox="`0 0 ${W} ${H}`" class="fu__svg" role="img" aria-label="AUC обраної конфігурації і лише знімка за джерелами">
      <g v-for="v in xTicks" :key="'x' + v">
        <line :x1="X(v)" :x2="X(v)" :y1="PT" :y2="PT + 3 * (2 * BH + 6)" class="fu__grid" />
        <text :x="X(v)" :y="PT + 3 * (2 * BH + 6) + 10" text-anchor="middle" class="fu__lbl">{{ num(v, 1) }}</text>
      </g>
      <g v-for="(b, i) in bars" :key="b.name" :transform="`translate(0, ${PT + i * (2 * BH + 6)})`">
        <text :x="PL - 6" :y="BH + 2" text-anchor="end" class="fu__name">{{ b.name }}</text>
        <rect :x="PL" :y="0" :width="X(b.v) - PL" :height="BH - 1" class="fu__cur" />
        <rect :x="PL" :y="BH" :width="X(b.b) - PL" :height="BH - 1" class="fu__base" />
        <text :x="X(b.v) + 4" :y="BH - 3" class="fu__lbl">{{ num(b.v) }}</text>
        <text :x="X(b.b) + 4" :y="2 * BH - 3" class="fu__lbl">{{ num(b.b) }}</text>
      </g>
    </svg>
    <div v-if="cur" class="fu__legend">
      <span><i class="fu__k fu__k--c"></i>обрана конфігурація</span>
      <span><i class="fu__k fu__k--b"></i>лише знімок</span>
    </div>
    <p class="lab__note">
      Без пропусків числа збігаються з таблицею виводу коду. Порівняйте способи злиття: середнє ймовірностей без навчання програє
      знімку, стекінг знімка з віком і статтю дає найбільший приріст на всіх знімках і в Shenzhen, а в Montgomery трохи поступається
      «лише знімку» — на 108 знімках це в межах шуму (інтервали — у розділі про парне порівняння); PCA + GBDT програє знімку
      в будь-якому поєднанні. Приховування віку майже не змінює стекінг, бо сигнал іде від знімка, а модель лише на таблиці
      втрачає помітно.
    </p>
  </div>
</template>

<style scoped>
.fu__label { font-size: 0.84rem; color: var(--vp-c-text-2); margin: 0.5rem 0 0.1rem; font-weight: 600; }
.fu__svg { width: 100%; height: auto; display: block; margin-top: 0.5rem; }
.fu__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.fu__lbl { fill: var(--vp-c-text-3); font-size: 8.5px; }
.fu__name { fill: var(--vp-c-text-2); font-size: 9.5px; }
.fu__cur { fill: var(--uk-warm); }
.fu__base { fill: var(--uk-accent); opacity: 0.55; }
.fu__legend { display: flex; flex-wrap: wrap; gap: 0.3rem 1rem; font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.2rem; }
.fu__k { display: inline-block; width: 14px; height: 9px; vertical-align: middle; margin-right: 0.35rem; border-radius: 2px; }
.fu__k--c { background: var(--uk-warm); }
.fu__k--b { background: var(--uk-accent); opacity: 0.55; }
.lab__pill:disabled { opacity: 0.4; cursor: default; }
</style>
