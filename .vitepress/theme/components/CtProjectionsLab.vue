<script setup lang="ts">
/**
 * Реконструкція зрізу LIDC-IDRI-0001 (z = −117,5 мм, 256 × 256) фільтрованою зворотною проєкцією за 15…360
 * проєкціями, без металу і зі сталевим диском у груднині. Кадри і RMSE — з tools/gen_lec02_ct.py, який
 * повторює блок коду розділу «Комп’ютерна томографія: зріз, відновлений із проєкцій» (той самий seed шуму
 * Пуассона, 100 000 фотонів на промінь), тож RMSE збігаються з таблицею виводу: без металу 362,3 → 47,3 HU
 * по зрізу, з металом за 360 проєкцій 108,4 HU у м’яких тканинах; 304 промені без фотонів.
 * Одразу вантажиться лише кадр за замовчуванням (360 проєкцій без металу, ≈ 18 КБ) і синограма (≈ 30 КБ);
 * усі 12 кадрів (≈ 0,2 МБ) — після першої дії читача, синограма з металом — за перемикачем «метал».
 */
import { ref, computed, onBeforeUnmount } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec02_ct.json'

const NS = data.n as number[]
const ni = ref(NS.length - 1)
const metal = ref(false)
const status = ref<'idle' | 'loading' | 'ok' | 'error'>('idle')
const progress = ref(0)
const spriteUrl = ref('')

const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const mb = (b: number) => num(b / 1e6, 1)
const row = computed(() => (metal.value ? 1 : 0))
const rmseSlice = computed(() => (data.rmse_slice as number[][])[row.value][ni.value])
const rmseSoft = computed(() => (data.rmse_soft as number[][])[row.value][ni.value])
const isDefault = computed(() => ni.value === NS.length - 1 && !metal.value)

/** Усі кадри — одним PNG; прогрес — за отриманими байтами */
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
      let got = 0
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        chunks.push(value)
        got += value.length
        progress.value = Math.min(1, got / total)
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

function setN(i: number) { ni.value = i; ensureFrames() }
function setMetal(v: boolean) { metal.value = v; ensureFrames() }

const frameStyle = computed(() => {
  if (status.value === 'ok') {
    const x = (ni.value / (NS.length - 1)) * 100
    return { backgroundImage: `url(${spriteUrl.value})`, backgroundSize: `${NS.length * 100}% 200%`, backgroundPosition: `${x}% ${row.value * 100}%` }
  }
  return { backgroundImage: `url(${withBase(data.default as string)})`, backgroundSize: '100% 100%' }
})
const showWait = computed(() => !isDefault.value && status.value !== 'ok')
const sino = computed(() => withBase((data.sino as string[])[metal.value ? 1 : 0]))

/* Позначки використаних кутів на синограмі (рядки — кути 0…180°, 360 рядків) */
const ticks = computed(() => {
  const n = NS[ni.value]
  const step = 360 / n
  return Array.from({ length: n }, (_, k) => k * step + 0.5)
})

