<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import previousIcon from '@iconify-icons/lucide/chevron-left'
import nextIcon from '@iconify-icons/lucide/chevron-right'
import listIcon from '@iconify-icons/lucide/list'
import maximizeIcon from '@iconify-icons/lucide/maximize'
import minimizeIcon from '@iconify-icons/lucide/minimize'
import notesIcon from '@iconify-icons/lucide/notebook-pen'
import playIcon from '@iconify-icons/lucide/play'
import closeIcon from '@iconify-icons/lucide/x'
import SlideImage from './SlideImage.vue'
import SlidePoints from './SlidePoints.vue'
import SlideTable from './SlideTable.vue'
import { comparisonBest, coverFlow, coverInfo, dataSource, demoFallback, demoPreparation, demoSteps, questions, slides } from './slides.js'

const assets = import.meta.glob('../images/streamlit-*.png', { eager: true, import: 'default', query: '?url' })
const asset = (file) => assets[`../images/${file}`]
const slideNumber = (index) => String(index + 1).padStart(2, '0')
const dashboardUrl = import.meta.env.VITE_DASHBOARD_URL || 'http://127.0.0.1:8501'
const indexFromHash = () => {
  const match = window.location.hash.match(/^#slide-(\d+)$/)
  const index = match ? Number(match[1]) - 1 : 0
  return index >= 0 && index < slides.length ? index : 0
}

const currentIndex = ref(indexFromHash())
const slide = computed(() => slides[currentIndex.value])
const screen = ref(null)
const heading = ref(null)
const panel = ref('')
const closePanelButton = ref(null)
const imageDialog = ref(null)
const zoomed = ref(null)
const isFullscreen = ref(false)
const comparisonSummary = ['Accuracy và Precision cao nhất', 'Recall và ROC-AUC cao nhất', 'F1 test cao nhất, dùng 16 đặc trưng']
const closingMetrics = [['0,6077', 'F1 lớp rời bỏ'], ['76,20%', 'Recall'], ['285/374', 'Khách rời bỏ được phát hiện']]
let panelTrigger

function syncSlide() {
  currentIndex.value = indexFromHash()
}

function go(index, focusTitle = false) {
  if (index < 0 || index >= slides.length || index === currentIndex.value) return
  window.history.pushState(null, '', `#slide-${index + 1}`)
  syncSlide()
  if (focusTitle) nextTick(() => heading.value?.focus({ preventScroll: true }))
}

function openPanel(name, trigger) {
  panelTrigger = trigger
  panel.value = name
  nextTick(() => closePanelButton.value?.focus())
}

function closePanel(focusTrigger = true) {
  panel.value = ''
  if (focusTrigger) nextTick(() => panelTrigger?.focus())
}

function selectSlide(index) {
  closePanel(false)
  go(index)
  nextTick(() => heading.value?.focus({ preventScroll: true }))
}

async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen()
    else await screen.value.requestFullscreen()
  } catch {
    // The slide stage already fills the browser viewport.
  }
}

function syncFullscreen() {
  isFullscreen.value = document.fullscreenElement === screen.value
}

function handleKey(event) {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || imageDialog.value?.open) return
  if (event.key === 'Escape' && panel.value) {
    event.preventDefault()
    closePanel()
    return
  }
  if (panel.value || event.target.closest?.('input, textarea, select, [contenteditable]')) return

  const key = event.key.toLowerCase()
  if (key === 'f' && !event.repeat) {
    toggleFullscreen()
    return
  }
  if (key === 'm' || key === 'n') {
    openPanel(key === 'm' ? 'outline' : 'notes', document.activeElement)
    return
  }

  const targets = {
    ArrowLeft: currentIndex.value - 1,
    PageUp: currentIndex.value - 1,
    ArrowRight: currentIndex.value + 1,
    PageDown: currentIndex.value + 1,
    Home: 0,
    End: slides.length - 1,
  }
  if (Object.hasOwn(targets, event.key) || (event.key === ' ' && !event.target.closest?.('button, a, summary'))) {
    event.preventDefault()
    go(targets[event.key] ?? currentIndex.value + 1, true)
  }
}

