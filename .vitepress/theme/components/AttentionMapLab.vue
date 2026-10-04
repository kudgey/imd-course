<script setup lang="ts">
/**
 * Карти уваги ViT-Ti/16 по шарах і головах (лекція 12, розділ «Карти уваги трансформера та межі їх тлумачення»).
 * Дві моделі на вході 224 px (14 × 14 патчів): ваги ImageNet і та сама мережа, донавчана на туберкульоз на
 * розбитті S1 (чекпойнт блоку розділу «ViT і CNN на рентгенограмах ТБ за однакового бюджету»). Для кожного шару —
 * вага, яку токен [CLS] дає кожному патчу, softmax(q_CLS kᵀ / √d_k), окремо для трьох голів і середнє голів;
 * розгортка уваги (Abnar, Zuidema, 2020): A_l = ½ W̄_l + ½ I, R_l = A_l … A_1. Кожна карта нормована на свій
 * максимум. Знімки — NIH ChestX-ray14 (мітки з Data_Entry_2017_v2020.csv). Дані: tools/gen_lec12_attn.py.
 */
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import data from '../../data/lec12_attn.json'

type Maps = { heads: string[][]; mean: string[]; rollout: string[] }
const images = data.images as { id: string; finding: string; src: string }[]
const maps = data.maps as Record<string, Record<string, Maps>>
const MODELS = [
  { key: 'ImageNet', label: 'ваги ImageNet' },
  { key: 'ТБ', label: 'донавчена на ТБ' },
]
const N = data.grid as number
// мітки NIH ChestX-ray14 українською (англійська мітка набору — в дужках)
const UK: Record<string, string> = {
  'Mass': 'об’ємне утворення', 'Nodule': 'вузлик',
  'Consolidation|Effusion': 'консолідація, випіт', 'No Finding': 'без знахідок',
}
const label = (f: string) => `${UK[f] ?? f} (${f})`

const img = ref(0)
const model = ref('ТБ')
const layer = ref(12)
const mode = ref<'h0' | 'h1' | 'h2' | 'mean' | 'rollout'>('mean')
const alpha = ref(0.6)

function decode(b64: string): number[] {
  const s = atob(b64)
  return Array.from({ length: s.length }, (_, i) => s.charCodeAt(i) / 255)
}
const values = computed(() => {
  const m = maps[model.value][images[img.value].id]
  const l = layer.value - 1
  if (mode.value === 'mean') return decode(m.mean[l])
  if (mode.value === 'rollout') return decode(m.rollout[l])
  return decode(m.heads[l][Number(mode.value[1])])
})
const stats = computed(() => {
  const v = values.value
  const tot = v.reduce((a, b) => a + b, 0)
  const top = [...v].sort((a, b) => b - a).slice(0, 20).reduce((a, b) => a + b, 0)
  let ring = 0
  v.forEach((x, k) => {
    const r = Math.floor(k / N), c = k % N
    if (r === 0 || c === 0 || r === N - 1 || c === N - 1) ring += x
  })
  return { top: top / tot, ring: ring / tot }
})

