<script setup lang="ts">
/**
 * Ознаки для CDR > 0 в OASIS-1 (лекція 14, розділ «Нейрозображення і когнітивні шкали: OASIS-1»).
 * Дані — tools/gen_lec14_oasis.py: перша сесія кожної особи віком ≥ 60 років з відомою CDR (198 осіб; до 60 років
 * хворих у наборі немає за дизайном), логістична регресія (порожні клітинки — медіаною навчального фолду,
 * стандартизація), п’ять стратифікованих фолдів; AUC для кожної з 127
 * непорожніх підмножин семи ознак. У JSON лише похідні AUC, без рядків таблиці (умови OASIS).
 * Підмножини з виводу блоку коду збігаються (перевіряє --check генератора).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec14_oasis.json'

const FEATS = data.features as string[]
const AUC = data.auc as Record<string, number>
const NAME: Record<string, string> = {
  Age: 'вік', 'чоловік': 'стать', Educ: 'освіта', SES: 'соц.-екон. статус', nWBV: 'nWBV (об’єм мозку)',
  eTIV: 'eTIV (внутрішньочерепний об’єм)', MMSE: 'MMSE (когнітивний тест)',
}
const on = ref<Record<string, boolean>>({ Age: true, nWBV: true })
const sel = computed(() => FEATS.filter((f) => on.value[f]))
const cur = computed(() => (sel.value.length ? AUC[sel.value.join(' + ')] : null))
const bestNoMmse = Object.entries(AUC).filter(([k]) => !k.includes('MMSE')).sort((a, b) => b[1] - a[1])[0]
const bestAll = Object.entries(AUC).sort((a, b) => b[1] - a[1])[0]
const singles = FEATS.map((f) => ({ f, v: AUC[f] })).sort((a, b) => b.v - a.v)
const num = (v: number, d = 3) => v.toFixed(d).replace('.', ',')
const pretty = (k: string) => k.split(' + ').map((f) => NAME[f] ?? f).join(' + ')
const toggle = (f: string) => { on.value = { ...on.value, [f]: !on.value[f] } }
const W = 100
const X = (v: number) => ((Math.max(0.5, v) - 0.5) / 0.5) * W
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">OASIS-1: які ознаки відрізняють CDR &gt; 0 від CDR = 0</div>
        <div class="lab__sub">
          {{ data.n }} осіб віком від 60 років із відомою CDR (молодших хворих у наборі немає за дизайном), з них
          {{ data.n_pos }} з CDR &gt; 0; логістична регресія, AUC на п’яти стратифікованих фолдах. Дані надано OASIS (OASIS-1: Cross-Sectional), некомерційне академічне використання.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <div class="lab__ctl">
        <span>ознаки моделі</span>
        <div class="lab__pills">
          <button v-for="f in FEATS" :key="f" type="button" class="lab__pill" :class="{ 'is-on': on[f], 'is-mmse': f === 'MMSE' }"
            @click="toggle(f)">{{ NAME[f] ?? f }}</button>
        </div>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat is-warm"><b>{{ cur === null ? '—' : num(cur) }}</b><span>AUC обраного набору</span></div>
      <div class="lab__stat"><b>{{ num(bestNoMmse[1]) }}</b><span>найкраща без MMSE: {{ pretty(bestNoMmse[0]) }}</span></div>
      <div class="lab__stat"><b>{{ num(bestAll[1]) }}</b><span>найкраща взагалі: {{ pretty(bestAll[0]) }}</span></div>
    </div>

    <div class="oa__bars">
      <div class="oa__cap">AUC кожної ознаки окремо</div>
      <div v-for="s in singles" :key="s.f" class="oa__row" :class="{ 'is-on': on[s.f] }">
        <div class="oa__name">{{ NAME[s.f] ?? s.f }}</div>
        <div class="oa__track"><i :style="{ width: X(s.v) + '%' }" :class="{ 'is-mmse': s.f === 'MMSE' }"></i></div>
        <div class="oa__val">{{ num(s.v) }}</div>
      </div>
      <div class="oa__axis"><span>0,5</span><span>0,75</span><span>1</span></div>
    </div>
    <p class="lab__note">
      Вік сам не розрізняє групи (0,478), а з об’ємом мозку, статтю, освітою і статусом не піднімається вище 0,745.
      Варто ввімкнути MMSE — і AUC стрибає до 0,86–0,90: когнітивний тест — частина тієї самої клінічної оцінки, з якої виводять CDR.
    </p>
  </div>
</template>

<style scoped>
.oa__bars { margin-top: 0.7rem; display: grid; gap: 0.3rem; }
.oa__cap { font-size: 0.76rem; color: var(--vp-c-text-3); }
.oa__row { display: grid; grid-template-columns: minmax(7rem, 14rem) 1fr 3rem; gap: 0.5rem; align-items: center; font-size: 0.8rem; opacity: 0.6; }
.oa__row.is-on { opacity: 1; font-weight: 600; }
.oa__name { color: var(--vp-c-text-2); }
.oa__track { background: var(--uk-fill); height: 11px; border-radius: 3px; overflow: hidden; }
.oa__track i { display: block; height: 100%; background: var(--uk-accent); }
.oa__track i.is-mmse { background: var(--uk-warm); }
.oa__val { text-align: right; color: var(--vp-c-text-2); }
.oa__axis { display: grid; grid-template-columns: minmax(7rem, 14rem) 1fr 3rem; gap: 0.5rem; font-size: 0.7rem; color: var(--vp-c-text-3); }
.oa__axis span:nth-child(1) { grid-column: 2; justify-self: start; }
.oa__axis span:nth-child(2) { grid-column: 2; justify-self: center; grid-row: 1; }
.oa__axis span:nth-child(3) { grid-column: 2; justify-self: end; grid-row: 1; }
.lab__pill.is-mmse.is-on { border-color: var(--uk-warm); color: var(--uk-warm); }
@media (max-width: 480px) {
  .oa__row, .oa__axis { grid-template-columns: 6.5rem 1fr 2.6rem; }
}
</style>
