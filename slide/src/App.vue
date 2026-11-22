<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import chartIcon from '@iconify-icons/lucide/chart-no-axes-combined'
import previousIcon from '@iconify-icons/lucide/chevron-left'
import nextIcon from '@iconify-icons/lucide/chevron-right'
import databaseIcon from '@iconify-icons/lucide/database'
import listIcon from '@iconify-icons/lucide/list'
import minimizeIcon from '@iconify-icons/lucide/minimize'
import notesIcon from '@iconify-icons/lucide/notebook-pen'
import playIcon from '@iconify-icons/lucide/play'
import signalIcon from '@iconify-icons/lucide/signal'
import closeIcon from '@iconify-icons/lucide/x'
import SlideImage from './SlideImage.vue'
import SlideTable from './SlideTable.vue'
import { courseName, coverInfo, demoNotes, demoPreparation, demoSteps, olsNotes, questions, retrainingSteps, slides } from './slides.js'

const assets = import.meta.glob('../images/streamlit-*.png', { eager: true, import: 'default', query: '?url' })
const image = (name) => assets[`../images/${name}`]
const slideNumber = (index) => String(index + 1).padStart(2, '0')
const indexFromHash = () => {
  const match = window.location.hash.match(/^#slide-(\d+)$/)
  const index = match ? Number(match[1]) - 1 : 0
  return index >= 0 && index < slides.length ? index : 0
}

const currentIndex = ref(indexFromHash())
const slide = computed(() => slides[currentIndex.value])
const sceneIndex = ref(slide.value.scenes ? slide.value.scenes.length - 1 : 0)
const activeScene = computed(() => slide.value.scenes?.[sceneIndex.value])
const panel = ref('')
const presenting = ref(false)
const zoomed = ref(null)
const heading = ref(null)
const host = ref(null)
const dialog = ref(null)
const closePanelButton = ref(null)
let panelTrigger = null

function syncSlide() {
  currentIndex.value = indexFromHash()
  sceneIndex.value = slide.value.scenes ? slide.value.scenes.length - 1 : 0
}

function go(index, focusTitle = false) {
  if (index < 0 || index >= slides.length || index === currentIndex.value) return
  window.history.pushState(null, '', `#slide-${index + 1}`)
  syncSlide()
  if (focusTitle) nextTick(() => heading.value?.focus({ preventScroll: true }))
}

function togglePanel(name, event) {
  if (panel.value === name) {
    closePanel()
    return
  }
  panelTrigger = event?.currentTarget ?? panelTrigger
  panel.value = name
  nextTick(() => closePanelButton.value?.focus())
}

function closePanel() {
  panel.value = ''
  nextTick(() => panelTrigger?.focus())
}

async function fullscreen() {
  if (presenting.value) {
    if (document.fullscreenElement) await document.exitFullscreen()
    else presenting.value = false
    return
  }
  panel.value = ''
  presenting.value = true
  try { await host.value.requestFullscreen() }
  catch { /* Presentation layout is still available when fullscreen is blocked. */ }
}

function syncFullscreen() {
  presenting.value = Boolean(document.fullscreenElement)
}

function handleKey(event) {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || dialog.value?.open) return
  if (event.key === 'Escape') {
    if (panel.value) closePanel()
    else if (presenting.value && !document.fullscreenElement) presenting.value = false
    return
  }
  if (panel.value || event.target.closest?.('input, textarea, select, [contenteditable]')) return
  if (event.key.toLowerCase() === 'f' && !event.repeat) {
    fullscreen()
    return
  }
  if (event.target.closest?.('[role="tablist"]')) return
  const interactive = event.target.closest?.('button, a')
  const targets = { ArrowLeft: currentIndex.value - 1, PageUp: currentIndex.value - 1,
    ArrowRight: currentIndex.value + 1, PageDown: currentIndex.value + 1, Home: 0, End: slides.length - 1 }
  if (event.key in targets || (event.key === ' ' && !interactive)) {
    event.preventDefault()
    go(targets[event.key] ?? currentIndex.value + 1, true)
  }
}

function changeScene(event, index) {
  const changes = { ArrowLeft: index - 1, ArrowRight: index + 1, Home: 0, End: slide.value.scenes.length - 1 }
  if (!(event.key in changes)) return
  event.preventDefault()
  sceneIndex.value = (changes[event.key] + slide.value.scenes.length) % slide.value.scenes.length
  nextTick(() => host.value.querySelector(`#scene-tab-${sceneIndex.value}`)?.focus())
}

