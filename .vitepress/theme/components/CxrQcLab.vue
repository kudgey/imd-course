<script setup lang="ts">
/**
 * Контроль якості 800 рентгенограм Montgomery і Shenzhen (лекція 04, розділ «Контроль якості
 * знімків до навчання»). Лише числа — три метрики копій 256 px: середня яскравість, SD (контраст),
 * частка пікселів ≤ 5; знімків NLM у віджеті немає. z-оцінка рахується в межах набору (SD з n − 1,
 * як у pandas); при порозі 3 і всіх трьох метриках прапорців 19, з них 16 з міткою «норма» — як у
 * виводі коду. Дані пише tools/gen_lec04_qc.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec04_qc.json'

const SETS = data.sets as string[]
const METRICS = data.metrics as string[]
const FILES = data.file as string[]
const SET = data.set as number[]
const LABEL = data.label as number[]
const V = data.v as number[][]
const n = FILES.length

const zMax = ref(data.z_default as number)
const use = ref([true, true, true])
const shown = ref(2)

const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')

/** Середнє і SD (n − 1) кожної метрики в кожному наборі */
const STATS = SETS.map((_, si) => {
  const rows = V.filter((_, i) => SET[i] === si)
  return METRICS.map((__, mi) => {
    const x = rows.map(r => r[mi])
    const mean = x.reduce((a, b) => a + b, 0) / x.length
    const sd = Math.sqrt(x.reduce((a, b) => a + (b - mean) ** 2, 0) / (x.length - 1))
    return { mean, sd }
  })
})
const Z = V.map((r, i) => r.map((v, mi) => (v - STATS[SET[i]][mi].mean) / STATS[SET[i]][mi].sd))

const flagged = computed(() => {
  const out: { i: number; why: string[]; z: number }[] = []
  for (let i = 0; i < n; i++) {
    const why = METRICS.filter((_, mi) => use.value[mi] && Math.abs(Z[i][mi]) > zMax.value)
    if (why.length) out.push({ i, why, z: Math.max(...METRICS.map((_, mi) => (use.value[mi] ? Math.abs(Z[i][mi]) : 0))) })
  }
  return out.sort((a, b) => b.z - a.z)
})
const normals = computed(() => flagged.value.filter(f => LABEL[f.i] === 0).length)
const bySet = computed(() => SETS.map((_, si) => flagged.value.filter(f => SET[f.i] === si).length))
function toggle(mi: number) {
  const u = [...use.value]
  u[mi] = !u[mi]
  use.value = u
}