async function showImage() {
  zoomed.value = slide.value.image
  await nextTick()
  imageDialog.value.showModal()
}

function coefficient(value) {
  return Number(value.replace('−', '-').replace(',', '.'))
}

onMounted(() => {
  window.addEventListener('popstate', syncSlide)
  window.addEventListener('hashchange', syncSlide)
  window.addEventListener('keydown', handleKey)
  document.addEventListener('fullscreenchange', syncFullscreen)
})

onUnmounted(() => {
  window.removeEventListener('popstate', syncSlide)
  window.removeEventListener('hashchange', syncSlide)
  window.removeEventListener('keydown', handleKey)
  document.removeEventListener('fullscreenchange', syncFullscreen)
})
</script>

<template>
  <div ref="screen" class="screen">
    <main class="stage" :inert="Boolean(panel)">
      <article :key="currentIndex" class="slide" :class="`slide--${slide.layout}`" aria-labelledby="slide-heading">
        <header v-if="slide.layout !== 'cover'" class="slide-header">
          <div class="chapter">{{ slide.chapter }}</div>
          <h1 id="slide-heading" ref="heading" tabindex="-1">{{ slide.title }}</h1>
        </header>

        <div v-if="slide.layout === 'cover'" class="cover">
          <div class="chapter">IBM Telco Customer Churn</div>
          <h1 id="slide-heading" ref="heading" tabindex="-1">{{ slide.statements[0] }}</h1>
          <SlidePoints :points="slide.points" />
          <ol class="flow cover-flow">
            <li v-for="step in coverFlow" :key="step">{{ step }}</li>
          </ol>
          <dl class="cover-meta">
            <div v-for="[label, value] in coverInfo" :key="label"><dt>{{ label }}</dt><dd>{{ value }}</dd></div>
          </dl>
        </div>

        <SlideTable v-else-if="slide.layout === 'roster'" class="roster slide-body" :table="slide.table" />

        <div v-else-if="slide.layout === 'comparison'" class="stack slide-body">
          <p class="lead">{{ slide.statements[0] }}</p>
          <SlideTable :table="slide.table" :best="comparisonBest" />
          <div class="tiles comparison-cards">
            <div v-for="([name], index) in slide.table.rows" :key="name" class="tile">
              <h2>{{ name }}</h2><p>{{ comparisonSummary[index] }}</p>
            </div>
          </div>
        </div>

        <div v-else-if="slide.layout === 'matrix'" class="split slide-body">
          <div class="chart-sheet">
            <h2>{{ slide.statements[0] }}</h2>
            <SlideTable class="matrix-table" :table="slide.table" />
          </div>
          <div class="stack">
            <div v-for="(point, index) in slide.points.slice(0, 2)" :key="point" class="tile metric">
              <span>{{ index === 0 ? 'Recall' : 'Precision' }}</span>
              <strong>{{ index === 0 ? '76,20%' : '50,53%' }}</strong>
              <span>{{ index === 0 ? '285 / 374 khách rời bỏ' : '285 / 564 cảnh báo' }}</span>
            </div>
            <SlidePoints :points="slide.points.slice(2)" />
          </div>
        </div>

        <div v-else-if="slide.layout === 'coefficients'" class="split slide-body">
          <figure class="chart-sheet">
            <figcaption>{{ slide.statements[0] }}</figcaption>
            <ul class="coefficient-chart">
              <li v-for="[name, value] in slide.table.rows" :key="name">
                <span>{{ name }}</span>
                <span class="coefficient-track" aria-hidden="true">
                  <span class="coefficient-bar" :class="{ negative: coefficient(value) < 0 }" :style="{ width: Math.abs(coefficient(value)) / 0.6 * 50 + '%' }"></span>
                </span>
                <strong>{{ value }}</strong>
              </li>
            </ul>
          </figure>
          <SlidePoints :points="slide.points" />
        </div>

        <div v-else-if="slide.layout === 'closing'" class="stack slide-body">
          <h2 class="result-label">{{ slide.statements[1] }}</h2>
          <dl class="tiles">
            <div v-for="[value, label] in closingMetrics" :key="label" class="tile metric"><dt>{{ label }}</dt><dd>{{ value }}</dd></div>
          </dl>
          <div class="split closing-columns">
            <section v-for="(label, index) in [slide.statements[0], slide.statements[3]]" :key="label">
              <h2>{{ label }}</h2>
              <SlidePoints :points="slide.points.slice(index * 3, index * 3 + 3)" />
            </section>
          </div>
          <p class="thanks">{{ slide.statements[4] }}</p>
        </div>

        <div v-else class="slide-body stack">
          <ol v-if="slide.layout === 'retraining'" class="flow retraining-flow">
            <li v-for="step in slide.statements[0].split(' → ')" :key="step">{{ step }}</li>
          </ol>
          <p v-else-if="['encoding', 'training'].includes(slide.layout)" class="banner">
            {{ slide.layout === 'encoding' ? 'Train 80% · Test 20% · Seed 42' : slide.statements[1] }}
          </p>

          <div v-if="slide.layout === 'scaling'" class="split scaling">
            <p class="formula">{{ slide.statements[0] }}</p>
            <p class="banner">{{ slide.statements[2] }}</p>
          </div>

          <div class="split" :class="{ 'split--wide-media': ['retraining', 'demo', 'quality'].includes(slide.layout) }">
            <div class="stack">
              <template v-if="slide.layout === 'quality'">
                <p class="lead">{{ slide.statements[0] }}</p>
                <div class="data-count" aria-label="7.043 khách hàng ban đầu, còn 7.032 hồ sơ sau làm sạch">7.043 <span aria-hidden="true">→</span> 7.032</div>
              </template>
              <SlideTable v-if="['attributes', 'models', 'training'].includes(slide.layout)" :table="slide.table" />
              <template v-if="slide.layout === 'demo'">
                <section v-for="(label, index) in slide.statements.slice(0, 2)" :key="label" class="demo-copy">
                  <h2>{{ label }}</h2>
                  <SlidePoints :points="index === 0 ? slide.points.slice(0, 2) : slide.points.slice(2)" />
                </section>
              </template>
              <SlidePoints v-else-if="slide.points.length" :points="slide.points" />
              <template v-if="slide.layout === 'models'">
                <p class="detail">{{ slide.statements[0] }}</p>
                <p class="banner">{{ slide.statements[1] }} · MonthlyCharges</p>
              </template>
              <p v-if="slide.layout === 'smote'" class="banner">{{ slide.statements[0] }}</p>
              <p v-if="slide.layout === 'scaling'" class="detail">Bảng minh họa trên train gốc. Scaler Logistic được fit sau SMOTE.</p>
              <p v-if="slide.layout === 'retraining'" class="banner">{{ slide.statements[1] }}</p>
              <a v-if="slide.layout === 'quality'" class="source-link" :href="dataSource" target="_blank" rel="noopener">Nguồn dữ liệu IBM Telco ↗</a>
            </div>

            <div v-if="slide.image" class="media">
              <SlideImage :src="asset(slide.image.file)" :alt="slide.image.alt" @zoom="showImage" />
              <p v-if="slide.layout === 'training'" class="caption">Logistic điều chỉnh · Recall kiểm định chéo ≈ 77,5%</p>
              <template v-if="slide.layout === 'demo'">
                <p class="caption">Kết quả ba khách hàng mẫu trong lần chạy đã chụp</p>
                <a class="demo-link" :href="dashboardUrl" target="_blank" rel="noopener"><Icon :icon="playIcon" /> Mở ứng dụng Streamlit</a>
              </template>
            </div>
          </div>
          <p v-if="slide.layout === 'demo'" class="banner">{{ slide.statements[2] }}</p>
        </div>

        <footer class="slide-footer" aria-hidden="true">
          <span>Telco Customer Churn</span><span>{{ slideNumber(currentIndex) }} / {{ slides.length }}</span>
        </footer>
      </article>
      <div class="sr-only" role="status">Slide {{ currentIndex + 1 }} trên {{ slides.length }}. {{ slide.title }}</div>
    </main>

    <nav class="controls" :inert="Boolean(panel)" aria-label="Điều khiển trình chiếu">
      <button type="button" aria-label="Slide trước" title="Slide trước (←)" :disabled="currentIndex === 0" @click="go(currentIndex - 1)"><Icon :icon="previousIcon" /></button>
      <button type="button" aria-label="Slide tiếp theo" title="Slide tiếp theo (→)" :disabled="currentIndex === slides.length - 1" @click="go(currentIndex + 1)"><Icon :icon="nextIcon" /></button>
      <button type="button" aria-label="Mục lục" title="Mục lục (M)" @click="openPanel('outline', $event.currentTarget)"><Icon :icon="listIcon" /></button>
      <button type="button" aria-label="Lời thoại" title="Lời thoại (N)" @click="openPanel('notes', $event.currentTarget)"><Icon :icon="notesIcon" /></button>
      <button type="button" :aria-label="isFullscreen ? 'Thoát toàn màn hình' : 'Toàn màn hình'" title="Toàn màn hình (F)" @click="toggleFullscreen"><Icon :icon="isFullscreen ? minimizeIcon : maximizeIcon" /></button>
    </nav>

    <div v-if="panel" class="panel-backdrop" @click.self="closePanel()">
      <aside class="side-panel" aria-labelledby="panel-title">
        <div class="panel-heading">
          <h2 id="panel-title">{{ panel === 'outline' ? 'Mục lục' : 'Lời thoại' }}</h2>
          <button ref="closePanelButton" type="button" aria-label="Đóng bảng bên" @click="closePanel()"><Icon :icon="closeIcon" /></button>
        </div>
        <ol v-if="panel === 'outline'" class="outline-list">
          <li v-for="(item, index) in slides" :key="item.title">
            <button type="button" :aria-current="currentIndex === index ? 'step' : undefined" @click="selectSlide(index)">
              <span>{{ slideNumber(index) }}</span>{{ item.title }}
            </button>
          </li>
        </ol>
        <div v-else class="speaker-notes">
          <p class="caption">Slide {{ currentIndex + 1 }} · {{ slide.notes.duration }}</p>
          <h3>{{ slide.title }}</h3>
          <template v-if="slide.layout === 'demo'">
            <h4>Chuẩn bị</h4>
            <ul><li v-for="item in demoPreparation" :key="item">{{ item }}</li></ul>
            <section v-for="[time, action, speech] in demoSteps" :key="time">
              <h4>{{ time }} · {{ action }}</h4><p>{{ speech }}</p>
            </section>
            <h4>Khi chiếu ảnh demo</h4>
            <p v-for="paragraph in demoFallback" :key="paragraph">{{ paragraph }}</p>
          </template>
          <p v-for="paragraph in slide.notes.paragraphs" :key="paragraph">{{ paragraph }}</p>
          <template v-if="slide.notes.transition"><h4>Chuyển ý</h4><p>{{ slide.notes.transition }}</p></template>
          <details v-if="slide.layout === 'closing'">
            <summary>Câu hỏi phản biện</summary>
            <section v-for="[question, answer] in questions" :key="question"><h4>{{ question }}</h4><p>{{ answer }}</p></section>
          </details>
        </div>
      </aside>
    </div>

    <dialog ref="imageDialog" class="image-dialog" aria-label="Ảnh phóng to" @click.self="imageDialog.close()">
      <figure v-if="zoomed">
        <figcaption>{{ zoomed.alt }} <button type="button" autofocus aria-label="Đóng ảnh" @click="imageDialog.close()"><Icon :icon="closeIcon" /></button></figcaption>
        <img :src="asset(zoomed.file)" :alt="zoomed.alt">
      </figure>
    </dialog>
  </div>
</template>
