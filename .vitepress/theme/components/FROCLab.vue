<script setup lang="ts">
/**
 * FROC кандидатів з карти активації класу (лекція 09, розділ «Зменшення хибнопозитивних: каскад і
 * пригнічення немаксимумів»). Дані — tools/gen_lec09_froc.py: для кожного варіанта каскаду (усі максимуми,
 * маска легень, NMS на 2 клітинки, маска + NMS, апріорна карта з маскою) — точки кривої (хибні на знімок,
 * частка знайдених 352 рамок) на 204 знімках і чутливість у точках 0,25; 0,5; 1; 2; 4 хибних на знімок.
 * Числа варіантів, що є в блоці коду, генератор звіряє з його виводом.
 */
import { ref, computed, watch } from 'vue'
import data from '../../data/lec09_froc.json'

type V = { key: string, label: string, fp: number[], sens: number[], at: number[], mean: number,
  fp_all: number, sens_max: number, n_boxes: number, n_images: number }
const VARS = data.variants as V[]
const FPS = data.fps as number[]
const byKey = Object.fromEntries(VARS.map(v => [v.key, v])) as Record<string, V>

const lung = ref(true)
const nms = ref(false)
const prior = ref(false)
const key = computed(() => prior.value ? 'prior' : (lung.value ? (nms.value ? 'lung_nms' : 'lung') : (nms.value ? 'nms' : 'raw')))
const cur = computed(() => byKey[key.value])
/** індекс точки кривої, найближчої за хибними на знімок до f — щоб перемикання ступенів тримало рівень FP */
const nearest = (v: V, f: number) => v.fp.reduce((best, x, i) => (Math.abs(x - f) < Math.abs(v.fp[best] - f) ? i : best), 0)
const k = ref(nearest(byKey.lung, 0.5))
watch(key, (_, old) => { k.value = nearest(cur.value, byKey[old].fp[k.value] ?? 0.5) })
const pt = computed(() => ({ fp: cur.value.fp[k.value], s: cur.value.sens[k.value] }))

const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const W = 380, H = 230, PL = 40, PR = 12, PT = 10, PB = 34
const X0 = Math.log10(0.05), X1 = Math.log10(6)
const X = (f: number) => PL + ((Math.log10(Math.max(f, 0.05)) - X0) / (X1 - X0)) * (W - PL - PR)
const Y = (s: number) => PT + (1 - s / 0.5) * (H - PT - PB)
function line(v: V) {
  let d = '', prev = 0
  v.fp.forEach((f, i) => {
    if (f <= 0) { prev = v.sens[i]; return }
    const x = X(f).toFixed(1), y = Y(v.sens[i]).toFixed(1)
    d += d ? ` H${x} V${y}` : `M${x},${Y(prev).toFixed(1)} V${y}`
    prev = v.sens[i]
  })
  return d
}
const COLORS: Record<string, string> = { raw: '#2A78D6', lung: '#EB6834', nms: '#4A3AA7', lung_nms: '#1BAF7A', prior: '#808080' }
const yTicks = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">FROC кандидатів з карти: ступені каскаду</div>
        <div class="lab__sub">
          {{ cur.n_images }} знімків (123 з рамками і 81 без туберкульозу), {{ cur.n_boxes }} рамок еталону; кандидат — локальний
          максимум карти 7 × 7, влучання — центр клітинки в рамці з допуском 15 px.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': lung }" :disabled="prior" @click="lung = !lung">маска легень</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': nms }" :disabled="prior" @click="nms = !nms">NMS на 2 клітинки</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': prior }" @click="prior = !prior">апріорна карта + маска</button>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>робоча точка (поріг оцінки, від найвищого): <b>{{ k + 1 }} з {{ cur.fp.length }}</b></span>
        <input v-model.number="k" type="range" min="0" :max="cur.fp.length - 1" step="1" aria-label="Робоча точка на кривій FROC">
      </label>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="fr__svg" role="img" aria-label="Криві FROC варіантів каскаду">
      <g v-for="t in yTicks" :key="'y' + t">
        <line :x1="PL" :x2="W - PR" :y1="Y(t)" :y2="Y(t)" class="fr__grid" />
        <text :x="PL - 4" :y="Y(t) + 3" text-anchor="end" class="fr__lbl">{{ num(t, 1) }}</text>
      </g>
      <g v-for="f in FPS" :key="'x' + f">
        <line :x1="X(f)" :x2="X(f)" :y1="PT" :y2="H - PB" class="fr__grid" />
        <text :x="X(f)" :y="H - PB + 12" text-anchor="middle" class="fr__lbl">{{ String(f).replace('.', ',') }}</text>
      </g>
      <text :x="(PL + W - PR) / 2" :y="H - 4" text-anchor="middle" class="fr__lbl">хибних спрацювань на знімок (лог. шкала)</text>
      <path v-for="v in VARS" :key="v.key" :d="line(v)" fill="none" :stroke="COLORS[v.key]"
        :stroke-width="v.key === key ? 2.4 : 1" :opacity="v.key === key ? 1 : 0.35" />
      <circle v-for="(s, i) in cur.at" :key="'a' + i" :cx="X(FPS[i])" :cy="Y(s)" r="2.6" :fill="COLORS[key]" />
      <circle :cx="X(pt.fp)" :cy="Y(pt.s)" r="4.5" fill="none" stroke="var(--vp-c-text-1)" stroke-width="1.6" />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ num(pt.s) }}</b><span>частка знайдених рамок у робочій точці</span></div>
      <div class="lab__stat"><b>{{ num(pt.fp, 2) }}</b><span>хибних спрацювань на знімок</span></div>
      <div class="lab__stat is-green"><b>{{ num(cur.mean) }}</b><span>середня чутливість у 5 точках (0,25…4)</span></div>
      <div class="lab__stat"><b>{{ num(cur.fp_all, 2) }}</b><span>хибних на знімок, якщо взяти всіх кандидатів</span></div>
    </div>
    <table>
      <thead><tr><th>хибних на знімок</th><th v-for="f in FPS" :key="'h' + f">{{ String(f).replace('.', ',') }}</th></tr></thead>
      <tbody><tr><td>чутливість</td><td v-for="(s, i) in cur.at" :key="'s' + i">{{ num(s) }}</td></tr></tbody>
    </table>
    <p class="lab__note">
      Маска легень зрізає хибні спрацювання в центрі кадру, а NMS — сусідні кандидати; на знімках, де рамки стоять
      поруч, друге коштує знайдених рамок. Апріорна карта (тут — побудована з другої половини знімків, середнє 20
      поділів) не знає, на якому знімку туберкульоз: за малої кількості хибних на знімок вона поступається карті
      класифікатора, а за 2–4 хибних на знімок випереджає її, бо вказує на типові місця уражень.
    </p>
  </div>
</template>

<style scoped>
.fr__svg { width: 100%; height: auto; display: block; }
.fr__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.fr__lbl { fill: var(--vp-c-text-3); font-size: 9px; }
</style>
