<script setup lang="ts">
/**
 * Закон ослаблення I/I0 = exp(−Σ (μ/ρ)·ρ·x) для двох променів однакової довжини: лише м’яка тканина
 * і тканина, у якій частину шляху займає кортикальна кістка. Масові коефіцієнти μ/ρ — таблиці NIST
 * (ICRU-44) у табличних вузлах енергії, густини — таблиця 2 NIST. На 60 кеВ, 20 см і 2 см кістки
 * віджет дає ті самі числа, що блок коду розділу «Медичне зображення — карта фізичної величини»:
 * 1,30 · 10⁻², 6,00 · 10⁻³, контраст 2,2 (і 1,63 · 10⁻² для 20 см води). Дані пише tools/gen_lec02_atten.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec02_atten.json'

type Mat = 'water' | 'tissue' | 'bone'
const E = data.energies_kev as number[]
const MU = data.mu_rho as Record<Mat, number[]>
const RHO = data.rho as Record<Mat, number>

const ei = ref(E.indexOf(data.default.kev))
const tissue = ref(data.default.tissue_cm)
const bone = ref(data.default.bone_cm)

const SUP: Record<string, string> = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' }
const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
/** Як у виводі коду: три значущі цифри, «1,63 · 10⁻²» */
function sci(v: number): string {
  const [m, e] = v.toExponential(2).split('e')
  if (Number(e) === 0) return m.replace('.', ',')
  const exp = String(Number(e)).split('').map(c => SUP[c] ?? c).join('')
  return `${m.replace('.', ',')} · 10${exp}`
}

const mu = (m: Mat) => MU[m][ei.value] * RHO[m]              // лінійний коефіцієнт, 1/см
const boneCm = computed(() => Math.min(bone.value, tissue.value))
const soft = computed(() => Math.exp(-mu('tissue') * tissue.value))
const withBone = computed(() => Math.exp(-mu('tissue') * (tissue.value - boneCm.value) - mu('bone') * boneCm.value))
const water = computed(() => Math.exp(-mu('water') * tissue.value))
const contrast = computed(() => soft.value / withBone.value)

/* Яскравість на рентгенограмі: що менше фотонів дійшло, то світліше (кістка біла) */
const shade = (t: number) => {
  const g = Math.round(Math.min(1, Math.max(0, -Math.log10(t) / 8)) * 235 + 10)
  return `rgb(${g},${g},${g})`
}

