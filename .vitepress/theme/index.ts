import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import './style.css'

import Figure from './components/Figure.vue'
import RunOutput from './components/RunOutput.vue'
import CodeFold from './components/CodeFold.vue'
import PresToggle from './components/PresToggle.vue'
import CourseHome from './components/CourseHome.vue'
import Materials from './components/Materials.vue'
import Cards from './components/Cards.vue'
import Steps from './components/Steps.vue'
import Compare from './components/Compare.vue'
import Timeline from './components/Timeline.vue'
import Resources from './components/Resources.vue'
import Flow from './components/Flow.vue'

// Віджети лекцій (*Lab.vue) реєструються автоматично за іменем файлу:
// новий віджет не потребує правки цього файла.
const labs = import.meta.glob('./components/*Lab.vue', { eager: true }) as Record<string, { default: any }>

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-bottom': () => h(PresToggle),
    })
  },
  enhanceApp({ app }) {
    app.component('Figure', Figure)
    app.component('RunOutput', RunOutput)
    app.component('CodeFold', CodeFold)
    app.component('CourseHome', CourseHome)
    app.component('Materials', Materials)
    app.component('Cards', Cards)
    app.component('Steps', Steps)
    app.component('Compare', Compare)
    app.component('Timeline', Timeline)
    app.component('Resources', Resources)
    app.component('Flow', Flow)
    for (const [path, mod] of Object.entries(labs)) {
      app.component(path.split('/').pop()!.replace('.vue', ''), mod.default)
    }
  },
} satisfies Theme
