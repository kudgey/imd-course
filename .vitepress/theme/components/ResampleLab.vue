<script setup lang="ts">
/**
 * Ресемплінг маски легень LUNA16 (LIDC-IDRI-0001) на сітки 1; 1,5 і 2 мм п’ятьма схемами —
 * тими самими, що в блоці коду розділу «Маски інтерполюють лише найближчим сусідом».
 * Усі числа (об’єм легень, Dice з найближчим сусідом, кількість значень, воксели поза мітками) і
 * фрагменти 80 × 80 мм на рівні z = −65 мм пораховано генератором tools/gen_lec05_resample.py;
 * для сітки 1 мм генератор звіряє їх із таблицею виводу коду: найближчий сусід 3774,8 мл;
 * лінійна + округлення 3705,6 мл, Dice 0,9890, 6 значень, 191 334 воксели поза мітками;
 * one-hot + argmax і поріг 0,5 — 3774,4 мл, Dice 0,9967; без порогу 3943,1 мл, 7408 значень.
 * Об’єм вокселів поза мітками (лінійна + округлення): 191,3 / 192,1 / 191,0 мл на сітках 1 / 1,5 / 2 мм —
 * облямівка завтовшки у воксель, тож на грубшій сітці вокселів менше, а об’єм той самий.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec05_resample.json'

type Row = { step: number; scheme: string; name: string; ml: number; dice: number; values: number; outside: number; outside_ml: number; png: string }
const rows = data.rows as Row[]
const steps = data.steps as number[]
const schemes = data.schemes as { key: string; name: string }[]
const vol0 = data.vol0_ml as number

const step = ref(1)
const scheme = ref('round')
const row = computed(() => rows.find((r) => r.step === step.value && r.scheme === scheme.value) as Row)
const atStep = computed(() => schemes.map((s) => rows.find((r) => r.step === step.value && r.scheme === s.key) as Row))

const at1 = (key: string) => rows.find((r) => r.step === 1 && r.scheme === key) as Row
const at2 = (key: string) => rows.find((r) => r.step === 2 && r.scheme === key) as Row
const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const spaced = (v: number) => String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
const isBinary = computed(() => scheme.value === 'thr' || scheme.value === 'raw')

const SHORT: Record<string, string> = {
  near: 'мітки: найближчий',
  round: 'мітки: лінійна + округлення',
  onehot: 'мітки: one-hot + argmax',
  thr: 'легені: поріг 0,5',
  raw: 'легені: без порогу',
}
const LEGEND = [
  { c: '#2A78D6', t: '3 — ліва легеня' },
  { c: '#EB6834', t: '4 — права легеня' },
  { c: '#1BAF7A', t: '5 — трахея' },
  { c: '#E87BA4', t: '1 — мітки немає' },
  { c: '#EDA100', t: '2 — мітки немає' },
]

/* Горизонтальні смуги: об’єм легень для п’яти схем на вибраній сітці */
const W = 360
const H = 150
const L = 132
const minMl = 3650
const maxMl = 3980
const sx = (ml: number) => L + ((ml - minMl) / (maxMl - minMl)) * (W - L - 12)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Маска легень на новій сітці: п’ять схем інтерполяції</div>
        <div class="lab__sub">
          Маска LUNA16 для LIDC-IDRI-0001 з мітками 0, 3, 4, 5 і бінарна маска обох легень, перенесені з сітки
          0,703 × 0,703 × 2,5 мм на ізотропну. Фрагмент — 80 × 80 мм на рівні z = −65 мм, де трахея проходить
          між легенями; кожен квадрат — один воксель.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <span class="rs__lbl">крок сітки:</span>
      <button v-for="s in steps" :key="s" class="lab__pill" type="button" :class="{ 'is-on': step === s }"
              @click="step = s">{{ num(s, s === 1.5 ? 1 : 0) }} мм</button>
    </div>
    <div class="lab__pills">
      <button v-for="s in schemes" :key="s.key" class="lab__pill" type="button" :class="{ 'is-on': scheme === s.key }"
              @click="scheme = s.key">{{ s.name }}</button>
    </div>

    <div class="rs__grid">
      <figure class="rs__fig">
        <img :src="withBase(data.orig_png as string)" alt="Фрагмент маски на вихідній сітці" />
        <figcaption>вихідна сітка, 0,703 мм у площині</figcaption>
      </figure>
      <figure class="rs__fig">
        <img :src="withBase(row.png)" :alt="`Фрагмент маски: ${row.name}, ${step} мм`" />
        <figcaption>{{ row.name }}, {{ num(step, step === 1.5 ? 1 : 0) }} мм</figcaption>
      </figure>
    </div>

    <div class="rs__legend">
      <template v-if="!isBinary">
        <span v-for="l in LEGEND" :key="l.t"><i :style="{ background: l.c }"></i>{{ l.t }}</span>
      </template>
      <span v-else>бінарна маска обох легень: білий — 1, чорний — 0, сірі — дробові значення лінійної інтерполяції</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(row.ml) }}</b><span>мл обох легень (вихідна сітка {{ num(vol0) }})</span></div>
      <div class="lab__stat"><b>{{ num(row.dice, 4) }}</b><span>Dice з найближчим сусідом на тій самій сітці</span></div>
      <div class="lab__stat" :class="{ 'is-warm': row.values > (isBinary ? 2 : 4) }"><b>{{ spaced(row.values) }}</b>
        <span>різних значень у масці (допустимо {{ isBinary ? 2 : 4 }})</span></div>
      <div class="lab__stat" :class="{ 'is-warm': row.outside > 0 }"><b>{{ spaced(row.outside) }}</b>
        <span>вокселів зі значенням, якого не було ({{ num(row.outside_ml) }} мл)</span></div>
    </div>

    <svg class="rs__bars" :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Об’єм легень за схемами">
      <line :x1="sx(vol0)" :x2="sx(vol0)" y1="4" :y2="H - 18" class="rs__ref" />
      <text :x="sx(vol0)" :y="H - 6" text-anchor="middle" class="rs__tick">{{ num(vol0) }} мл — вихідна сітка</text>
      <g v-for="(r, k) in atStep" :key="r.scheme">
        <text :x="L - 6" :y="12 + k * 24 + 10" text-anchor="end" class="rs__tick">{{ SHORT[r.scheme] }}</text>
        <rect :x="L" :y="12 + k * 24" :width="Math.max(sx(r.ml) - L, 1)" height="15"
              :class="['rs__bar', { 'is-on': r.scheme === scheme, 'is-bad': Math.abs(r.ml - vol0) > 20 }]" />
        <text :x="sx(r.ml) + 4" :y="12 + k * 24 + 11" class="rs__tick">{{ num(r.ml) }}</text>
      </g>
    </svg>

    <p class="lab__note">
      На сітці 1 мм найближчий сусід зберігає об’єм ({{ num(at1('near').ml) }} мл проти {{ num(vol0) }}) і чотири
      мітки; лінійна інтерполяція міток з округленням обводить кожну структуру облямівкою з міток 1 і 2 та вокселями
      чужої легені, а бінарна маска без порогу «додає» легеням {{ num(at1('raw').ml - at1('near').ml) }} мл. Перемкніть крок на 2 мм: вокселів поза мітками
      стає менше ({{ spaced(at1('round').outside) }} → {{ spaced(at2('round').outside) }}), але їхній об’єм майже той самий
      ({{ num(at1('round').outside_ml) }} і {{ num(at2('round').outside_ml) }} мл) — облямівка завтовшки у воксель просто
      стала вдвічі товщою в міліметрах. One-hot з argmax і поріг 0,5 і далі повторюють найближчого сусіда.
    </p>
  </div>
