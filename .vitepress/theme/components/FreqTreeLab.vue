<script setup lang="ts">
/**
 * Дерево натуральних частот для 10 000 обстежених (лекція 01, розділ «Поширеність змінює
 * зміст позитивного результату»). Формули — ті самі, що в блоці коду 4 лекції: хворих =
 * round(N · поширеність), виявлених = round(чутливість · хворих), хибних тривог =
 * round((1 − специфічність) · здорових); round — як у Python (до парного на рівно .5).
 * Пресети поширеності й цілей WHO — з tools/gen_lec01_freq.py; за замовчуванням
 * 0,322 % і 90 / 70 дають вивід коду: 32 хворі, 29 / 3, 2 990 хибних тривог, 103 і 345.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec01_freq.json'

type Prev = { key: string; label: string; num: number; den: number; shown: string }
type Test = { key: string; label: string; sens: number; spec: number }

const N = data.N as number
const PREVS = data.prevalence as Prev[]
const TESTS = data.tests as Test[]
const P_MIN = 0.0001 // 0,01 %
const P_MAX = 0.6 // 60 %

const start = PREVS.find(p => p.key === data.default.prevalence) as Prev
const startTest = TESTS.find(t => t.key === data.default.test) as Test
const prev = ref<number>(start.num / start.den)
const sens = ref<number>(startTest.sens)
const spec = ref<number>(startTest.spec)

/** round() Python: рівно .5 заокруглюється до парного — так рахує блок коду 4. */
function pyRound(x: number): number {
  const f = Math.floor(x)
  const d = x - f
  if (d > 0.5) return f + 1
  if (d < 0.5) return f
  return f % 2 === 0 ? f : f + 1
}

// повзунок поширеності — логарифмічна шкала 0,01 %…60 %, позиція 0…1000
const prevPos = computed<number>({
  get: () => Math.round((1000 * Math.log(prev.value / P_MIN)) / Math.log(P_MAX / P_MIN)),
  set: (t: number) => {
    prev.value = P_MIN * Math.pow(P_MAX / P_MIN, t / 1000)
  },
})

const activePrev = computed(() => PREVS.find(p => Math.abs(prev.value - p.num / p.den) < 1e-12) ?? null)
const activeTest = computed(() => TESTS.find(t => t.sens === sens.value && t.spec === spec.value) ?? null)
const isCode = computed(() => activePrev.value?.key === start.key && activeTest.value?.key === startTest.key)

const res = computed(() => {
  const sick = pyRound(N * prev.value)
  const healthy = N - sick
  const tp = pyRound((sens.value / 100) * sick)
  const fp = pyRound((1 - spec.value / 100) * healthy)
  const pos = tp + fp
  return {
    sick, healthy, tp, fp, fn: sick - tp, tn: healthy - fp, pos,
    ppv: pos > 0 ? tp / pos : NaN,
    fpPerTp: tp > 0 ? fp / tp : NaN,
    nPerTp: tp > 0 ? N / tp : NaN,
    posShare: pos / N,
  }
})

const NB = ' '
const int = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, NB)
const dec = (v: number, d: number) => v.toFixed(d).replace('.', ',')
const pct = (v: number, d: number) => (Number.isFinite(v) ? dec(v * 100, d) + NB + '%' : '—')
const ratio = (v: number) => (!Number.isFinite(v) ? '—' : v >= 10 ? int(Math.round(v)) : dec(v, 1))
const prevDigits = (v: number) => (v < 0.01 ? 3 : v < 0.1 ? 2 : 1)
const prevText = computed(() => activePrev.value?.shown ?? pct(prev.value, prevDigits(prev.value)))
const restText = computed(() => {
  const shown = activePrev.value?.shown
  const d = shown ? (shown.split(',')[1] ?? '').replace(/\D/g, '').length : prevDigits(prev.value)
  return pct(1 - prev.value, d)
})
const ppvText = computed(() => pct(res.value.ppv, res.value.ppv < 0.1 ? 2 : 1))
const tpWidth = computed(() => {
  const r = res.value
  if (r.pos === 0) return 0
  return r.tp === 0 ? 0 : Math.max((100 * r.tp) / r.pos, 0.8)
})

function setTest(t: Test) {
  sens.value = t.sens
  spec.value = t.spec
}
function resetToCode() {
  prev.value = start.num / start.den
  setTest(startTest)
}

// вузли дерева: x-центри, ширина листка 78, висота 50
const LEAVES = [
  { x: 41, key: 'tp', top: 'виявлено', sub: 'позитивні', cls: 'is-sick is-pos' },
  { x: 127, key: 'fn', top: 'пропущено', sub: 'негативні', cls: 'is-sick' },
  { x: 213, key: 'fp', top: 'хибна тривога', sub: 'позитивні', cls: 'is-ok is-pos' },
  { x: 299, key: 'tn', top: 'правильно', sub: 'негативні', cls: 'is-ok' },
] as const
</script>

