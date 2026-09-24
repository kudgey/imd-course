<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { withBase } from 'vitepress'

defineProps<{ src: string; alt?: string }>()

const zoomed = ref<string | null>(null)

function open(src: string) {
  zoomed.value = src
  document.addEventListener('keydown', onKey)
}
function close() {
  zoomed.value = null
  document.removeEventListener('keydown', onKey)
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <figure class="uk-figure">
    <div class="uk-figure__frame" @click="open(withBase(src))" :title="'Збільшити: ' + (alt || '')">
      <img :src="withBase(src)" :alt="alt" loading="lazy" />
    </div>
    <figcaption class="uk-figure__caption">
      <slot />
    </figcaption>
  </figure>

  <Teleport to="body">
    <div v-if="zoomed" class="uk-lightbox" @click="close">
      <img :src="zoomed" :alt="alt" />
    </div>
  </Teleport>
</template>
