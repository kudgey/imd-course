<script setup lang="ts">
/**
 * Розбиття ТБ-лінії курсу splits/cxr_tb_v1.csv (лекція 04, розділ «Стратифіковане розбиття
 * Montgomery + Shenzhen для курсу»). Склад частин схем S1 і S2 за набором і міткою, знімки з
 * рамками, частка чоловіків і медіана віку — ті самі числа, що друкує блок коду (S1: тест 162,
 * dev-фолди 127–128; S2: 464 / 99 / 99 і зовнішній Montgomery 138). Для S1 віджет складає
 * навчальну частину з чотирьох dev-фолдів, валідаційну — з обраного. Дані пише
 * tools/gen_lec04_splits.py (зі звіркою, що make_splits.py відтворює файл курсу).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec04_splits.json'

type Row = { part: string; counts: number[]; bbox: number; male: number; age: number; patients: number }
type Scheme = 's1' | 's2'

const S1 = data.s1 as Row[]
const S2 = data.s2 as Row[]
const CELLS = ['Montgomery · норма', 'Montgomery · ТБ', 'Shenzhen · норма', 'Shenzhen · ТБ']
const COLORS = ['#9EC1EE', '#2A78D6', '#F5C08F', '#EB6834']

const scheme = ref<Scheme>('s1')
const val = ref('dev0')

const num = (v: number, d = 1) => v.toFixed(d).replace('.', ',')
const sum = (a: number[]) => a.reduce((x, y) => x + y, 0)
const add = (rows: Row[]) => rows.reduce((acc, r) => acc.map((v, i) => v + r.counts[i]), [0, 0, 0, 0])

/** Частини для смуг: S1 — навчальна (4 фолди), валідаційна (обраний), тест; S2 — як у файлі */
const parts = computed(() => {
  if (scheme.value === 's2') {
    const names: Record<string, string> = { train: 'навчальна (train)', val: 'валідаційна (val)', test: 'тест (test)', external: 'зовнішній тест (Montgomery)' }
    // S2: частки Shenzhen рахуються від усіх знімків Shenzhen, зовнішній тест — від усіх знімків Montgomery
    const sz = sum(S2.filter(r => r.part !== 'external').map(r => sum(r.counts)))
    return S2.map(r => {
      const ext = r.part === 'external'
      const den = ext ? sum(r.counts) : sz
      return { name: names[r.part], counts: r.counts, bbox: r.bbox, den, of: ext ? 'знімків Montgomery' : 'знімків Shenzhen' }
    })
  }
  const dev = S1.filter(r => r.part.startsWith('dev'))
  const train = dev.filter(r => r.part !== val.value)
  const v = dev.find(r => r.part === val.value)!
  const t = S1.find(r => r.part === 'test')!
  return [
    { name: `навчальна (${train.map(r => r.part).join(', ')})`, counts: add(train), bbox: sum(train.map(r => r.bbox)), den: ALL, of: 'усіх знімків' },
    { name: `валідаційна (${v.part})`, counts: v.counts, bbox: v.bbox, den: ALL, of: 'усіх знімків' },
    { name: 'тест (test)', counts: t.counts, bbox: t.bbox, den: ALL, of: 'усіх знімків' },
  ]
})
const ALL = data.n_images as number
const rows = computed(() => (scheme.value === 's1' ? S1 : S2))
const W = 340
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Розбиття курсу: склад частин S1 і S2</div>
        <div class="lab__sub">
          Файл splits/cxr_tb_v1.csv: {{ data.n_images }} знімків, {{ data.n_patients }} пацієнтів. Смуги — частини
          розбиття, кольори — набір і мітка. У S1 оберіть, який dev-фолд буде валідаційним.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': scheme === 's1' }" @click="scheme = 's1'">
        S1: тест 20 % + 5 dev-фолдів</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': scheme === 's2' }" @click="scheme = 's2'">
        S2: Shenzhen 70/15/15 + Montgomery як зовнішній тест</button>
    </div>
    <div v-if="scheme === 's1'" class="lab__pills">
      <span class="cs__lbl">валідаційний фолд:</span>
      <button v-for="r in S1.filter(x => x.part.startsWith('dev'))" :key="r.part" type="button" class="lab__pill"
              :class="{ 'is-on': val === r.part }" @click="val = r.part">{{ r.part }}</button>
    </div>

    <div class="cs__bars">
      <div v-for="p in parts" :key="p.name" class="cs__row">
        <div class="cs__name">{{ p.name }} — <b>{{ sum(p.counts) }}</b> знімків
          ({{ num((100 * sum(p.counts)) / p.den, 1) }} % {{ p.of }}), ТБ {{ num((100 * (p.counts[1] + p.counts[3])) / Math.max(sum(p.counts), 1), 1) }} %,
          з рамками {{ p.bbox }}</div>
        <svg :viewBox="`0 0 ${W} 16`" preserveAspectRatio="none" role="img" :aria-label="p.name">
          <template v-for="(c, i) in p.counts" :key="i">
            <rect :x="(W * p.counts.slice(0, i).reduce((a, b) => a + b, 0)) / Math.max(...parts.map(q => sum(q.counts)))"
                  y="0" :width="(W * c) / Math.max(...parts.map(q => sum(q.counts)))" height="16" :fill="COLORS[i]" />
          </template>
        </svg>
      </div>
    </div>
    <div class="cs__legend">
      <span v-for="(c, i) in CELLS" :key="c"><i :style="{ background: COLORS[i] }"></i>{{ c }}</span>
    </div>

    <div class="cs__wrap">
    <table class="cs__table">
      <tbody>
        <tr><th>частина</th><th>Mon · 0</th><th>Mon · 1</th><th>She · 0</th><th>She · 1</th><th>разом</th>
          <th>рамки</th><th>чол., %</th><th>вік, мед.</th></tr>
        <tr v-for="r in rows" :key="r.part" :class="{ 'is-val': scheme === 's1' && r.part === val }">
          <td>{{ r.part }}</td><td v-for="(c, i) in r.counts" :key="i">{{ c }}</td><td>{{ sum(r.counts) }}</td>
          <td>{{ r.bbox }}</td><td>{{ num(r.male, 1) }}</td><td>{{ num(r.age, 1) }}</td>
        </tr>
      </tbody>
    </table>
    </div>
    <div class="cs__cap">Таблиця — склад кожної частини у файлі, знімків; Mon/She — набір, 0/1 — мітка. Вік — медіана в
      роках за клінічними записами; частка чоловіків — за ними ж.</div>

    <p class="lab__note">
      У S1 частка ТБ і частка Montgomery майже однакові в усіх частинах — це і є стратифікація «набір × мітка».
      Тест має 162 знімки, бо обидві групи повторних знімків Montgomery (заключення прямо називають їх одним
      пацієнтом) потрапили в тест цілком. У S2 зовнішній тест — інший апарат і популяція: 45,7 % чоловіків і
      медіана віку 40 років проти 65,7 % і 33 років у навчальній частині Shenzhen.
    </p>
  </div>
