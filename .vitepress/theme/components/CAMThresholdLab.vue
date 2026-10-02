<script setup lang="ts">
/**
 * Рамки з карти активації класу (лекція 09, розділ «Від карти до рамок-кандидатів»).
 * Дані — tools/gen_lec09_cam.py: карти 7 × 7 для 123 знімків з рамками консенсусу (знімків NLM немає —
 * лише карти й рамки на нейтральному тлі), рамки еталону в px копії 256 px, середній контур легень SCR і
 * для кожного порогу θ = 0,10…0,90 рамки з карти (min–max → клітинки ≥ θ → 8-зв’язні компоненти) та
 * частки 352 рамок еталону, знайдених з IoU чи IoBB ≥ τ. Частки по набору — з генератора (при θ = 0,5
 * вони збігаються з виводом блоку коду); частку для одного знімка віджет рахує сам тією самою формулою.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec09_cam.json'

type Box = number[]
const FILES = data.files as string[]
const CAM = data.cam as number[][][]
const GT = data.gt as Box[][]
const LUNG = data.lung as number[][][]
const FRAME = data.frame as number[][]
const THETAS = data.thetas as number[]
const TAUS = data.taus as number[]
const PRED = data.pred as Record<string, number[][][][]>
const STATS = data.stats as Record<string, Record<string, number>[]>
const TOTAL = data.prior_total as number[][]
const HITS = data.hits as string[]
const S = data.cell_px as number
const N_BOX = data.n_boxes as number

const SRCS = ['cam', 'prior'] as const
const METRICS = ['IoU', 'IoBB'] as const
const idx = ref(0)
const ti = ref(THETAS.indexOf(0.5))
const src = ref<'cam' | 'prior'>('cam')
const metric = ref<'IoU' | 'IoBB'>('IoU')
const tau = ref(0.1)

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const theta = computed(() => THETAS[ti.value])

/** Карта, яку бачить читач: CAM знімка або апріорна карта без самого знімка; нормування min–max */
const grid = computed(() => {
  const m = src.value === 'cam'
    ? CAM[idx.value]
    : TOTAL.map((row, r) => row.map((v, c) => v - Number(HITS[idx.value][r * 7 + c])))
  const flat = m.flat()
  const lo = Math.min(...flat), hi = Math.max(...flat)
  return m.map(row => row.map(v => (v - lo) / (hi - lo)))
})

const STOPS = ['#000004', '#320a5e', '#781c6d', '#bc3754', '#ed6925', '#fbb61a', '#fcffa4']
function heat(v: number) {
  const x = Math.min(0.9999, Math.max(0, v)) * (STOPS.length - 1)
  const i = Math.floor(x), f = x - i
  const a = STOPS[i], b = STOPS[i + 1]
  const ch = (s: string, k: number) => parseInt(s.slice(1 + 2 * k, 3 + 2 * k), 16)
  const mix = [0, 1, 2].map(k => Math.round(ch(a, k) + (ch(b, k) - ch(a, k)) * f))
  return `rgb(${mix.join(',')})`
}

const predBoxes = computed<Box[]>(() =>
  PRED[src.value][ti.value][idx.value].map(([r0, c0, r1, c1]) => [c0 * S, r0 * S, c1 * S, r1 * S]))

function measure(g: Box, p: Box) {
  const w = Math.max(0, Math.min(g[2], p[2]) - Math.max(g[0], p[0]))
  const h = Math.max(0, Math.min(g[3], p[3]) - Math.max(g[1], p[1]))
  const inter = w * h
  const ag = (g[2] - g[0]) * (g[3] - g[1]), ap = (p[2] - p[0]) * (p[3] - p[1])
  return metric.value === 'IoU' ? inter / (ag + ap - inter) : inter / ap
}

