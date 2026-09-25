<script setup lang="ts">
/**
 * Порядок зрізів трьох серій TCIA: як в архіві, за проєкцією ImagePositionPatient на нормаль
 * (d = n · p) і за InstanceNumber. Числа ті самі, що друкує блок коду розділу «Порядок файлів в архіві —
 * не порядок зрізів»: перший файл LIDC-IDRI-0001 — InstanceNumber 80, z = −207,5 мм; кроки 2,5 / 5,0 /
 * 4,0 мм; у косій Prostate-3T «крок по z» 3,62 мм проти 4,00 мм уздовж нормалі.
 * Дані пише tools/gen_lec03_order.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec03_order.json'

type File = { file: number; inst: number; z: number; d: number }
type Series = {
  name: string; label: string; n: number; thickness: number; normal: number[]; tilt: number
  step_normal: number; step_z: number; files: File[]
}
type Mode = 'archive' | 'position' | 'instance'

const series = data.series as Series[]
const si = ref(0)
const mode = ref<Mode>('archive')
const MODES: { id: Mode; label: string }[] = [
  { id: 'archive', label: 'порядок в архіві' },
  { id: 'position', label: 'за проєкцією IPP на нормаль' },
  { id: 'instance', label: 'за InstanceNumber' },
]

const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const cur = computed(() => series[si.value])
const order = computed<File[]>(() => {
  const f = [...cur.value.files]
  if (mode.value === 'position') f.sort((a, b) => a.d - b.d)
  if (mode.value === 'instance') f.sort((a, b) => a.inst - b.inst)
  return f
})
const steps = computed(() => order.value.slice(1).map((f, k) => f.d - order.value[k].d))

/** Кроки між сусідніми зрізами поточного порядку, згруповані за величиною (0,01 мм) */
const stepTable = computed(() => {
  const m = new Map<string, number>()
  for (const s of steps.value) {
    const key = s.toFixed(2)
    m.set(key, (m.get(key) ?? 0) + 1)
  }
  return [...m.entries()].map(([v, n]) => ({ v: Number(v), n })).sort((a, b) => b.n - a.n)
})
const uniform = computed(() => stepTable.value.length === 1)
const trendOf = (x: number[]) => {
  const d = x.slice(1).map((v, k) => v - x[k])
  if (d.every(v => v > 0)) return 'зростає'
  if (d.every(v => v < 0)) return 'спадає'
  return 'немонотонна'
}
const dTrend = computed(() => trendOf(order.value.map(f => f.d)))
const instTrend = computed(() => trendOf(order.value.map(f => f.inst)))
const oblique = computed(() => cur.value.tilt > 0.5)

