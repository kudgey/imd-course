<script setup lang="ts">
/**
 * Несумісність критеріїв справедливості (лекція 17, розділ «Критерії справедливості та їхня несумісність»).
 * Дані — tools/gen_lec17_fair.py: скори моделі S2 і мітки знімків Montgomery окремо для жінок (F) і
 * чоловіків (M) та поріг t за правилом теми про валідацію. Для порогу кожної групи рахуються TPR, FPR,
 * PPV, поширеність і права частина тотожності Chouldechova π/(1 − π) · (1 − PPV)/PPV · TPR; за спільного
 * порогу t числа збігаються з виводом коду розділу про підгрупи. Пороги на зовнішньому тесті тут
 * рухаються лише для ілюстрації тотожності.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec17_fair.json'

type G = { score: number[]; label: number[] }
const GR = data.groups as Record<'F' | 'M', G>
const T = data.t as number
// пороги-кандидати: усі різні скори обох груп і t
const GRID = [...new Set([...GR.F.score, ...GR.M.score, T])].sort((a, b) => a - b)
const iT = GRID.indexOf(T)
const kF = ref(iT)
const kM = ref(iT)

function stats(g: G, t: number) {
  let tp = 0, fp = 0, fn = 0, tn = 0
  g.score.forEach((s, i) => {
    const hit = s >= t
    if (g.label[i]) { if (hit) tp++; else fn++ } else { if (hit) fp++; else tn++ }
  })
  const n = tp + fp + fn + tn
  const p = (tp + fn) / n, tpr = tp / (tp + fn), fpr = fp / (fp + tn)
  const ppv = tp + fp ? tp / (tp + fp) : NaN
  return { n, p, tpr, fpr, ppv, rhs: (p / (1 - p)) * ((1 - ppv) / ppv) * tpr }
}
const sF = computed(() => stats(GR.F, GRID[kF.value]))
const sM = computed(() => stats(GR.M, GRID[kM.value]))

function matchBoth() { // пара порогів (без вироджених FPR = 0), за якої FPR і PPV груп найближчі
  const sf = GRID.map((t) => stats(GR.F, t)), sm = GRID.map((t) => stats(GR.M, t))
  let best = [kF.value, kM.value], gap = Infinity
  sf.forEach((a, i) => sm.forEach((b, j) => {
    const g = Math.abs(a.fpr - b.fpr) + Math.abs(a.ppv - b.ppv)
    if (Number.isFinite(g) && a.fpr > 0 && b.fpr > 0 && g < gap) { gap = g; best = [i, j] }
  }))
  kF.value = best[0]; kM.value = best[1]
}
function match(key: 'fpr' | 'ppv') { // поріг для чоловіків, за якого показник найближчий до жіночого
  const target = sF.value[key]
  let best = kM.value, gap = Infinity
  GRID.forEach((t, i) => {
    const v = stats(GR.M, t)[key]
    if (Number.isFinite(v) && Math.abs(v - target) < gap) { gap = Math.abs(v - target); best = i }
  })
  kM.value = best
}
const num = (v: number, d = 3) => (Number.isFinite(v) ? v.toFixed(d).replace('.', ',') : '—')
const rows = computed(() => [
  { id: 'F', name: 'жінки', s: sF.value, t: GRID[kF.value] },
  { id: 'M', name: 'чоловіки', s: sM.value, t: GRID[kM.value] },
])
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">TPR, FPR і PPV: усі три рівними не бувають</div>
        <div class="lab__sub">
          Montgomery, модель S2. Рухайте поріг окремо для жінок і чоловіків або натисніть кнопку, що підбирає пороги.
          Поширеність у групах різна, тому TPR, FPR і PPV не бувають рівними всі три одночасно: зрівняна пара
          розводить третій показник.
        </div>
      </div>
    </div>
    <div class="lab__controls">
      <label class="lab__ctl">
        <span>поріг для жінок: <b>{{ num(GRID[kF], 4) }}</b>{{ kF === iT ? ' (t)' : '' }}</span>
        <input v-model.number="kF" type="range" min="0" :max="GRID.length - 1" step="1" aria-label="Поріг для жінок" />
      </label>
      <label class="lab__ctl">
        <span>поріг для чоловіків: <b>{{ num(GRID[kM], 4) }}</b>{{ kM === iT ? ' (t)' : '' }}</span>
        <input v-model.number="kM" type="range" min="0" :max="GRID.length - 1" step="1" aria-label="Поріг для чоловіків" />
      </label>
    </div>
    <div class="fa__btns">
      <button type="button" class="lab__btn" @click="kF = iT; kM = iT">спільний поріг t = {{ num(T, 4) }}</button>
      <button type="button" class="lab__btn" @click="match('fpr')">зрівняти FPR</button>
      <button type="button" class="lab__btn" @click="match('ppv')">зрівняти PPV</button>
      <button type="button" class="lab__btn" @click="matchBoth()">зрівняти FPR і PPV</button>
    </div>
    <div class="fa__wrap">
      <table class="fa__table">
        <thead><tr><th>група</th><th>знімків</th><th>поширеність π</th><th>TPR</th><th>FPR</th><th>PPV</th><th>π/(1−π)·(1−PPV)/PPV·TPR</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td>{{ r.name }}</td><td>{{ r.s.n }}</td><td>{{ num(r.s.p) }}</td><td>{{ num(r.s.tpr) }}</td>
            <td>{{ num(r.s.fpr) }}</td><td>{{ num(r.s.ppv) }}</td><td>{{ num(r.s.rhs) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="lab__stats">
      <div class="lab__stat"><b>{{ num(Math.abs(sF.tpr - sM.tpr)) }}</b><span>різниця TPR</span></div>
      <div class="lab__stat"><b>{{ num(Math.abs(sF.fpr - sM.fpr)) }}</b><span>різниця FPR</span></div>
      <div class="lab__stat is-warm"><b>{{ num(Math.abs(sF.ppv - sM.ppv)) }}</b><span>різниця PPV</span></div>
    </div>
    <p class="lab__note">
      Останній стовпчик — права частина тотожності; вона завжди дорівнює FPR своєї групи. Зрівняти можна пару
      показників — наприклад, FPR і PPV, — але тоді розходиться TPR; усі три рівними за різної поширеності не
      бувають. У групах кілька десятків знімків, тому кожна зміна порогу перекидає одразу кілька відсоткових пунктів.
    </p>
  </div>
</template>

<style scoped>
.fa__btns { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.8rem; }
.fa__wrap { overflow-x: auto; }
.fa__table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.fa__table th { font-weight: 500; font-size: 0.75rem; color: var(--vp-c-text-2); text-align: right; padding: 0.3rem 0.5rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; }
.fa__table th:first-child, .fa__table td:first-child { text-align: left; }
.fa__table td { font-size: 0.85rem; text-align: right; padding: 0.3rem 0.5rem !important; border-bottom: 1px solid var(--vp-c-divider) !important; }
</style>
