<script setup lang="ts">
/**
 * IoU двох рамок (лекція 09, розділ «Рамка, IoU і зіставлення знахідок»). Дані — tools/gen_lec09_iou.py:
 * кадр HyperKvasir (CC BY 4.0), рамка еталону з bounding-boxes.json і найупевненіше передбачення YOLOv8n,
 * навченого в блоці коду лекції, у координатах кадру шириною 320 px. Без зсуву IoU дорівнює значенню
 * генератора; далі віджет рахує IoU = перетин / об’єднання тією самою формулою.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec09_iou.json'

const W = data.w as number, H = data.h as number
const GT = data.gt as number[]
const CONF = data.conf as number
const IMG = data.image as string
const P0 = data.pred as number[]
const dx = ref(0), dy = ref(0), sc = ref(100)

const pred = computed(() => {
  const cx = (P0[0] + P0[2]) / 2 + dx.value, cy = (P0[1] + P0[3]) / 2 + dy.value
  const w = (P0[2] - P0[0]) * sc.value / 100, h = (P0[3] - P0[1]) * sc.value / 100
  return [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
})
const parts = computed(() => {
  const p = pred.value
  const iw = Math.max(0, Math.min(GT[2], p[2]) - Math.max(GT[0], p[0]))
  const ih = Math.max(0, Math.min(GT[3], p[3]) - Math.max(GT[1], p[1]))
  const inter = iw * ih
  const union = (GT[2] - GT[0]) * (GT[3] - GT[1]) + (p[2] - p[0]) * (p[3] - p[1]) - inter
  return { inter, union, iou: inter / union, ix: [Math.max(GT[0], p[0]), Math.max(GT[1], p[1]), iw, ih] }
})
const num = (v: number, d = 2) => v.toFixed(d).replace('.', ',')
const big = (v: number) => Math.round(v).toLocaleString('uk-UA').replace(/\s/g, ' ')
const reset = () => { dx.value = 0; dy.value = 0; sc.value = 100 }
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">IoU: рамка еталону і рамка детектора</div>
        <div class="lab__sub">
          Кадр HyperKvasir (CC BY 4.0, ширина 320 px): жовта — еталон, блакитна пунктирна — передбачення YOLOv8n з
          упевненістю {{ num(CONF, 2) }}; заштриховано перетин.
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl"><span>зсув по x: <b>{{ dx }} px</b></span>
        <input v-model.number="dx" type="range" min="-80" max="80" step="1" aria-label="Зсув передбаченої рамки по x"></label>
      <label class="lab__ctl"><span>зсув по y: <b>{{ dy }} px</b></span>
        <input v-model.number="dy" type="range" min="-80" max="80" step="1" aria-label="Зсув передбаченої рамки по y"></label>
      <label class="lab__ctl"><span>масштаб: <b>{{ sc }} %</b></span>
        <input v-model.number="sc" type="range" min="40" max="220" step="2" aria-label="Масштаб передбаченої рамки"></label>
      <div class="lab__ctl"><span>&nbsp;</span><button type="button" class="lab__btn" @click="reset">справжнє передбачення</button></div>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="iou__svg" role="img" aria-label="Кадр з рамкою еталону і передбаченою рамкою">
      <image :href="withBase(IMG)" x="0" y="0" :width="W" :height="H" />
      <rect :x="parts.ix[0]" :y="parts.ix[1]" :width="parts.ix[2]" :height="parts.ix[3]" fill="#33C3FF" opacity="0.35" />
      <rect :x="GT[0]" :y="GT[1]" :width="GT[2] - GT[0]" :height="GT[3] - GT[1]" fill="none" stroke="#000" stroke-width="3.2" opacity="0.5" />
      <rect :x="GT[0]" :y="GT[1]" :width="GT[2] - GT[0]" :height="GT[3] - GT[1]" fill="none" stroke="#FFCC33" stroke-width="1.8" />
      <rect :x="pred[0]" :y="pred[1]" :width="pred[2] - pred[0]" :height="pred[3] - pred[1]" fill="none" stroke="#33C3FF" stroke-width="1.8" stroke-dasharray="5 3" />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ big(parts.inter) }}</b><span>перетин, px²</span></div>
      <div class="lab__stat"><b>{{ big(parts.union) }}</b><span>об’єднання, px²</span></div>
      <div class="lab__stat is-warm"><b>{{ num(parts.iou, 3) }}</b><span>IoU = перетин / об’єднання</span></div>
      <div v-for="t in [0.5, 0.3, 0.1]" :key="t" class="lab__stat" :class="{ 'is-green': parts.iou >= t }">
        <b>{{ parts.iou >= t ? 'TP' : 'FP' }}</b><span>при τ = {{ num(t, 1) }}</span>
      </div>
    </div>
    <p class="lab__note">
      Поліп великий, тож зсув на кілька пікселів мало змінює IoU. Для рамки консенсусу на рентгенограмі з меншою
      стороною 16–20 px у копії 256 px той самий абсолютний зсув коштував би значно більше.
    </p>
  </div>
</template>

<style scoped>
.iou__svg { width: 100%; max-width: 480px; height: auto; display: block; margin: 0.5rem auto; }
</style>
