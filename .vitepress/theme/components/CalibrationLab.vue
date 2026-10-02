<script setup lang="ts">
/**
 * Діаграма надійності і температурне масштабування (лекція 08, розділ «Температурне масштабування на
 * валідації»). Логіти повного донавчання ResNet-18 на валідації (dev0, 128 знімків) і тесті S1
 * (162 знімки). p = σ(z / T); ECE = Σ_b (n_b / N)·|ȳ_b − p̄_b| за кошиками рівної ширини, NLL — середня
 * бінарна крос-ентропія, показник Браєра — середнє (p − y)². T* — мінімум NLL на валідації (перебір з
 * кроком 0,001), як у блоці коду. Дані: tools/gen_lec08_calib.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec08_calib.json'

type Part = { z: number[]; y: number[] }
const parts = data.parts as Record<string, Part>
const TSTAR = data.T as number

const T = ref(1)
const bins = ref(10)
const part = ref<'val' | 'test'>('test')

const res = computed(() => {
  const { z, y } = parts[part.value]
  const p = z.map((v) => 1 / (1 + Math.exp(-v / T.value)))
  const N = p.length
  const cnt = new Array(bins.value).fill(0)
  const sp = new Array(bins.value).fill(0)
  const sy = new Array(bins.value).fill(0)
  let nll = 0, brier = 0, mean = 0
  p.forEach((v, i) => {
    const b = Math.min(bins.value - 1, Math.floor(v * bins.value))
    cnt[b]++; sp[b] += v; sy[b] += y[i]
    const zt = z[i] / T.value
    nll += Math.max(zt, 0) + Math.log1p(Math.exp(-Math.abs(zt))) - y[i] * zt
    brier += (v - y[i]) ** 2
    mean += v
  })
  let ece = 0
  const bars = cnt.map((c, b) => {
    if (!c) return null
    const pb = sp[b] / c
    const yb = sy[b] / c
    ece += (c / N) * Math.abs(yb - pb)
    return { b, c, pb, yb }
  }).filter((x) => x !== null) as { b: number; c: number; pb: number; yb: number }[]
  return { ece, nll: nll / N, brier: brier / N, mean: mean / N, bars, N, rate: y.reduce((a, v) => a + v, 0) / N }
})

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const S = 230
const P = 28
const X = (v: number) => P + v * (S - P - 8)
const Y = (v: number) => S - P - v * (S - P - 8)
const TMIN = 0.5
const TMAX = 3
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Діаграма надійності і температура</div>
        <div class="lab__sub">
          Рухайте температуру T: логіти діляться на T, ранжування знімків не змінюється, а ймовірності
          стискаються до 0,5 (T &gt; 1) або розтягуються до 0 і 1 (T &lt; 1). Кнопка ставить T*, підібране на валідації.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': part === 'test' }" @click="part = 'test'">тест, 162 знімки</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': part === 'val' }" @click="part = 'val'">валідація (dev0), 128 знімків</button>
      <button v-for="b in [5, 10, 15, 20]" :key="b" type="button" class="lab__pill" :class="{ 'is-on': bins === b }"
              @click="bins = b">{{ b }} кошиків</button>
    </div>
    <div class="lab__controls ca__ctl">
      <label class="lab__ctl">
        <span>температура T: <b>{{ num(T, 2) }}</b></span>
        <input v-model.number="T" type="range" :min="TMIN" :max="TMAX" step="0.01" aria-label="Температура" />
      </label>
      <div class="ca__btns">
        <button type="button" class="lab__btn" @click="T = 1">T = 1</button>
        <button type="button" class="lab__btn" @click="T = TSTAR">T* = {{ num(TSTAR, 3) }}</button>
      </div>
    </div>

    <div class="ca__grid">
      <svg :viewBox="`0 0 ${S} ${S}`" role="img" aria-label="Діаграма надійності">
        <line :x1="X(0)" :y1="Y(0)" :x2="X(1)" :y2="Y(1)" class="ca__diag" />
        <g v-for="r in res.bars" :key="r.b">
          <rect :x="X(r.b / bins) + 1" :y="Y(r.yb)" :width="X(1 / bins) - X(0) - 2" :height="Y(0) - Y(r.yb)" class="ca__bar" />
          <circle :cx="X(r.pb)" :cy="Y(r.yb)" r="3" class="ca__pt" />
          <text :x="X((r.b + 0.5) / bins)" :y="Y(0) - 3" text-anchor="middle" class="ca__n">{{ r.c }}</text>
        </g>
        <line :x1="X(0)" :x2="X(1)" :y1="Y(0)" :y2="Y(0)" class="ca__axis" />
        <line :x1="X(0)" :x2="X(0)" :y1="Y(0)" :y2="Y(1)" class="ca__axis" />
        <text v-for="v in [0, 0.5, 1]" :key="'x' + v" :x="X(v)" :y="S - 14" text-anchor="middle" class="ca__lbl">{{ num(v, 1) }}</text>
        <text v-for="v in [0.5, 1]" :key="'y' + v" :x="P - 4" :y="Y(v) + 3" text-anchor="end" class="ca__lbl">{{ num(v, 1) }}</text>
        <text :x="X(0.5)" :y="S - 2" text-anchor="middle" class="ca__lbl">середня p у кошику</text>
      </svg>
      <div class="ca__legend">
        <p><span class="ca__sw ca__sw--bar" /> стовпчик — частка ТБ ȳ_b серед знімків кошика; число під ним — n_b.</p>
        <p><span class="ca__sw ca__sw--pt" /> точка — середня передбачена p̄_b у тому самому кошику.</p>
        <p>Для ідеально каліброваної моделі точки лежать на діагоналі. ECE — середня відстань від точок до
          діагоналі, зважена часткою знімків у кошику.</p>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat" :class="{ 'is-warm': res.ece > 0.08 }"><b>{{ num(res.ece) }}</b><span>ECE, {{ bins }} кошиків</span></div>
      <div class="lab__stat"><b>{{ num(res.nll) }}</b><span>NLL (середня крос-ентропія)</span></div>
      <div class="lab__stat"><b>{{ num(res.brier) }}</b><span>показник Браєра</span></div>
      <div class="lab__stat"><b>{{ num(res.mean) }}</b><span>середня p (частка ТБ {{ num(res.rate) }})</span></div>
    </div>

    <p class="lab__note">
      T* підібрано лише на валідації і без змін перенесено на тест. Перемкніть кількість кошиків: на 162 знімках
      ECE помітно залежить від цього вибору: з 10 кошиками виграш від температури помітний, з 20 — майже зникає.
    </p>
  </div>
</template>

<style scoped>
.ca__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
@media (max-width: 760px) { .ca__grid { grid-template-columns: 1fr; } }
.ca__ctl { align-items: end; }
.ca__btns { display: flex; gap: 0.4rem; flex-wrap: wrap; }
svg { width: 100%; max-width: 340px; height: auto; display: block; }
.ca__diag { stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 4 3; }
.ca__bar { fill: var(--uk-warm); opacity: 0.35; }
.ca__pt { fill: var(--uk-accent); stroke: var(--vp-c-bg); stroke-width: 1; }
.ca__n { fill: var(--vp-c-text-2); font-size: 8.5px; }
.ca__axis { stroke: var(--uk-line); }
.ca__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
.ca__legend { font-size: 0.8rem; color: var(--vp-c-text-2); line-height: 1.5; }
.ca__legend p { margin: 0.3rem 0; }
.ca__sw { display: inline-block; width: 11px; height: 11px; margin-right: 4px; vertical-align: -1px; border-radius: 2px; }
.ca__sw--bar { background: var(--uk-warm); opacity: 0.5; }
.ca__sw--pt { background: var(--uk-accent); border-radius: 50%; }
</style>
