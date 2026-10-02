<script setup lang="ts">
/**
 * Криві навчання і рання зупинка (лекція 08, розділ «Криві навчання і момент зупинки»).
 * Числа — з кривих, які записали блоки коду лекції: повне донавчання ResNet-18 і «layer4 + fc» (6 епох,
 * 128 px) та мала мережа з нуля (30 епох, 256 px), розбиття S1 (навчання dev1…dev4, валідація dev0).
 * Рання зупинка за val AUC: найкраща епоха — найбільша val AUC (за рівності — раніша); з «терпінням» p
 * навчання зупиняється після p епох поспіль без нової найкращої val AUC. Тестова AUC кожної епохи
 * записана лише для цього пояснення: жодне рішення її не бачить. Дані: tools/gen_lec08_curves.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec08_curves.json'

type Ep = { ep: number; train: number; val: number; auc: number; test: number; sec: number }
type S = { key: string; label: string; epochs: Ep[] }
const strategies = data.strategies as S[]

const sk = ref(0)
const patience = ref(0) // 0 — без ранньої зупинки
const s = computed(() => strategies[sk.value])
const n = computed(() => s.value.epochs.length)

const run = computed(() => {
  const eps = s.value.epochs
  let best = 0
  let stop = eps.length - 1
  for (let i = 0; i < eps.length; i++) {
    if (eps[i].auc > eps[best].auc) best = i
    if (patience.value > 0 && i - best >= patience.value) { stop = i; break }
  }
  const spent = eps.slice(0, stop + 1).reduce((a, e) => a + e.sec, 0)
  const total = eps.reduce((a, e) => a + e.sec, 0)
  return { best, stop, spent, total }
})

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const W = 340
const H = 150
const PL = 34
const PB = 22
const x = (i: number) => PL + (n.value > 1 ? (i / (n.value - 1)) * (W - PL - 10) : 0)
const lossMax = computed(() => Math.max(...s.value.epochs.flatMap((e) => [e.train, e.val])) * 1.05)
const yL = (v: number) => 8 + (1 - v / lossMax.value) * (H - PB - 8)
const yA = (v: number) => 8 + (1 - (v - 0.6) / 0.4) * (H - PB - 8)
const path = (f: (e: Ep) => number, y: (v: number) => number) =>
  s.value.epochs.map((e, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(f(e)).toFixed(1)}`).join(' ')
const ticks = computed(() => s.value.epochs.filter((e) => n.value <= 8 || e.ep % 5 === 0 || e.ep === 1))
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Криві навчання і рання зупинка</div>
        <div class="lab__sub">
          Оберіть стратегію і «терпіння» ранньої зупинки: скільки епох поспіль без нової найкращої val AUC
          чекати, перш ніж зупинитися. Обрана епоха — найкраща за валідацією до моменту зупинки.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(st, k) in strategies" :key="st.key" type="button" class="lab__pill" :class="{ 'is-on': sk === k }"
              @click="sk = k">{{ st.label }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>терпіння: <b>{{ patience === 0 ? 'без зупинки' : patience + ' еп.' }}</b></span>
        <input v-model.number="patience" type="range" min="0" max="3" step="1" aria-label="Терпіння ранньої зупинки" />
      </label>
    </div>

    <div class="lc__grid">
      <div>
        <div class="lc__cap">Втрати (BCE): <span class="lc__k lc__k--tr">навчання</span> <span class="lc__k lc__k--va">валідація</span></div>
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Втрати навчання і валідації за епохами">
          <rect v-if="run.stop < n - 1" :x="x(run.stop)" y="8" :width="W - 10 - x(run.stop)" :height="H - PB - 8" class="lc__cut" />
          <path :d="path((e) => e.train, yL)" class="lc__tr" />
          <path :d="path((e) => e.val, yL)" class="lc__va" />
          <line :x1="x(run.best)" :x2="x(run.best)" y1="8" :y2="H - PB" class="lc__best" />
          <line :x1="PL" :x2="W - 10" :y1="H - PB" :y2="H - PB" class="lc__axis" />
          <text v-for="e in ticks" :key="e.ep" :x="x(e.ep - 1)" :y="H - 6" text-anchor="middle" class="lc__lbl">{{ e.ep }}</text>
          <text :x="PL - 4" :y="yL(0) + 3" text-anchor="end" class="lc__lbl">0</text>
          <text :x="PL - 4" :y="yL(lossMax / 1.05) + 3" text-anchor="end" class="lc__lbl">{{ num(lossMax / 1.05, 2) }}</text>
        </svg>
      </div>
      <div>
        <div class="lc__cap">AUC: <span class="lc__k lc__k--va">валідація</span> <span class="lc__k lc__k--te">тест (лише для пояснення)</span></div>
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Валідаційна і тестова AUC за епохами">
          <rect v-if="run.stop < n - 1" :x="x(run.stop)" y="8" :width="W - 10 - x(run.stop)" :height="H - PB - 8" class="lc__cut" />
          <path :d="path((e) => e.auc, yA)" class="lc__va" />
          <path :d="path((e) => e.test, yA)" class="lc__te" />
          <circle :cx="x(run.best)" :cy="yA(s.epochs[run.best].auc)" r="3.5" class="lc__dot" />
          <line :x1="PL" :x2="W - 10" :y1="H - PB" :y2="H - PB" class="lc__axis" />
          <text v-for="e in ticks" :key="e.ep" :x="x(e.ep - 1)" :y="H - 6" text-anchor="middle" class="lc__lbl">{{ e.ep }}</text>
          <text v-for="v in [0.6, 0.8, 1]" :key="v" :x="PL - 4" :y="yA(v) + 3" text-anchor="end" class="lc__lbl">{{ num(v, 1) }}</text>
        </svg>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ run.stop + 1 }} / {{ n }}</b><span>епоха зупинки / усього епох</span></div>
      <div class="lab__stat"><b>{{ s.epochs[run.best].ep }}</b><span>обрана епоха (найкраща val AUC)</span></div>
      <div class="lab__stat"><b>{{ num(s.epochs[run.best].auc) }}</b><span>val AUC обраної епохи</span></div>
      <div class="lab__stat is-warm"><b>{{ num(s.epochs[run.best].test) }}</b><span>тестова AUC обраної епохи</span></div>
      <div class="lab__stat"><b>{{ Math.round(run.spent) }} с</b><span>витрачено з {{ Math.round(run.total) }} с</span></div>
    </div>

    <p class="lab__note">
      Сіра смуга — епохи, яких рання зупинка вже не навчала б. Порівняйте криві тестової і валідаційної AUC:
      вони рухаються разом лише приблизно, тому обрана за валідацією епоха рідко збігається з найкращою на тесті.
      Вибирати епоху за тестом — значить підганяти модель під дані, на яких її потім оцінюють.
    </p>
  </div>
</template>

<style scoped>
.lc__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; }
@media (max-width: 760px) { .lc__grid { grid-template-columns: 1fr; } }
svg { width: 100%; height: auto; display: block; }
.lc__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin-bottom: 0.25rem; }
.lc__k { white-space: nowrap; margin-right: 0.5rem; }
.lc__k::before { content: ''; display: inline-block; width: 14px; height: 0; border-top: 2px solid; margin-right: 4px; vertical-align: middle; }
.lc__k--tr::before { border-color: var(--uk-accent); }
.lc__k--va::before { border-color: #1baf7a; }
.lc__k--te::before { border-color: #eda100; border-top-style: dashed; }
.lc__tr { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
.lc__va { fill: none; stroke: #1baf7a; stroke-width: 2; }
.lc__te { fill: none; stroke: #eda100; stroke-width: 2; stroke-dasharray: 5 3; }
.lc__best { stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 3 3; }
.lc__dot { fill: #1baf7a; stroke: var(--vp-c-bg); stroke-width: 1.5; }
.lc__cut { fill: var(--uk-fill); }
.lc__axis { stroke: var(--uk-line); }
.lc__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
</style>
