<script setup lang="ts">
/**
 * Каскадна рандомізація ваг (лекція 16, розділ «Перевірка каскадною рандомізацією ваг»).
 * Дані — tools/gen_lec16_sanity.py: модель S2, карти Grad-CAM layer3 (сітка 8 × 8), градієнт і
 * градієнт × вхід для навченої моделі і після шести стадій рандомізації (fc → … → conv1), для
 * чотирьох рентгенограм NIH ChestX-ray14 (чужий для моделі домен; знімків NLM у віджеті немає).
 * ρ Спірмена і SSIM — подібність до карти навченої моделі; медіани за 12 знімками тесту Shenzhen
 * — з виводу блоку коду (генератор звіряє їх). Картинки 128 px вантажаться лише для вибраного стану.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec16_sanity.json'

type Pair = { spearman: (number | null)[][]; ssim: (number | null)[][] }
const STAGES = data.stages as string[]
const METHODS = data.methods as string[]
const NIH = data.nih as string[]
const BLOCK = data.block as Record<string, { spearman: number[]; ssim: number[] }>
const PER = data.nih_metrics as Record<string, Pair>
const GRID = data.gradcam as number[][][][]
const NB = data.n_block as number

const img = ref(0)
const method = ref(0)
const stage = ref(0)

const STOPS = ['#000004', '#320a5e', '#781c6d', '#bc3754', '#ed6925', '#fbb61a', '#fcffa4']
function heat(v: number) {
  const x = Math.min(0.9999, Math.max(0, v)) * (STOPS.length - 1)
  const i = Math.floor(x), f = x - i
  const a = STOPS[i], b = STOPS[i + 1]
  const ch = (s: string, k: number) => parseInt(s.slice(1 + 2 * k, 3 + 2 * k), 16)
  return `rgb(${[0, 1, 2].map(k => Math.round(ch(a, k) + (ch(b, k) - ch(a, k)) * f)).join(',')})`
}

const grid = computed(() => GRID[stage.value][img.value])
const salSrc = computed(() => withBase(`/data/lec16/sal_${NIH[img.value]}_m${method.value}_s${stage.value}.webp`))
const nihSrc = computed(() => withBase(`/data/lec16/nih_${NIH[img.value]}.webp`))
const mine = computed(() => {
  const k = METHODS[method.value]
  return { r: PER[k].spearman[stage.value][img.value], s: PER[k].ssim[stage.value][img.value] }
})
const block = computed(() => stage.value === 0 ? null
  : { r: BLOCK[METHODS[method.value]].spearman[stage.value - 1], s: BLOCK[METHODS[method.value]].ssim[stage.value - 1] })
const num = (v: number | null, d = 3) => v === null ? '—' : v.toFixed(d).replace('.', ',').replace('-', '−')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Каскадна рандомізація ваг моделі S2</div>
        <div class="lab__sub">
          Повзунок замінює навчені ваги випадковими, починаючи з голови fc; у підписі — до якого шару включно.
          Ліворуч — рентгенограма NIH ChestX-ray14 (чужий для моделі домен), праворуч — карта поверх неї.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(n, i) in NIH" :key="n" type="button" class="lab__pill" :class="{ 'is-on': img === i }"
              @click="img = i">NIH {{ n }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="(m, i) in METHODS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': method === i }"
              @click="method = i">{{ m }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>стадія: <b>{{ STAGES[stage] }}</b></span>
        <input v-model.number="stage" type="range" min="0" :max="STAGES.length - 1" step="1" aria-label="Стадія рандомізації">
      </label>
    </div>

    <div class="cs__row">
      <figure class="cs__fig">
        <img :src="nihSrc" alt="Рентгенограма NIH ChestX-ray14, 128 px" width="128" height="128" loading="lazy">
        <figcaption>знімок, 128 px</figcaption>
      </figure>
      <figure class="cs__fig cs__stack">
        <img :src="nihSrc" alt="" width="128" height="128" aria-hidden="true" loading="lazy">
        <svg v-if="method === 0" viewBox="0 0 8 8" class="cs__over" role="img" aria-label="Сітка Grad-CAM 8 × 8">
          <g v-for="(row, r) in grid" :key="'r' + r">
            <rect v-for="(v, c) in row" :key="'c' + c" :x="c" :y="r" width="1" height="1" :fill="heat(v)" opacity="0.7" />
          </g>
        </svg>
        <img v-else :src="salSrc" class="cs__over cs__sal" alt="Карта атрибуції" width="128" height="128" loading="lazy">
        <figcaption>{{ METHODS[method] }}</figcaption>
      </figure>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(mine.r) }}</b><span>ρ Спірмена до карти навченої моделі, цей знімок</span></div>
      <div class="lab__stat"><b>{{ num(mine.s) }}</b><span>SSIM до карти навченої моделі, цей знімок</span></div>
      <div class="lab__stat is-warm"><b>{{ block ? num(block.r) + ' / ' + num(block.s) : '1 / 1' }}</b>
        <span>медіани ρ / SSIM за {{ NB }} знімками тесту Shenzhen (вивід коду)</span></div>
    </div>

    <p class="lab__note">
      Карта, що проходить перевірку, має змінитися вже на перших стадіях. Градієнт × вхід зберігає обриси знімка навіть
      при повністю випадковій мережі: цю структуру вносить множення на сам знімок, а не модель.
    </p>
  </div>
</template>

<style scoped>
.cs__row { display: flex; flex-wrap: wrap; gap: 1rem; margin: 0.6rem 0; }
.cs__fig { margin: 0; width: min(46%, 220px); }
.cs__fig img, .cs__fig svg { width: 100%; height: auto; display: block; image-rendering: auto; border-radius: 4px; }
.cs__fig figcaption { font-size: 0.78rem; color: var(--vp-c-text-2); margin-top: 0.25rem; }
.cs__stack { position: relative; }
.cs__over { position: absolute; left: 0; top: 0; }
.cs__sal { opacity: 0.8; }
</style>
