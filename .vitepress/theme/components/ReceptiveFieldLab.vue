<script setup lang="ts">
/**
 * Рецептивне поле стадій ResNet-18 на рентгенограмі (лекція 08, розділ «Рецептивне поле в міліметрах»).
 * Поле r і крок j кожної стадії пораховано проходом по шарах torchvision (r ← r + (k − 1)·j, j ← j·s) —
 * тим самим, що в блоці коду; міліметри на піксель — з медіани довшої сторони кадрів Montgomery
 * (крок 0,0875 мм). Показ — рентгенограма NIH ChestX-ray14 00000511_000 (довша сторона ≈ 427,7 мм — той
 * самий масштаб), доповнена до квадрата і зменшена до 256, 224 або 128 px. Торкніться знімка, щоб
 * перенести центр поля; квадрат — теоретичне поле одного виходу стадії, сітка — клітинки її карти ознак.
 * Дані: tools/gen_lec08_rf.py.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec08_rf.json'

type Stage = { name: string; layers: number; rf: number; jump: number }
const stages = data.stages as Stage[]
const sizes = data.sizes as number[]
const side = data.side_mm as number

const si = ref(4) // layer3 за замовчуванням
const size = ref(224)
const cx = ref(0.38) // центр — права легеня пацієнта (ліва половина кадру), частки сторони
const cy = ref(0.42)

const st = computed(() => stages[si.value])
const mmPx = computed(() => side / size.value)
const rfMm = computed(() => st.value.rf * mmPx.value)
const map = computed(() => Math.ceil(size.value / st.value.jump))
const cover = computed(() => Math.min(1, st.value.rf / size.value))

const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',')
const V = 256 // система координат SVG, сторона кадру
const box = computed(() => {
  const w = (st.value.rf / size.value) * V
  return { x: cx.value * V - w / 2, y: cy.value * V - w / 2, w }
})
const cells = computed(() => {
  const n = map.value
  if (n > 32) return [] as number[]
  return Array.from({ length: n - 1 }, (_, k) => ((k + 1) * V) / n)
})

function pick(e: MouseEvent) {
  const el = e.currentTarget as SVGSVGElement
  const r = el.getBoundingClientRect()
  cx.value = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width))
  cy.value = Math.min(1, Math.max(0, (e.clientY - r.top) / r.height))
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Рецептивне поле ResNet-18 у міліметрах</div>
        <div class="lab__sub">
          Оберіть розмір входу і стадію мережі. Квадрат — ділянка входу, яку «бачить» один вихід стадії;
          сітка — клітинки карти ознак цієї стадії. Торкніться знімка, щоб перенести центр поля.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="s in sizes" :key="s" type="button" class="lab__pill" :class="{ 'is-on': size === s }"
              @click="size = s">вхід {{ s }} × {{ s }} px</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>стадія: <b>{{ st.name }}</b> (згорток і пулінгів у стадії: {{ st.layers }})</span>
        <input v-model.number="si" type="range" min="0" :max="stages.length - 1" step="1" aria-label="Стадія ResNet-18" />
      </label>
    </div>

    <div class="rf__grid">
      <div class="rf__frame">
        <img :src="withBase(data.png[String(size)])" :alt="`Рентгенограма NIH ChestX-ray14 ${data.nih}, ${size} px`" />
        <svg :viewBox="`0 0 ${V} ${V}`" class="rf__ov" role="img" aria-label="Рецептивне поле на знімку" @click="pick">
          <line v-for="c in cells" :key="'v' + c" :x1="c" :x2="c" y1="0" :y2="V" class="rf__cell" />
          <line v-for="c in cells" :key="'h' + c" :y1="c" :y2="c" x1="0" :x2="V" class="rf__cell" />
          <rect :x="box.x" :y="box.y" :width="box.w" :height="box.w" class="rf__box" />
          <circle :cx="cx * V" :cy="cy * V" r="2.2" class="rf__dot" />
        </svg>
      </div>
      <div>
        <div class="rf__cap">Поле стадій при вході {{ size }} px, мм</div>
        <div v-for="(s, k) in stages" :key="s.name" class="lab__row" :class="{ 'rf__on': k === si }">
          <span class="lab__label rf__nm">{{ s.name }}</span>
          <div class="lab__bar"><i :style="{ width: Math.min(100, (s.rf / size) * 100) + '%' }" /></div>
          <span class="lab__num rf__v">{{ Math.round(s.rf * mmPx) }}</span>
        </div>
        <div class="rf__cap">Смуга заповнена повністю, коли поле більше за весь вхід.</div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(mmPx, 2) }}</b><span>мм на піксель входу</span></div>
      <div class="lab__stat"><b>{{ st.rf }} px</b><span>рецептивне поле стадії</span></div>
      <div class="lab__stat" :class="{ 'is-warm': cover >= 1 }"><b>{{ Math.round(rfMm) }} мм</b><span>те саме в міліметрах</span></div>
      <div class="lab__stat"><b>{{ map }} × {{ map }}</b><span>карта ознак (відстань між виходами {{ st.jump }} px)</span></div>
      <div class="lab__stat"><b>{{ num(st.jump * mmPx, 1) }} мм</b><span>відстань між сусідніми виходами</span></div>
    </div>

    <p class="lab__note">
      На вході 128 px один піксель — {{ num(side / 128, 2) }} мм, тож вогнище діаметром 5 мм займає півтора пікселя ще до
      першої згортки. Поле layer4 при будь-якому з трьох розмірів більше за весь кадр, але це теоретична межа:
      внесок пікселів у вихід спадає від центру поля до країв.
    </p>
  </div>
</template>

<style scoped>
.rf__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1.1rem;
  align-items: start;
}
@media (max-width: 760px) { .rf__grid { grid-template-columns: 1fr; } }
.rf__frame { position: relative; width: 100%; max-width: 360px; aspect-ratio: 1; background: #000; border-radius: 6px; overflow: hidden; }
.rf__frame img { position: absolute; inset: 0; width: 100%; height: 100%; image-rendering: pixelated; }
.rf__ov { position: absolute; inset: 0; width: 100%; height: 100%; cursor: crosshair; }
.rf__box { fill: rgba(255, 204, 51, 0.12); stroke: #ffcc33; stroke-width: 1.6; }
.rf__cell { stroke: rgba(51, 195, 255, 0.35); stroke-width: 0.5; }
.rf__dot { fill: #ffcc33; stroke: #000; stroke-width: 0.6; }
.rf__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.4rem; line-height: 1.4; }
.rf__nm { width: 4.6rem; }
.rf__v { width: 3.2rem; }
.rf__on .rf__nm, .rf__on .rf__v { color: var(--uk-accent); font-weight: 600; }
</style>
