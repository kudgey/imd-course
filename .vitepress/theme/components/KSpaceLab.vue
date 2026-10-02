<script setup lang="ts">
/**
 * k-простір середнього зрізу Prostate-3T 01-0019: залишаються центральні рядки фазового кодування (вісь —
 * з тегу InPlanePhaseEncodingDirection), за перемикачем — ще й кожен другий рядок; зображення — модуль
 * оберненого ДПФ. Кадри й помилки — з tools/gen_lec02_kspace.py, який повторює блок коду розділу
 * «k-простір: МРТ вимірює частоти, а не пікселі»: 50 % рядків — 6,28 %, пропуск кожного другого — 36,64 %.
 * Одразу вантажаться вихідний зріз і k-простір (≈ 45 КБ кожен), 16 кадрів (≈ 0,5 МБ) — після першої дії.
 */
import { ref, computed, onBeforeUnmount } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec02_kspace.json'

const F = data.fracs as number[]
const N = data.n as number
const AXIS = data.axis as number                      // 1 — фазове кодування вздовж стовпців k-простору
const fi = ref(0)
const skip = ref(false)
const status = ref<'idle' | 'loading' | 'ok' | 'error'>('idle')
const progress = ref(0)
const spriteUrl = ref('')

const num = (v: number, d = 2) => v.toFixed(d).replace('.', ',')
const pctF = (v: number) => (Number.isInteger(v * 100) ? String(v * 100) : num(v * 100, 2).replace(/0+$/, '').replace(/,$/, '')) + ' %'
const lines = computed(() => (data.lines as number[])[fi.value])
const got = computed(() => (skip.value ? (data.lines_skip as number[]) : (data.lines as number[]))[fi.value])
const err = computed(() => (skip.value ? (data.err_skip as number[]) : (data.err as number[]))[fi.value])
const step = computed(() => (data.step_mm as number[])[fi.value])
const isDefault = computed(() => fi.value === 0 && !skip.value)

async function ensureFrames() {
  if (status.value === 'loading' || status.value === 'ok') return
  status.value = 'loading'
  progress.value = 0
  try {
    const res = await fetch(withBase(data.frames as string))
    if (!res.ok) throw new Error(String(res.status))
    const total = (data.frames_bytes as number) || 1
    const chunks: Uint8Array[] = []
    if (res.body) {
      const reader = res.body.getReader()
      let n = 0
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        chunks.push(value)
        n += value.length
        progress.value = Math.min(1, n / total)
      }
    } else {
      chunks.push(new Uint8Array(await res.arrayBuffer()))
    }
    spriteUrl.value = URL.createObjectURL(new Blob(chunks, { type: 'image/png' }))
    status.value = 'ok'
  } catch {
    status.value = 'error'
  }
}
onBeforeUnmount(() => { if (spriteUrl.value) URL.revokeObjectURL(spriteUrl.value) })
function setF(i: number) { fi.value = i; ensureFrames() }
function setSkip(v: boolean) { skip.value = v; ensureFrames() }

const frameStyle = computed(() => {
  if (status.value === 'ok') {
    const x = (fi.value / (F.length - 1)) * 100
    return { backgroundImage: `url(${spriteUrl.value})`, backgroundSize: `${F.length * 100}% 200%`, backgroundPosition: `${x}% ${skip.value ? 100 : 0}%` }
  }
  return { backgroundImage: `url(${withBase(data.default as string)})`, backgroundSize: '100% 100%' }
})
const showWait = computed(() => !isDefault.value && status.value !== 'ok')

