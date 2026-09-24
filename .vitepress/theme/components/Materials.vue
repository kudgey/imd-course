<script setup lang="ts">
/**
 * Матеріали до розділу: першоджерела, документація, інтерактивні демо.
 * Стоять поруч із темою, а не загальним списком у кінці — щоб студент
 * читав їх тоді, коли питання виникло, а не через сорок розділів.
 */
defineProps<{
  items: { title: string; url: string; kind?: string; note?: string }[]
}>()

const ICON: Record<string, string> = {
  PDF: '📄', стаття: '📄', книга: '📘', документація: '⚙',
  демо: '▶', курс: '🎓', код: '⌨', дані: '📊', відео: '▶'
}
</script>

<template>
  <aside class="mt">
    <div class="mt__head">Матеріали до розділу</div>
    <ul class="mt__list">
      <li v-for="it in items" :key="it.url">
        <a :href="it.url" target="_blank" rel="noopener">
          <span class="mt__icon">{{ ICON[it.kind || ''] || '↗' }}</span>
          <span class="mt__title">{{ it.title }}</span>
          <span v-if="it.kind" class="mt__kind">{{ it.kind }}</span>
        </a>
        <p v-if="it.note" class="mt__note">{{ it.note }}</p>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.mt {
  margin: 1.6rem 0;
  padding: 0.95rem 1.15rem 1rem;
  border: 1px solid var(--uk-line);
  border-left: 3px solid var(--uk-green);
  border-radius: 0 10px 10px 0;
  background: var(--uk-fill);
}
.mt__head {
  font-size: 0.74rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--vp-c-text-3);
  margin-bottom: 0.6rem;
}
.mt__list { list-style: none; margin: 0; padding: 0; }
.mt__list li + li { margin-top: 0.55rem; }
.mt__list a {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--vp-c-text-1);
  font-size: 0.92rem;
  line-height: 1.45;
}
.mt__list a:hover .mt__title {
  color: var(--uk-accent);
  border-bottom-color: currentColor;
}
.mt__icon { flex: none; font-size: 0.88rem; opacity: 0.75; }
.mt__title { border-bottom: 1px solid transparent; }
.mt__kind {
  flex: none;
  font-size: 0.68rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--vp-c-text-3);
  border: 1px solid var(--uk-line);
  border-radius: 4px;
  padding: 0.05em 0.35em;
  background: var(--vp-c-bg);
}
.mt__note {
  margin: 0.2rem 0 0 1.9rem;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--vp-c-text-3);
}
</style>
