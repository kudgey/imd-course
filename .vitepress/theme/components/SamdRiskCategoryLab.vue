<script setup lang="ts">
/**
 * Категорія IMDRF і клас MDR для програми (лекція 18, розділ «Класифікація програмного
 * забезпечення за MDR»). Дев’ять клітинок «значущість інформації × стан» — IMDRF N12 §7.2 і
 * MDCG 2019-11 rev.1, Annex III, Table 1; наслідки класу — MDR ст. 52(6) і AIB 2025-1 / MDCG 2025-6,
 * Table 1. Дані пише tools/gen_lec18_samd.py; його --check звіряє клітинки з PDF першоджерел і
 * з рядком тексту «drive × serious → II.ii → IIa» (пресет «прототип курсу»).
 */
import { ref, computed } from 'vue'
import data from '../../data/lec18_samd.json'

type Cell = { sig: string; state: string; imdrf: string; label: string; mdr: string; notified_body: boolean; high_risk: boolean }
type Axis = { key: string; ua: string; en: string }
type Preset = { name: string; sig: string; state: string; why: string }

const SIG = data.sig as Axis[]
const STATE = data.state as Axis[]
const CELLS = data.cells as Cell[]
const PRESETS = data.presets as Preset[]

const sig = ref(PRESETS[0].sig)
const state = ref(PRESETS[0].state)
const cellOf = (g: string, s: string) => CELLS.find(c => c.sig === g && c.state === s) as Cell
const cur = computed(() => cellOf(sig.value, state.value))
const preset = computed(() => PRESETS.find(p => p.sig === sig.value && p.state === state.value))
const proto = PRESETS[0]
const level = (cls: string) => (cls === 'III' ? 'is-high' : cls === 'IIb' ? 'is-mid' : 'is-low')
function pick(p: Preset) {
  sig.value = p.sig
  state.value = p.state
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Від призначення до класу: IMDRF і правило 11 MDR</div>
        <div class="lab__sub">
          Оберіть значущість інформації і стан пацієнта — клітинкою таблиці або одним із варіантів призначення.
          Таблиця відтворює MDCG 2019-11 rev.1, Annex III, Table 1.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="p in PRESETS" :key="p.name" type="button" class="lab__pill"
              :class="{ 'is-on': preset && preset.name === p.name }" @click="pick(p)">{{ p.name }}</button>
    </div>

    <div class="sr__wrap">
      <table class="sr__table">
        <thead>
          <tr>
            <th class="sr__corner">стан ↓ / значущість →</th>
            <th v-for="g in SIG" :key="g.key"><span>{{ g.ua }}</span><small>{{ g.en }}</small></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in STATE" :key="s.key">
            <th><span>{{ s.ua }}</span><small>{{ s.en }}</small></th>
            <td v-for="g in SIG" :key="g.key">
              <button type="button" class="sr__cell" :class="[level(cellOf(g.key, s.key).mdr), { 'is-on': g.key === sig && s.key === state }]"
                      :aria-label="`${s.ua}, ${g.ua}`" @click="sig = g.key; state = s.key">
                <b>{{ cellOf(g.key, s.key).mdr }}</b>
                <span>кат. {{ cellOf(g.key, s.key).label }}</span>
                <i v-if="g.key === proto.sig && s.key === proto.state">прототип</i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ cur.imdrf }}</b><span>категорія IMDRF (N12, §7.2)</span></div>
      <div class="lab__stat"><b>{{ cur.label }}</b><span>позначка в Table 1 MDCG</span></div>
      <div class="lab__stat is-warm"><b>{{ cur.mdr }}</b><span>клас MDR за правилом 11</span></div>
      <div class="lab__stat"><b>{{ cur.notified_body ? 'так' : 'ні' }}</b><span>нотифікований орган (ст. 52(6) MDR)</span></div>
      <div class="lab__stat is-green"><b>{{ cur.high_risk ? 'високий' : '—' }}</b><span>ризик за AI Act, ст. 6(1); вимоги з {{ data.ai_act_date }}</span></div>
    </div>

    <p class="lab__note">
      <template v-if="preset"><b>{{ preset.name }}:</b> {{ preset.why }}. </template>
      Таблиця «intended for illustrative purposes only» і не враховує програм класу I; клас визначає виробник за
      власним призначенням. Позначку I.i в нижньому правому куті надруковано так у самій Table 1. Будь-яка клітинка
      таблиці — клас IIa або вище, тобто нотифікований орган і система високого ризику за AI Act.
    </p>
  </div>
</template>

<style scoped>
.sr__wrap { width: 100%; overflow-x: auto; }
.sr__table { width: 100%; border-collapse: separate; border-spacing: 4px; table-layout: fixed; min-width: 300px; }
.sr__table th { font-weight: 500; font-size: 0.78rem; color: var(--vp-c-text-2); text-align: center; padding: 0.2rem; line-height: 1.25; border: none; background: none; }
.sr__table tbody th { text-align: right; width: 22%; }
.sr__table th small { display: block; font-size: 0.68rem; color: var(--vp-c-text-3); }
.sr__corner { font-size: 0.7rem !important; color: var(--vp-c-text-3) !important; width: 22%; }
.sr__table td { padding: 0; border: none; background: none; }
.sr__cell { width: 100%; min-height: 64px; border: 1px solid var(--uk-line); border-radius: 8px; background: var(--vp-c-bg); cursor: pointer;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.1rem; padding: 0.35rem 0.2rem; position: relative; }
.sr__cell b { font-size: 1.05rem; font-weight: 600; }
.sr__cell span { font-size: 0.7rem; color: var(--vp-c-text-3); }
.sr__cell i { font-style: normal; font-size: 0.62rem; color: var(--uk-accent); }
.sr__cell.is-low b { color: var(--uk-accent); }
.sr__cell.is-mid b { color: var(--uk-warm); }
.sr__cell.is-high b { color: var(--uk-warm); text-decoration: underline; }
.sr__cell.is-low { background: var(--uk-accent-soft); }
.sr__cell.is-mid, .sr__cell.is-high { background: var(--uk-warm-soft); }
.sr__cell.is-on { outline: 2px solid var(--uk-ink); outline-offset: 1px; }
</style>
