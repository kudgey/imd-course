<script setup lang="ts">
/**
 * Витік через відбір ознак (лекція 07, розділ «Відбір ознак поза крос-валідацією як витік»).
 * Дані — tools/gen_lec07_leak.py: мітки dev-частини S1 (638 знімків), N гаусових шумових ознак
 * (без зв’язку з міткою) або шум разом із 66 реальними ознаками; k ознак відбирає SelectKBest(f_classif)
 * один раз до крос-валідації або всередині конвеєра на кожному фолді; далі логістична регресія,
 * StratifiedGroupKFold(5) за пацієнтами, 5 повторів. Точка N = 2000, k = 20 збігається з виводом
 * блоку коду (перевіряє --check генератора).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec07_leak.json'

const NS = data.N as number[]
const KS = data.k as number[]
const TABLE = { noise: data.noise as Record<string, number[]>, real: data.real as Record<string, number[]> }
const ni = ref(NS.indexOf(2000))
const ki = ref(KS.indexOf(20))
const variant = ref<'noise' | 'real'>('noise')
const get = (n: number, k: number, mode: string) => TABLE[variant.value][`${n}_${k}_${mode}`]
const cur = computed(() => {
  const b = get(NS[ni.value], KS[ki.value], 'before'), i = get(NS[ni.value], KS[ki.value], 'inside')
  return { b, i, gap: b[0] - i[0] }
})
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const big = (v: number) => v.toLocaleString('uk-UA').replace(/\s/g, ' ')

const W = 380, H = 200, PL = 36, PR = 12, PT = 10, PB = 30
const Y0 = 0.35, Y1 = 1.0
const X = (j: number) => PL + (j / (KS.length - 1)) * (W - PL - PR)
const Y = (v: number) => PT + (1 - (v - Y0) / (Y1 - Y0)) * (H - PT - PB)
const pathFor = (mode: string) => computed(() => KS.map((k, j) => `${X(j).toFixed(1)},${Y(get(NS[ni.value], k, mode)[0]).toFixed(1)}`).join(' '))
const beforePath = pathFor('before')
const insidePath = pathFor('inside')
const yTicks = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Відбір ознак до крос-валідації і всередині неї</div>
        <div class="lab__sub">
          Мітки ТБ 638 dev-знімків і N шумових ознак, не пов’язаних із міткою. Відібрати k «найкращих» за F-статистикою,
          потім логістична регресія і AUC на п’яти валідаційних фолдах (середнє ± SD за 5 повторами).
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>шумових ознак N: <b>{{ big(NS[ni]) }}</b></span>
        <input v-model.number="ni" type="range" min="0" :max="NS.length - 1" step="1" aria-label="Кількість шумових ознак">
      </label>
      <label class="lab__ctl">
        <span>відібрати k: <b>{{ KS[ki] }}</b></span>
        <input v-model.number="ki" type="range" min="0" :max="KS.length - 1" step="1" aria-label="Кількість відібраних ознак">
      </label>
      <div class="lab__ctl">
        <span>ознаки</span>
        <div class="lab__pills">
          <button type="button" class="lab__pill" :class="{ 'is-on': variant === 'noise' }" @click="variant = 'noise'">лише шум</button>
          <button type="button" class="lab__pill" :class="{ 'is-on': variant === 'real' }" @click="variant = 'real'">шум + 66 реальних</button>
        </div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(cur.b[0]) }} ± {{ num(cur.b[1]) }}</b><span>AUC, відбір до CV</span></div>
      <div class="lab__stat is-green"><b>{{ num(cur.i[0]) }} ± {{ num(cur.i[1]) }}</b><span>AUC, відбір усередині CV</span></div>
      <div class="lab__stat"><b>{{ num(cur.gap) }}</b><span>завищення оцінки</span></div>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="fl__svg" role="img" aria-label="AUC залежно від k для двох способів відбору">
      <g v-for="v in yTicks" :key="'y' + v">
        <line :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" :class="v === 0.5 ? 'fl__half' : 'fl__grid'" />
        <text :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="fl__lbl">{{ num(v, 1) }}</text>
      </g>
      <text v-for="(k, j) in KS" :key="'x' + k" :x="X(j)" :y="H - PB + 13" text-anchor="middle" class="fl__lbl">{{ k }}</text>
      <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="fl__lbl">відібрано ознак k (при N = {{ big(NS[ni]) }})</text>
      <polyline :points="beforePath" class="fl__before" />
      <polyline :points="insidePath" class="fl__inside" />
      <line :x1="X(ki)" :x2="X(ki)" :y1="PT" :y2="H - PB" class="fl__cur" />
    </svg>
    <div class="fl__legend">
      <span><i class="fl__k fl__k--b"></i>відбір до CV</span>
      <span><i class="fl__k fl__k--i"></i>відбір усередині CV</span>
      <span><i class="fl__k fl__k--h"></i>AUC 0,5 — вгадування</span>
    </div>
    <p class="lab__note">
      На чистому шумі правильна оцінка тримається біля 0,5 за будь-яких N і k, а відбір до крос-валідації дає тим вищу AUC,
      чим більше шумових ознак є з чого вибирати. Із реальними ознаками розрив зникає, поки k мале і в набір потрапляють
      сильні реальні ознаки; він з’являється знову, коли k велике і разом із ними відбирається шум.
    </p>
  </div>
</template>

<style scoped>
.fl__svg { width: 100%; height: auto; display: block; }
.fl__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.fl__half { stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 4 3; }
.fl__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.fl__before { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.fl__inside { fill: none; stroke: var(--uk-green); stroke-width: 2; }
.fl__cur { stroke: var(--vp-c-text-1); stroke-width: 1; stroke-dasharray: 2 2; }
.fl__legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.3rem; }
.fl__k { display: inline-block; width: 18px; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 0.35rem; }
.fl__k--b { border-color: var(--uk-warm); }
.fl__k--i { border-color: var(--uk-green); }
.fl__k--h { border-top: 1px dashed var(--vp-c-text-3); }
</style>
