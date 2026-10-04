<script setup lang="ts">
/**
 * Втрата NT-Xent на чотирьох видах двох знімків (лекція 13, розділ «Контрастивне навчання: SimCLR і втрата NT-Xent»).
 * Вектори z — нормовані виходи проєкційної голови SimCLR для видів A1, B1, A2, B2 (A — знімок норми, B — знімок
 * пневмонії з тесту PneumoniaMNIST) після навчання і для тих самих ваг до навчання; їх записує блок коду розділу
 * «Маленький SimCLR на CPU». Віджет рахує косинусну подібність s_ik = z_i·z_k, імовірності
 * exp(s_ik/τ) / Σ_{k≠i} exp(s_ik/τ) і втрату −log імовірності позитивної пари для будь-якої температури τ.
 * При τ = 0,5 матриця й середня втрата збігаються з виводом блоку (перевіряє tools/gen_lec13_ntxent.py).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec13_ntxent.json'

const Z = data.z as number[][][]
const V = data.views as string[]
const st = ref(0)
const logTau = ref(Math.log(0.5))
const tau = computed(() => Math.exp(logTau.value))
const anchor = ref(0)
const N = 4
const pos = (i: number) => (i + N / 2) % N

const S = computed(() => Z[st.value].map((a) => Z[st.value].map((b) => a.reduce((s, v, k) => s + v * b[k], 0))))
function rowProbs(i: number, t: number) {
  const ks = [...Array(N).keys()].filter((k) => k !== i)
  const m = Math.max(...ks.map((k) => S.value[i][k] / t))
  const e = ks.map((k) => Math.exp(S.value[i][k] / t - m))
  const sum = e.reduce((s, v) => s + v, 0)
  return ks.map((k, j) => ({ k, p: e[j] / sum }))
}
const probs = computed(() => rowProbs(anchor.value, tau.value))
const lossI = (i: number, t: number) => -Math.log(rowProbs(i, t).find((r) => r.k === pos(i))!.p)
const loss = computed(() => [...Array(N).keys()].reduce((s, i) => s + lossI(i, tau.value), 0) / N)
const loss05 = computed(() => [...Array(N).keys()].reduce((s, i) => s + lossI(i, 0.5), 0) / N)
const chance = Math.log(N - 1)
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const cell = (v: number) => `rgba(61, 78, 196, ${Math.max(0, Math.min(1, (v + 1) / 2)) * 0.85})`
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">NT-Xent: як температура змінює ціну негативів</div>
        <div class="lab__sub">
          Чотири види двох знімків: A1 і A2 — два випадкові види знімка норми, B1 і B2 — знімка пневмонії. Позитивна пара
          для A1 — A2, для B1 — B2. Оберіть рядок-якір у матриці і рухайте τ.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="(s, i) in data.states" :key="s" type="button" class="lab__pill" :class="{ 'is-on': st === i }" @click="st = i">{{ s }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>температура τ: <b>{{ num(tau, 2) }}</b></span>
        <input v-model.number="logTau" type="range" :min="Math.log(0.05)" :max="Math.log(2)" step="0.01" aria-label="Температура" />
      </label>
      <button type="button" class="lab__btn" @click="logTau = Math.log(0.5)">τ = 0,5 як у коді</button>
    </div>

    <div class="nx__grid">
      <div>
        <div class="nx__cap">косинусна подібність s<sub>ik</sub> = z<sub>i</sub>·z<sub>k</sub> (рядок — якір i)</div>
        <table class="nx__m">
          <tbody>
            <tr><th></th><th v-for="v in V" :key="v">{{ v }}</th></tr>
            <tr v-for="(row, i) in S" :key="i" :class="{ 'is-on': anchor === i }" @click="anchor = i">
              <th>{{ V[i] }}</th>
              <td v-for="(v, k) in row" :key="k" :class="{ 'is-pos': k === pos(i), 'is-diag': k === i }"
                  :style="{ background: k === i ? 'transparent' : cell(v), color: v > 0.3 && k !== i ? '#fff' : '' }">
                {{ k === i ? '—' : num(v) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div>
        <div class="nx__cap">якір {{ V[anchor] }}: імовірності кандидатів exp(s/τ) / Σ<sub>k≠i</sub> exp(s/τ)</div>
        <div v-for="r in probs" :key="r.k" class="nx__bar">
          <span class="nx__lab">{{ V[r.k] }}{{ r.k === pos(anchor) ? ' (позитив)' : '' }}</span>
          <span class="nx__track"><i :style="{ width: `${100 * r.p}%` }" :class="{ 'is-pos': r.k === pos(anchor) }" /></span>
          <span class="nx__val">{{ num(r.p) }}</span>
        </div>
        <div class="nx__cap">втрата якоря −log p<sub>позитив</sub> = {{ num(lossI(anchor, tau)) }}</div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(loss) }}</b><span>NT-Xent при τ = {{ num(tau, 2) }} (середнє за 4 якорями)</span></div>
      <div class="lab__stat"><b>{{ num(loss05) }}</b><span>NT-Xent при τ = 0,5 — як у виводі коду</span></div>
      <div class="lab__stat"><b>{{ num(chance) }}</b><span>ln 3: рівень вгадування, коли всі подібності однакові</span></div>
    </div>
    <p class="lab__note">
      Мала τ підсилює різницю подібностей: найближчий кандидат забирає майже всю ймовірність, і втрата карає саме його.
      Зі зростанням τ імовірності вирівнюються, і втрата прямує до ln 3, але повільно: при τ = 2 вона ще помітно нижча,
      бо подібність позитивних пар набагато більша за інші. До навчання всі чотири види майже однакові, тож втрата
      дорівнює рівню вгадування за будь-якої τ.
    </p>
  </div>
</template>

<style scoped>
.nx__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 760px) { .nx__grid { grid-template-columns: 1fr; } }
.nx__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.35rem; }
.nx__m { border-collapse: collapse; font-variant-numeric: tabular-nums; font-size: 0.8rem; width: 100%; }
.nx__m th { font-weight: 500; color: var(--vp-c-text-3); padding: 0.2rem 0.35rem !important; font-size: 0.74rem; }
.nx__m td { text-align: center; padding: 0.35rem 0.25rem !important; border: 1px solid var(--vp-c-bg) !important; font-family: var(--vp-font-family-mono); cursor: pointer; }
.nx__m td.is-pos { outline: 2px solid var(--uk-warm); outline-offset: -2px; }
.nx__m tr.is-on th { color: var(--uk-warm); }
.nx__m tr { cursor: pointer; }
.nx__bar { display: flex; align-items: center; gap: 0.4rem; margin: 0.25rem 0; font-size: 0.8rem; }
.nx__lab { flex: 0 0 6.5rem; }
.nx__track { flex: 1; height: 10px; background: var(--uk-fill); border-radius: 3px; overflow: hidden; }
.nx__track i { display: block; height: 100%; background: var(--uk-accent); opacity: 0.55; }
.nx__track i.is-pos { background: var(--uk-warm); opacity: 1; }
.nx__val { flex: 0 0 3rem; text-align: right; font-family: var(--vp-font-family-mono); }
</style>
