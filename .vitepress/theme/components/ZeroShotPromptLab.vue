<script setup lang="ts">
/**
 * Класифікація без прикладів і формулювання підказки (лекція 12, розділ «Без прикладів (zero-shot): BiomedCLIP і
 * текстові підказки»). Косинуси ознак 638 знімків dev (фолди dev0…dev4 розбиття S1; тестових знімків тут немає)
 * з п’ятьма описами туберкульозу і чотирма описами норми — ті самі тексти, що в блоці коду. Оцінка знімка —
 * s(опис ТБ) − s(опис норми); softmax двох косинусів — монотонна функція цієї різниці, тож AUC та сама.
 * AUC рахується за Манном — Вітні: частка пар (ТБ, норма), у яких знімок ТБ має вищу оцінку (нічия — ½).
 * П’ять пар блоку дають ті самі AUC dev, що в його виводі. Дані: tools/gen_lec12_zeroshot.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec12_zeroshot.json'

const pos = data.pos as string[]
const neg = data.neg as string[]
const pairs = data.pairs as number[][]
const label = data.label as number[]
const source = data.source as string[]
const sims = data.sims as number[][]

const pi = ref(1)
const ni = ref(1)
const ens = ref(false)

const score = computed(() => label.map((_, k) => {
  if (ens.value) {
    const p = pos.reduce((a, _, i) => a + sims[i][k], 0) / pos.length
    const n = neg.reduce((a, _, j) => a + sims[pos.length + j][k], 0) / neg.length
    return (p - n) / 10000
  }
  return (sims[pi.value][k] - sims[pos.length + ni.value][k]) / 10000
}))

function auc(s: number[], y: number[]) {
  const idx = s.map((v, k) => [v, k]).sort((a, b) => a[0] - b[0])
  const rank = new Array(s.length)
  for (let i = 0; i < idx.length;) {
    let j = i
    while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++
    for (let k = i; k <= j; k++) rank[idx[k][1]] = (i + j) / 2 + 1
    i = j + 1
  }
  const n1 = y.filter((v) => v === 1).length, n0 = y.length - n1
  const r1 = y.reduce((a, v, k) => a + (v === 1 ? rank[k] : 0), 0)
  return (r1 - n1 * (n1 + 1) / 2) / (n1 * n0)
}
const res = computed(() => {
  const s = score.value
  const sub = (src: string) => {
    const k = source.map((v, i) => (v === src ? i : -1)).filter((i) => i >= 0)
    return auc(k.map((i) => s[i]), k.map((i) => label[i]))
  }
  return { all: auc(s, label), M: sub('M'), S: sub('S') }
})
const inBlock = computed(() => ens.value ? 0 : pairs.findIndex(([i, j]) => i === pi.value && j === ni.value) + 1)

// гістограми оцінки за класом
const W = 320, H = 150, L = 8, R = 8, T = 8, B = 22, NB = 24
const hist = computed(() => {
  const s = score.value
  const lo = Math.min(...s), hi = Math.max(...s), w = (hi - lo) / NB || 1
  const h = [0, 1].map((c) => {
    const cnt = new Array(NB).fill(0)
    s.forEach((v, k) => { if (label[k] === c) cnt[Math.min(NB - 1, Math.floor((v - lo) / w))]++ })
    return cnt
  })
  const mx = Math.max(...h[0], ...h[1])
  return { h, mx, lo, hi }
})
const bx = (i: number) => L + (i / NB) * (W - L - R)
const by = (c: number) => H - B - (c / hist.value.mx) * (H - T - B)
const num = (v: number, k = 3) => v.toFixed(k).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Класифікація без прикладів: як формулювання змінює AUC</div>
        <div class="lab__sub">
          Оберіть опис туберкульозу й опис норми. Оцінка знімка — різниця косинусів його ознак із двома описами;
          AUC — частка пар «ТБ, норма», у яких знімок із туберкульозом отримав вищу оцінку.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>опис туберкульозу</span>
        <select v-model.number="pi" :disabled="ens" aria-label="Опис туберкульозу">
          <option v-for="(p, i) in pos" :key="p" :value="i">{{ p }}</option>
        </select>
      </label>
      <label class="lab__ctl">
        <span>опис норми</span>
        <select v-model.number="ni" :disabled="ens" aria-label="Опис норми">
          <option v-for="(n, j) in neg" :key="n" :value="j">{{ n }}</option>
        </select>
      </label>
    </div>
    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': !ens }" @click="ens = false">одна пара описів</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': ens }" @click="ens = true">ансамбль: середнє всіх описів</button>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Розподіл оцінки за класом">
      <line :x1="L" :x2="W - R" :y1="H - B" :y2="H - B" class="zs__axis" />
      <g v-for="c in [0, 1]" :key="c">
        <rect v-for="(v, i) in hist.h[c]" :key="i" :x="bx(i) + 0.5" :y="by(v)" :width="bx(1) - bx(0) - 1"
              :height="H - B - by(v)" :class="c ? 'zs__tb' : 'zs__nm'" />
      </g>
      <text :x="L" :y="H - 6" class="zs__lbl">{{ num(hist.lo, 3) }}</text>
      <text :x="W - R" :y="H - 6" text-anchor="end" class="zs__lbl">{{ num(hist.hi, 3) }}</text>
      <text :x="W / 2" :y="H - 6" text-anchor="middle" class="zs__lbl">оцінка: s(опис ТБ) − s(опис норми)</text>
      <text :x="W - R" :y="T + 8" text-anchor="end" class="zs__lbl zs__tbt">■ туберкульоз</text>
      <text :x="W - R" :y="T + 20" text-anchor="end" class="zs__lbl zs__nmt">■ норма</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat" :class="{ 'is-warm': res.all < 0.7 }"><b>{{ num(res.all) }}</b><span>AUC dev, 638 знімків</span></div>
      <div class="lab__stat"><b>{{ num(res.M) }}</b><span>AUC лише Montgomery</span></div>
      <div class="lab__stat"><b>{{ num(res.S) }}</b><span>AUC лише Shenzhen</span></div>
      <div class="lab__stat"><b>{{ inBlock ? `№ ${inBlock}` : '—' }}</b><span>{{ inBlock ? 'ця пара є в таблиці коду' : 'пари немає в таблиці коду' }}</span></div>
    </div>

    <p class="lab__note">
      Підказку вибирають на dev, а тест відкривають один раз для вже вибраної — тому тестових знімків у віджеті немає.
      AUC окремо за джерелами показує, чи не вгадує оцінка лікарню замість хвороби.
    </p>
  </div>
</template>

<style scoped>
svg { width: 100%; max-width: 520px; height: auto; display: block; margin: 0.2rem auto 0; }
.zs__axis { stroke: var(--uk-line); }
.zs__tb { fill: var(--uk-warm); opacity: 0.55; }
.zs__nm { fill: var(--uk-accent); opacity: 0.45; }
.zs__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.zs__tbt { fill: var(--uk-warm); }
.zs__nmt { fill: var(--uk-accent); }
.lab__ctl select { font-size: 0.8rem; }
</style>
