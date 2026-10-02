<script setup lang="ts">
/**
 * Пригнічення немаксимумів на виході детектора (лекція 09, розділ «Безякірні детектори: YOLO, FCOS, YOLOv8»).
 * Дані — tools/gen_lec09_nms.py: сирі рамки YOLOv8n (ваги з блоку коду лекції) з упевненістю від 0,01 на двох
 * валідаційних кадрах HyperKvasir (CC BY 4.0) і, для сітки порогів упевненості та IoU, рамки після жадібного
 * NMS разом із TP/FP при зіставленні з еталоном за IoU ≥ 0,5. Генератор звіряє своє NMS з torchvision, а вузол
 * «0,25 / 0,7» — з predict ultralytics за замовчуванням.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec09_nms.json'

type G = { keep: number[], tp: number, fp: number, n: number }
type F = { id: string, image: string, w: number, h: number, boxes: number[][], conf: number[], gt: number[][], grid: Record<string, G> }
const FR = data.frames as F[]
const CONFS = data.confs as number[]
const IOUS = data.ious as number[]

const fi = ref(0)
const ci = ref(CONFS.indexOf(0.25))
const ii = ref(IOUS.indexOf(0.7))
const showAll = ref(true)
const f = computed(() => FR[fi.value])
const cell = computed(() => f.value.grid[`${CONFS[ci.value]}|${IOUS[ii.value]}`])
const kept = computed(() => new Set(cell.value.keep))
const above = computed(() => f.value.boxes.map((b, i) => ({ b, i, c: f.value.conf[i] })).filter(x => x.c >= CONFS[ci.value]))
const num = (v: number, d = 2) => v.toFixed(d).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">NMS на виході YOLOv8n: пороги впевненості й IoU</div>
        <div class="lab__sub">
          Сирі рамки детектора на валідаційному кадрі HyperKvasir (CC BY 4.0): блакитні — залишені після NMS, сірі —
          пригнічені, жовті — еталон.
        </div>
      </div>
    </div>
    <div class="lab__pills">
      <button v-for="(x, k) in FR" :key="x.id" type="button" class="lab__pill" :class="{ 'is-on': fi === k }" @click="fi = k">
        кадр {{ k + 1 }}: поліпів {{ x.gt.length }}
      </button>
      <button type="button" class="lab__pill" :class="{ 'is-on': showAll }" @click="showAll = !showAll">показати пригнічені</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl"><span>поріг упевненості: <b>{{ num(CONFS[ci]) }}</b></span>
        <input v-model.number="ci" type="range" min="0" :max="CONFS.length - 1" step="1" aria-label="Поріг упевненості"></label>
      <label class="lab__ctl"><span>поріг IoU для NMS: <b>{{ num(IOUS[ii]) }}</b></span>
        <input v-model.number="ii" type="range" min="0" :max="IOUS.length - 1" step="1" aria-label="Поріг IoU"></label>
    </div>

    <svg :viewBox="`0 0 ${f.w} ${f.h}`" class="nms__svg" role="img" aria-label="Кадр з рамками детектора до і після NMS">
      <image :href="withBase(f.image)" x="0" y="0" :width="f.w" :height="f.h" />
      <template v-if="showAll">
        <rect v-for="x in above.filter(x => !kept.has(x.i))" :key="'s' + x.i" :x="x.b[0]" :y="x.b[1]" :width="x.b[2] - x.b[0]"
          :height="x.b[3] - x.b[1]" fill="none" stroke="#d0d0d0" stroke-width="0.7" opacity="0.6" />
      </template>
      <rect v-for="(b, i) in f.gt" :key="'g' + i" :x="b[0]" :y="b[1]" :width="b[2] - b[0]" :height="b[3] - b[1]"
        fill="none" stroke="#FFCC33" stroke-width="2" />
      <g v-for="i in cell.keep" :key="'k' + i">
        <rect :x="f.boxes[i][0]" :y="f.boxes[i][1]" :width="f.boxes[i][2] - f.boxes[i][0]" :height="f.boxes[i][3] - f.boxes[i][1]"
          fill="none" stroke="#33C3FF" stroke-width="1.8" stroke-dasharray="5 3" />
        <text :x="f.boxes[i][0] + 3" :y="f.boxes[i][1] + 11" class="nms__txt">{{ num(f.conf[i]) }}</text>
      </g>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ cell.n }}</b><span>рамок вище порогу впевненості</span></div>
      <div class="lab__stat is-warm"><b>{{ cell.keep.length }}</b><span>залишилося після NMS</span></div>
      <div class="lab__stat is-green"><b>{{ cell.tp }}</b><span>TP (IoU з еталоном ≥ 0,5)</span></div>
      <div class="lab__stat"><b>{{ cell.fp }}</b><span>FP, зокрема дублікати</span></div>
    </div>
    <p class="lab__note">
      На першому кадрі при впевненості 0,25 одна рамка лишається аж до порогу IoU 0,85; за 0,9 з’являється дублікат,
      за 0,95 — ще кілька, і кожен з них — хибне спрацювання. При впевненості 0,01 і порозі 0,95 лишається понад
      два десятки рамок. На кадрі з двома поліпами їхні рамки майже не перекриваються, тож навіть поріг 0,3 зберігає
      обидві; якби поліпи стояли впритул, низький поріг прибрав би рамку сусіда.
    </p>
  </div>
</template>

<style scoped>
.nms__svg { width: 100%; max-width: 480px; height: auto; display: block; margin: 0.5rem auto; }
.nms__txt { fill: #ffffff; font-size: 9px; paint-order: stroke; stroke: #000; stroke-width: 2px; }
</style>
