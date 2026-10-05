<script setup lang="ts">
/**
 * Журнал аудиту з ланцюжком SHA-256 (лекція 18, розділ «Журнал аудиту»). Шість записів — ті самі,
 * що пише блок коду (tools/gen_lec18_audit.py). Хеші рахуються в браузері через Web Crypto від
 * канонічного JSON без поля hash: ключі за абеткою, значення — рядки, без пробілів. Генератор
 * у --check запускає цю саму канонізацію в Node і звіряє хеші з Python і з виводом блоку.
 */
import { ref, computed, onMounted, watch } from 'vue'
import data from '../../data/lec18_audit.json'

type Rec = Record<string, string>
const ORIGINAL = data.records as Rec[]
const ANCHOR = data.anchor as string
const ZERO = '0'.repeat(64)

const recs = ref<Rec[]>(ORIGINAL.map(r => ({ ...r })))
const actual = ref<string[]>([]) // хеш, перерахований від вмісту кожного запису
const ready = ref(false)
const noCrypto = ref(false)

const canon = (r: Rec) =>
  '{' + Object.keys(r).filter(k => k !== 'hash').sort().map(k => JSON.stringify(k) + ':' + JSON.stringify(r[k])).join(',') + '}'

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('')
}

async function recompute() {
  if (noCrypto.value) return
  actual.value = await Promise.all(recs.value.map(r => sha256(canon(r))))
  ready.value = true
}

onMounted(() => {
  if (typeof crypto === 'undefined' || !crypto.subtle) {
    noCrypto.value = true
    return
  }
  recompute()
})
watch(recs, recompute, { deep: true })

const marks = computed(() =>
  recs.value.map((r, i) => {
    const prevOk = r.prev === (i === 0 ? ZERO : recs.value[i - 1].hash)
    const selfOk = actual.value[i] === r.hash
    return prevOk && selfOk
  }),
)
const firstBad = computed(() => marks.value.findIndex(ok => !ok))
const anchorOk = computed(() => recs.value[recs.value.length - 1].hash === ANCHOR)
const edited = computed(() => recs.value.some((r, i) => Object.keys(r).some(k => r[k] !== ORIGINAL[i][k])))

function reset() {
  recs.value = ORIGINAL.map(r => ({ ...r }))
}
function tamper() {
  reset()
  const i = Number(data.tamper.n) - 1
  recs.value[i][data.tamper.field] = data.tamper.value
}
async function rewriteTail() {
  // «підчищення»: від першого зламаного запису до кінця перераховуємо prev і hash
  const start = firstBad.value
  if (start < 0 || noCrypto.value) return
  const next = recs.value.map(r => ({ ...r }))
  for (let i = start; i < next.length; i++) {
    next[i].prev = i === 0 ? ZERO : next[i - 1].hash
    next[i].hash = await sha256(canon(next[i]))
  }
  recs.value = next
}
const short = (h: string) => h.slice(0, 12)
// у записі число зберігається з крапкою (як у JSON, від якого рахується хеш); на екрані — з комою
const comma = (s: string) => s.replace('.', ',')
function setScore(r: Rec, e: Event) {
  r.score = (e.target as HTMLInputElement).value.replace(',', '.')
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Ланцюжок SHA-256: що видно після зміни запису</div>
        <div class="lab__sub">
          Змініть оцінку, рішення або дію лікаря в будь-якому записі — хеші перераховуються в браузері. Останній хеш
          дня («якір») збережено окремо від журналу.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': !edited }" @click="reset">чистий журнал</button>
      <button type="button" class="lab__pill" @click="tamper">змінити запис {{ data.tamper.n }}, як у коді</button>
      <button type="button" class="lab__btn" :disabled="firstBad < 0 || noCrypto" @click="rewriteTail">перерахувати хвіст</button>
    </div>

    <p v-if="noCrypto" class="lab__note">Браузер не дає доступу до Web Crypto (сторінку відкрито не через https чи localhost) — хеші не перераховуються.</p>

    <div class="ac__wrap">
      <table class="ac__table">
        <thead>
          <tr><th>№</th><th>оцінка</th><th>рішення</th><th>лікар</th><th>prev</th><th>hash</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in recs" :key="r.n" :class="{ 'is-bad': ready && !marks[i] }">
            <td>{{ r.n }}</td>
            <td><input :value="comma(r.score)" class="ac__in" type="text" :aria-label="`оцінка запису ${r.n}`" @input="setScore(r, $event)"></td>
            <td>
              <select v-model="r.decision" :aria-label="`рішення запису ${r.n}`">
                <option>Xpert</option><option>без Xpert</option>
              </select>
            </td>
            <td>
              <select v-model="r.reader" :aria-label="`дія лікаря в записі ${r.n}`">
                <option>погодився</option><option>не погодився</option>
              </select>
            </td>
            <td><code>{{ short(r.prev) }}</code></td>
            <td><code :title="ready ? `перераховано: ${short(actual[i])}` : ''">{{ short(r.hash) }}</code></td>
            <td class="ac__mark">{{ ready ? (marks[i] ? '✓' : '✗') : '…' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="lab__stats">
      <div class="lab__stat" :class="firstBad < 0 ? 'is-green' : 'is-warm'">
        <b>{{ !ready ? '…' : firstBad < 0 ? 'цілий' : `з № ${firstBad + 1}` }}</b><span>ланцюжок записів</span>
      </div>
      <div class="lab__stat" :class="anchorOk ? 'is-green' : 'is-warm'">
        <b>{{ anchorOk ? 'збігся' : 'не збігся' }}</b><span>якір {{ short(ANCHOR) }} і останній hash</span>
      </div>
      <div class="lab__stat"><b>{{ ready && firstBad >= 0 ? short(actual[firstBad]) : '—' }}</b><span>перерахований хеш зламаного запису</span></div>
    </div>

    <p class="lab__note">
      Зміна поля ламає саме цей запис: його збережений hash більше не відповідає вмісту. Кнопка «перерахувати хвіст»
      робить те, що зробив би зловмисник із доступом до всього журналу: перераховує prev і hash до кінця — і кожен запис
      знову цілий. Видає підміну лише якір, збережений поза журналом.
    </p>
  </div>
</template>

<style scoped>
.ac__wrap { width: 100%; overflow-x: auto; }
.ac__table { width: 100%; border-collapse: collapse; font-size: 0.8rem; min-width: 330px; }
.ac__table th, .ac__table td { border: none; border-bottom: 1px solid var(--uk-line); padding: 0.28rem 0.3rem; text-align: left; background: none; }
.ac__table th { font-weight: 500; color: var(--vp-c-text-3); font-size: 0.74rem; }
.ac__table code { font-size: 0.72rem; }
.ac__table select, .ac__in { font-size: 0.78rem; padding: 0.15rem 0.25rem; border: 1px solid var(--uk-line); border-radius: 5px; background: var(--vp-c-bg); color: var(--vp-c-text-1); max-width: 7.5rem; }
.ac__in { width: 4.6rem; font-family: var(--vp-font-family-mono); }
.ac__mark { font-weight: 600; text-align: center !important; }
tr.is-bad td { background: var(--uk-warm-soft); }
tr.is-bad .ac__mark { color: var(--uk-warm); }
</style>