async function showImage({ file, alt }) {
  zoomed.value = { src: image(file), label: alt }
  await nextTick()
  dialog.value.showModal()
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
  <div ref="host" class="shell" :class="{ presenting }">
    <header class="toolbar" :inert="Boolean(panel)">
      <div class="frame-width flex h-full items-center justify-between gap-4">
        <button class="brand flex shrink-0 items-center gap-3" type="button" aria-label="Telco Churn, về slide đầu" @click="go(0)">
          <span class="brand-icon"><Icon :icon="chartIcon" /></span>
          <span>Telco Churn</span>
        </button>
        <div class="toolbar-actions flex items-center gap-2">
          <button type="button" class="utility" :class="{ selected: panel === 'outline' }" :aria-expanded="panel === 'outline'" aria-controls="deck-panel" aria-label="Mục lục" @click="togglePanel('outline', $event)">
            <Icon :icon="listIcon" /> <span>Mục lục</span>
          </button>
          <button type="button" class="utility" :class="{ selected: panel === 'notes' }" :aria-expanded="panel === 'notes'" aria-controls="deck-panel" aria-label="Lời thoại" @click="togglePanel('notes', $event)">
            <Icon :icon="notesIcon" /> <span>Lời thoại</span>
          </button>
          <span class="toolbar-separator" aria-hidden="true"></span>
          <button type="button" class="present-button" :aria-label="presenting ? 'Thoát trình chiếu' : 'Trình chiếu toàn màn hình'" @click="fullscreen">
            <Icon :icon="presenting ? minimizeIcon : playIcon" /> <span>{{ presenting ? 'Thoát' : 'Trình chiếu' }}</span>
          </button>
        </div>
      </div>
    </header>

    <main class="frame-width main-frame" :inert="Boolean(panel)">
      <div class="deck-context flex items-center justify-between gap-3">
        <span class="flex items-center gap-2"><span class="section-dot"></span>{{ slide.section }}</span>
        <span>{{ courseName }}</span>
      </div>

      <article :key="currentIndex" class="slide" :class="`slide--${slide.type}`" aria-labelledby="slide-heading">
        <template v-if="slide.type === 'cover'">
          <div class="cover-copy">
            <div class="section-label">{{ courseName }}</div>
            <h1 id="slide-heading" ref="heading" tabindex="-1">{{ slide.title }}</h1>
            <p>{{ slide.lead }}</p>
            <dl class="cover-meta">
              <div v-for="[label, value] in coverInfo" :key="label"><dt>{{ label }}</dt><dd>{{ value }}</dd></div>
            </dl>
          </div>
          <div class="cover-visual" aria-label="26,58% khách hàng đã rời bỏ trong bộ dữ liệu IBM" role="img">
            <div class="visual-grid"></div>
            <div class="orbit orbit-main"></div><div class="orbit orbit-inner"></div><div class="orbit orbit-outer"></div>
            <div class="orbit-point point-top"></div><div class="orbit-point point-bottom"></div>
            <div class="visual-stat">
              <Icon :icon="signalIcon" />
              <strong>26,58<span>%</span></strong>
              <span>Tỷ lệ khách rời bỏ</span>
            </div>
            <div class="visual-chip sample-chip"><Icon :icon="databaseIcon" /> <div><strong>7.032</strong><span>khách hàng hợp lệ</span></div></div>
            <div class="visual-chip churn-chip"><span></span><div><strong>1.869</strong><span>đã rời bỏ</span></div></div>
            <div class="visual-source">IBM Telco Customer Churn</div>
          </div>
        </template>

        <template v-else>
          <div class="slide-head">
            <div class="section-label">{{ slide.section }}</div>
            <h1 id="slide-heading" ref="heading" tabindex="-1">{{ slide.title }}</h1>
            <p v-if="slide.lead" class="slide-lead">{{ slide.lead }}</p>
          </div>

          <SlideTable v-if="slide.type === 'table'" class="slide-body roster-table" :table="slide.table" />

          <div v-else-if="slide.type === 'demo'" class="slide-body demo-layout">
            <div class="scene-tabs" role="tablist" aria-label="Các cảnh trên dashboard">
              <button v-for="(scene, index) in slide.scenes" :id="`scene-tab-${index}`" :key="scene.label" type="button" role="tab" aria-controls="scene-panel" :aria-selected="sceneIndex === index" :tabindex="sceneIndex === index ? 0 : -1" @click="sceneIndex = index" @keydown="changeScene($event, index)">{{ scene.label }}</button>
            </div>
            <div id="scene-panel" class="demo-panel" role="tabpanel" :aria-labelledby="`scene-tab-${sceneIndex}`">
              <SlideImage :src="image(activeScene.image.file)" :alt="activeScene.image.alt" @zoom="showImage(activeScene.image)" />
              <aside class="demo-results">
                <h2>{{ activeScene.action }}</h2>
                <p class="card-note">{{ activeScene.result }}</p>
                <template v-if="sceneIndex === slide.scenes.length - 1">
                  <div v-for="[id, score, prediction, risk] in slide.rows" :key="id" class="demo-row">
                    <div><strong>{{ id }}</strong><span>{{ prediction }} · {{ risk }}</span></div><b>{{ score }}</b>
                  </div>
                </template>
                <a class="secondary-button" href="http://127.0.0.1:8501" target="_blank" rel="noopener"><Icon :icon="playIcon" /> Mở dashboard</a>
              </aside>
            </div>
          </div>

          <div v-else-if="slide.type === 'comparison'" class="slide-body comparison-layout">
            <SlideTable :table="slide.table" :best="slide.best" />
            <div class="comparison-foot">
              <div class="callout">
                <Icon :icon="chartIcon" />
                <div><strong>76,2% Recall với Logistic điều chỉnh</strong><p>Phát hiện 285 trong 374 khách rời bỏ. Đây là cấu hình mặc định trên dashboard.</p></div>
              </div>
              <SlideImage :src="image(slide.image.file)" :alt="slide.image.alt" crop @zoom="showImage(slide.image)" />
            </div>
          </div>

          <div v-else-if="slide.type === 'closing'" class="slide-body closing-layout">
            <dl class="metric-grid">
              <div v-for="[value, label] in slide.metrics" :key="label" class="tile"><dt>{{ value }}</dt><dd>{{ label }}</dd></div>
            </dl>
            <p class="slide-detail">{{ slide.detail }}</p>
            <p class="closing-thanks">Cảm ơn thầy cô và các bạn đã lắng nghe.</p>
          </div>

          <div v-else class="slide-body evidence-layout" :class="{ 'evidence-layout--wide': slide.layout === 'wide' }">
            <ol v-if="slide.steps" class="flow-steps" aria-label="Các bước huấn luyện lại">
              <li v-for="step in slide.steps" :key="step">{{ step }}</li>
            </ol>

            <div v-if="slide.metrics || slide.points || slide.table || slide.formula || slide.detail" class="evidence-copy">
              <dl v-if="slide.metrics" class="metric-grid">
                <div v-for="[value, label] in slide.metrics" :key="label" class="tile"><dt>{{ value }}</dt><dd>{{ label }}</dd></div>
              </dl>
              <div v-if="slide.points" class="point-list">
                <section v-for="[title, detail] in slide.points" :key="title">
                  <h2>{{ title }}</h2><p>{{ detail }}</p>
                </section>
              </div>
              <SlideTable v-if="slide.table" :table="slide.table" />
              <p v-if="slide.formula" class="formula">{{ slide.formula }}</p>
              <p v-if="slide.detail" class="slide-detail">{{ slide.detail }}</p>
            </div>

            <figure v-if="slide.image" class="media-figure">
              <SlideImage :src="image(slide.image.file)" :alt="slide.image.alt" @zoom="showImage(slide.image)" />
            </figure>
          </div>
        </template>
      </article>

      <footer class="player-footer">
        <div class="slide-position"><strong>{{ slideNumber(currentIndex) }}</strong><span> / {{ slides.length }}</span></div>
        <nav class="progress-steps" aria-label="Chuyển nhanh đến slide">
          <button v-for="(item, index) in slides" :key="item.nav" type="button" :class="{ 'step-past': index < currentIndex, 'step-active': index === currentIndex }" :aria-current="index === currentIndex ? 'step' : undefined" :aria-label="`Slide ${index + 1}: ${item.nav}`" :title="item.nav" @click="go(index)"><span></span></button>
        </nav>
        <div class="player-actions flex items-center gap-2">
          <button type="button" class="navigation-button" aria-label="Slide trước" title="Slide trước" :disabled="currentIndex === 0" @click="go(currentIndex - 1)"><Icon :icon="previousIcon" /></button>
          <button type="button" class="navigation-button navigation-button--next" aria-label="Slide tiếp theo" title="Slide tiếp theo" :disabled="currentIndex === slides.length - 1" @click="go(currentIndex + 1)"><Icon :icon="nextIcon" /></button>
        </div>
      </footer>
      <div class="keyboard-tip"><kbd>←</kbd> <kbd>→</kbd> Đổi slide <span>·</span> <kbd>F</kbd> Toàn màn hình</div>
      <div class="sr-only" role="status">Slide {{ currentIndex + 1 }} trên {{ slides.length }}. {{ slide.nav }}</div>
    </main>

    <div v-if="presenting" class="fullscreen-controls" aria-label="Điều khiển toàn màn hình">
      <button type="button" class="navigation-button" aria-label="Slide trước" :disabled="currentIndex === 0" @click="go(currentIndex - 1)"><Icon :icon="previousIcon" /></button>
      <button type="button" class="navigation-button" aria-label="Slide tiếp theo" :disabled="currentIndex === slides.length - 1" @click="go(currentIndex + 1)"><Icon :icon="nextIcon" /></button>
      <button type="button" class="navigation-button" aria-label="Thoát trình chiếu" @click="fullscreen"><Icon :icon="minimizeIcon" /></button>
    </div>

    <div v-if="panel" class="panel-backdrop" @click.self="closePanel">
      <aside id="deck-panel" class="side-panel" :aria-label="panel === 'outline' ? 'Mục lục slide' : 'Lời thoại'">
        <div class="panel-heading flex items-center justify-between gap-4"><h2>{{ panel === 'outline' ? 'Mục lục' : 'Lời thoại' }}</h2><button ref="closePanelButton" class="navigation-button" type="button" aria-label="Đóng bảng bên" @click="closePanel"><Icon :icon="closeIcon" /></button></div>
        <ol v-if="panel === 'outline'" class="outline-list">
          <li v-for="(item, index) in slides" :key="item.nav"><button type="button" :aria-current="currentIndex === index ? 'step' : undefined" @click="closePanel(); go(index, true)"><span>{{ slideNumber(index) }}</span><strong>{{ item.nav }}</strong></button></li>
        </ol>
        <div v-else class="speaker-notes">
          <div class="section-label">Slide {{ currentIndex + 1 }}<template v-if="slide.notes?.duration"> · {{ slide.notes.duration }}</template></div><h3>{{ slide.title }}</h3>
          <template v-if="slide.notes?.cue"><h4>Khi trình chiếu</h4><p>{{ slide.notes.cue }}</p></template>
          <template v-if="slide.type === 'demo'">
            <h4>Chuẩn bị</h4><p>{{ demoPreparation }}</p>
            <div v-for="[action, speech] in demoSteps" :key="action"><h4>{{ action }}</h4><p>{{ speech }}</p></div>
            <h4>Lời chốt demo</h4><p>{{ demoNotes }}</p>
          </template>
          <template v-else>
            <p v-for="paragraph in slide.notes.paragraphs" :key="paragraph">{{ paragraph }}</p>
          </template>
          <template v-if="slide.notes?.transition"><h4>Chuyển ý</h4><p>{{ slide.notes.transition }}</p></template>
          <a v-if="slide.type === 'demo'" href="http://127.0.0.1:8501" rel="noopener" target="_blank">Mở dashboard để demo trực tiếp</a>
          <details v-if="slide.type === 'process' && retrainingSteps.length" class="notes-questions">
            <summary>Demo huấn luyện lại</summary>
            <ol class="notes-steps"><li v-for="step in retrainingSteps" :key="step">{{ step }}</li></ol>
          </details>
          <details v-if="slide.type === 'closing'" class="notes-questions">
            <summary>Hồi quy tuyến tính về phí hàng tháng</summary>
            <p>{{ olsNotes.paragraphs[0] }}</p>
            <SlideTable :table="olsNotes.table" />
            <p>{{ olsNotes.paragraphs[1] }}</p>
          </details>
          <details v-if="slide.type === 'closing'" class="notes-questions">
            <summary>Câu hỏi phản biện</summary>
            <div v-for="[question, answer] in questions" :key="question"><h4>{{ question }}</h4><p>{{ answer }}</p></div>
          </details>
        </div>
      </aside>
    </div>

    <dialog ref="dialog" class="image-dialog" aria-label="Ảnh phóng to" @click.self="dialog.close()">
      <figure v-if="zoomed">
        <figcaption class="image-dialog-header flex items-center justify-between gap-4">
          <span>{{ zoomed.label }}</span>
          <button type="button" autofocus class="navigation-button" aria-label="Đóng ảnh" @click="dialog.close()"><Icon :icon="closeIcon" /></button>
        </figcaption>
        <img :src="zoomed.src" :alt="zoomed.label">
      </figure>
    </dialog>
  </div>
</template>