</template>

<style scoped>
.cs__lbl { font-size: 0.78rem; color: var(--vp-c-text-3); align-self: center; margin-right: 0.2rem; }
.cs__bars { display: flex; flex-direction: column; gap: 0.55rem; margin: 0.4rem 0 0.6rem; }
.cs__name { font-size: 0.8rem; color: var(--vp-c-text-2); margin-bottom: 0.15rem; }
.cs__row svg { width: 100%; height: 16px; display: block; border-radius: 3px; background: var(--uk-fill); }
.cs__legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.76rem; color: var(--vp-c-text-2); margin-bottom: 0.8rem; }
.cs__legend i { display: inline-block; width: 0.8rem; height: 0.8rem; border-radius: 2px; margin-right: 0.3rem; vertical-align: -0.1rem; }
.cs__wrap { width: 100%; overflow-x: auto; }
.cs__table { width: 100%; min-width: 420px; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.cs__table th { font-weight: 500; font-size: 0.7rem; color: var(--vp-c-text-3); text-align: right; padding: 0.15rem 0.35rem !important; white-space: nowrap; }
.cs__table td {
  font-family: var(--vp-font-family-mono);
  font-size: 0.76rem;
  text-align: right;
  padding: 0.18rem 0.35rem !important;
  border-top: 1px solid var(--uk-line) !important;
}
.cs__table tr.is-val td { color: var(--uk-accent); font-weight: 600; }
.cs__cap { font-size: 0.76rem; color: var(--vp-c-text-3); margin-top: 0.4rem; line-height: 1.4; }
</style>