/* Графік: позиція вздовж нормалі d проти номера в поточному порядку */
const W = 360
const H = 190
const PL = 44
const PR = 10
const PT = 10
const PB = 30
const yr = computed(() => {
  const ds = cur.value.files.map(f => f.d)
  const lo = Math.min(...ds)
  const hi = Math.max(...ds)
  const pad = (hi - lo) * 0.06 || 1
  return [lo - pad, hi + pad]
})
const X = (k: number) => PL + (k / Math.max(order.value.length - 1, 1)) * (W - PL - PR)
const Y = (d: number) => PT + (1 - (d - yr.value[0]) / (yr.value[1] - yr.value[0])) * (H - PT - PB)
const path = computed(() => order.value.map((f, k) => `${X(k).toFixed(1)},${Y(f.d).toFixed(1)}`).join(' '))
const yTicks = computed(() => {
  const [lo, hi] = yr.value
  const span = hi - lo
  const step = span > 200 ? 100 : span > 80 ? 50 : span > 40 ? 20 : 10
  const out: number[] = []
  for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) out.push(v)
  return out
})
const xTicks = computed(() => {
  const n = order.value.length
  const step = n > 100 ? 25 : n > 40 ? 10 : 5
  const out = [1]
  for (let v = step; v <= n; v += step) out.push(v)
  return out
})
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Порядок зрізів: архів, проєкція на нормаль, InstanceNumber</div>
        <div class="lab__sub">
          Позиція кожного зрізу вздовж нормалі d = n · p з заголовків усіх файлів серії, ті самі, що рахує код.
          Оберіть серію і спосіб упорядкування.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(s, n) in series" :key="s.name" type="button" class="lab__pill" :class="{ 'is-on': si === n }"
              @click="si = n">{{ s.name }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="m in MODES" :key="m.id" type="button" class="lab__pill" :class="{ 'is-on': mode === m.id }"
              @click="mode = m.id">{{ m.label }}</button>
    </div>

    <div class="so__grid">
      <div>
        <div class="so__cap">{{ cur.label }}; {{ cur.n }} файлів. Точки — зрізи в поточному порядку, лінія з’єднує сусідні.</div>
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Позиція зрізу вздовж нормалі проти номера в поточному порядку">
          <g v-for="t in yTicks" :key="'y' + t">
            <line :x1="PL" :x2="W - PR" :y1="Y(t)" :y2="Y(t)" class="so__grid-line" />
            <text :x="PL - 4" :y="Y(t) + 3" text-anchor="end" class="so__lbl">{{ num(t, 0) }}</text>
          </g>
          <g v-for="t in xTicks" :key="'x' + t">
            <text :x="X(t - 1)" :y="H - PB + 13" text-anchor="middle" class="so__lbl">{{ t }}</text>
          </g>
          <polyline :points="path" class="so__path" :class="{ 'is-sorted': uniform }" />
          <circle v-for="(f, k) in order" :key="f.file" :cx="X(k)" :cy="Y(f.d)" :r="order.length > 60 ? 1.8 : 2.8" class="so__pt" />
          <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="so__lbl">номер зрізу в поточному порядку</text>
          <text :x="10" :y="(PT + H - PB) / 2" text-anchor="middle" class="so__lbl"
                :transform="`rotate(-90 10 ${(PT + H - PB) / 2})`">d, мм</text>
        </svg>
      </div>
      <div>
        <table class="so__table">
          <tbody>
            <tr><th>№</th><th>файл</th><th>InstanceNumber</th><th>z, мм</th><th>d, мм</th></tr>
            <tr v-for="(f, k) in order.slice(0, 5)" :key="f.file">
              <td>{{ k + 1 }}</td><td>{{ String(f.file).padStart(2, '0') }}</td><td>{{ f.inst }}</td>
              <td>{{ num(f.z) }}</td><td>{{ num(f.d) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="so__cap">Перші 5 зрізів у поточному порядку; z — третя координата ImagePositionPatient,
          d — проєкція на нормаль ({{ num(cur.normal[0], 3) }}; {{ num(cur.normal[1], 3) }}; {{ num(cur.normal[2], 3) }}).</div>
        <table class="so__table so__steps">
          <tbody>
            <tr><th>крок між сусідніми, мм</th><th>скільки разів</th></tr>
            <tr v-for="r in stepTable.slice(0, 4)" :key="r.v"><td>{{ num(r.v, 2) }}</td><td>{{ r.n }}</td></tr>
            <tr v-if="stepTable.length > 4"><td colspan="2">… ще {{ stepTable.length - 4 }} різних значень</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat" :class="{ 'is-green': uniform, 'is-warm': !uniform }">
        <b>{{ uniform ? num(Math.abs(stepTable[0].v), 2) + ' мм' : stepTable.length }}</b>
        <span>{{ uniform ? 'один крок на всю серію' : 'різних кроків між сусідніми' }}</span>
      </div>
      <div class="lab__stat"><b>{{ dTrend }}</b><span>позиція d у цьому порядку</span></div>
      <div class="lab__stat"><b>{{ instTrend }}</b><span>InstanceNumber у цьому порядку</span></div>
      <div v-if="oblique" class="lab__stat is-warm">
        <b>{{ num(cur.step_z, 2) }} / {{ num(cur.step_normal, 2) }}</b>
        <span>«крок по z» / крок уздовж нормалі, мм: менший на {{ num(100 * (1 - cur.step_z / cur.step_normal), 1) }} %; нахил {{ num(cur.tilt, 1) }}°</span>
      </div>
      <div v-else class="lab__stat"><b>{{ num(cur.thickness, 1) }} мм</b><span>SliceThickness у тезі</span></div>
    </div>

    <p class="lab__note">
      В архіві точки розкидані: у LIDC-IDRI-0001 перший файл має InstanceNumber 80 і z = −207,5 мм, а в
      Prostate-3T переставлено лише файли 4 і 5 — на графіку це одна «сходинка». Після сортування за d лінія
      стає рівною, а крок — одним на всю серію. Сортування за InstanceNumber теж дає рівну лінію, але в обох КТ
      вона спадає, а в МРТ зростає: номер не каже, в який бік іде серія. У косій Prostate-3T z і d різні, і
      різниця сусідніх z (3,62 мм) коротша за справжній крок 4,00 мм.
    </p>
  </div>
</template>

<style scoped>
.so__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
  gap: 1.1rem;
  align-items: start;
}
@media (max-width: 760px) { .so__grid { grid-template-columns: 1fr; } }
.so__grid svg { width: 100%; height: auto; display: block; }
.so__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.4rem; line-height: 1.4; }
.so__grid-line { stroke: var(--uk-line); stroke-width: 0.6; }
.so__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.so__path { fill: none; stroke: var(--uk-warm); stroke-width: 0.9; opacity: 0.7; }
.so__path.is-sorted { stroke: var(--uk-green); stroke-width: 1.6; opacity: 1; }
.so__pt { fill: var(--uk-accent); }
.so__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.so__table th {
  font-weight: 500;
  font-size: 0.7rem;
  color: var(--vp-c-text-3);
  text-align: right;
  padding: 0.15rem 0.3rem !important;
}
.so__table td {
  font-family: var(--vp-font-family-mono);
  font-size: 0.76rem;
  text-align: right;
  padding: 0.2rem 0.3rem !important;
  border-top: 1px solid var(--uk-line) !important;
}
.so__steps { margin-top: 0.6rem; }
.so__steps td[colspan] { text-align: left; font-family: var(--vp-font-family-base); color: var(--vp-c-text-3); }
</style>