/* Гістограми вибраної метрики в кожному наборі; межі — середнє ± z · SD */
const W = 340
const H = 84
const BINS = 30
const hist = computed(() => {
  const mi = shown.value
  const all = V.map(r => r[mi])
  const lo = Math.min(...all)
  const hi = Math.max(...all)
  const w = (hi - lo) / BINS || 1
  return SETS.map((_, si) => {
    const counts = new Array(BINS).fill(0)
    const flag = new Array(BINS).fill(0)
    const fs = new Set(flagged.value.map(f => f.i))
    V.forEach((r, i) => {
      if (SET[i] !== si) return
      const b = Math.min(Math.floor((r[mi] - lo) / w), BINS - 1)
      counts[b] += 1
      if (fs.has(i)) flag[b] += 1
    })
    const mx = Math.max(...counts, 1)
    const st = STATS[si][mi]
    const X = (v: number) => 8 + ((v - lo) / (hi - lo || 1)) * (W - 16)
    return { counts, flag, mx, X, lo: X(st.mean - zMax.value * st.sd), hi: X(st.mean + zMax.value * st.sd) }
  })
})
const fmtMetric = (mi: number, v: number) => (mi === 2 ? num(100 * v, 1) + ' %' : num(v, 1))
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Контроль якості 800 знімків: поріг z і прапорці</div>
        <div class="lab__sub">
          Метрики копій 256 px; знімок отримує прапорець, якщо за модулем z-оцінка (у межах свого набору)
          більша за поріг хоча б за однією з вибраних метрик. Самих знімків тут немає — лише числа.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поріг |z| &gt; <b>{{ num(zMax, 1) }}</b></span>
        <input v-model.number="zMax" type="range" min="2" max="5" step="0.1" aria-label="Поріг z" />
      </label>
    </div>
    <div class="lab__pills">
      <span class="qc__lbl">метрики для прапорців:</span>
      <button v-for="(m, mi) in METRICS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': use[mi] }"
              @click="toggle(mi)">{{ m }}</button>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ flagged.length }}</b><span>знімків із прапорцем з {{ n }}</span></div>
      <div class="lab__stat"><b>{{ bySet[0] }} / {{ bySet[1] }}</b><span>Montgomery / Shenzhen</span></div>
      <div class="lab__stat"><b>{{ normals }}</b><span>із них з міткою «норма»</span></div>
    </div>

    <div class="qc__grid">
      <div>
        <div class="lab__pills">
          <span class="qc__lbl">гістограма:</span>
          <button v-for="(m, mi) in METRICS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': shown === mi }"
                  @click="shown = mi">{{ m }}</button>
        </div>
        <div v-for="(h, si) in hist" :key="si">
          <div class="qc__cap">{{ SETS[si] }}: середнє {{ fmtMetric(shown, STATS[si][shown].mean) }}, SD
            {{ fmtMetric(shown, STATS[si][shown].sd) }}; пунктир — межі ± {{ num(zMax, 1) }} SD</div>
          <svg :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="`Гістограма метрики, ${SETS[si]}`">
            <g v-for="(c, b) in h.counts" :key="b">
              <rect :x="8 + (b * (W - 16)) / BINS" :y="H - 6 - (c / h.mx) * (H - 14)" :width="(W - 16) / BINS - 1"
                    :height="(c / h.mx) * (H - 14)" class="qc__bar" />
              <rect v-if="h.flag[b]" :x="8 + (b * (W - 16)) / BINS" :y="H - 6 - (h.flag[b] / h.mx) * (H - 14)"
                    :width="(W - 16) / BINS - 1" :height="(h.flag[b] / h.mx) * (H - 14)" class="qc__bar is-flag" />
            </g>
            <line :x1="h.lo" :x2="h.lo" y1="4" :y2="H - 6" class="qc__lim" />
            <line :x1="h.hi" :x2="h.hi" y1="4" :y2="H - 6" class="qc__lim" />
            <line x1="8" :x2="W - 8" :y1="H - 6" :y2="H - 6" class="qc__axis" />
          </svg>
        </div>
      </div>
      <div>
        <div class="qc__cap">Знімки з прапорцем, від найбільшого |z|</div>
        <div class="qc__list">
          <table>
            <tbody>
              <tr><th>файл</th><th>мітка</th><th>причина</th><th>|z|</th></tr>
              <tr v-for="f in flagged.slice(0, 60)" :key="f.i">
                <td>{{ FILES[f.i] }}</td><td>{{ LABEL[f.i] ? 'ТБ' : 'норма' }}</td>
                <td class="qc__why">{{ f.why.join(', ') }}</td><td>{{ num(f.z, 1) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="flagged.length > 60" class="qc__cap">… і ще {{ flagged.length - 60 }}</div>
        </div>
      </div>
    </div>

    <p class="lab__note">
      При порозі 3 прапорців 19: один у Montgomery і 18 у Shenzhen, переважно через широке чорне поле; 16 з них
      мають мітку «норма». Опустіть поріг до 2,5 — прапорців стає 41, і серед них з’являються знімки з низьким
      контрастом. Вимкніть «частку чорного» при порозі 3: у Shenzhen лишається 3 прапорці з 18, бо саме чорні
      поля відрізняють ці знімки від решти. Прапорець — запрошення переглянути файл, а не автоматичне видалення.
    </p>
  </div>
</template>

<style scoped>
.qc__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 1.1rem;
  margin-top: 1rem;
  align-items: start;
}
@media (max-width: 760px) { .qc__grid { grid-template-columns: 1fr; } }
.qc__lbl { font-size: 0.78rem; color: var(--vp-c-text-3); align-self: center; margin-right: 0.2rem; }
.qc__cap { font-size: 0.75rem; color: var(--vp-c-text-3); margin: 0.3rem 0 0.2rem; line-height: 1.4; }
.qc__bar { fill: var(--uk-accent); opacity: 0.45; }
.qc__bar.is-flag { fill: var(--uk-warm); opacity: 1; }
.qc__lim { stroke: var(--uk-warm); stroke-width: 1; stroke-dasharray: 3 3; }
.qc__axis { stroke: var(--uk-line); stroke-width: 1; }
.qc__list { max-height: 330px; overflow-y: auto; }
.qc__list table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.qc__list th { font-weight: 500; font-size: 0.7rem; color: var(--vp-c-text-3); text-align: left; padding: 0.15rem 0.3rem !important; }
.qc__list td {
  font-family: var(--vp-font-family-mono);
  font-size: 0.72rem;
  padding: 0.18rem 0.3rem !important;
  border-top: 1px solid var(--uk-line) !important;
}
.qc__why { font-family: var(--vp-font-family-base) !important; }
svg { width: 100%; height: auto; display: block; }
</style>
