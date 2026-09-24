<script setup lang="ts">
/**
 * Два режими:
 *   три колонки — «ознака | A | B», зліва підпис рядка;
 *   дві колонки — паралельні списки («Що фіксує протокол | Що лишається вашим»),
 *   де підпису рядка немає і обидві колонки рівноправні.
 */
import { computed } from 'vue'

const props = defineProps<{
  head: string[]
  items: { k: string; v: string; extra?: string }[]
}>()

const twoCol = computed(() => props.head.filter(Boolean).length === 2)
</script>

<template>
  <div class="cmp" :class="{ 'is-two': twoCol }">
    <div class="cmp__heads">
      <span v-if="!twoCol" class="cmp__label">{{ head[0] }}</span>
      <span class="cmp__side is-a">{{ twoCol ? head[0] : head[1] }}</span>
      <span class="cmp__side is-b">{{ twoCol ? head[1] : head[2] }}</span>
    </div>
    <div v-for="(it, i) in items" :key="i" class="cmp__row">
      <span v-if="!twoCol" class="cmp__label" v-html="it.k" />
      <span class="cmp__cell is-a" v-html="twoCol ? it.k : it.v" />
      <span class="cmp__cell is-b" v-html="twoCol ? it.v : it.extra" />
    </div>
  </div>
</template>

<style scoped>
.cmp { margin: 1.6rem 0; border: 1px solid var(--uk-line); border-radius: 10px; overflow: hidden; }
.cmp__heads, .cmp__row {
  display: grid;
  grid-template-columns: minmax(6rem, 1fr) 1.4fr 1.4fr;
  gap: 0.7rem;
  padding: 0.6rem 0.85rem;
  align-items: start;
}
.cmp__heads { background: var(--uk-fill); border-bottom: 1px solid var(--uk-line); }
.cmp__row + .cmp__row { border-top: 1px solid var(--uk-line); }
.cmp__label { font-size: 0.8rem; color: var(--vp-c-text-3); line-height: 1.4; }
.cmp__heads .cmp__label { font-weight: 600; color: var(--vp-c-text-2); }
.cmp__side { font-size: 0.84rem; font-weight: 600; }
.cmp__side.is-a { color: var(--uk-accent); }
.cmp__side.is-b { color: var(--uk-warm); }
.cmp__cell { font-size: 0.84rem; line-height: 1.5; }
.cmp__cell.is-a { color: var(--vp-c-text-1); }
.cmp__cell.is-b { color: var(--vp-c-text-1); }
.cmp__row:hover { background: var(--uk-fill); }
.cmp.is-two .cmp__heads,
.cmp.is-two .cmp__row { grid-template-columns: 1fr 1fr; }
.cmp.is-two .cmp__cell.is-a { font-weight: 500; }
@media (max-width: 620px) {
  .cmp__heads { display: none; }
  .cmp__row { grid-template-columns: 1fr; gap: 0.2rem; }
  .cmp__cell.is-a::before { content: '▸ '; color: var(--uk-accent); }
  .cmp__cell.is-b::before { content: '▸ '; color: var(--uk-warm); }
}
</style>
