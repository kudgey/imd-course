<script setup lang="ts">
/** Таблиця з датами або етапами інциденту як вертикальна хронологія. */
defineProps<{ items: { k: string; v: string; extra?: string }[] }>()
</script>

<template>
  <ol class="tml">
    <li v-for="(it, i) in items" :key="i" class="tml__item">
      <span class="tml__dot" aria-hidden="true" />
      <div class="tml__body">
        <b class="tml__k" v-html="it.k" />
        <span class="tml__v" v-html="it.v" />
        <span v-if="it.extra" class="tml__extra" v-html="it.extra" />
      </div>
    </li>
  </ol>
</template>

<style scoped>
.tml { list-style: none; margin: 1.6rem 0; padding: 0 0 0 1.1rem; position: relative; }
.tml::before {
  content: '';
  position: absolute;
  left: 0.32rem;
  top: 0.5rem;
  bottom: 0.5rem;
  width: 2px;
  background: var(--uk-line);
}
.tml__item { position: relative; display: flex; gap: 0.7rem; padding: 0.45rem 0; }
.tml__dot {
  position: absolute;
  left: -0.95rem;
  top: 0.85rem;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--uk-accent);
  border: 2px solid var(--vp-c-bg);
}
.tml__body { display: flex; flex-direction: column; gap: 0.1rem; }
.tml__k {
  font-family: var(--vp-font-family-mono);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--uk-accent);
}
.tml__v { font-size: 0.86rem; line-height: 1.5; }
.tml__extra { font-size: 0.78rem; line-height: 1.45; color: var(--vp-c-text-3); }
</style>
