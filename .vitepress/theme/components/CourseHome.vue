<script setup lang="ts">
/** Головна: карта курсу за розділами силабусу. Назви — з .vitepress/course.json. */
import { withBase, useData } from 'vitepress'
import course from '../../course.json'

const { theme } = useData()
const published: string[] = theme.value.published ?? []
</script>

<template>
  <div class="uk-hero">
    <div class="uk-hero__eyebrow">КПІ ім. Ігоря Сікорського · магістратура · 2026/2027</div>
    <h1>{{ course.title }}</h1>
    <p class="uk-hero__lead">
      Вісімнадцять лекцій про те, як із медичного зображення отримати діагностично
      корисну відповідь і як перевірити, що їй можна довіряти. Наскрізний приклад —
      грудна клітка: рентгенограми для скринінгу туберкульозу та КТ-серії легень
      у форматі DICOM. Кожен метод проходить один шлях: клінічна задача → дані
      та їхні дефекти → принцип методу → код → результат на відкритих даних →
      обмеження. Усі дані відкриті й деідентифіковані; прототипи курсу не є
      медичними виробами.
    </p>
    <p class="uk-hero__author">Kirill Riazanovskiy, PhD</p>
  </div>

  <div class="uk-blocks">
    <section v-for="b in course.blocks" :key="b.code" class="uk-block">
      <div class="uk-block__tag">РОЗДІЛ {{ b.code }}</div>
      <h3>{{ b.name }}</h3>
      <p class="uk-block__lead">{{ b.lead }}</p>
      <ol :start="Number(b.lectures[0].n)">
        <li v-for="l in b.lectures" :key="l.n">
          <a v-if="published.includes(l.n)" :href="withBase(`/lectures/${l.n}`)">{{ l.t }}</a>
          <span v-else>{{ l.t }}</span>
        </li>
      </ol>
    </section>
  </div>

  <section class="uk-sources">
    <h3>Джерела курсу</h3>
    <p>
      Основа курсу — довідники
      <a href="https://doi.org/10.1016/C2017-0-04608-6">Zhou, Rueckert, Fichtinger. Handbook of
      Medical Image Computing and Computer Assisted Intervention (2020)</a> та
      <a href="https://doi.org/10.1016/B978-0-12-373904-9.X0001-4">Bankman. Handbook of Medical
      Image Processing and Analysis (2009)</a>, підручник
      <a href="https://www.deeplearningbook.org/">Goodfellow, Bengio, Courville. Deep Learning (2016)</a>,
      стандарт <a href="https://www.dicomstandard.org/current">DICOM (NEMA)</a> і документація
      <a href="https://monai.readthedocs.io/en/stable/">MONAI</a>.
    </p>
    <p class="uk-sources__note">
      Статті, набори даних і документація до кожної теми — в останньому розділі кожної лекції.
    </p>
  </section>
</template>

<style scoped>
.uk-hero__author {
  margin-top: 1.4rem;
  font-size: 0.95rem;
  color: var(--vp-c-text-2);
  border-left: 3px solid var(--uk-accent);
  padding-left: 0.8rem;
}
.uk-block__lead {
  font-size: 0.86rem;
  line-height: 1.5;
  color: var(--vp-c-text-3);
  margin: 0 0 0.7rem;
}
.uk-block ol { list-style: decimal; }
.uk-block ol li::marker {
  font-family: var(--vp-font-family-mono);
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
}


.uk-sources {
  margin-top: 2.5rem;
  padding-top: 1.8rem;
  border-top: 1px solid var(--uk-line);
}
.uk-sources h3 {
  margin: 0 0 0.8rem;
  font-size: 1rem;
  letter-spacing: -0.01em;
}
.uk-sources p {
  margin: 0 0 0.7rem;
  font-size: 0.86rem;
  line-height: 1.6;
  color: var(--vp-c-text-2);
  max-width: 78ch;
}
.uk-sources__note {
  color: var(--vp-c-text-3);
}
</style>
