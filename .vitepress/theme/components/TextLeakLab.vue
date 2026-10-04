<script setup lang="ts">
/**
 * Витік мітки через текст висновку (лекція 14, розділ «Висновок рентгенолога містить мітку»).
 * Дані — tools/gen_lec14_textleak.py: TF-IDF (уніграми і біграми) + логістична регресія за текстом
 * заключень ClinicalReadings, навчання dev1…dev4 S1, валідація dev0. На кожному кроці k вирізається
 * слово з найбільшою за модулем вагою, і модель навчається заново. Крок k = 0 збігається з виводом
 * блоку коду (AUC і перше слово перевіряє --check генератора).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec14_textleak.json'

type Step = { k: number; auc: number; empty: number; next: string }
const S = data.steps as Step[]
const K = S.length - 1
const k = ref(0)
const cur = computed(() => S[k.value])
const removed = computed(() => S.slice(0, k.value).map((s) => s.next))
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const pct = (v: number) => (100 * v).toFixed(1).replace('.', ',') + ' %'

const W = 360, H = 170, PL = 34, PR = 10, PT = 10, PB = 28
const X = (i: number) => PL + (i / K) * (W - PL - PR)
const Y = (v: number) => PT + (1 - (v - 0.4) / 0.6) * (H - PT - PB)
const aucPath = computed(() => S.map((s, i) => `${X(i).toFixed(1)},${Y(s.auc).toFixed(1)}`).join(' '))
const emptyPath = computed(() => S.map((s, i) => `${X(i).toFixed(1)},${Y(0.4 + 0.6 * s.empty).toFixed(1)}`).join(' '))
const yTicks = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Чи можна «почистити» висновок рентгенолога, вирізавши слова</div>
        <div class="lab__sub">
          Модель TF-IDF + логістична регресія вчиться на {{ data.n_train }} заключеннях і оцінюється на {{ data.n_val }}
          валідаційних. На кожному кроці вирізається слово з найбільшою вагою, і модель навчається заново.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>вирізано слів: <b>{{ k }}</b></span>
        <input v-model.number="k" type="range" min="0" :max="K" step="1" aria-label="Кількість вирізаних слів">
      </label>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(cur.auc) }}</b><span>AUC на валідації</span></div>
      <div class="lab__stat"><b>{{ pct(cur.empty) }}</b><span>валідаційних текстів стали порожніми</span></div>
      <div class="lab__stat"><b>{{ cur.next }}</b><span>наступне слово з найбільшою вагою</span></div>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="tl__svg" role="img" aria-label="AUC і частка порожніх текстів залежно від кількості вирізаних слів">
      <g v-for="v in yTicks" :key="'y' + v">
        <line :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" :class="v === 0.5 ? 'tl__half' : 'tl__grid'" />
        <text :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="tl__lbl">{{ num(v, 1) }}</text>
      </g>
      <text v-for="i in [0, 5, 10, 15, 20, 25, 30]" :key="'x' + i" :x="X(i)" :y="H - PB + 12" text-anchor="middle" class="tl__lbl">{{ i }}</text>
      <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="tl__lbl">вирізано слів</text>
      <polyline :points="emptyPath" class="tl__empty" />
      <polyline :points="aucPath" class="tl__auc" />
      <line :x1="X(k)" :x2="X(k)" :y1="PT" :y2="H - PB" class="tl__cur" />
      <circle :cx="X(k)" :cy="Y(cur.auc)" r="3.5" class="tl__dot" />
    </svg>
    <div class="tl__legend">
      <span><i class="tl__k tl__k--a"></i>AUC на валідації</span>
      <span><i class="tl__k tl__k--e"></i>частка порожніх текстів (шкала 0…100 % на тій самій висоті)</span>
    </div>

    <div class="tl__words">
      <span class="tl__wlabel">вирізані слова:</span>
      <span v-if="!removed.length" class="tl__none">жодного</span>
      <code v-for="w in removed" :key="w">{{ w }}</code>
    </div>
    <p class="lab__note">
      Після вирізання слова normal половина валідаційних текстів стає порожньою, а AUC лишається 1,000: порожній текст
      сам означає «норма». Кожне наступне слово знижує AUC повільно, бо в описах туберкульозу лишаються інші слова — про
      локалізацію, плевру, давні зміни.
    </p>
  </div>
</template>

<style scoped>
.tl__svg { width: 100%; height: auto; display: block; margin-top: 0.4rem; }
.tl__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.tl__half { stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 4 3; }
.tl__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.tl__auc { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.tl__empty { fill: none; stroke: var(--uk-accent); stroke-width: 1.4; stroke-dasharray: 3 2; }
.tl__cur { stroke: var(--vp-c-text-1); stroke-width: 1; stroke-dasharray: 2 2; }
.tl__dot { fill: var(--uk-warm); }
.tl__legend { display: flex; flex-wrap: wrap; gap: 0.3rem 1rem; font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.3rem; }
.tl__k { display: inline-block; width: 18px; height: 0; border-top: 2px solid; vertical-align: middle; margin-right: 0.35rem; }
.tl__k--a { border-color: var(--uk-warm); }
.tl__k--e { border-top: 2px dashed var(--uk-accent); }
.tl__words { display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; margin-top: 0.6rem; font-size: 0.8rem; }
.tl__wlabel { color: var(--vp-c-text-2); margin-right: 0.2rem; }
.tl__none { color: var(--vp-c-text-3); }
.tl__words code { font-size: 0.76rem; }
</style>