const perImage = computed(() => {
  const g = GT[idx.value]
  const best = g.map(b => Math.max(0, ...predBoxes.value.map(p => measure(b, p))))
  return { best, found: best.filter(v => v >= tau.value).length }
})
const stat = computed(() => STATS[src.value][ti.value])
const share = computed(() => stat.value[`${metric.value}|${tau.value}`])
/** середній контур легень SCR, вписаний у кадр знімка (x0, y0, w, h) всередині квадрата 256 */
const path = (c: number[][]) => {
  const [x0, y0, w, h] = FRAME[idx.value]
  return c.map((p, i) => `${i ? 'L' : 'M'}${(x0 + p[0] * w / 256).toFixed(1)},${(y0 + p[1] * h / 256).toFixed(1)}`).join(' ') + ' Z'
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Рамки з карти 7 × 7 проти рамок консенсусу</div>
        <div class="lab__sub">
          123 знімки з рамками; знімків NLM немає — лише карта, рамки еталону (жовті) і рамки з карти (блакитні
          пунктирні) у координатах копії 256 px; білий контур — середня маска легень SCR, вписана в кадр знімка.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>знімок {{ idx + 1 }} з {{ FILES.length }}: <b>{{ FILES[idx].replace('.png', '') }}</b></span>
        <input v-model.number="idx" type="range" min="0" :max="FILES.length - 1" step="1" aria-label="Номер знімка">
      </label>
      <label class="lab__ctl">
        <span>поріг θ: <b>{{ num(theta, 2) }}</b></span>
        <input v-model.number="ti" type="range" min="0" :max="THETAS.length - 1" step="1" aria-label="Поріг θ">
      </label>
    </div>
    <div class="lab__pills">
      <button v-for="s in SRCS" :key="s" type="button" class="lab__pill" :class="{ 'is-on': src === s }" @click="src = s">
        {{ s === 'cam' ? 'карта активації класу' : 'апріорна карта' }}
      </button>
      <button v-for="m in METRICS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': metric === m }" @click="metric = m">{{ m }}</button>
      <button v-for="t in TAUS" :key="t" type="button" class="lab__pill" :class="{ 'is-on': tau === t }" @click="tau = t">τ = {{ num(t, 2).replace(/0$/, '') }}</button>
    </div>

    <svg viewBox="0 0 256 256" class="ct__svg" role="img" aria-label="Карта 7 × 7, рамки еталону і рамки з карти">
      <rect x="0" y="0" width="256" height="256" fill="#2a2a2a" />
      <g v-for="(row, r) in grid" :key="'r' + r">
        <rect v-for="(v, c) in row" :key="'c' + c" :x="c * S" :y="r * S" :width="S" :height="S" :fill="heat(v)"
          :opacity="0.85" :stroke="v >= theta ? '#ffffff' : 'none'" stroke-width="0.6" />
      </g>
      <path v-for="(c, i) in LUNG" :key="'l' + i" :d="path(c)" fill="none" stroke="#ffffff" stroke-width="1.1" />
      <rect v-for="(b, i) in GT[idx]" :key="'g' + i" :x="b[0]" :y="b[1]" :width="b[2] - b[0]" :height="b[3] - b[1]"
        fill="none" stroke="#FFCC33" stroke-width="1.6" />
      <rect v-for="(b, i) in predBoxes" :key="'p' + i" :x="b[0]" :y="b[1]" :width="b[2] - b[0]" :height="b[3] - b[1]"
        fill="none" stroke="#33C3FF" stroke-width="1.6" stroke-dasharray="4 3" />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(share) }}</b><span>частка {{ N_BOX }} рамок еталону, знайдених з {{ metric }} ≥ {{ num(tau, 2).replace(/0$/, '') }} (усі 123 знімки)</span></div>
      <div class="lab__stat"><b>{{ num(stat.boxes_per_img, 2) }}</b><span>рамок з карти на знімок</span></div>
      <div class="lab__stat"><b>{{ perImage.found }} з {{ GT[idx].length }}</b><span>рамок цього знімка знайдено</span></div>
      <div class="lab__stat"><b>{{ num(Math.max(0, ...perImage.best), 3) }}</b><span>найкраща {{ metric }} на цьому знімку</span></div>
    </div>

    <p class="lab__note">
      Найменша рамка з карти — одна клітинка {{ num(S, 1) }} × {{ num(S, 1) }} px, а рамки еталону здебільшого
      менші. Низький поріг θ зливає клітинки в одну велику рамку: IoBB падає, бо зростає площа рамки з карти; високий
      лишає одну-дві клітинки, і вони рідко накривають саме ту ділянку, де лежить рамка.
    </p>
  </div>
</template>

<style scoped>
.ct__svg { width: 100%; max-width: 420px; height: auto; display: block; margin: 0.5rem auto; }
</style>
