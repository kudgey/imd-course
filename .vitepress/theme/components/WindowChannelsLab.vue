<script setup lang="ts">
/**
 * Три вікна КТ як канали R, G, B на еталонному зрізі LIDC-IDRI-0001 (k = 89, z = −117,5 мм).
 * Канал = clip((HU − (c − w/2)) / w, 0, 1) — та сама функція, що в блоці коду розділу про нормалізацію.
 * Зріз: /data/lec05/lidc0001_k089_256_int16.bin (кожен другий рядок і стовпець, 128 КБ, вантажиться одразу).
 * Частки вокселів рахуються з точної гістограми повної роздільності 512 × 512 у полі реконструкції.
 * Значення каналів для шести HU при вікнах −600/1600, 45/400, 400/1800 збігаються з другою таблицею виводу коду
 * (tools/gen_lec05_window.py --check).
 */
import { ref, shallowRef, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec05_window.json'

type Win = { name: string; c: number; w: number; on: boolean }
const [NY, NX] = data.shape as number[]
const hist = data.hist as number[]
const hLo = data.hist_lo as number
const nFov = data.n_fov as number
const PAD = data.pad as number
const PROBE = data.probe as number[]
const NAMES = ['повітря', 'легеня', 'жир', 'м’яз', 'контраст', 'кістка']
const COLORS = ['#e5484d', '#30a46c', '#3e63dd']
const CH = ['R', 'G', 'B']

const CHEST = (data.windows as { name: string; c: number; w: number }[]).map((w) => ({ ...w, on: true }))
const HEAD = [
  { name: 'мозкове', c: 40, w: 80, on: true },
  { name: 'субдуральне', c: 175, w: 50, on: true },
  { name: 'кісткове (голова)', c: 500, w: 3000, on: true },
]
const wins = ref<Win[]>(CHEST.map((w) => ({ ...w })))
const view = ref<'rgb' | 0 | 1 | 2>('rgb')
const slice = shallowRef<Int16Array | null>(null)
const status = ref<'loading' | 'ok' | 'error'>('loading')
const canvas = ref<HTMLCanvasElement | null>(null)
const hover = ref<{ hu: number; i: number; j: number } | null>(null)

const chan = (x: number, c: number, w: number) => Math.min(Math.max((x - (c - w / 2)) / w, 0), 1)
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const pct = (v: number) => (100 * v).toFixed(1).replace('.', ',') + ' %'

function setPreset(p: Win[]) {
  wins.value = p.map((w) => ({ ...w }))
}
const isChest = computed(() => wins.value.every((w, k) => w.c === CHEST[k].c && w.w === CHEST[k].w))
const isHead = computed(() => wins.value.every((w, k) => w.c === HEAD[k].c && w.w === HEAD[k].w))

/** Частки з гістограми повної роздільності: проміжні в кожному каналі і хоча б в одному увімкненому */
function fractions(ws: Win[]) {
  const per = ws.map(() => 0)
  let any = 0
  for (let n = 0; n < hist.length; n++) {
    if (!hist[n]) continue
    const hu = hLo + n
    let hit = false
    ws.forEach((w, k) => {
      const v = chan(hu, w.c, w.w)
      if (v > 0 && v < 1) {
        per[k] += hist[n]
        if (w.on) hit = true
      }
    })
    if (hit) any += hist[n]
  }
  return { per: per.map((p) => p / nFov), any: any / nFov }
}
const stats = computed(() => fractions(wins.value))
const head = fractions(HEAD)
const probeVals = computed(() => wins.value.map((w) => PROBE.map((p) => chan(p, w.c, w.w))))

function draw() {
  const cv = canvas.value
  const s = slice.value
  if (!cv || !s) return
  const ctx = cv.getContext('2d')
  if (!ctx) return
  const img = ctx.createImageData(NX, NY)
  const ws = wins.value
  for (let p = 0; p < NX * NY; p++) {
    const hu = s[p]
    const q = 4 * p
    if (hu <= PAD) {
      img.data[q] = img.data[q + 1] = img.data[q + 2] = 0
    } else if (view.value === 'rgb') {
      for (let k = 0; k < 3; k++) img.data[q + k] = ws[k].on ? Math.round(255 * chan(hu, ws[k].c, ws[k].w)) : 0
    } else {
      const w = ws[view.value]
      const g = Math.round(255 * chan(hu, w.c, w.w))
      img.data[q] = img.data[q + 1] = img.data[q + 2] = g
    }
    img.data[q + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
}

function toInt16(buf: ArrayBuffer): Int16Array {
  if (new Uint8Array(new Uint16Array([1]).buffer)[0] === 1) return new Int16Array(buf)
  const dv = new DataView(buf)
  const arr = new Int16Array(buf.byteLength / 2)
  for (let n = 0; n < arr.length; n++) arr[n] = dv.getInt16(2 * n, true)
  return arr
}
onMounted(async () => {
  try {
    const res = await fetch(withBase(data.bin as string))
    if (!res.ok) throw new Error(String(res.status))
    slice.value = toInt16(await res.arrayBuffer())
    status.value = 'ok'
  } catch {
    status.value = 'error'
  }
})
watch([slice, wins, view, canvas], draw, { deep: true, flush: 'post' })

function onMove(e: MouseEvent) {
  const cv = canvas.value
  const s = slice.value
  if (!cv || !s) return
  const r = cv.getBoundingClientRect()
  const i = Math.floor(((e.clientX - r.left) / r.width) * NX)
  const j = Math.floor(((e.clientY - r.top) / r.height) * NY)
  if (i < 0 || j < 0 || i >= NX || j >= NY) { hover.value = null; return }
  hover.value = { hu: s[j * NX + i], i: i * 2, j: j * 2 }
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Три вікна — три канали входу</div>
        <div class="lab__sub">
          Зріз LIDC-IDRI-0001 k = 89 (z = −117,5 мм). Кожен канал — вікно з центром c і шириною w: нижче c − w/2
          нуль, вище c + w/2 одиниця. Роздільність картинки знижено вдвічі; частки внизу — з гістограми повної
          роздільності 512 × 512.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" type="button" :class="{ 'is-on': isChest }" @click="setPreset(CHEST)">грудна клітка: −600/1600, 45/400, 400/1800</button>
      <button class="lab__pill" type="button" :class="{ 'is-on': isHead }" @click="setPreset(HEAD)">вікна КТ голови (Chilamkurthy et al.): 40/80, 175/50, 500/3000</button>
    </div>

    <div class="wc__chans">
      <div v-for="(w, k) in wins" :key="k" class="wc__chan" :style="{ borderColor: COLORS[k] }">
        <label class="wc__on"><input type="checkbox" v-model="w.on" /> <b :style="{ color: COLORS[k] }">{{ CH[k] }}</b> {{ w.name }}</label>
        <label class="lab__ctl"><span>центр <b>{{ num(w.c, 0) }}</b> HU</span>
          <input type="range" min="-1100" max="1200" step="5" v-model.number="w.c" /></label>
        <label class="lab__ctl"><span>ширина <b>{{ w.w }}</b> HU</span>
          <input type="range" min="10" max="3000" step="10" v-model.number="w.w" /></label>
        <div class="wc__frac">проміжних значень: {{ pct(stats.per[k]) }}</div>
      </div>
    </div>

    <div class="wc__grid">
      <div>
        <div class="lab__pills">
          <button class="lab__pill" type="button" :class="{ 'is-on': view === 'rgb' }" @click="view = 'rgb'">RGB разом</button>
          <button v-for="k in [0, 1, 2]" :key="k" class="lab__pill" type="button" :class="{ 'is-on': view === k }"
                  @click="view = k">лише {{ CH[k] }}</button>
        </div>
        <div class="wc__frame">
          <canvas ref="canvas" :width="NX" :height="NY" @mousemove="onMove" @mouseleave="hover = null"
                  aria-label="Зріз КТ у трьох вікнах"></canvas>
          <div v-if="status !== 'ok'" class="wc__status">{{ status === 'loading' ? 'завантаження зрізу…' : 'не вдалося завантажити зріз' }}</div>
        </div>
        <div class="wc__probe">
          <template v-if="hover && hover.hu > PAD">
            <b>{{ num(hover.hu, 0) }} HU</b> → R {{ num(chan(hover.hu, wins[0].c, wins[0].w)) }},
            G {{ num(chan(hover.hu, wins[1].c, wins[1].w)) }}, B {{ num(chan(hover.hu, wins[2].c, wins[2].w)) }};
            піксель (i, j) = ({{ hover.i }}, {{ hover.j }})
          </template>
          <span v-else class="wc__hint">наведіть курсор на зріз — з’являться HU і три значення каналів</span>
        </div>
      </div>
      <div>
        <div class="wc__table">
          <div class="wc__row wc__head"><span>тканина</span><span>HU</span><span v-for="k in [0, 1, 2]" :key="k" :style="{ color: COLORS[k] }">{{ CH[k] }}</span></div>
          <div v-for="(p, n) in PROBE" :key="p" class="wc__row">
            <span>{{ NAMES[n] }}</span><span>{{ num(p, 0) }}</span>
            <span v-for="k in [0, 1, 2]" :key="k">{{ num(probeVals[k][n]) }}</span>
          </div>
        </div>
        <div class="lab__stats">
          <div class="lab__stat"><b>{{ pct(stats.any) }}</b><span>вокселів поля мають проміжне значення хоча б в одному увімкненому каналі</span></div>
          <div class="lab__stat is-warm"><b>{{ pct(1 - stats.any) }}</b><span>насичені (0 або 1) в усіх увімкнених каналах</span></div>
        </div>
      </div>
    </div>

    <p class="lab__note">
      Вимкніть усі канали, крім одного: частка вокселів без жодного проміжного значення різко зростає — одне вікно
      втрачає решту діапазону. Увімкніть вікна КТ голови: вузькі мозкове і субдуральне на грудній клітці дають проміжні
      значення лише {{ pct(head.per[0]) }} і {{ pct(head.per[1]) }} вокселів поля, а широке кісткове 500/3000 охоплює
      −1000…2000 HU — тож разом {{ pct(head.any) }}, але майже всю інформацію несе один канал. Вікна задають під анатомію
      і задачу.
    </p>
  </div>
</template>

<style scoped>
.wc__chans { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 0.7rem; margin-bottom: 1rem; }
.wc__chan { border: 1px solid; border-left-width: 4px; border-radius: 8px; padding: 0.5rem 0.7rem; }
.wc__chan .lab__ctl { display: block; margin-top: 0.35rem; }
.wc__on { font-size: 0.82rem; color: var(--vp-c-text-2); cursor: pointer; }
.wc__frac { font-size: 0.75rem; color: var(--vp-c-text-3); margin-top: 0.3rem; }
.wc__grid { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: 1.1rem; align-items: start; }
@media (max-width: 760px) { .wc__grid { grid-template-columns: 1fr; } }
.wc__frame { position: relative; width: 100%; max-width: 420px; aspect-ratio: 1 / 1; background: #000; border-radius: 6px; overflow: hidden; }
.wc__frame canvas { width: 100%; height: 100%; display: block; cursor: crosshair; }
.wc__status { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #ddd; font-size: 0.8rem; background: rgba(0, 0, 0, 0.6); }
.wc__probe { font-size: 0.78rem; color: var(--vp-c-text-2); min-height: 2.8em; margin-top: 0.35rem; line-height: 1.45; }
.wc__probe b { font-family: var(--vp-font-family-mono); color: var(--uk-accent); font-weight: 500; }
.wc__hint { color: var(--vp-c-text-3); }
.wc__table { display: grid; gap: 0.1rem; font-size: 0.8rem; }
.wc__row { display: grid; grid-template-columns: 1.3fr 0.8fr repeat(3, 0.8fr); gap: 0.3rem; padding: 0.15rem 0.2rem; border-bottom: 1px dashed var(--uk-line); font-family: var(--vp-font-family-mono); }
.wc__row span:first-child { font-family: var(--vp-font-family-base); }
.wc__head { font-family: var(--vp-font-family-base); color: var(--vp-c-text-3); font-size: 0.74rem; }
</style>
