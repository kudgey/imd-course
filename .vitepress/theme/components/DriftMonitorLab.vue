<script setup lang="ts">
/**
 * Моніторинг після впровадження: CUSUM (лекція 17, розділ «Моніторинг після впровадження»).
 * Дані — tools/gen_lec17_drift.py: три статистики знімка без мітки (відстань до 5 найближчих знімків
 * еталону в просторі ознак моделі S2, скор моделі, рішення «ТБ»), стандартизовані за валідаційною
 * частиною Shenzhen, для 99 знімків тестової частини Shenzhen і 138 знімків Montgomery, і 200 порядків
 * потоку (спершу Shenzhen, потім Montgomery) — ті самі, що в коді. Віджет рахує двобічну CUSUM:
 * S⁺ = max(0, S⁺ + x − k), S⁻ = max(0, S⁻ − x − k), тривога при S > H, після тривоги суми обнуляються.
 * За k = 0,5 і H = 5 підсумки збігаються з виводом коду.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec17_drift.json'

const NAMES = data.names as string[]
const TEST = data.test as number[][]
const EXT = data.ext as number[][]
const NT = data.n_test as number
const raw = atob(data.perms as string)
const PERMS: Uint8Array = new Uint8Array(raw.length)
for (let i = 0; i < raw.length; i++) PERMS[i] = raw.charCodeAt(i)
const NS = TEST[0].length + EXT[0].length
const NP = PERMS.length / NS

const stat = ref(0)
const k = ref(0.5)
const H = ref(5)
const seed = ref(0)

function stream(j: number, s: number) {
  const x: number[] = []
  for (let i = 0; i < NS; i++) {
    const idx = PERMS[s * NS + i]
    x.push(i < NT ? TEST[j][idx] : EXT[j][idx])
  }
  return x
}
function cusum(x: number[], kk: number, hh: number) {
  let up = 0, lo = 0
  const alarms: number[] = [], P: number[][] = []
  x.forEach((v, i) => {
    up = Math.max(0, up + v - kk); lo = Math.max(0, lo - v - kk)
    P.push([up, lo])
    if (up > hh || lo > hh) { alarms.push(i + 1); up = 0; lo = 0 }
  })
  return { alarms, P }
}
function q(a: number[], p: number) { // лінійна інтерполяція, як pandas.Series.quantile
  const s = [...a].sort((x, y) => x - y)
  const i = (s.length - 1) * p
  const lo = Math.floor(i), hi = Math.ceil(i)
  return s[lo] + (s[hi] - s[lo]) * (i - lo)
}
const one = computed(() => cusum(stream(stat.value, seed.value), k.value, H.value))
const summary = computed(() => {
  const fa: number[] = [], delay: number[] = []
  for (let s = 0; s < NP; s++) {
    const a = cusum(stream(stat.value, s), k.value, H.value).alarms
    fa.push(a.filter((i) => i <= NT).length)
    const late = a.filter((i) => i > NT)
    if (late.length) delay.push(late[0] - NT)
  }
  return {
    fa: fa.reduce((u, v) => u + v, 0) / NP, faShare: fa.filter((v) => v > 0).length / NP,
    det: delay.length / NP, q: delay.length ? [q(delay, 0.5), q(delay, 0.25), q(delay, 0.75)] : null,
  }
})

const r0 = (v: number) => { const r = Math.round(v); return Math.abs(v % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r } // як Python: до парного
const num = (v: number, d = 2) => v.toFixed(d).replace('.', ',')
const pct = (v: number) => `${r0(100 * v)} %`
const W = 600, HH = 220, L = 34, R = 10, T0 = 10, B = 28
const X = (i: number) => L + (i / NS) * (W - L - R)
const yMax = computed(() => Math.max(H.value * 1.15, 2))
const Y = (v: number) => T0 + (1 - Math.min(v, yMax.value) / yMax.value) * (HH - T0 - B)
const paths = computed(() => [0, 1].map((c) => one.value.P.map((p, i) => `${i ? 'L' : 'M'}${X(i + 1).toFixed(1)},${Y(p[c]).toFixed(1)}`).join(' ')))
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">CUSUM на потоці: Shenzhen, потім Montgomery</div>
        <div class="lab__sub">
          Спершу надходять {{ NT }} знімків тестової частини Shenzhen, потім {{ NS - NT }} знімків Montgomery. Оберіть
          статистику, допуск k і межу H; графік показує один порядок потоку, числа під ним — підсумок за {{ NP }} порядками.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="(n, j) in NAMES" :key="n" type="button" class="lab__pill" :class="{ 'is-on': stat === j }" @click="stat = j">{{ n }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>допуск k: <b>{{ num(k) }}</b></span>
        <input v-model.number="k" type="range" min="0.1" max="1.5" step="0.05" aria-label="Допуск k" />
      </label>
      <label class="lab__ctl">
        <span>межа тривоги H: <b>{{ num(H, 1) }}</b></span>
        <input v-model.number="H" type="range" min="1" max="15" step="0.5" aria-label="Межа тривоги H" />
      </label>
      <label class="lab__ctl">
        <span>порядок потоку: <b>{{ seed + 1 }}</b> з {{ NP }}</span>
        <input v-model.number="seed" type="range" min="0" :max="NP - 1" step="1" aria-label="Порядок потоку" />
      </label>
    </div>
    <svg :viewBox="`0 0 ${W} ${HH}`" role="img" aria-label="Суми CUSUM на потоці знімків">
      <rect :x="X(NT)" :y="T0" :width="X(NS) - X(NT)" :height="HH - T0 - B" class="dm__ext" />
      <line :x1="L" :x2="W - R" :y1="Y(H)" :y2="Y(H)" class="dm__h" />
      <text :x="W - R - 2" :y="Y(H) - 4" text-anchor="end" class="dm__lbl">H = {{ num(H, 1) }}</text>
      <path :d="paths[0]" fill="none" stroke="var(--uk-warm)" stroke-width="1.8" />
      <path :d="paths[1]" fill="none" stroke="var(--uk-accent)" stroke-width="1.8" />
      <g v-for="a in one.alarms" :key="a">
        <line :x1="X(a)" :x2="X(a)" :y1="T0" :y2="HH - B" :class="a <= NT ? 'dm__fa' : 'dm__al'" />
      </g>
      <text :x="X(NT / 2)" :y="T0 + 12" text-anchor="middle" class="dm__lbl">Shenzhen test</text>
      <text :x="X(NT + (NS - NT) / 2)" :y="T0 + 12" text-anchor="middle" class="dm__lbl">Montgomery</text>
      <text v-for="i in [0, 50, 100, 150, 200]" :key="i" :x="X(i)" :y="HH - B + 14" text-anchor="middle" class="dm__lbl">{{ i }}</text>
      <text :x="(L + W - R) / 2" :y="HH - 2" text-anchor="middle" class="dm__lbl">номер знімка в потоці</text>
    </svg>
    <div class="dm__legend">
      <span><i style="background: var(--uk-warm)" />S⁺ — сума відхилень угору</span>
      <span><i style="background: var(--uk-accent)" />S⁻ — сума відхилень униз</span>
      <span><i class="dm__swfa" />хибна тривога (до зміни)</span>
      <span><i class="dm__swal" />тривога після зміни</span>
    </div>
    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(summary.fa) }}</b><span>хибних тривог на потік (у {{ pct(summary.faShare) }} потоків)</span></div>
      <div class="lab__stat"><b>{{ pct(summary.det) }}</b><span>потоків із тривогою після зміни</span></div>
      <div class="lab__stat is-green"><b>{{ summary.q ? r0(summary.q[0]) : '—' }}</b><span>медіанна затримка, знімків{{ summary.q ? ` [${r0(summary.q[1])}; ${r0(summary.q[2])}]` : '' }}</span></div>
    </div>
    <p class="lab__note">
      Статистики стандартизовано за еталонним періодом (валідаційна частина Shenzhen), тому k і H — у стандартних
      відхиленнях. За k = 0,5 і H = 5 підсумки збігаються з виводом коду в розділі; межу H у лікарні підбирають на
      еталонному періоді за прийнятною частотою хибних тривог.
    </p>
  </div>
</template>

<style scoped>
svg { width: 100%; height: auto; display: block; }
.dm__ext { fill: var(--uk-warm); opacity: 0.06; }
.dm__h { stroke: var(--vp-c-text-2); stroke-dasharray: 4 3; }
.dm__fa { stroke: #e34948; stroke-width: 1.2; opacity: 0.8; }
.dm__al { stroke: #1baf7a; stroke-width: 1.2; opacity: 0.8; }
.dm__lbl { fill: var(--vp-c-text-2); font-size: 10.5px; }
.dm__legend { display: flex; flex-wrap: wrap; gap: 0.9rem; font-size: 0.8rem; color: var(--vp-c-text-2); margin: 0.4rem 0; }
.dm__legend i { display: inline-block; width: 14px; height: 4px; border-radius: 2px; margin-right: 0.35rem; vertical-align: middle; }
.dm__legend .dm__swfa { background: #e34948; width: 3px; height: 12px; }
.dm__legend .dm__swal { background: #1baf7a; width: 3px; height: 12px; }
</style>
