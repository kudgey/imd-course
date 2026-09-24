<script setup lang="ts">
/**
 * Таблиця «поняття → пояснення» у вигляді сітки карток.
 * Джерело те саме, що йде в Gamma: у `.src.md` це звичайна markdown-таблиця,
 * загорнута маркером ::: cards. Жодне слово не втрачається.
 */
withDefaults(
  defineProps<{
    items: { k: string; v: string; extra?: string }[]
    accent?: 'accent' | 'warm' | 'green'
    numbered?: boolean
  }>(),
  { accent: 'accent', numbered: false }
)
</script>

<template>
  <div class="cds" :class="'is-' + accent">
    <div v-for="(it, i) in items" :key="i" class="cds__item">
      <span v-if="numbered" class="cds__n">{{ i + 1 }}</span>
      <div class="cds__body">
        <b class="cds__k" v-html="it.k" />
        <span class="cds__v" v-html="it.v" />
        <span v-if="it.extra" class="cds__extra" v-html="it.extra" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.cds {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
  gap: 0.6rem;
  margin: 1.6rem 0;
}
.cds__item {
  display: flex;
  gap: 0.6rem;
  align-items: flex-start;
  padding: 0.75rem 0.85rem;
  border: 1px solid var(--uk-line);
  border-left: 3px solid var(--uk-accent);
  border-radius: 9px;
  background: var(--vp-c-bg);
  transition: border-color 0.16s ease, transform 0.16s ease;
}
.is-warm .cds__item { border-left-color: var(--uk-warm); }
.is-green .cds__item { border-left-color: var(--uk-green); }
.cds__item:hover { transform: translateY(-1px); border-color: var(--uk-accent); }
.is-warm .cds__item:hover { border-color: var(--uk-warm); }
.is-green .cds__item:hover { border-color: var(--uk-green); }
.cds__n {
  flex: none;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 50%;
  background: var(--uk-accent-soft);
  color: var(--uk-accent);
  font-family: var(--vp-font-family-mono);
  font-size: 0.72rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 0.1rem;
}
.is-warm .cds__n { background: var(--uk-warm-soft); color: var(--uk-warm); }
.is-green .cds__n { background: var(--uk-green-soft); color: var(--uk-green); }
.cds__body { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.cds__k { font-size: 0.9rem; font-weight: 600; line-height: 1.35; letter-spacing: -0.01em; }
.cds__v { font-size: 0.83rem; line-height: 1.5; color: var(--vp-c-text-2); }
.cds__extra {
  font-size: 0.76rem;
  line-height: 1.45;
  color: var(--vp-c-text-3);
  font-family: var(--vp-font-family-mono);
  margin-top: 0.1rem;
}
.cds :deep(code) { font-size: 0.85em; }
</style>