</template>

<style scoped>
.rs__lbl { font-size: 0.78rem; color: var(--vp-c-text-3); align-self: center; margin-right: 0.2rem; }
.rs__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8rem; max-width: 560px; }
.rs__fig { margin: 0; }
.rs__fig img {
  width: 100%;
  aspect-ratio: 1 / 1;
  image-rendering: pixelated;
  border-radius: 6px;
  background: #101010;
  display: block;
}
.rs__fig figcaption { font-size: 0.75rem; color: var(--vp-c-text-3); margin-top: 0.3rem; line-height: 1.35; }
.rs__legend { display: flex; flex-wrap: wrap; gap: 0.4rem 0.9rem; font-size: 0.75rem; color: var(--vp-c-text-2); margin: 0.6rem 0 0.2rem; }
.rs__legend i { display: inline-block; width: 0.75rem; height: 0.75rem; border-radius: 2px; margin-right: 0.3rem; vertical-align: -1px; }
.rs__bars { width: 100%; max-width: 560px; height: auto; display: block; margin-top: 0.8rem; }
.rs__bar { fill: var(--uk-accent); opacity: 0.35; }
.rs__bar.is-on { opacity: 0.9; }
.rs__bar.is-bad { fill: var(--uk-warm); }
.rs__ref { stroke: var(--vp-c-text-2); stroke-dasharray: 3 3; stroke-width: 1; }
.rs__tick { fill: var(--vp-c-text-2); font-size: 9.5px; }
</style>
