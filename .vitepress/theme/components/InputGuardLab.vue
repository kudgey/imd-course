<script setup lang="ts">
/**
 * Страж входу за тегами DICOM (лекція 18, розділ «Страж входу за призначенням»). Правила ті
 * самі, що в блоці коду: клас SOP і модальність CR/DX, проєкція PA, вік від 15 до 120 років,
 * BitsStored ≥ 10 і один канал. Набори тегів — сім синтетичних заголовків блоку і заголовок
 * файлів miniJSRT; очікуване рішення кожного набору пише tools/gen_lec18_guard.py, його --check
 * звіряє рішення з виводом блоку.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec18_guard.json'

type Preset = { name: string; note: string; sop: string; modality: string; view: string; age: number | null; age_src: string; bits: number; spp: number; reasons: string[]; accepted: boolean }
const PRESETS = data.presets as Preset[]

const SOPS = [
  { key: 'DX', ua: 'Digital X-Ray (DX)' },
  { key: 'CR', ua: 'Computed Radiography (CR)' },
  { key: 'SC', ua: 'Secondary Capture — вторинний знімок' },
  { key: 'CT', ua: 'CT Image — КТ' },
]
const sop = ref('DX')
const modality = ref('DX')
const view = ref('PA')
const ageKnown = ref(true)
const age = ref(45)
const bits = ref(12)
const spp = ref(1)
const active = ref<string>(PRESETS[0].name)

const fmt = (v: number) => v.toFixed(1).replace('.', ',').replace('-', '−')
const reasons = computed(() => {
  const why: string[] = []
  if (!['CR', 'DX'].includes(sop.value) || !['CR', 'DX'].includes(modality.value))
    why.push(`не рентгенограма CR/DX (${modality.value || '—'})`)
  if (view.value !== 'PA') why.push(`проєкція ${view.value || 'невідома'}, потрібна PA`)
  if (!ageKnown.value) why.push('вік невідомий')
  else if (!(age.value >= 15 && age.value < 120)) why.push(`вік ${fmt(age.value)} р. поза 15–120`)
  if (bits.value < 10 || spp.value !== 1) why.push('не сирий сірий знімок (біти/канали)')
  return why
})
const preset = computed(() => PRESETS.find(p => p.name === active.value))
// причини з коду (Python, десяткова крапка) порівнюємо з причинами віджета (кома, мінус −) дослівно
const norm = (s: string) => s.replace(/(\d)\.(\d)/g, '$1,$2').replace(/-(\d)/g, '−$1')
const same = computed(() => {
  const p = preset.value
  if (!p) return null
  const a = p.reasons.map(norm)
  const b = reasons.value
  return a.length === b.length && a.every((r, i) => r === b[i])
})

function load(p: Preset) {
  active.value = p.name
  sop.value = p.sop
  modality.value = p.modality
  view.value = p.view
  ageKnown.value = p.age !== null
  age.value = p.age ?? 45
  bits.value = p.bits
  spp.value = p.spp
}
function touch() {
  active.value = ''
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Страж входу: протипоказання як правила</div>
        <div class="lab__sub">
          Змінюйте теги заголовка DICOM або оберіть випадок із коду. Кожне правило — рядок призначення виробу;
          будь-яка причина означає відмову ще до моделі.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="p in PRESETS" :key="p.name" type="button" class="lab__pill" :class="{ 'is-on': active === p.name }"
              @click="load(p)">{{ p.name }}</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl"><span>клас SOP</span>
        <select v-model="sop" @change="touch"><option v-for="s in SOPS" :key="s.key" :value="s.key">{{ s.ua }}</option></select>
      </label>
      <label class="lab__ctl"><span>Modality</span>
        <select v-model="modality" @change="touch"><option>DX</option><option>CR</option><option>OT</option><option>CT</option></select>
      </label>
      <label class="lab__ctl"><span>ViewPosition</span>
        <select v-model="view" @change="touch"><option>PA</option><option>AP</option><option>LL</option><option value="">тегу немає</option></select>
      </label>
      <label class="lab__ctl"><span>вік, років: <b>{{ ageKnown ? fmt(age) : 'невідомий' }}</b></span>
        <input v-model.number="age" type="range" min="-1" max="100" step="0.1" :disabled="!ageKnown" aria-label="Вік у роках" @input="touch">
        <span class="ig__chk"><input v-model="ageKnown" type="checkbox" @change="touch"> вік відомий (PatientAge або дати)</span>
      </label>
      <label class="lab__ctl"><span>BitsStored</span>
        <select v-model.number="bits" @change="touch"><option :value="8">8</option><option :value="10">10</option><option :value="12">12</option><option :value="16">16</option></select>
      </label>
      <label class="lab__ctl"><span>SamplesPerPixel</span>
        <select v-model.number="spp" @change="touch"><option :value="1">1 (сірий)</option><option :value="3">3 (RGB)</option></select>
      </label>
    </div>

    <div class="ig__verdict" :class="reasons.length ? 'is-no' : 'is-yes'">
      <b>{{ reasons.length ? 'ВІДМОВА' : 'ПРИЙНЯТО' }}</b>
      <ul v-if="reasons.length"><li v-for="r in reasons" :key="r">{{ r }}</li></ul>
      <span v-else>знімок іде до попередньої обробки й моделі</span>
    </div>

    <p class="lab__note">
      <template v-if="preset">
        <b>{{ preset.name }}</b> ({{ preset.note }}<template v-if="preset.age_src === 'дати'">; вік обчислено з дат</template>):
        у виводі коду — {{ preset.accepted ? 'прийнято' : `відмова, причин ${preset.reasons.length}` }};
        тут — {{ same ? 'те саме' : 'інакше' }}.
      </template>
      Для miniJSRT дата народження пізніша за дату дослідження, тож вік із дат від’ємний, а тегу проєкції немає
      зовсім — такий вхід неможливо перевірити, і страж відмовляє з трьох причин.
    </p>
  </div>
</template>

<style scoped>
.ig__chk { display: flex !important; align-items: center; gap: 0.35rem; font-size: 0.74rem; margin-top: 0.3rem; color: var(--vp-c-text-3); }
.ig__verdict { border-radius: 8px; padding: 0.6rem 0.8rem; border: 1px solid var(--uk-line); }
.ig__verdict b { display: block; font-size: 1rem; letter-spacing: 0.02em; }
.ig__verdict ul { margin: 0.3rem 0 0; padding-left: 1.1rem; font-size: 0.84rem; }
.ig__verdict span { font-size: 0.84rem; color: var(--vp-c-text-2); }
.ig__verdict.is-yes { background: var(--uk-accent-soft); }
.ig__verdict.is-yes b { color: var(--uk-green); }
.ig__verdict.is-no { background: var(--uk-warm-soft); }
.ig__verdict.is-no b { color: var(--uk-warm); }
</style>
