<script setup lang="ts">
/**
 * Передача невизначених знімків лікарю (лекція 16, розділ «Відмова від рішення і передача лікарю»).
 * Дані — tools/gen_lec16_referral.py: логіт моделі S2, взаємна інформація MC dropout і SD п’яти
 * логістичних голів для валідації Shenzhen, тесту Shenzhen і Montgomery; поріг t — правило теми
 * про валідацію. Віджет передає лікарю ⌊r·N + 0,5⌋ найменш певних знімків (стабільне сортування за
 * сигналом, як у блоці коду) і рахує чутливість і специфічність моделі на решті.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec16_referral.json'

type Part = { label: number[]; pos: number[]; logit: number[]; mi: number[]; sd: number[] }
const D = data.data as Record<string, Part>
const T = data.t as number
const LT = Math.log(T / (1 - T))
const SIGNALS = data.signals as string[]
const PARTS = data.parts as Record<string, string>

const part = ref('test')
const sig = ref(SIGNALS[2])
const r = ref(20)

const sigmoid = (z: number) => 1 / (1 + Math.exp(-z))
function signal(p: Part, name: string): number[] {
  return p.logit.map((z, i) => {
    if (name === SIGNALS[0]) return -Math.abs(sigmoid(z) - 0.5)
    if (name === SIGNALS[1]) return -Math.abs(z - LT)
    if (name === SIGNALS[2]) return p.mi[i]
    return p.sd[i]
  })
}

function evalAt(p: Part, name: string, frac: number) {
  const s = signal(p, name)
  const order = s.map((v, i) => [v, i] as [number, number]).sort((a, b) => a[0] - b[0]).map(x => x[1])
  const n = order.length
  const nRef = Math.floor(frac * n + 0.5)  // те саме правило, що в блоці коду: половина — вгору
  const keep = order.slice(0, n - nRef)
  const ref_ = order.slice(n - nRef)
  let tp = 0, fn = 0, tn = 0, fp = 0, errRef = 0
  keep.forEach(i => {
    const pos = p.pos[i] === 1
    if (p.label[i] === 1) { if (pos) tp++; else fn++ } else { if (pos) fp++; else tn++ }
  })
  ref_.forEach(i => { if ((p.pos[i] === 1) !== (p.label[i] === 1)) errRef++ })
  return { sens: tp / Math.max(1, tp + fn), spec: tn / Math.max(1, tn + fp), n, nRef, errRef, fp, fn }
}

const cur = computed(() => evalAt(D[part.value], sig.value, r.value / 100))
const base = computed(() => evalAt(D[part.value], sig.value, 0))
const curve = computed(() => Array.from({ length: 51 }, (_, k) => ({ k, ...evalAt(D[part.value], sig.value, k / 100) })))

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const W = 360, H = 200, PL = 34, PR = 10, PT = 10, PB = 28
const X = (k: number) => PL + (k / 50) * (W - PL - PR)
const Y = (v: number) => PT + (1 - v) * (H - PT - PB)
const path = (key: 'sens' | 'spec') => curve.value.map((c, i) => `${i ? 'L' : 'M'}${X(c.k).toFixed(1)},${Y(c[key]).toFixed(1)}`).join(' ')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Передача невизначених знімків лікарю</div>
        <div class="lab__sub">
          Модель S2 вирішує при p ≥ t = {{ num(T, 4) }}. Найменш певні за вибраним сигналом знімки передаються лікарю,
          на решті рахуються чутливість і специфічність моделі.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(lbl, k) in PARTS" :key="k" type="button" class="lab__pill" :class="{ 'is-on': part === k }"
              @click="part = k">{{ lbl }} ({{ D[k].label.length }})</button>
    </div>
    <div class="lab__pills">
      <button v-for="s in SIGNALS" :key="s" type="button" class="lab__pill" :class="{ 'is-on': sig === s }"
              @click="sig = s">{{ s }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>передано лікарю: <b>{{ r }} %</b> ({{ cur.nRef }} з {{ cur.n }} знімків)</span>
        <input v-model.number="r" type="range" min="0" max="50" step="1" aria-label="Частка переданих лікарю">
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="rc__svg" role="img" aria-label="Чутливість і специфічність на залишених знімках">
      <line v-for="v in [0, 0.25, 0.5, 0.75, 1]" :key="'g' + v" :x1="PL" :x2="W - PR" :y1="Y(v)" :y2="Y(v)" class="rc__grid" />
      <text v-for="v in [0, 0.5, 1]" :key="'y' + v" :x="PL - 4" :y="Y(v) + 3" text-anchor="end" class="rc__lbl">{{ num(v, 1) }}</text>
      <text v-for="k in [0, 10, 20, 30, 40, 50]" :key="'x' + k" :x="X(k)" :y="H - 12" text-anchor="middle" class="rc__lbl">{{ k }} %</text>
      <path :d="path('sens')" class="rc__sens" />
      <path :d="path('spec')" class="rc__spec" />
      <line :x1="X(r)" :x2="X(r)" :y1="PT" :y2="H - PB" class="rc__mark" />
      <text :x="W - PR" :y="H - 1" text-anchor="end" class="rc__lbl">частка переданих лікарю</text>
    </svg>
    <div class="rc__legend">
      <span><i class="rc__sw rc__sw--sens" /> чутливість на залишених</span>
      <span><i class="rc__sw rc__sw--spec" /> специфічність на залишених</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(cur.sens) }}</b><span>чутливість (без передачі {{ num(base.sens) }})</span></div>
      <div class="lab__stat is-warm"><b>{{ num(cur.spec) }}</b><span>специфічність (без передачі {{ num(base.spec) }})</span></div>
      <div class="lab__stat"><b>{{ cur.errRef }} з {{ cur.nRef }}</b><span>переданих — помилки моделі</span></div>
      <div class="lab__stat"><b>{{ r * 10 }}</b><span>переглядів лікарем на 1000 знімків</span></div>
    </div>

    <p class="lab__note">
      Головний сигнал вибрано наперед на валідації — найменше помилок на залишених знімках при передачі 20 %.
      Перемкніть сигнал: на тесті Shenzhen інші сигнали при 20 % дають навіть більше, а відстань до порогу t
      знижує специфічність — правильні негативні знімки біля порогу передаються, а хибні тривоги лишаються.
    </p>
  </div>
</template>

<style scoped>
.rc__svg { width: 100%; max-width: 520px; height: auto; display: block; margin: 0.4rem 0; }
.rc__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.rc__lbl { fill: var(--vp-c-text-3); font-size: 9.5px; }
.rc__sens { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
.rc__spec { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.rc__mark { stroke: var(--vp-c-text-2); stroke-width: 1; stroke-dasharray: 3 3; }
.rc__legend { display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.8rem; color: var(--vp-c-text-2); }
.rc__sw { display: inline-block; width: 14px; height: 3px; vertical-align: middle; margin-right: 4px; }
.rc__sw--sens { background: var(--uk-accent); }
.rc__sw--spec { background: var(--uk-warm); }
</style>
