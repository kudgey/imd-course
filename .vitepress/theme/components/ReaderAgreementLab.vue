<script setup lang="ts">
/**
 * Консенсус чотирьох радіологів LIDC-IDRI-0001 (лекція 04, розділ «Консенсус чотирьох масок:
 * більшість голосів і STAPLE»). Вирізка серії навколо вузла з 069.xml: рівні сірого (вікно
 * −600/1600) і маски читачів 1–4 та STAPLE, побудовані способом курсу (заливка без пікселів лінії —
 * за LIDC лінія є зовнішньою межею; зріз за SOP UID). Об’єми «≥ k з 4» віджет рахує з масок:
 * 8091,8 / 6708,8 / 5947,4 / 5171,3 мм³, STAPLE — 6708,8 мм³, як у виводі коду. Праворуч — розподіл 1017 КТ колекції: скільки вузлів
 * ≥ 3 мм позначили щонайменше k читачів при порозі зіставлення τ (при τ = 10 — як у виводі коду:
 * 779 / 488 / 485 / 907). Дані пише tools/gen_lec04_readers.py.
 */
import { ref, shallowRef, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec04_readers.json'

type Reader = { contours: number; z0: number; z1: number; voxels: number; volume: number; malignancy: number }
type Mode = 1 | 2 | 3 | 4 | 'staple'

const [NZ, NY, NX] = data.shape as number[]
const N = NZ * NY * NX
const VOX = data.voxel_mm3 as number
const READERS = data.readers as Reader[]
const ZS = data.z as number[]
const TAUS = data.taus as number[]
const COUNTS = data.collection.counts as Record<string, number[]>
const COLORS = ['#2A78D6', '#EB6834', '#1BAF7A', '#E87BA4']   // палітра класів курсу
const S = 5                                                    // масштаб: пікселів екрана на піксель вирізки

const gray = shallowRef<Uint8Array | null>(null)
const bits = shallowRef<Uint8Array | null>(null)
const status = ref<'loading' | 'ok' | 'error'>('loading')
const mode = ref<Mode>(3)
const k = ref(data.k_ref as number)
const show = ref([true, true, true, true])
const tau = ref(10)
const canvas = ref<HTMLCanvasElement | null>(null)

const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const spaced = (v: number) => String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

onMounted(async () => {
  try {
    const res = await fetch(withBase(data.bin as string))
    if (!res.ok) throw new Error(String(res.status))
    const buf = new Uint8Array(await res.arrayBuffer())
    if (buf.length !== 2 * N) throw new Error('size')
    gray.value = buf.subarray(0, N)
    bits.value = buf.subarray(N)
    status.value = 'ok'
  } catch {
    status.value = 'error'
  }
})

/** Чи належить воксель масці консенсусу поточного режиму */
function inCons(b: number): boolean {
  if (mode.value === 'staple') return ((b >> 4) & 1) === 1
  const votes = (b & 1) + ((b >> 1) & 1) + ((b >> 2) & 1) + ((b >> 3) & 1)
  return votes >= mode.value
}

/** Об’єм консенсусу по всіх зрізах вирізки і вокселі на поточному зрізі */
const volume = computed(() => {
  const b = bits.value
  if (!b) return { all: 0, slice: 0 }
  let all = 0
  let slice = 0
  const off = k.value * NY * NX
  for (let p = 0; p < N; p++) {
    if (inCons(b[p])) {
      all += 1
      if (p >= off && p < off + NY * NX) slice += 1
    }
  }
  return { all, slice }
})

function draw() {
  const cv = canvas.value
  const g = gray.value
  const b = bits.value
  if (!cv || !g || !b) return
  cv.width = NX * S
  cv.height = NY * S
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(NX * S, NY * S)
  const off = k.value * NY * NX
  for (let y = 0; y < NY; y++) {
    for (let x = 0; x < NX; x++) {
      const v = g[off + y * NX + x]
      const m = inCons(b[off + y * NX + x])
      // заливка консенсусу: жовтий еталонний колір курсу, α 0,35
      const r = m ? v * 0.65 + 255 * 0.35 : v
      const gg = m ? v * 0.65 + 204 * 0.35 : v
      const bb = m ? v * 0.65 + 51 * 0.35 : v
      for (let dy = 0; dy < S; dy++) {
        for (let dx = 0; dx < S; dx++) {
          const p = 4 * ((y * S + dy) * NX * S + x * S + dx)
          img.data[p] = r
          img.data[p + 1] = gg
          img.data[p + 2] = bb
          img.data[p + 3] = 255
        }
      }
    }
  }
  ctx.putImageData(img, 0, 0)
  // контури читачів: відрізки по межах пікселів, де маска змінюється
  for (let i = 0; i < 4; i++) {
    if (!show.value[i]) continue
    const at = (y: number, x: number) =>
      y >= 0 && y < NY && x >= 0 && x < NX && ((b[off + y * NX + x] >> i) & 1) === 1
    ctx.strokeStyle = COLORS[i]
    ctx.lineWidth = 2
    ctx.beginPath()
    for (let y = 0; y < NY; y++) {
      for (let x = 0; x < NX; x++) {
        if (!at(y, x)) continue
        if (!at(y - 1, x)) { ctx.moveTo(x * S, y * S); ctx.lineTo((x + 1) * S, y * S) }
        if (!at(y + 1, x)) { ctx.moveTo(x * S, (y + 1) * S); ctx.lineTo((x + 1) * S, (y + 1) * S) }
        if (!at(y, x - 1)) { ctx.moveTo(x * S, y * S); ctx.lineTo(x * S, (y + 1) * S) }
        if (!at(y, x + 1)) { ctx.moveTo((x + 1) * S, y * S); ctx.lineTo((x + 1) * S, (y + 1) * S) }
      }
    }
    ctx.stroke()
  }
}
watch([gray, bits, mode, k, show, canvas], draw, { flush: 'post', deep: true })

const MODES: { id: Mode; label: string }[] = [
  { id: 1, label: '≥ 1 з 4 (об’єднання)' },
  { id: 2, label: '≥ 2 з 4' },
  { id: 3, label: '≥ 3 з 4 (більшість)' },
  { id: 4, label: '≥ 4 з 4 (перетин)' },
  { id: 'staple', label: 'STAPLE, p ≥ 0,5' },
]
const onSlice = (i: number) => ZS[k.value] >= READERS[i].z0 && ZS[k.value] <= READERS[i].z1
function toggle(i: number) {
  const s = [...show.value]
  s[i] = !s[i]
  show.value = s
}

/* Колекція LIDC: вузли за кількістю читачів при порозі τ */
const exact = computed(() => COUNTS[String(tau.value)])
const total = computed(() => exact.value.reduce((a, b) => a + b, 0))
const kSel = computed(() => (mode.value === 'staple' ? null : mode.value))
const atLeast = computed(() => (kSel.value ? exact.value.slice(kSel.value - 1).reduce((a, b) => a + b, 0) : null))
const BW = 300
const BH = 120
const maxC = computed(() => Math.max(...Object.values(COUNTS).flat()))
const barH = (c: number) => (c / maxC.value) * (BH - 34)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Згода чотирьох радіологів: консенсус масок і вузли всієї колекції</div>
        <div class="lab__sub">
          LIDC-IDRI-0001, вузол з 069.xml. Маски читачів — способом курсу: заливка контуру без пікселів самої
          лінії, бо за LIDC лінія — зовнішня межа вузла. Жовтим — маска консенсусу, кольоровими лініями — межі
          масок окремих читачів. Об’єм рахується
          по всіх {{ NZ }} зрізах вирізки: вокселі × {{ num(VOX, 6) }} мм³.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="m in MODES" :key="String(m.id)" type="button" class="lab__pill" :class="{ 'is-on': mode === m.id }"
              @click="mode = m.id">{{ m.label }}</button>
    </div>

    <div class="ra__grid">
      <div>
        <div class="ra__frame" :style="{ aspectRatio: `${NX} / ${NY}` }">
          <canvas ref="canvas" aria-label="Зріз КТ із маскою консенсусу й контурами читачів"></canvas>
          <div v-if="status !== 'ok'" class="ra__status">
            {{ status === 'loading' ? 'завантаження вирізки…' : 'не вдалося завантажити вирізку' }}
          </div>
        </div>
        <label class="lab__ctl ra__slice">
          <span>зріз z = <b>{{ num(ZS[k], 1) }}</b> мм ({{ k + 1 }} з {{ NZ }} у вирізці)</span>
          <input v-model.number="k" type="range" min="0" :max="NZ - 1" step="1" aria-label="Зріз" />
        </label>
        <div class="lab__pills ra__readers">
          <button v-for="(r, i) in READERS" :key="i" type="button" class="lab__pill" :class="{ 'is-on': show[i] }"
                  :style="{ borderColor: show[i] ? COLORS[i] : undefined, color: show[i] ? COLORS[i] : undefined }"
                  @click="toggle(i)">
            читач {{ i + 1 }}{{ onSlice(i) ? '' : ' (не на цьому зрізі)' }}
          </button>
        </div>
      </div>

      <div>
        <div class="lab__stats ra__stats">
          <div class="lab__stat is-warm">
            <b>{{ status === 'ok' ? num(volume.all * VOX, 1) : '…' }}</b>
            <span>мм³ — об’єм консенсусу ({{ spaced(volume.all) }} вокселів)</span>
          </div>
          <div class="lab__stat">
            <b>{{ status === 'ok' ? volume.slice : '…' }}</b><span>вокселів консенсусу на цьому зрізі</span>
          </div>
        </div>
        <table class="ra__table">
          <tbody>
            <tr><th>читач</th><th>контурів</th><th>об’єм, мм³</th><th>злоякісність</th></tr>
            <tr v-for="(r, i) in READERS" :key="i">
              <td :style="{ color: COLORS[i] }">{{ i + 1 }}</td><td>{{ r.contours }}</td>
              <td>{{ num(r.volume, 1) }}</td><td>{{ r.malignancy }}</td>
            </tr>
          </tbody>
        </table>

        <div class="ra__cap">Уся колекція: вузли ≥ 3 мм за кількістю читачів, що їх позначили
          (1017 КТ, поріг зіставлення центрів τ у пікселях)</div>
        <label class="lab__ctl">
          <span>поріг τ = <b>{{ tau }}</b> пікселів; вузлів усього {{ spaced(total) }}</span>
          <select v-model.number="tau" aria-label="Поріг зіставлення">
            <option v-for="t in TAUS" :key="t" :value="t">{{ t }} пікселів</option>
          </select>
        </label>
        <svg :viewBox="`0 0 ${BW} ${BH}`" role="img" aria-label="Кількість вузлів за кількістю читачів">
          <g v-for="(c, i) in exact" :key="i">
            <rect :x="20 + i * 70" :y="BH - 18 - barH(c)" width="50" :height="barH(c)"
                  :class="['ra__bar', { 'is-on': kSel !== null && i + 1 >= kSel }]" />
            <text :x="45 + i * 70" :y="BH - 22 - barH(c)" text-anchor="middle" class="ra__lbl">{{ spaced(c) }}</text>
            <text :x="45 + i * 70" :y="BH - 5" text-anchor="middle" class="ra__lbl">{{ i + 1 }} {{ i === 0 ? 'читач' : 'читачі' }}</text>
          </g>
        </svg>
        <div class="lab__stats">
          <div class="lab__stat">
            <b>{{ atLeast === null ? '—' : spaced(atLeast) }}</b>
            <span>{{ atLeast === null ? 'для STAPLE політики «≥ k» немає' : `вузлів позначили щонайменше ${kSel} з 4` }}</span>
          </div>
        </div>
      </div>
    </div>

    <p class="lab__note">
      Об’єднання (≥ 1) дає 8091,8 мм³, перетин (≥ 4) — 5171,3 мм³; STAPLE з порогом 0,5 збігається з «≥ 2 з 4»
      воксель у воксель. Гортайте зрізи до країв вузла: на найвищому зрізі (z = −105 мм) його обвів лише читач 4, а на найнижчому
      (z = −125 мм) немає контуру читача 2. Праворуч та сама політика застосована до всієї колекції: «≥ 3 з 4»
      лишає 1392 вузли з 2659 при τ = 10, а поріг зіставлення змінює числа на десятки, не змінюючи форми розподілу.
    </p>
  </div>
</template>

<style scoped>
.ra__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  gap: 1.1rem;
  align-items: start;
}
@media (max-width: 760px) { .ra__grid { grid-template-columns: 1fr; } }
.ra__frame {
  position: relative;
  width: 100%;
  max-width: 360px;
  background: #000;
  border-radius: 6px;
  overflow: hidden;
}
.ra__frame canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; image-rendering: pixelated; }
.ra__status {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ddd;
  font-size: 0.8rem;
  background: rgba(0, 0, 0, 0.6);
}
.ra__slice { display: block; margin-top: 0.6rem; max-width: 360px; }
.ra__readers { margin-top: 0.5rem; }
.ra__stats { margin-top: 0; }
.ra__table { width: 100%; border-collapse: collapse; margin: 0.7rem 0; font-variant-numeric: tabular-nums; }
.ra__table th { font-weight: 500; font-size: 0.72rem; color: var(--vp-c-text-3); text-align: right; padding: 0.15rem 0.3rem !important; }
.ra__table td {
  font-family: var(--vp-font-family-mono);
  font-size: 0.78rem;
  text-align: right;
  padding: 0.18rem 0.3rem !important;
  border-top: 1px solid var(--uk-line) !important;
}
.ra__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.6rem 0 0.4rem; line-height: 1.4; }
.ra__bar { fill: var(--uk-line); }
.ra__bar.is-on { fill: var(--uk-accent); }
.ra__lbl { fill: var(--vp-c-text-2); font-size: 10px; }
svg { width: 100%; height: auto; display: block; }
</style>
