<script setup lang="ts">
/**
 * Grad-CAM трьох шарів моделі S2 (лекція 16, розділ «Роздільність карти і вибір шару»).
 * Дані — tools/gen_lec16_gradcam.py: для 12 знімків Montgomery (по три з рішеннями TP, FP, FN, TN)
 * сітки Grad-CAM layer2 (16 × 16), layer3 (8 × 8), layer4 (4 × 4), кожна нормована на свій максимум;
 * частки маси збільшеної карти в легенях (ручна маска), решті кадру і полях доповнення; контур маски і
 * кадр знімка. Знімків NLM у віджеті немає — лише карта на темному тлі й контури.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec16_gradcam.json'

type Item = {
  file: string; out: string; p: number
  grids: Record<string, number[][]>; empty: Record<string, boolean>
  share: Record<string, Record<string, number> | null>
  lung: number[][][]; frame: number[]
}
const ITEMS = data.items as Item[]
const LAYERS = data.layers as string[]
const T = data.t as number
const OUTS = ['TP', 'FP', 'FN', 'TN']
const OUT_UA: Record<string, string> = { TP: 'туберкульоз знайдено', FP: 'хибна тривога', FN: 'туберкульоз пропущено', TN: 'норма, правильно' }

const layer = ref('layer3')
const outc = ref('TP')
const k = ref(1)

const list = computed(() => ITEMS.filter(it => it.out === outc.value))
const item = computed(() => list.value[Math.min(k.value, list.value.length - 1)])
const grid = computed(() => item.value.grids[layer.value])
const cell = computed(() => 128 / grid.value.length)
const share = computed(() => item.value.share[layer.value])

const STOPS = ['#000004', '#320a5e', '#781c6d', '#bc3754', '#ed6925', '#fbb61a', '#fcffa4']
function heat(v: number) {
  const x = Math.min(0.9999, Math.max(0, v)) * (STOPS.length - 1)
  const i = Math.floor(x), f = x - i
  const a = STOPS[i], b = STOPS[i + 1]
  const ch = (s: string, j: number) => parseInt(s.slice(1 + 2 * j, 3 + 2 * j), 16)
  return `rgb(${[0, 1, 2].map(j => Math.round(ch(a, j) + (ch(b, j) - ch(a, j)) * f)).join(',')})`
}
const path = (c: number[][]) => c.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join(' ') + ' Z'
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Grad-CAM трьох шарів на знімках Montgomery</div>
        <div class="lab__sub">
          Карта класу «туберкульоз» у рідній сітці шару на темному тлі; білий контур — ручна маска легень, сірі смуги —
          поля доповнення до квадрата. Поріг рішення t = {{ num(T, 4) }}.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="l in LAYERS" :key="l" type="button" class="lab__pill" :class="{ 'is-on': layer === l }"
              @click="layer = l">{{ l }} ({{ item.grids[l].length }} × {{ item.grids[l].length }})</button>
    </div>
    <div class="lab__pills">
      <button v-for="o in OUTS" :key="o" type="button" class="lab__pill" :class="{ 'is-on': outc === o }"
              @click="outc = o; k = 1">{{ o }} — {{ OUT_UA[o] }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>знімок {{ Math.min(k, list.length - 1) + 1 }} з {{ list.length }}: <b>{{ item.file }}</b>, p = {{ num(item.p) }}</span>
        <input v-model.number="k" type="range" min="0" :max="list.length - 1" step="1" aria-label="Знімок">
      </label>
    </div>

    <svg viewBox="0 0 128 128" class="gl__svg" role="img" aria-label="Карта Grad-CAM, контур легень і поля доповнення">
      <rect x="0" y="0" width="128" height="128" fill="#2a2a2a" />
      <g v-for="(row, r) in grid" :key="'r' + r">
        <rect v-for="(v, c) in row" :key="'c' + c" :x="c * cell" :y="r * cell" :width="cell" :height="cell"
              :fill="heat(v)" opacity="0.9" />
      </g>
      <rect x="0" y="0" :width="item.frame[0]" height="128" fill="#888" opacity="0.6" />
      <rect :x="item.frame[2]" y="0" :width="128 - item.frame[2]" height="128" fill="#888" opacity="0.6" />
      <rect x="0" y="0" width="128" :height="item.frame[1]" fill="#888" opacity="0.6" />
      <rect x="0" :y="item.frame[3]" width="128" :height="128 - item.frame[3]" fill="#888" opacity="0.6" />
      <path v-for="(c, i) in item.lung" :key="'l' + i" :d="path(c)" fill="none" stroke="#fff" stroke-width="0.9" />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat" :class="{ 'is-warm': item.empty[layer] }">
        <b>{{ item.empty[layer] ? 'порожня' : 'є' }}</b><span>карта {{ layer }}</span></div>
      <template v-if="share">
        <div class="lab__stat"><b>{{ num(share['легені']) }}</b><span>частка маси в легенях</span></div>
        <div class="lab__stat"><b>{{ num(share['кадр']) }}</b><span>у решті кадру</span></div>
        <div class="lab__stat"><b>{{ num(share['поля']) }}</b><span>у полях доповнення</span></div>
      </template>
    </div>

    <p class="lab__note">
      Карта layer4 порожня, коли жодна з 16 клітинок не має додатного внеску в логіт: так буває лише при логіті, нижчому
      за зсув голови, — на Montgomery в усіх рішеннях «норма» (FN, TN) і в частині хибних тривог (FP). Частку маси в
      легенях варто порівнювати з часткою площі легень у кадрі — близько п’ятої частини.
    </p>
  </div>
</template>

<style scoped>
.gl__svg { width: 100%; max-width: 380px; height: auto; display: block; margin: 0.5rem auto; }
</style>