// палітра inferno (matplotlib), 9 опорних точок
const INF = [[0, 0, 4], [31, 12, 72], [85, 15, 109], [136, 34, 106], [186, 54, 85], [227, 89, 51], [249, 140, 10], [249, 201, 50], [252, 255, 164]]
function color(v: number) {
  const x = Math.min(1, Math.max(0, v)) * (INF.length - 1)
  const i = Math.min(INF.length - 2, Math.floor(x)), f = x - i
  const c = INF[i].map((a, k) => Math.round(a + (INF[i + 1][k] - a) * f))
  return `rgb(${c[0]},${c[1]},${c[2]})`
}
const pct = (v: number) => (100 * v).toFixed(1).replace('.', ',')
const MODES = [
  { key: 'h0', label: 'голова 1' }, { key: 'h1', label: 'голова 2' }, { key: 'h2', label: 'голова 3' },
  { key: 'mean', label: 'середнє голів' }, { key: 'rollout', label: 'розгортка до шару' },
] as const
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Куди дивиться токен [CLS]: шари, голови, розгортка</div>
        <div class="lab__sub">
          Оберіть знімок, модель і шар. Колір — вага уваги [CLS] до кожного з 14 × 14 патчів (нормована на максимум
          карти). Порівняйте ранні й пізні шари, окремі голови і дві моделі на тому самому знімку.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(im, k) in images" :key="im.id" type="button" class="lab__pill" :class="{ 'is-on': img === k }"
              @click="img = k">{{ im.id }} · {{ UK[im.finding] ?? im.finding }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="m in MODELS" :key="m.key" type="button" class="lab__pill" :class="{ 'is-on': model === m.key }"
              @click="model = m.key">{{ m.label }}</button>
      <button v-for="m in MODES" :key="m.key" type="button" class="lab__pill" :class="{ 'is-on': mode === m.key }"
              @click="mode = m.key">{{ m.label }}</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>шар: <b>{{ layer }}</b> з 12</span>
        <input v-model.number="layer" type="range" min="1" max="12" step="1" aria-label="Шар енкодера" />
      </label>
      <label class="lab__ctl">
        <span>непрозорість карти: <b>{{ alpha.toFixed(2).replace('.', ',') }}</b></span>
        <input v-model.number="alpha" type="range" min="0" max="0.9" step="0.05" aria-label="Непрозорість карти" />
      </label>
    </div>

    <div class="am__grid">
      <div class="am__frame">
        <img :src="withBase(images[img].src)" :alt="`Рентгенограма NIH ChestX-ray14 ${images[img].id}, 224 px`" />
        <svg :viewBox="`0 0 ${N} ${N}`" preserveAspectRatio="none" class="am__ov" role="img" aria-label="Карта уваги">
          <rect v-for="(v, k) in values" :key="k" :x="k % N" :y="Math.floor(k / N)" width="1.02" height="1.02"
                :fill="color(v)" :opacity="alpha" />
        </svg>
      </div>
      <div class="am__side">
        <div class="am__scale">
          <span>0</span>
          <i :style="{ background: `linear-gradient(90deg, ${[0, 0.25, 0.5, 0.75, 1].map(color).join(',')})` }" />
          <span>макс.</span>
        </div>
        <p>Знімок: NIH ChestX-ray14 {{ images[img].id }}, мітка набору — {{ label(images[img].finding) }}. Модель туберкульозу
          цієї мітки не знає: карта показує, які патчі змішує [CLS], а не де хвороба.</p>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ pct(stats.top) }} %</b><span>уваги на 20 найсильніших патчах із 196</span></div>
      <div class="lab__stat" :class="{ 'is-warm': stats.ring > 0.4 }"><b>{{ pct(stats.ring) }} %</b><span>уваги на 52 патчах краю кадру (26,5 % площі)</span></div>
    </div>

    <p class="lab__note">
      Знімки: NIH Clinical Center, ChestX-ray14 (Wang et al., 2017); використання без обмежень із цитуванням. Рівномірна увага дала б 20 найсильнішим патчам 10,2 % і краю кадру 26,5 %. Карта уваги — це ваги змішування
      токенів у трансформері, а не пояснення рішення: що з неї випливає і чого ні, розбирає тема про пояснюваність.
    </p>
  </div>
</template>

<style scoped>
.am__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
@media (max-width: 760px) { .am__grid { grid-template-columns: 1fr; } }
.am__frame { position: relative; width: 100%; max-width: 360px; aspect-ratio: 1; }
.am__frame img { width: 100%; height: 100%; display: block; border-radius: 6px; }
.am__ov { position: absolute; inset: 0; width: 100%; height: 100%; }
.am__side p { font-size: 0.8rem; color: var(--vp-c-text-2); line-height: 1.5; margin: 0.6rem 0 0; }
.am__scale { display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: var(--vp-c-text-3); }
.am__scale i { flex: 1; height: 10px; border-radius: 3px; display: block; }
</style>
