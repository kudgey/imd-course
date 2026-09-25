<script setup lang="ts">
/**
 * Оглядач заголовка першого файлу LIDC-IDRI-0001 (TCIA, CC BY 3.0): 97 елементів даних —
 * 8 у групі 0002 і 89 у наборі даних. Для кожного — тег, ключове слово, VR, VM, значення,
 * пояснення (що задає, що зламається без нього) і сирі байти з файлу (явний VR, little endian).
 * Звірка з кодом: байти (0008,0060) Modality — 08 00 60 00 43 53 02 00 43 54, як у виводі блоку
 * розділу «Файл DICOM…». Дані пише tools/gen_lec03_tags.py.
 */
import { ref, computed } from 'vue'
import data from '../../data/lec03_tags.json'

type Item = {
  tag: string; group: string; keyword: string; name: string; vr: string; vm: number; value: string
  offset: number; head: number; length: number; hex: string; more: number; what: string; broken: string
}
type Group = { g: string; label: string; n: number }

const items = data.items as Item[]
const groups = data.groups as Group[]
const query = ref('')
const group = ref('')
const selected = ref('(0008,0060)')

const shown = computed(() => {
  const q = query.value.trim().toLowerCase()
  return items.filter(it =>
    (!group.value || it.group === group.value) &&
    (!q || `${it.tag} ${it.keyword} ${it.name} ${it.value} ${it.vr}`.toLowerCase().includes(q)))
})
const groupLabel = computed(() => groups.find(g => g.g === group.value)?.label ?? 'усі групи')
const short = (s: string, n = 34) => (s.length > n ? s.slice(0, n - 1) + '…' : s)

/** Сирі байти елемента, розбиті на поля: тег, VR, [резерв], довжина, значення */
function fields(it: Item) {
  const b = it.hex.split(' ')
  const out = [
    { k: 'тег', v: b.slice(0, 4).join(' '), cls: 'is-tag' },
    { k: 'VR', v: b.slice(4, 6).join(' ') + ` («${it.vr}»)`, cls: 'is-vr' },
  ]
  if (it.head === 12) {
    out.push({ k: 'резерв', v: b.slice(6, 8).join(' '), cls: 'is-res' })
    out.push({ k: 'довжина', v: b.slice(8, 12).join(' ') + ` (${it.length})`, cls: 'is-len' })
  } else {
    out.push({ k: 'довжина', v: b.slice(6, 8).join(' ') + ` (${it.length})`, cls: 'is-len' })
  }
  const val = b.slice(it.head).join(' ')
  out.push({ k: 'значення', v: (val || '—') + (it.more ? ` … ще ${it.more} байт` : ''), cls: 'is-val' })
  return out
}
const cur = computed(() => items.find(it => it.tag === selected.value) ?? null)
const n = (v: number) => String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
const pix = items.find(it => it.keyword === 'PixelData') as Item
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Заголовок файлу DICOM: усі елементи даних</div>
        <div class="lab__sub">
          Файл 00000001.dcm серії LIDC-IDRI-0001, {{ n(data.size) }} байт, синтаксис {{ data.syntax }}.
          Торкніться елемента в списку — праворуч (на телефоні — під списком) з’являться пояснення і його байти у файлі.
        </div>
      </div>
    </div>

    <div class="lab__controls dt__controls">
      <label class="lab__ctl">
        <span>пошук: тег, ключове слово, значення</span>
        <input type="text" v-model="query" placeholder="наприклад, Pixel або 0028" />
      </label>
      <label class="lab__ctl">
        <span>група: {{ groupLabel }}</span>
        <select v-model="group">
          <option value="">усі групи ({{ items.length }})</option>
          <option v-for="g in groups" :key="g.g" :value="g.g">{{ g.g }} — {{ g.label }} ({{ g.n }})</option>
        </select>
      </label>
    </div>

    <div class="dt__grid">
      <div>
        <div class="dt__count">показано {{ shown.length }} з {{ items.length }}</div>
        <ul class="dt__list">
          <li v-for="it in shown" :key="it.tag" :class="{ 'is-open': selected === it.tag, 'is-private': it.keyword === '(приватний)' }">
            <button type="button" class="dt__row" :aria-pressed="selected === it.tag" @click="selected = it.tag">
              <span class="dt__tag">{{ it.tag }}</span>
              <span class="dt__kw">{{ it.keyword }}</span>
              <span class="dt__vr">{{ it.vr }}·{{ it.vm }}</span>
              <span class="dt__val">{{ it.vm === 0 ? '(порожньо)' : short(it.value) }}</span>
            </button>
          </li>
        </ul>
      </div>
      <div v-if="cur" class="dt__detail" aria-live="polite">
        <div class="dt__dhead"><span class="dt__tag">{{ cur.tag }}</span> <b>{{ cur.keyword }}</b></div>
        <div class="dt__name">
          <template v-if="cur.name">{{ cur.name }} — назва в словнику PS3.6; </template>VR {{ cur.vr }}, VM {{ cur.vm }}
        </div>
        <div class="dt__full"><b>значення:</b> {{ cur.vm === 0 ? '(порожньо)' : cur.value }}</div>
        <p><b>Що задає:</b> {{ cur.what }}.</p>
        <p><b>Що зламається без нього:</b> {{ cur.broken }}.</p>
        <div class="dt__bytes-cap">байти у файлі від зміщення {{ n(cur.offset) }}: заголовок {{ cur.head }} байтів + значення {{ n(cur.length) }}</div>
        <div class="dt__bytes">
          <span v-for="f in fields(cur)" :key="f.k" class="dt__field" :class="f.cls">
            <i>{{ f.k }}</i><span class="dt__hex">{{ f.v }}</span>
          </span>
        </div>
      </div>
    </div>

    <p class="lab__note">
      Номери груп стандартних атрибутів парні; три елементи непарної групи 0013 — приватні, їх записала програма
      CTP. Значення з VR «DS» і «IS» — числа, записані текстом, тому товщина зрізу виглядає як «2.500000». Порожні
      елементи (VM 0) лишилися після деідентифікації: атрибут є, значення немає. Найбільший елемент — PixelData:
      заголовок {{ pix.head }} байтів і {{ n(pix.length) }} байтів пікселів; усе, що над ним, займає перші {{ n(pix.offset) }} байтів файлу.
    </p>
  </div>
