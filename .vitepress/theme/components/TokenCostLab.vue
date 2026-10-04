<script setup lang="ts">
/**
 * Ціна моделей зору за кількістю токенів (лекція 12, розділ «Ціна обчислень: параметри, FLOPs, пам’ять уваги»).
 * Для ResNet-18, ViT-Ti/S/B (патчі 8/16/32 px) і Swin-T на входах 224/384/512 px: токени n = (H/P)² + 1 для ViT,
 * параметри, GFLOPs прямого проходу (FlopCounterMode, 2 FLOP на множення-додавання; увага ViT — явними
 * матмноженнями, частка QKᵀ і AV — окремо), пам’ять матриць уваги одного шару n² · h · 4 Б і час на CPU
 * (батч 1, медіана п’яти прогонів). Рядки 224 px і ViT-S 384/512 px при P = 16 — ті самі числа, що в таблиці
 * блоку коду; решта — заміри генератора на тому самому процесорі. Дані: tools/gen_lec12_cost.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec12_cost.json'

type Row = {
  model: string; size: number; patch: number | null; tokens: number | null; params: number
  gflops: number; attn_gflops: number; attn_mib: number | null; ms: number; src: string
}
const rows = data.rows as Row[]
const MODELS = ['ResNet-18', 'ViT-Ti', 'ViT-S', 'ViT-B', 'Swin-T']
const SIZES = [224, 384, 512]
const PATCHES = [8, 16, 32]

const model = ref('ViT-S')
const size = ref(224)
const patch = ref(16)

const isVit = computed(() => model.value.startsWith('ViT'))
const row = computed(() => rows.find((r) => r.model === model.value && r.size === size.value
  && (isVit.value ? r.patch === patch.value : r.patch === null)) as Row)
const family = computed(() => rows.filter((r) => r.model === model.value))
const attnShare = computed(() => row.value.gflops ? row.value.attn_gflops / row.value.gflops : 0)

const num = (v: number, d = 1) => v.toLocaleString('uk-UA', { minimumFractionDigits: d, maximumFractionDigits: d })
const int = (v: number) => v.toLocaleString('uk-UA')

// графік: GFLOPs (ліва вісь, log) проти кількості токенів (log) для всіх варіантів обраної моделі
const W = 340, H = 200, L = 40, R = 10, T = 10, B = 34
const xv = (r: Row) => r.tokens ?? r.size // для ResNet-18 — сторона входу
const xs = computed(() => family.value.map(xv))
const lx = (v: number) => Math.log10(v)
const xMin = computed(() => Math.min(...xs.value) / 1.5)
const xMax = computed(() => Math.max(...xs.value) * 1.5)
const yMin = computed(() => Math.min(...family.value.map((r) => r.gflops)) / 1.5)
const yMax = computed(() => Math.max(...family.value.map((r) => r.gflops)) * 1.5)
const X = (v: number) => L + (lx(v) - lx(xMin.value)) / (lx(xMax.value) - lx(xMin.value)) * (W - L - R)
const Y = (v: number) => H - B - (lx(v) - lx(yMin.value)) / (lx(yMax.value) - lx(yMin.value)) * (H - T - B)
const ticks = (lo: number, hi: number) => {
  const out: number[] = []
  for (let e = Math.floor(lx(lo)); e <= Math.ceil(lx(hi)); e++) {
    for (const m of [1, 3]) {
      const v = m * 10 ** e
      if (v >= lo && v <= hi) out.push(v)
    }
  }
  return out
}
const pts = computed(() => family.value.map((r) => ({
  r, x: X(xv(r)), y: Y(r.gflops),
  on: r === row.value,
})))
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Ціна моделі за кількістю токенів</div>
        <div class="lab__sub">
          Оберіть модель, розмір входу і (для ViT) розмір патча. Токенів n = (H/P)² + 1; кожен шар ViT рахує
          n × n ваг уваги для кожної голови, тому FLOPs уваги і пам’ять ростуть як n², а частка уваги у FLOPs
          збільшується з розміром входу.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="m in MODELS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': model === m }"
              @click="model = m">{{ m }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="s in SIZES" :key="s" type="button" class="lab__pill" :class="{ 'is-on': size === s }"
              @click="size = s">вхід {{ s }} px</button>
      <template v-if="isVit">
        <button v-for="p in PATCHES" :key="p" type="button" class="lab__pill" :class="{ 'is-on': patch === p }"
                @click="patch = p">патч {{ p }} px</button>
      </template>
    </div>

    <div class="tc__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="GFLOPs проти кількості токенів">
        <line :x1="L" :x2="W - R" :y1="H - B" :y2="H - B" class="tc__axis" />
        <line :x1="L" :x2="L" :y1="T" :y2="H - B" class="tc__axis" />
        <g v-for="v in ticks(xMin, xMax)" :key="'x' + v">
          <line :x1="X(v)" :x2="X(v)" :y1="T" :y2="H - B" class="tc__grid-l" />
          <text :x="X(v)" :y="H - B + 12" text-anchor="middle" class="tc__lbl">{{ int(v) }}</text>
        </g>
        <g v-for="v in ticks(yMin, yMax)" :key="'y' + v">
          <line :x1="L" :x2="W - R" :y1="Y(v)" :y2="Y(v)" class="tc__grid-l" />
          <text :x="L - 4" :y="Y(v) + 3" text-anchor="end" class="tc__lbl">{{ int(v) }}</text>
        </g>
        <circle v-for="(p, k) in pts" :key="k" :cx="p.x" :cy="p.y" :r="p.on ? 5 : 3"
                :class="p.on ? 'tc__pt is-on' : 'tc__pt'" />
        <text :x="(L + W - R) / 2" :y="H - 4" text-anchor="middle" class="tc__lbl">
          {{ model.startsWith('ViT') ? 'токенів n' : model === 'Swin-T' ? 'токенів на стадії 1' : 'сторона входу, px' }}
          (логарифмічна шкала)
        </text>
        <text :x="10" :y="(T + H - B) / 2" text-anchor="middle" class="tc__lbl"
              :transform="`rotate(-90 10 ${(T + H - B) / 2})`">GFLOPs</text>
      </svg>
      <div>
        <div class="tc__split" v-if="isVit || model === 'Swin-T'">
          <span>частка FLOPs на QKᵀ і AV: <b>{{ num(100 * attnShare, 1) }} %</b></span>
          <div class="lab__bar"><i :style="{ width: `${Math.max(1, 100 * attnShare)}%`, background: 'var(--uk-warm)' }" /></div>
        </div>
        <p class="tc__legend">
          Точки — усі варіанти обраної моделі (входи 224/384/512 px{{ isVit ? ' × патчі 8/16/32 px' : '' }}); більша
          точка — обраний. Для ResNet-18 уваги немає: ціна росте лише з площею входу.
        </p>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ row.tokens ? int(row.tokens) : '—' }}</b><span>токенів{{ model === 'Swin-T' ? ' (стадія 1, вікна 7 × 7)' : '' }}</span></div>
      <div class="lab__stat"><b>{{ num(row.params, 2) }}</b><span>млн параметрів</span></div>
      <div class="lab__stat"><b>{{ num(row.gflops, 2) }}</b><span>GFLOPs прямого проходу</span></div>
      <div class="lab__stat" :class="{ 'is-warm': (row.attn_mib ?? 0) > 50 }"><b>{{ row.attn_mib === null ? '—' : num(row.attn_mib, 2) }}</b><span>МіБ уваги на шар</span></div>
      <div class="lab__stat"><b>{{ num(row.ms, 1) }}</b><span>мс на CPU, батч 1 ({{ row.src }})</span></div>
    </div>

    <p class="lab__note">
      Заміри: {{ data.threads }} потоків torch, ваги випадкові (на FLOPs і час не впливають). Рядки на 224 px і ViT-S
      на 384/512 px з патчем 16 px — ті самі числа, що в таблиці коду; решта — заміри генератора на тому самому
      процесорі. Пам’ять уваги — лише матриці ваг одного шару в float32, без активацій.
    </p>
  </div>
</template>

<style scoped>
.tc__grid { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
@media (max-width: 760px) { .tc__grid { grid-template-columns: 1fr; } }
svg { width: 100%; height: auto; display: block; }
.tc__axis { stroke: var(--uk-line); }
.tc__grid-l { stroke: var(--uk-line); stroke-dasharray: 2 3; opacity: 0.6; }
.tc__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
.tc__pt { fill: var(--uk-accent); opacity: 0.45; }
.tc__pt.is-on { opacity: 1; stroke: var(--vp-c-bg); stroke-width: 1.5; }
.tc__split span { display: block; font-size: 0.8rem; color: var(--vp-c-text-2); margin-bottom: 0.3rem; }
.tc__split b { font-family: var(--vp-font-family-mono); color: var(--uk-warm); font-weight: 500; }
.tc__legend { font-size: 0.8rem; color: var(--vp-c-text-2); line-height: 1.5; margin: 0.8rem 0 0; }
</style>
