<script setup lang="ts">
/**
 * Крок сітки B-сплайна на POPI (лекція 11, розділ «TRE до і після: афінне перетворення і B-сплайн»).
 * Дані — tools/gen_lec11_bspline.py: поверх афінного перетворення з блоку коду та сама B-сплайн-
 * реєстрація (NCC, L-BFGS-B, 100 ітерацій, піраміда 2–1, 5 % вокселів, зерно 1) для кроків сітки
 * 20…100 мм; для кожного — кількість параметрів, TRE на 40 орієнтирах, частка вокселів легень з
 * det J ≤ 0 і час реєстрації. Рядок 50 мм генератор звіряє з виводом блоку коду (3240 параметрів).
 * Зрізів КТ POPI немає (ліцензії набору немає) — лише числа.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec11_bspline.json'

type Row = { grid: number; mesh: number[]; params: number; tre: number[]; mean: number; median: number; max: number; fold_pct: number; jac_min: number; sec: number }
const ROWS = data.rows as Row[]
const NONE = data.none as number[]
const AFF = data.affine as number[]
const STATS = data.stats as Record<string, number[]>
const k = ref(ROWS.findIndex(r => r.grid === 50))
const row = computed(() => ROWS[k.value])
const num = (v: number, d = 2) => v.toFixed(d).replace('.', ',').replace('-', '−')
const order = NONE.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]).map(p => p[1])

// графік TRE за орієнтирами
const W = 620, H = 250, L = 40, R = 10, T = 12, B = 32
const YMAX = Math.ceil(Math.max(...NONE, ...ROWS.flatMap(r => r.tre)))
const x = (i: number) => L + (i / (order.length - 1)) * (W - L - R)
const y = (v: number) => T + (1 - v / YMAX) * (H - T - B)
const path = (a: number[]) => order.map((j, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(a[j]).toFixed(1)}`).join(' ')
const yTicks = Array.from({ length: Math.floor(YMAX / 2) + 1 }, (_, i) => i * 2)

// графік середньої й максимальної TRE за кроком сітки
const SW = 300, SH = 170, SL = 36, SR = 10, ST = 10, SB = 30
const G = ROWS.map(r => r.grid)
const sx = (g: number) => SL + ((g - G[0]) / (G[G.length - 1] - G[0])) * (SW - SL - SR)
const SMAX = Math.ceil(Math.max(...ROWS.map(r => r.max)))
const sy = (v: number) => ST + (1 - v / SMAX) * (SH - ST - SB)
const sPath = (key: 'mean' | 'max') => ROWS.map((r, i) => `${i ? 'L' : 'M'}${sx(r.grid).toFixed(1)},${sy(r[key]).toFixed(1)}`).join(' ')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Крок сітки B-сплайна: гнучкість проти гладкості</div>
        <div class="lab__sub">
          POPI, фази 10 → 60, 40 орієнтирів. Для кожного кроку сітки реєстрацію виконано тим самим кодом, що в розділі;
          крок 50 мм — рядок «B-сплайн (3240 п.)» таблиці над віджетом.
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>крок сітки контрольних точок: <b>{{ row.grid }} мм</b> (вузлів {{ row.mesh.map(v => v + 3).join(' × ') }}, параметрів {{ row.params.toLocaleString('uk-UA') }})</span>
        <input v-model.number="k" type="range" min="0" :max="ROWS.length - 1" step="1" aria-label="Крок сітки, мм">
      </label>
    </div>
    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(row.mean) }}</b><span>TRE середня, мм (афінне — {{ num(STATS.affine[0]) }})</span></div>
      <div class="lab__stat"><b>{{ num(row.median) }}</b><span>TRE медіана, мм</span></div>
      <div class="lab__stat is-warm"><b>{{ num(row.max) }}</b><span>TRE найгірша, мм</span></div>
      <div class="lab__stat is-green"><b>{{ num(row.fold_pct, 3) }} %</b><span>вокселів легень з det J ≤ 0 (мінімум det J {{ num(row.jac_min, 2) }})</span></div>
      <div class="lab__stat"><b>≈ {{ Math.round(row.sec) }} с</b><span>час реєстрації (порядок величини)</span></div>
    </div>
    <div class="bg__grid">
      <svg :viewBox="`0 0 ${W} ${H}`" class="bg__svg" role="img" aria-label="TRE на кожному орієнтирі">
        <g v-for="v in yTicks" :key="v">
          <line :x1="L" :x2="W - R" :y1="y(v)" :y2="y(v)" stroke="var(--vp-c-divider)" />
          <text :x="L - 5" :y="y(v) + 4" text-anchor="end" class="bg__tick">{{ v }}</text>
        </g>
        <line :x1="L" :x2="W - R" :y1="y(2)" :y2="y(2)" stroke="var(--vp-c-text-3)" stroke-dasharray="4 3" />
        <text :x="W - R" :y="y(2) - 4" text-anchor="end" class="bg__tick">2 мм — крок між зрізами</text>
        <path :d="path(NONE)" fill="none" stroke="#1B1B27" stroke-width="1.4" />
        <path :d="path(AFF)" fill="none" stroke="#EB6834" stroke-width="1.4" />
        <path :d="path(row.tre)" fill="none" stroke="#2A78D6" stroke-width="2.2" />
        <circle v-for="(j, i) in order" :key="i" :cx="x(i)" :cy="y(row.tre[j])" r="2.6" fill="#2A78D6" />
        <text :x="(L + W - R) / 2" :y="H - 6" text-anchor="middle" class="bg__tick">орієнтир (упорядковано за зсувом без реєстрації)</text>
        <text :x="12" :y="(T + H - B) / 2" text-anchor="middle" class="bg__tick" :transform="`rotate(-90 12 ${(T + H - B) / 2})`">TRE, мм</text>
      </svg>
      <svg :viewBox="`0 0 ${SW} ${SH}`" class="bg__svg" role="img" aria-label="Середня й найгірша TRE залежно від кроку сітки">
        <g v-for="v in [0, Math.round(SMAX / 2), SMAX]" :key="v">
          <line :x1="SL" :x2="SW - SR" :y1="sy(v)" :y2="sy(v)" stroke="var(--vp-c-divider)" />
          <text :x="SL - 4" :y="sy(v) + 4" text-anchor="end" class="bg__tick">{{ v }}</text>
        </g>
        <text v-for="g in G" :key="g" :x="sx(g)" :y="SH - 16" text-anchor="middle" class="bg__tick">{{ g }}</text>
        <text :x="(SL + SW - SR) / 2" :y="SH - 2" text-anchor="middle" class="bg__tick">крок сітки, мм</text>
        <path :d="sPath('mean')" fill="none" stroke="#2A78D6" stroke-width="2" />
        <path :d="sPath('max')" fill="none" stroke="#EDA100" stroke-width="2" />
        <circle :cx="sx(row.grid)" :cy="sy(row.mean)" r="4" fill="#2A78D6" />
        <circle :cx="sx(row.grid)" :cy="sy(row.max)" r="4" fill="#EDA100" />
      </svg>
    </div>
    <div class="bg__legend">
      <span><i style="background:#1B1B27"></i>без реєстрації (середня {{ num(STATS.none[0]) }} мм)</span>
      <span><i style="background:#EB6834"></i>афінне</span>
      <span><i style="background:#2A78D6"></i>B-сплайн, вибраний крок (праворуч — середня)</span>
      <span><i style="background:#EDA100"></i>найгірший орієнтир</span>
    </div>
    <p class="lab__note">
      Груба сітка не встигає за рухом діафрагми, дрібна — підганяється під локальні деталі, і найгірший орієнтир
      погіршується; у середині діапазону середня TRE змінюється на соті частки міліметра, а це в межах похибки
      позначення орієнтирів (до 2 мм через крок між зрізами). Час — порядок величини на процесорі машини курсу.
    </p>
  </div>
</template>

<style scoped>
.bg__grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 0.8rem; align-items: center; margin-top: 0.8rem; }
@media (max-width: 720px) { .bg__grid { grid-template-columns: 1fr; } }
.bg__svg { width: 100%; height: auto; display: block; }
.bg__tick { font-size: 10px; fill: var(--vp-c-text-2); }
.bg__legend { display: flex; flex-wrap: wrap; gap: 0.9rem; font-size: 0.78rem; color: var(--vp-c-text-2); margin-top: 0.4rem; }
.bg__legend i { display: inline-block; width: 14px; height: 4px; border-radius: 2px; margin-right: 0.35rem; vertical-align: middle; }
</style>
