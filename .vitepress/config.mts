import { defineConfig } from 'vitepress'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import course from './course.json'

// GitHub Pages у підкаталозі вимагає base='/<репозиторій>/'.
// Задається змінною оточення, тому той самий код працює і на власному домені.
// Той самий base потрібен і для тегів у <head>: вони не проходять через withBase.
const base = process.env.BASE ?? '/'

// Лекція потрапляє в сайдбар посиланням лише тоді, коли її сторінка існує:
// інакше живий сайт віддасть 404 на клік. Решта назв — просто текст.
const root = fileURLToPath(new URL('..', import.meta.url))
const published = course.blocks
  .flatMap(b => b.lectures.map(l => l.n))
  .filter(n => existsSync(`${root}lectures/${n}.md`))

export default defineConfig({
  title: course.short,
  description: `Магістерський курс «${course.title}». КПІ ім. Ігоря Сікорського.`,
  lang: 'uk-UA',
  base,
  cleanUrls: true,
  srcExclude: ['README.md'],
  markdown: {
    math: true,
    lineNumbers: true,
    theme: { light: 'github-light', dark: 'github-dark' },
    image: { lazyLoading: true }
  },
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: base + 'favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#3D4EC4' }],
    ['meta', { property: 'og:title', content: course.title }],
  ],
  themeConfig: {
    published,
    outline: { level: [2, 2], label: 'На цій сторінці' },
    nav: [
      ...(published.length ? [{ text: 'Лекції', link: `/lectures/${published[0]}` }] : []),
      { text: 'Лабораторні', link: '/labs' }
    ],
    sidebar: [
      { text: 'Курс', items: [
        { text: 'Огляд і структура', link: '/' },
        { text: 'Лабораторні роботи', link: '/labs' }
      ]},
      ...course.blocks.map(b => ({
        text: `Розділ ${b.code} · ${b.short}`,
        collapsed: false,
        items: b.lectures.map(l => ({
          text: `${l.n} · ${l.t}`,
          ...(published.includes(l.n) ? { link: `/lectures/${l.n}` } : {})
        }))
      })),
    ],
    docFooter: { prev: 'Попередня', next: 'Наступна' },
    darkModeSwitchLabel: 'Тема',
    lightModeSwitchTitle: 'Світла тема',
    darkModeSwitchTitle: 'Темна тема',
    sidebarMenuLabel: 'Розділи',
    returnToTopLabel: 'Догори',
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: 'Пошук', buttonAriaLabel: 'Пошук' },
          modal: {
            noResultsText: 'Нічого не знайдено',
            resetButtonTitle: 'Очистити',
            footer: { selectText: 'вибрати', navigateText: 'навігація', closeText: 'закрити' }
          }
        }
      }
    },
    footer: {
      message: 'Матеріали курсу. Схеми із зовнішніх джерел належать їхнім авторам — посилання під кожною ілюстрацією.',
      copyright: 'КПІ ім. Ігоря Сікорського · 2026/2027'
    }
  }
})
