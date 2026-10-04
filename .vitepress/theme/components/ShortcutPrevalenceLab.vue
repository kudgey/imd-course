<script setup lang="ts">
/**
 * Частка міток NIH ChestX-ray14 за групами (лекція 14, розділ «Проєкція AP/PA і прихована тяжкість стану»).
 * Дані — tools/gen_lec14_nih_meta.py: лише таблиця Data_Entry_2017_v2020.csv, без знімків; для кожної мітки
 * і групування (проєкція, вікова група, стать) — кількість знімків і знімків із міткою, окремо для всіх
 * знімків і для першого візиту кожного пацієнта. Частки AP/PA збігаються з таблицею виводу блоку коду
 * (перевіряє --check генератора).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec14_nih_meta.json'

type Level = { groups: string[]; n: number[]; pos: Record<string, number[]> }
type Grouping = Record<string, Level>
const G = data.groupings as Record<string, Grouping>
const LABELS = data.labels as string[]
const GROUPINGS = Object.keys(G)
const LEVELS = ['усі знімки', 'перший візит']
const label = ref('Edema')
const grouping = ref('проєкція')
const level = ref('усі знімки')

const rows = computed(() => {
  const L = G[grouping.value][level.value]
  return L.groups.map((g, i) => ({ g, n: L.n[i], p: L.pos[label.value][i], share: (100 * L.pos[label.value][i]) / L.n[i] }))
})
const maxShare = computed(() => Math.max(...rows.value.map((r) => r.share), 0.1))
const ratio = computed(() => {
  const s = rows.value.map((r) => r.share)
  const lo = Math.min(...s)
  return lo > 0 ? Math.max(...s) / lo : Infinity
})
const total = computed(() => rows.value.reduce((a, r) => a + r.n, 0))
const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',')
const big = (v: number) => v.toLocaleString('uk-UA').replace(/\s/g, ' ')
const GNAME: Record<string, string> = { AP: 'AP (у ліжку, палатний апарат)', PA: 'PA (стоячи)', F: 'жінки', M: 'чоловіки' }
const gname = (g: string) => GNAME[g] ?? (grouping.value === 'вік' ? `${g} років` : g)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Частка мітки в групах ChestX-ray14: проєкція, вік, стать</div>
        <div class="lab__sub">
          {{ big(data.n_images) }} знімків від {{ big(data.n_patients) }} пацієнтів; лише таблиця метаданих. «Перший візит» —
          по одному знімку на пацієнта з найменшим номером Follow-up #.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>мітка</span>
        <select v-model="label" aria-label="Мітка ChestX-ray14">
          <option v-for="l in LABELS" :key="l" :value="l">{{ l }}</option>
        </select>
      </label>
      <div class="lab__ctl">
        <span>групування</span>
        <div class="lab__pills">
          <button v-for="g in GROUPINGS" :key="g" type="button" class="lab__pill" :class="{ 'is-on': grouping === g }" @click="grouping = g">{{ g }}</button>
        </div>
      </div>
      <div class="lab__ctl">
        <span>що рахувати</span>
        <div class="lab__pills">
          <button v-for="l in LEVELS" :key="l" type="button" class="lab__pill" :class="{ 'is-on': level === l }" @click="level = l">{{ l }}</button>
        </div>
      </div>
    </div>

    <div class="sp__bars">
      <div v-for="r in rows" :key="r.g" class="sp__row">
        <div class="sp__name">{{ gname(r.g) }}</div>
        <div class="sp__track"><i :style="{ width: (100 * r.share / maxShare) + '%' }"></i></div>
        <div class="sp__val"><b>{{ num(r.share) }} %</b> <span>{{ big(r.p) }} з {{ big(r.n) }}</span></div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ Number.isFinite(ratio) ? num(ratio) + '×' : '—' }}</b><span>найбільша частка / найменша</span></div>
      <div class="lab__stat"><b>{{ big(total) }}</b><span>{{ level === 'усі знімки' ? 'знімків' : 'пацієнтів' }} у групах</span></div>
    </div>
    <p class="lab__note">
      Для набряку (Edema) на всіх знімках AP і PA різняться в 11 разів, а на першому візиті частки обох груп значно
      менші. Перемкніть групування на вік і «перший візит»: частки емфіземи, фіброзу, випоту й ателектазу в групі 60+ у
      кілька разів вищі, ніж у 18–39, тож модель, яка «бачить» вік на знімку, отримує ще один короткий шлях.
    </p>
  </div>
</template>

<style scoped>
.sp__bars { display: grid; gap: 0.45rem; margin: 0.6rem 0 0.2rem; }
.sp__row { display: grid; grid-template-columns: minmax(6rem, 11rem) 1fr minmax(6.5rem, auto); gap: 0.6rem; align-items: center; font-size: 0.82rem; }
.sp__name { color: var(--vp-c-text-2); }
.sp__track { background: var(--uk-fill); border-radius: 3px; height: 14px; overflow: hidden; }
.sp__track i { display: block; height: 100%; background: var(--uk-warm); border-radius: 3px; }
.sp__val b { color: var(--vp-c-text-1); }
.sp__val span { color: var(--vp-c-text-3); font-size: 0.74rem; }
@media (max-width: 480px) {
  .sp__row { grid-template-columns: 1fr; gap: 0.15rem; }
}
</style>