/* Графік RMSE м’яких тканин від кількості проєкцій, логарифмічна вісь x */
const GW = 330
const GH = 170
const GL = 44
const GR = 10
const GT = 10
const GB = 30
const gx = (n: number) => GL + ((Math.log10(n) - Math.log10(NS[0])) / (Math.log10(NS[NS.length - 1]) - Math.log10(NS[0]))) * (GW - GL - GR)
const YMAX = Math.log10(3000)
const YMIN = Math.log10(30)
const gy = (v: number) => GT + (1 - (Math.log10(v) - YMIN) / (YMAX - YMIN)) * (GH - GT - GB)
const curve = (r: number) => NS.map((n, i) => `${gx(n).toFixed(1)},${gy((data.rmse_soft as number[][])[r][i]).toFixed(1)}`).join(' ')
const YT = [30, 100, 300, 1000, 3000]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Скільки проєкцій потрібно КТ і що робить метал</div>
        <div class="lab__sub">
          Зріз LIDC-IDRI-0001 256 × 256, μ при 60 кеВ, лічба фотонів з шумом Пуассона, фільтрована зворотна
          проєкція. Кути рівномірно на 180°. Показано вікно −160…240 HU.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(n, i) in NS" :key="n" type="button" class="lab__pill" :class="{ 'is-on': ni === i }"
              @click="setN(i)">{{ n }} проєкцій</button>
    </div>
    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': !metal }" @click="setMetal(false)">без металу</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': metal }" @click="setMetal(true)">сталевий диск у груднині</button>
    </div>

    <div class="cp__grid">
      <div>
        <div class="cp__frame" :style="frameStyle" role="img" :aria-label="`Реконструкція за ${NS[ni]} проєкціями`">
          <div v-if="showWait" class="cp__wait">
            <template v-if="status === 'error'">
              не вдалося завантажити кадри
              <button class="lab__btn" type="button" @click="status = 'idle'; ensureFrames()">ще раз</button>
            </template>
            <template v-else>завантаження кадрів: {{ Math.round(progress * 100) }} %</template>
          </div>
        </div>
        <div v-if="status === 'idle'" class="cp__hint">
          Зараз показано 360 проєкцій без металу. Будь-яка кнопка завантажить усі 12 кадрів (≈ {{ mb(data.frames_bytes as number) }} МБ).
        </div>
      </div>
      <div>
        <div class="cp__cap">Синограма: рядок — кут від 0° (угорі) до 180°, стовпець — положення на детекторі.
          Риски ліворуч — використані кути.</div>
        <div class="cp__sino" :style="{ backgroundImage: `url(${sino})` }">
          <svg viewBox="0 0 256 360" preserveAspectRatio="none" aria-hidden="true">
            <line v-for="y in ticks" :key="y" x1="0" :x2="NS[ni] <= 30 ? 256 : 14" :y1="y" :y2="y"
                  :class="NS[ni] <= 30 ? 'cp__tick cp__tick--full' : 'cp__tick'" />
          </svg>
        </div>
      </div>
      <div>
        <div class="cp__cap">RMSE м’яких тканин, HU (логарифмічні осі): синя — без металу, тепла — з металом</div>
        <svg :viewBox="`0 0 ${GW} ${GH}`" role="img" aria-label="RMSE від кількості проєкцій">
          <g v-for="t in YT" :key="t">
            <line :x1="GL" :x2="GW - GR" :y1="gy(t)" :y2="gy(t)" class="cp__grid-line" />
            <text :x="GL - 4" :y="gy(t) + 3" text-anchor="end" class="cp__lbl">{{ t }}</text>
          </g>
          <g v-for="n in NS" :key="'x' + n">
            <text :x="gx(n)" :y="GH - GB + 13" text-anchor="middle" class="cp__lbl">{{ n }}</text>
          </g>
          <polyline :points="curve(0)" class="cp__c0" />
          <polyline :points="curve(1)" class="cp__c1" />
          <circle :cx="gx(NS[ni])" :cy="gy(rmseSoft)" r="4.5" :class="metal ? 'cp__p1' : 'cp__p0'" />
          <text :x="(GL + GW - GR) / 2" :y="GH - 3" text-anchor="middle" class="cp__lbl">кількість проєкцій</text>
        </svg>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(rmseSlice) }}</b><span>RMSE по зрізу, HU</span></div>
      <div class="lab__stat" :class="{ 'is-warm': metal }"><b>{{ num(rmseSoft) }}</b><span>RMSE м’яких тканин, HU</span></div>
      <div class="lab__stat"><b>{{ num(180 / NS[ni], NS[ni] > 90 ? 1 : 0) }}°</b><span>крок між кутами</span></div>
      <div class="lab__stat" :class="{ 'is-warm': metal }"><b>{{ (data.zero as number[])[row] }}</b><span>променів без жодного фотона</span></div>
    </div>

    <p class="lab__note">
      Почніть з 15 проєкцій: зріз покреслений радіальними смугами. Додавайте проєкції й стежте за RMSE під
      зображенням і на графіку: після 90 проєкцій виграш стає малим. Потім увімкніть диск — смуги розходяться від
      груднини через усю клітку, а на синограмі з’являється світла синусоїда диска з обрізаними променями. Як
      розкласти помилку з металом на частини, пояснює розділ про артефакти КТ.
    </p>
  </div>
</template>

<style scoped>
.cp__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, 0.75fr) minmax(0, 1.1fr);
  gap: 1rem;
  align-items: start;
}
@media (max-width: 860px) { .cp__grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 560px) { .cp__grid { grid-template-columns: 1fr; } }
.cp__grid svg { width: 100%; height: auto; display: block; }
.cp__frame {
  position: relative;
  width: 100%;
  max-width: 380px;
  aspect-ratio: 1 / 1;
  background-color: #000;
  background-repeat: no-repeat;
  border-radius: 6px;
}
.cp__wait {
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
  border-radius: 6px;
}
.cp__hint { font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.4rem; line-height: 1.4; max-width: 380px; }
.cp__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0 0 0.4rem; line-height: 1.4; }
.cp__sino {
  position: relative;
  width: 100%;
  max-width: 200px;
  aspect-ratio: 256 / 360;
  background-size: 100% 100%;
  background-color: #000;
  border-radius: 4px;
}
.cp__sino svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.cp__tick { stroke: #f2c94c; stroke-width: 1; opacity: 0.9; }
.cp__tick--full { opacity: 0.45; }
.cp__grid-line { stroke: var(--uk-line); stroke-width: 0.6; }
.cp__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.cp__c0 { fill: none; stroke: var(--uk-accent); stroke-width: 1.8; }
.cp__c1 { fill: none; stroke: var(--uk-warm); stroke-width: 1.8; }
.cp__p0 { fill: var(--uk-accent); }
.cp__p1 { fill: var(--uk-warm); }
</style>
