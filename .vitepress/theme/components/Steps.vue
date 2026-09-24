<script setup lang="ts">
/** Таблиця «крок → що відбувається» як конвеєр із стрілками. */
withDefaults(
  defineProps<{ items: { k: string; v: string; extra?: string }[]; accent?: string }>(),
  { accent: 'accent' }
)
</script>

<template>
  <div class="stp" :class="'is-' + accent">
    <template v-for="(it, i) in items" :key="i">
      <div class="stp__node">
        <span class="stp__n">{{ i + 1 }}</span>
        <b v-html="it.k" />
        <span v-html="it.v" />
        <em v-if="it.extra" v-html="it.extra" />
      </div>
      <span v-if="i < items.length - 1" class="stp__arrow" aria-hidden="true">→</span>
    </template>
  </div>
</template>

<style scoped>
.stp { display: flex; flex-wrap: wrap; align-items: stretch; gap: 0.4rem; margin: 1.6rem 0; }
.stp__node {
  flex: 1 1 9rem;
  min-width: 9rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--uk-line);
  border-top: 3px solid var(--uk-accent);
  border-radius: 9px;
  background: var(--vp-c-bg);
}
.is-warm .stp__node { border-top-color: var(--uk-warm); }
.is-green .stp__node { border-top-color: var(--uk-green); }
.stp__n {
  font-family: var(--vp-font-family-mono);
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--uk-accent);
  letter-spacing: 0.06em;
}
.is-warm .stp__n { color: var(--uk-warm); }
.is-green .stp__n { color: var(--uk-green); }
.stp__node b { font-size: 0.86rem; font-weight: 600; line-height: 1.3; }
.stp__node span { font-size: 0.79rem; line-height: 1.45; color: var(--vp-c-text-2); }
.stp__node em {
  font-style: normal;
  font-size: 0.72rem;
  color: var(--vp-c-text-3);
  font-family: var(--vp-font-family-mono);
}
.stp__arrow { align-self: center; color: var(--vp-c-text-3); font-size: 1rem; }
@media (max-width: 640px) {
  .stp { flex-direction: column; }
  .stp__arrow { transform: rotate(90deg); align-self: flex-start; margin-left: 1.5rem; }
}
</style>
