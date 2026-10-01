<script setup lang="ts">
/**
 * CLAHE на рентгенограмі NIH ChestX-ray14 00000511_000 (PA, «No Finding»; NIH Clinical Center, використання без
 * обмежень із цитуванням Wang et al., 2017), зменшеній до 256 × 256: вихідний знімок, глобальне вирівнювання
 * гістограми і CLAHE (skimage.exposure.equalize_adapthist, плитка 1/8 кадру) при семи значеннях clip limit.
 * Кадри PNG і показники пораховано генератором tools/gen_lec05_clahe.py на цьому самому знімку: контраст у легенях
 * (середнє СКО у вікні 7 × 7 у двох прямокутниках легеневих полів), шум у печінці (СКО різниці зі знімком після
 * медіанного фільтра 3 × 3 у прямокутнику під правим куполом діафрагми), різниця середніх рівнів легень і печінки.
 * Прямокутники показано поверх кадру. Медіани тих самих відношень на 247 сирих знімках JSRT (miniJSRT; на сайті не
 * показуються) — у тексті розділу. Кадри вантажаться по одному, коли повзунок до них доходить (≈ 30–45 КБ кожен).
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec05_clahe.json'

type V = { key: string; label: string; clip: number | null; contrast: number; noise: number; diff: number; hist: number[]; png: string }
const variants = data.variants as V[]
const lungBoxes = data.lung_boxes as number[][]
const liverBox = data.liver_box as number[]
const idx = ref(0)
const v = computed(() => variants[idx.value])
const base = variants[0]
const he = variants[1]
const clahe = variants.filter((x) => x.clip !== null)

const num = (x: number, d = 4) => x.toFixed(d).replace('.', ',').replace('-', '−')
const ratio = (x: number, b: number) => '×' + (x / b).toFixed(2).replace('.', ',')

/* Гістограма рівнів (32 кошики по 8 рівнів) */
const HW = 300
const HH = 110
const hmax = computed(() => Math.max(...v.value.hist))
/* Контраст і шум відносно вихідного знімка для всіх clip limit */
const CW = 300
const CHt = 130
const PL = 30
const xs = (k: number) => PL + (k / (clahe.length - 1)) * (CW - PL - 10)
const ymax = Math.max(...clahe.map((x) => x.noise / base.noise), ...clahe.map((x) => x.contrast / base.contrast))
const ys = (r: number) => CHt - 20 - (r / ymax) * (CHt - 32)
const line = (f: (x: V) => number) => clahe.map((x, k) => `${xs(k).toFixed(1)},${ys(f(x)).toFixed(1)}`).join(' ')
const pathC = line((x) => x.contrast / base.contrast)
const pathN = line((x) => x.noise / base.noise)
const curK = computed(() => clahe.findIndex((x) => x.key === v.value.key))
const c003 = variants.find((x) => x.key === 'c003') as V
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">CLAHE: скільки контрасту і скільки шуму</div>
        <div class="lab__sub">
          Рентгенограма NIH ChestX-ray14 00000511_000, зменшена до 256 × 256. Повзунок перебирає вихідний знімок,
          глобальне вирівнювання гістограми і CLAHE з clip limit від 0,002 до 0,1 (плитка — 1/8 кадру). Жовті
          прямокутники — легеневі поля, блакитний — печінка під правим куполом діафрагми: у них рахуються показники.
        </div>
      </div>
    </div>

    <label class="lab__ctl cl__slider">
      <span>варіант: <b>{{ v.label }}</b></span>
      <input type="range" min="0" :max="variants.length - 1" step="1" v-model.number="idx" />
    </label>

    <div class="cl__grid">
      <div class="cl__frame">
        <img :src="withBase(v.png)" :alt="`Рентгенограма NIH: ${v.label}`" />
        <svg viewBox="0 0 256 256" class="cl__ov" aria-hidden="true">
          <rect v-for="(b, k) in lungBoxes" :key="k" :x="b[2]" :y="b[0]" :width="b[3] - b[2]" :height="b[1] - b[0]" class="cl__box" />
          <rect :x="liverBox[2]" :y="liverBox[0]" :width="liverBox[3] - liverBox[2]" :height="liverBox[1] - liverBox[0]" class="cl__box cl__box--h" />
        </svg>
      </div>
      <div>
        <div class="cl__cap">Гістограма рівнів сірого, 32 кошики</div>
        <svg :viewBox="`0 0 ${HW} ${HH}`" class="cl__svg" role="img" aria-label="Гістограма рівнів">
          <rect v-for="(c, k) in v.hist" :key="k" :x="6 + k * ((HW - 12) / 32)" :y="HH - 14 - (c / hmax) * (HH - 22)"
                :width="(HW - 12) / 32 - 1" :height="(c / hmax) * (HH - 22)" class="cl__bar" />
          <text x="6" :y="HH - 2" class="cl__lbl">0</text>
          <text :x="HW - 6" :y="HH - 2" text-anchor="end" class="cl__lbl">255</text>
        </svg>
        <div class="cl__cap">Контраст у легенях (синя) і шум у печінці (помаранчева) відносно вихідного знімка, CLAHE</div>
        <svg :viewBox="`0 0 ${CW} ${CHt}`" class="cl__svg" role="img" aria-label="Контраст і шум залежно від clip limit">
          <line :x1="PL" :x2="CW - 10" :y1="ys(1)" :y2="ys(1)" class="cl__ref" />
          <text :x="PL - 4" :y="ys(1) + 3" text-anchor="end" class="cl__lbl">×1</text>
          <polyline :points="pathC" class="cl__c" />
          <polyline :points="pathN" class="cl__n" />
          <template v-if="curK >= 0">
            <circle :cx="xs(curK)" :cy="ys(clahe[curK].contrast / base.contrast)" r="3.5" class="cl__dc" />
            <circle :cx="xs(curK)" :cy="ys(clahe[curK].noise / base.noise)" r="3.5" class="cl__dn" />
          </template>
          <text v-for="(x, k) in clahe" :key="x.key" :x="xs(k)" :y="CHt - 6" text-anchor="middle" class="cl__lbl">
            {{ String(x.clip).replace('.', ',') }}</text>
        </svg>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(v.contrast) }}</b><span>контраст у легенях ({{ ratio(v.contrast, base.contrast) }} до вихідного)</span></div>
      <div class="lab__stat is-warm"><b>{{ num(v.noise) }}</b><span>шум у печінці ({{ ratio(v.noise, base.noise) }})</span></div>
      <div class="lab__stat is-green"><b>{{ num(v.diff, 3) }}</b><span>легені − печінка, середні рівні</span></div>
    </div>

    <p class="lab__note">
      При clip limit 0,03 контраст у легенях зростає в {{ ratio(c003.contrast, base.contrast).slice(1) }} раза, а шум у
      печінці — в {{ ratio(c003.noise, base.noise).slice(1) }}; різниця середніх рівнів легень і печінки за модулем
      зменшується з {{ num(Math.abs(base.diff), 3) }} до {{ num(Math.abs(c003.diff), 3) }} — CLAHE вирівнює яскравість
      великих структур. Глобальне вирівнювання на цьому знімку дає контраст {{ ratio(he.contrast, base.contrast) }} при шумі
      {{ ratio(he.noise, base.noise) }}, але робить легені ще темнішими відносно печінки.
    </p>
  </div>
</template>

<style scoped>
.cl__slider { display: block; max-width: 520px; margin-bottom: 0.9rem; }
.cl__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
@media (max-width: 720px) { .cl__grid { grid-template-columns: 1fr; } }
.cl__frame { position: relative; width: 100%; max-width: 380px; aspect-ratio: 1 / 1; background: #000; border-radius: 6px; overflow: hidden; }
.cl__frame img, .cl__ov { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.cl__box { fill: none; stroke: #ffcc33; stroke-width: 1.2; }
.cl__box--h { stroke: #33c3ff; }
.cl__svg { width: 100%; max-width: 360px; height: auto; display: block; }
.cl__cap { font-size: 0.75rem; color: var(--vp-c-text-3); margin: 0.2rem 0 0.3rem; line-height: 1.35; }
.cl__bar { fill: var(--uk-accent); opacity: 0.6; }
.cl__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.cl__ref { stroke: var(--uk-line); stroke-dasharray: 3 3; }
.cl__c { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
.cl__n { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.cl__dc { fill: var(--uk-accent); }
.cl__dn { fill: var(--uk-warm); }
</style>