</template>

<style scoped>
.dt__controls { grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); margin-bottom: 0.6rem; }
.dt__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}
@media (max-width: 760px) { .dt__grid { grid-template-columns: 1fr; } }
.dt__count { font-size: 0.75rem; color: var(--vp-c-text-3); margin-bottom: 0.35rem; }
.dt__list {
  list-style: none;
  margin: 0 !important;
  padding: 0 !important;
  max-height: 430px;
  overflow-y: auto;
  border: 1px solid var(--uk-line);
  border-radius: 8px;
}
@media (max-width: 760px) { .dt__list { max-height: 300px; } }
.dt__list li { margin: 0 !important; border-top: 1px solid var(--uk-line); }
.dt__list li:first-child { border-top: 0; }
.dt__row {
  display: grid;
  grid-template-columns: 6.6em minmax(0, 1fr) auto;
  column-gap: 0.5rem;
  row-gap: 0.05rem;
  width: 100%;
  padding: 0.35rem 0.6rem;
  background: transparent;
  border: 0;
  text-align: left;
  font: inherit;
  font-size: 0.8rem;
  line-height: 1.35;
  color: var(--vp-c-text-1);
  cursor: pointer;
}
.dt__row:hover, .is-open > .dt__row { background: var(--uk-accent-soft); }
.dt__tag { font-family: var(--vp-font-family-mono); font-size: 0.76rem; color: var(--uk-accent); }
.dt__kw { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.is-private .dt__kw { color: var(--uk-warm); }
.dt__vr { font-family: var(--vp-font-family-mono); font-size: 0.72rem; color: var(--vp-c-text-3); white-space: nowrap; }
.dt__val {
  grid-column: 2 / -1;
  font-family: var(--vp-font-family-mono);
  font-size: 0.72rem;
  color: var(--vp-c-text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dt__detail {
  border: 1px solid var(--uk-line);
  border-radius: 8px;
  padding: 0.6rem 0.8rem 0.75rem;
  background: var(--uk-fill);
  font-size: 0.82rem;
  line-height: 1.5;
  min-width: 0;
}
.dt__detail p { margin: 0.3rem 0 !important; }
.dt__dhead { font-size: 0.9rem; }
.dt__name { font-size: 0.74rem; color: var(--vp-c-text-3); }
.dt__full { font-family: var(--vp-font-family-mono); font-size: 0.74rem; word-break: break-all; margin-top: 0.25rem; }
.dt__bytes-cap { font-size: 0.74rem; color: var(--vp-c-text-3); margin-top: 0.45rem; }
.dt__bytes { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.3rem; }
.dt__field {
  display: inline-flex;
  flex-direction: column;
  border-radius: 6px;
  padding: 0.2rem 0.45rem;
  border: 1px solid var(--uk-line);
  background: var(--vp-c-bg);
  max-width: 100%;
}
.dt__field i { font-style: normal; font-size: 0.66rem; color: var(--vp-c-text-3); }
.dt__hex { font-family: var(--vp-font-family-mono); font-size: 0.74rem; word-break: break-all; }
.dt__field.is-tag .dt__hex { color: var(--uk-accent); }
.dt__field.is-vr .dt__hex { color: var(--uk-green); }
.dt__field.is-len .dt__hex { color: var(--uk-warm); }
</style>