/* Відкинута частина k-простору: смуги поза центральним вікном і (за перемикачем) кожен непарний рядок у ньому */
const lo = computed(() => (N - lines.value) / 2)
const hi = computed(() => (N + lines.value) / 2)
const rect = (a: number, b: number) => (AXIS === 1 ? { x: a, y: 0, width: b - a, height: N } : { x: 0, y: a, width: N, height: b - a })
const oddLines = computed(() => {
  if (!skip.value) return ''
  const out: string[] = []
  for (let k = Math.ceil(lo.value); k < hi.value; k++) {
    if (k % 2 === 1) out.push(AXIS === 1 ? `M${k + 0.5} 0V${N}` : `M0 ${k + 0.5}H${N}`)
  }
  return out.join('')
})
const peName = AXIS === 1 ? 'вертикальні стовпці' : 'горизонтальні рядки'
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">k-простір МРТ: обрізання і пропуск рядків фазового кодування</div>
        <div class="lab__sub">
          Середній зріз Prostate-3T 01-0019, 256 × 256, крок 0,75 мм, поле зору {{ num(data.fov_mm as number, 0) }} мм.
          Фазове кодування ({{ data.pe }}) — {{ peName }} k-простору; час сканування пропорційний їхній кількості.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(f, i) in F" :key="f" type="button" class="lab__pill" :class="{ 'is-on': fi === i }"
              @click="setF(i)">{{ pctF(f) }}</button>
    </div>
    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': !skip }" @click="setSkip(false)">усі рядки вікна</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': skip }" @click="setSkip(true)">кожен другий рядок</button>
    </div>

    <div class="ks__grid">
      <div>
        <div class="ks__cap">log(1 + |k|): центр — низькі частоти, затемнено відкинуті рядки</div>
        <div class="ks__img" :style="{ backgroundImage: `url(${withBase(data.kspace as string)})` }">
          <svg :viewBox="`0 0 ${N} ${N}`" aria-hidden="true">
            <rect v-bind="rect(0, lo)" class="ks__cut" />
            <rect v-bind="rect(hi, N)" class="ks__cut" />
            <path v-if="skip" :d="oddLines" class="ks__odd" />
          </svg>
        </div>
      </div>
      <div>
        <div class="ks__cap">Відновлений зріз (модуль оберненого ДПФ)</div>
        <div class="ks__img" :style="frameStyle" role="img" aria-label="Відновлений зріз МРТ">
          <div v-if="showWait" class="ks__wait">
            <template v-if="status === 'error'">
              не вдалося завантажити кадри
              <button class="lab__btn" type="button" @click="status = 'idle'; ensureFrames()">ще раз</button>
            </template>
            <template v-else>завантаження кадрів: {{ Math.round(progress * 100) }} %</template>
          </div>
        </div>
        <div v-if="status === 'idle'" class="ks__cap">Будь-яка кнопка завантажить 16 кадрів
          (≈ {{ num((data.frames_bytes as number) / 1e6, 1) }} МБ).</div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ got }}</b><span>рядків фазового кодування з {{ N }}</span></div>
      <div class="lab__stat"><b>{{ num(step) }} мм</b><span>роздільність уздовж фазового кодування (поле зору / рядки)</span></div>
      <div class="lab__stat" :class="{ 'is-warm': skip }"><b>{{ num(err) }} %</b><span>помилка ‖x̂ − x‖ / ‖x‖</span></div>
      <div class="lab__stat is-green"><b>{{ Math.round((got / N) * 100) }} %</b><span>час сканування від повного</span></div>
    </div>

    <p class="lab__note">
      Зменшуйте частку центральних рядків: зріз розмивається вздовж фазового кодування, а біля різких меж
      з’являються хвилі Гіббса; навіть при найменшій частці контраст органів ще впізнаваний — він живе в центрі
      k-простору. Увімкніть «кожен другий рядок»: час удвічі менший, роздільність та сама, але зріз накладається
      на свою копію, зсунуту на половину поля зору, і помилка стрибає.
    </p>
  </div>
</template>

<style scoped>
.ks__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 1.1rem;
  align-items: start;
}
.ks__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.4rem; line-height: 1.4; }
.ks__img {
  position: relative;
  width: 100%;
  max-width: 340px;
  aspect-ratio: 1 / 1;
  background-color: #000;
  background-repeat: no-repeat;
  background-size: 100% 100%;
  border-radius: 6px;
  overflow: hidden;
}
.ks__img svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.ks__cut { fill: rgba(10, 10, 20, 0.78); }
.ks__odd { stroke: rgba(10, 10, 20, 0.78); stroke-width: 1; fill: none; }
.ks__wait {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  color: #ddd;
  font-size: 0.8rem;
}
</style>