/* Графік μ від енергії, обидві осі логарифмічні */
const W = 340
const H = 190
const PL = 42
const PR = 12
const PT = 10
const PB = 32
const lx = (e: number) => PL + ((Math.log10(e) - Math.log10(E[0])) / (Math.log10(E[E.length - 1]) - Math.log10(E[0]))) * (W - PL - PR)
const Y0 = Math.log10(0.1)
const Y1 = Math.log10(10)
const ly = (m: number) => PT + (1 - (Math.log10(m) - Y0) / (Y1 - Y0)) * (H - PT - PB)
const line = (m: Mat) => E.map((e, i) => `${lx(e).toFixed(1)},${ly(MU[m][i] * RHO[m]).toFixed(1)}`).join(' ')
const SERIES: { m: Mat; name: string; cls: string }[] = [
  { m: 'bone', name: 'кортикальна кістка', cls: 'at__bone' },
  { m: 'tissue', name: 'м’яка тканина', cls: 'at__tissue' },
]
const YT = [0.1, 0.3, 1, 3, 10]
const tickLabel = (t: number) => num(t, t >= 1 ? 0 : 1)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Закон ослаблення: скільки фотонів доходить до детектора</div>
        <div class="lab__sub">
          Два промені однакової довжини: лише м’яка тканина і тканина, частину якої займає кортикальна кістка.
          Коефіцієнти μ = (μ/ρ)·ρ — таблиці NIST для табличних енергій.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(e, i) in E" :key="e" type="button" class="lab__pill" :class="{ 'is-on': ei === i }"
              @click="ei = i">{{ e }} кеВ</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>повна довжина шляху в тілі: <b>{{ tissue }}</b> см</span>
        <input type="range" min="1" max="40" step="1" v-model.number="tissue" />
      </label>
      <label class="lab__ctl">
        <span>з неї займає кістка: <b>{{ num(boneCm, 1) }}</b> см</span>
        <input type="range" min="0" max="5" step="0.5" v-model.number="bone" />
      </label>
    </div>

    <div class="at__grid">
      <div>
        <div class="at__cap">Яскравість на рентгенограмі: що менше фотонів дійшло, то світліше</div>
        <div class="at__rays">
          <div class="at__ray">
            <div class="at__beam"><span class="at__seg at__seg--t" style="width: 100%"></span></div>
            <div class="at__det" :style="{ background: shade(soft) }"></div>
            <div class="at__lbl">лише тканина</div>
          </div>
          <div class="at__ray">
            <div class="at__beam">
              <span class="at__seg at__seg--t" :style="{ width: `${(1 - boneCm / tissue) * 50}%` }"></span>
              <span class="at__seg at__seg--b" :style="{ width: `${(boneCm / tissue) * 100}%` }"></span>
              <span class="at__seg at__seg--t" :style="{ width: `${(1 - boneCm / tissue) * 50}%` }"></span>
            </div>
            <div class="at__det" :style="{ background: shade(withBone) }"></div>
            <div class="at__lbl">тканина + кістка</div>
          </div>
        </div>
      </div>
      <div>
        <div class="at__cap">Лінійний коефіцієнт ослаблення μ, 1/см, від енергії (обидві осі логарифмічні)</div>
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Коефіцієнт ослаблення кістки і м’якої тканини від енергії">
          <g v-for="t in YT" :key="'y' + t">
            <line :x1="PL" :x2="W - PR" :y1="ly(t)" :y2="ly(t)" class="at__grid-line" />
            <text :x="PL - 4" :y="ly(t) + 3" text-anchor="end" class="at__tick">{{ tickLabel(t) }}</text>
          </g>
          <g v-for="e in E" :key="'x' + e">
            <text :x="lx(e)" :y="H - PB + 13" text-anchor="middle" class="at__tick">{{ e }}</text>
          </g>
          <line :x1="lx(E[ei])" :x2="lx(E[ei])" :y1="PT" :y2="H - PB" class="at__now" />
          <g v-for="s in SERIES" :key="s.m">
            <polyline :points="line(s.m)" :class="s.cls" />
            <circle :cx="lx(E[ei])" :cy="ly(MU[s.m][ei] * RHO[s.m])" r="3.5" :class="s.cls + '-pt'" />
          </g>
          <text :x="lx(E[1]) + 4" :y="ly(MU.bone[1] * RHO.bone) - 6" class="at__name at__bone-txt">кістка</text>
          <text :x="lx(E[1]) + 4" :y="ly(MU.tissue[1] * RHO.tissue) + 14" class="at__name at__tissue-txt">тканина</text>
          <text :x="(PL + W - PR) / 2" :y="H - 3" text-anchor="middle" class="at__tick">енергія фотонів, кеВ</text>
        </svg>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ sci(soft) }}</b><span>пройшло крізь {{ tissue }} см тканини</span></div>
      <div class="lab__stat is-warm"><b>{{ sci(withBone) }}</b><span>той самий шлях, з них {{ num(boneCm, 1) }} см кістки</span></div>
      <div class="lab__stat is-green"><b>{{ num(contrast, 1) }}</b><span>контраст кістки: у скільки разів менше фотонів</span></div>
      <div class="lab__stat"><b>{{ sci(water) }}</b><span>для порівняння: {{ tissue }} см води</span></div>
    </div>

    <p class="lab__note">
      На 60 кеВ крізь 20 см тканини проходить 1,30 · 10⁻² пучка, з 2 см кістки — 6,00 · 10⁻³, контраст 2,2; ті самі
      числа дає код. Перемкніть на 30 кеВ — контраст зросте до 74,3, але крізь тіло пройде в десятки разів менше
      фотонів; на 100 кеВ контраст лише 1,4. Подовжте шлях до 40 см: частка падає експоненційно, і сигнал на
      детекторі стає дуже малим. Кістка ослаблює сильніше на низьких енергіях, бо вміст кальцію посилює поглинання,
      — це видно з того, як розходяться лінії на графіку ліворуч від 60 кеВ.
    </p>
  </div>
</template>

<style scoped>
.at__grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 1.1rem;
  align-items: start;
}
@media (max-width: 760px) { .at__grid { grid-template-columns: 1fr; } }
.at__grid svg { width: 100%; height: auto; display: block; }
.at__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin: 0.1rem 0 0.5rem; line-height: 1.4; }
.at__rays { display: flex; flex-direction: column; gap: 0.9rem; }
.at__ray { display: grid; grid-template-columns: minmax(0, 1fr) 46px; gap: 0.5rem; align-items: center; }
.at__beam {
  display: flex;
  height: 22px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--uk-line);
}
.at__seg { display: block; height: 100%; }
.at__seg--t { background: #e8b9a0; }
.at__seg--b { background: #f4f1ea; border-left: 1px solid #b8b2a5; border-right: 1px solid #b8b2a5; }
.at__det { width: 46px; height: 46px; border-radius: 4px; border: 1px solid var(--uk-line); grid-row: span 2; }
.at__lbl { font-size: 0.76rem; color: var(--vp-c-text-2); }
.at__grid-line { stroke: var(--uk-line); stroke-width: 0.6; }
.at__tick { fill: var(--vp-c-text-3); font-size: 9px; }
.at__now { stroke: var(--uk-accent); stroke-width: 1; stroke-dasharray: 3 3; }
.at__bone { fill: none; stroke: var(--uk-warm); stroke-width: 2; }
.at__tissue { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
.at__bone-pt { fill: var(--uk-warm); }
.at__tissue-pt { fill: var(--uk-accent); }
.at__name { font-size: 10px; }
.at__bone-txt { fill: var(--uk-warm); }
.at__tissue-txt { fill: var(--uk-accent); }
</style>