<template>
  <div class="lab ft">
    <div class="lab__head">
      <div>
        <div class="lab__title">Дерево натуральних частот: 10 000 обстежених</div>
        <div class="lab__sub">
          Замість відсотків — люди. Оберіть поширеність і якість тесту: дерево, частка хворих серед
          позитивних і кількість хибних тривог на одного виявленого перераховуються так само, як у коді
          вище, з заокругленням до цілих людей.
        </div>
      </div>
    </div>

    <div class="ft__group">
      <span class="ft__glabel">Поширеність</span>
      <div class="lab__pills">
        <button v-for="p in PREVS" :key="p.key" type="button" class="lab__pill"
                :class="{ 'is-on': activePrev?.key === p.key }" @click="prev = p.num / p.den">
          {{ p.label }}
        </button>
      </div>
    </div>
    <div class="ft__group">
      <span class="ft__glabel">Тест</span>
      <div class="lab__pills">
        <button v-for="t in TESTS" :key="t.key" type="button" class="lab__pill"
                :class="{ 'is-on': activeTest?.key === t.key }" @click="setTest(t)">
          {{ t.label }}: {{ t.sens }} / {{ t.spec }}
        </button>
        <button type="button" class="lab__pill" :class="{ 'is-on': isCode }" @click="resetToCode">
          як у коді вище
        </button>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Поширеність (логарифмічна шкала 0,01–60 %) = <b>{{ prevText }}</b></span>
        <input v-model.number="prevPos" type="range" min="0" max="1000" step="1" aria-label="Поширеність" />
      </label>
      <label class="lab__ctl">
        <span>Чутливість = <b>{{ sens }} %</b></span>
        <input v-model.number="sens" type="range" min="50" max="100" step="1" aria-label="Чутливість" />
      </label>
      <label class="lab__ctl">
        <span>Специфічність = <b>{{ spec }} %</b></span>
        <input v-model.number="spec" type="range" min="50" max="100" step="1" aria-label="Специфічність" />
      </label>
    </div>

    <svg class="ft__tree" viewBox="0 0 340 222" role="img"
         :aria-label="`Дерево: ${res.sick} хворих, ${res.tp} виявлено, ${res.fp} хибних тривог`">
      <g class="ft__edges">
        <line x1="170" y1="44" x2="84" y2="82" />
        <line x1="170" y1="44" x2="256" y2="82" />
        <line x1="84" y1="122" x2="41" y2="168" />
        <line x1="84" y1="122" x2="127" y2="168" />
        <line x1="256" y1="122" x2="213" y2="168" />
        <line x1="256" y1="122" x2="299" y2="168" />
      </g>
      <g class="ft__elab">
        <text x="122" y="64" text-anchor="end">{{ prevText }}</text>
        <text x="218" y="64">{{ restText }}</text>
        <text x="58" y="149" text-anchor="end">{{ sens }} %</text>
        <text x="110" y="149">{{ 100 - sens }} %</text>
        <text x="230" y="149" text-anchor="end">{{ 100 - spec }} %</text>
        <text x="282" y="149">{{ spec }} %</text>
      </g>

      <g class="ft__node is-root">
        <rect x="110" y="4" width="120" height="40" rx="8" />
        <text x="170" y="23" class="ft__num">{{ int(N) }}</text>
        <text x="170" y="37" class="ft__cap">обстежених</text>
      </g>
      <g class="ft__node is-sick">
        <rect x="26" y="82" width="116" height="40" rx="8" />
        <text x="84" y="101" class="ft__num">{{ int(res.sick) }}</text>
        <text x="84" y="115" class="ft__cap">хворі на ТБ</text>
      </g>
      <g class="ft__node is-ok">
        <rect x="198" y="82" width="116" height="40" rx="8" />
        <text x="256" y="101" class="ft__num">{{ int(res.healthy) }}</text>
        <text x="256" y="115" class="ft__cap">без ТБ</text>
      </g>
      <g v-for="l in LEAVES" :key="l.key" class="ft__node ft__leaf" :class="l.cls">
        <rect :x="l.x - 39" y="168" width="78" height="50" rx="8" />
        <text :x="l.x" y="186" class="ft__num">{{ int(res[l.key]) }}</text>
        <text :x="l.x" y="200" class="ft__cap">{{ l.top }}</text>
        <text :x="l.x" y="211" class="ft__cap ft__cap--sub">{{ l.sub }}</text>
      </g>
    </svg>
    <p class="ft__hint">
      На гілках — частки: поширеність і решта; чутливість і пропуски серед хворих; хибні тривоги
      і специфічність серед здорових.
    </p>

    <div class="ft__pos">
      <div class="ft__poshead">
        Позитивних результатів <b>{{ int(res.pos) }}</b>: хворих серед них <b>{{ int(res.tp) }}</b>,
        здорових <b>{{ int(res.fp) }}</b>
      </div>
      <div class="ft__bar" role="img" :aria-label="`Хворих серед позитивних ${ppvText}`">
        <i class="ft__bar-tp" :style="{ width: tpWidth + '%' }" />
        <i class="ft__bar-fp" :style="{ width: (res.pos ? 100 - tpWidth : 0) + '%' }" />
      </div>
      <div class="ft__legend">
        <span><i class="ft__sw ft__sw--tp" />хворі: виявлено</span>
        <span><i class="ft__sw ft__sw--fp" />здорові: хибна тривога</span>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ ppvText }}</b><span>хворих серед позитивних результатів</span></div>
      <div class="lab__stat"><b>{{ ratio(res.fpPerTp) }}</b><span>хибних тривог на одного виявленого хворого</span></div>
      <div class="lab__stat"><b>{{ ratio(res.nPerTp) }}</b><span>обстежених на одного виявленого хворого</span></div>
      <div class="lab__stat"><b>{{ pct(res.posShare, 1) }}</b><span>обстежених отримують позитивний результат</span></div>
    </div>

    <p class="lab__note">
      За замовчуванням — сценарій коду вище: оцінка поширеності, скоригована, 0,322 % і мінімальні
      цілі WHO 90 / 70. Перемкніть поширеність на навчальну вибірку курсу, не чіпаючи тесту: позитивний
      результат стає «швидше за все ТБ». Поверніть скринінг і поставте бажані цілі WHO: хибних тривог
      меншає, але хворі серед позитивних однаково в меншості.
    </p>
  </div>
