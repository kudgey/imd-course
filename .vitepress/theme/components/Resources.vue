<script setup lang="ts">
/**
 * Добірка зовнішніх матеріалів за темою картки.
 * Тип ресурсу визначається з адреси, тому в джерелі досить звичайного посилання:
 * у Gamma це лишається таблицею з клікабельними назвами.
 */
import { computed } from 'vue'

const props = defineProps<{ items: { k: string; v: string; extra?: string }[] }>()

const KIND: [RegExp, string, string][] = [
  [/\.pdf($|\?)/i, 'PDF', 'pdf'],
  [/github\.com/i, 'репозиторій', 'repo'],
  [/arxiv\.org/i, 'стаття', 'paper'],
  [/(youtube|youtu\.be)/i, 'відео', 'video'],
  [/registry\./i, 'реєстр', 'repo'],
  [/(docs\.|documentation|\/docs\/)/i, 'документація', 'doc'],
]

function meta(html: string) {
  const m = html.match(/href="([^"]+)"/)
  const url = m ? m[1] : ''
  for (const [rx, label, cls] of KIND) if (rx.test(url)) return { label, cls, url }
  return { label: 'гайд', cls: 'guide', url }
}

const rows = computed(() => props.items.map((it) => ({ ...it, ...meta(it.k) })))
</script>

<template>
  <div class="rsc">
    <div v-for="(r, i) in rows" :key="i" class="rsc__item" :class="'is-' + r.cls">
      <span class="rsc__badge">{{ r.label }}</span>
      <div class="rsc__body">
        <span class="rsc__name" v-html="r.k" />
        <span class="rsc__desc" v-html="r.v" />
      </div>
      <span class="rsc__host">{{ r.url.replace(/^https?:\/\//, '').split('/')[0] }}</span>
    </div>
  </div>
</template>

<style scoped>
.rsc { display: flex; flex-direction: column; gap: 0.4rem; margin: 1.6rem 0; }
.rsc__item {
  display: flex;
  align-items: baseline;
  gap: 0.7rem;
  padding: 0.55rem 0.8rem;
  border: 1px solid var(--uk-line);
  border-radius: 9px;
  background: var(--vp-c-bg);
  transition: border-color 0.16s ease, transform 0.16s ease;
}
.rsc__item:hover { border-color: var(--uk-accent); transform: translateX(2px); }
.rsc__badge {
  flex: none;
  font-size: 0.66rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.2rem 0.45rem;
  border-radius: 5px;
  background: var(--uk-fill);
  color: var(--vp-c-text-3);
  min-width: 6.4rem;
  text-align: center;
}
.is-doc .rsc__badge { background: var(--uk-accent-soft); color: var(--uk-accent); }
.is-repo .rsc__badge { background: var(--uk-fill); color: var(--vp-c-text-2); }
.is-paper .rsc__badge { background: var(--uk-green-soft); color: var(--uk-green); }
.is-pdf .rsc__badge { background: var(--uk-warm-soft); color: var(--uk-warm); }
.is-video .rsc__badge { background: var(--uk-warm-soft); color: var(--uk-warm); }
.rsc__body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 0.1rem; }
.rsc__name { font-size: 0.88rem; font-weight: 500; line-height: 1.4; }
.rsc__name :deep(a) { color: var(--uk-accent); text-decoration: none; border-bottom: 1px solid transparent; }
.rsc__name :deep(a:hover) { border-bottom-color: var(--uk-accent); }
.rsc__desc { font-size: 0.8rem; line-height: 1.45; color: var(--vp-c-text-2); }
.rsc__host {
  flex: none;
  font-family: var(--vp-font-family-mono);
  font-size: 0.68rem;
  color: var(--vp-c-text-3);
}
@media (max-width: 640px) {
  .rsc__item { flex-wrap: wrap; }
  .rsc__host { display: none; }
}
</style>