</template>

<style scoped>
.ft__group { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.2rem 0.6rem; }
.ft__glabel { flex: 0 0 6.5rem; font-size: 0.78rem; color: var(--vp-c-text-3); }
.ft__group .lab__pills { flex: 1 1 16rem; margin-bottom: 0.6rem; }
.lab__pill { text-align: left; }
.ft__tree { display: block; width: 100%; max-width: 540px; height: auto; margin: 0.2rem auto 0; }
.ft__edges line { stroke: var(--vp-c-text-3); stroke-width: 1.2; opacity: 0.6; }
.ft__elab text {
  font-size: 10px;
  fill: var(--vp-c-text-2);
  paint-order: stroke;
  stroke: var(--vp-c-bg);
  stroke-width: 3px;
}
.ft__node rect { stroke-width: 1.4; }
.ft__node text { text-anchor: middle; }
.ft__num { font-size: 15px; font-weight: 600; fill: var(--vp-c-text-1); font-variant-numeric: tabular-nums; }
.ft__cap { font-size: 9.5px; fill: var(--vp-c-text-2); }
.ft__cap--sub { fill: var(--vp-c-text-3); font-size: 9px; }
.is-root rect { fill: var(--uk-fill); stroke: var(--uk-ink); }
.is-sick rect { fill: var(--vp-c-bg); stroke: var(--uk-warm); }
.is-ok rect { fill: var(--vp-c-bg); stroke: var(--uk-accent); }
.ft__node.is-sick:not(.ft__leaf) rect,
.ft__leaf.is-sick.is-pos rect { fill: var(--uk-warm-soft); }
.ft__node.is-ok:not(.ft__leaf) rect,
.ft__leaf.is-ok.is-pos rect { fill: var(--uk-accent-soft); }
.ft__leaf:not(.is-pos) rect { stroke-dasharray: 4 3; }
.ft__hint { font-size: 0.76rem; color: var(--vp-c-text-3); text-align: center; margin: 0.2rem 0 0.9rem; }
.ft__pos { margin: 0.4rem 0 0.2rem; }
.ft__poshead { font-size: 0.84rem; color: var(--vp-c-text-2); margin-bottom: 0.35rem; }
.ft__poshead b { color: var(--vp-c-text-1); font-variant-numeric: tabular-nums; }
.ft__bar {
  display: flex;
  height: 16px;
  border-radius: 5px;
  overflow: hidden;
  background: var(--uk-fill);
}
.ft__bar i { display: block; height: 100%; transition: width 0.3s ease; }
.ft__bar-tp { background: var(--uk-warm); }
.ft__bar-fp { background: var(--uk-accent); opacity: 0.45; }
.ft__legend {
  display: flex; flex-wrap: wrap; gap: 0.3rem 1rem;
  font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.35rem;
}
.ft__sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 0.3rem; vertical-align: -1px; }
.ft__sw--tp { background: var(--uk-warm); }
.ft__sw--fp { background: var(--uk-accent); opacity: 0.45; }
@media (max-width: 480px) {
  .lab.ft { padding: 1rem 0.8rem; }
  .ft__glabel { flex-basis: 100%; }
  .ft__num { font-size: 16px; }
  .ft__cap { font-size: 10px; }
  .ft__elab text { font-size: 11px; }
}
</style>
