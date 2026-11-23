<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import previousIcon from '@iconify-icons/lucide/chevron-left'
import nextIcon from '@iconify-icons/lucide/chevron-right'
import listIcon from '@iconify-icons/lucide/list'
import maximizeIcon from '@iconify-icons/lucide/maximize'
import minimizeIcon from '@iconify-icons/lucide/minimize'
import notesIcon from '@iconify-icons/lucide/notebook-pen'
import closeIcon from '@iconify-icons/lucide/x'
import treeIcon from '@iconify-icons/lucide/git-branch'
import chartIcon from '@iconify-icons/lucide/bar-chart-3'
import trendIcon from '@iconify-icons/lucide/trending-up'
import settingsIcon from '@iconify-icons/lucide/settings'
import usersIcon from '@iconify-icons/lucide/users'
import scaleIcon from '@iconify-icons/lucide/scale'
import SlideImage from './SlideImage.vue'
import SlidePoints from './SlidePoints.vue'
import SlideTable from './SlideTable.vue'
import { assets, comparisonBest, comparisonMetrics, coverInfo, demoCards, importance, modelIcons, slides, smotePhases, sourceName } from './slides.js'

const images = import.meta.glob(['../images/streamlit-chuan-hoa.png', '../../outputs/figures/05_churn_by_Contract.png'], { eager: true, import: 'default', query: '?url' })
const imageUrl = (file) => images[`../images/${file}`] || images[`../../outputs/figures/${file}`]
const icons = { tree: treeIcon, chart: chartIcon, trend: trendIcon, settings: settingsIcon, users: usersIcon }
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
let panelTrigger

function syncSlide() { currentIndex.value = indexFromHash() }
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
function selectSlide(index) { closePanel(false); go(index, true) }
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen()
    else await screen.value.requestFullscreen()
  } catch { /* Browser permission may prevent fullscreen. */ }
}
function syncFullscreen() { isFullscreen.value = document.fullscreenElement === screen.value }
function handleKey(event) {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || imageDialog.value?.open) return
  if (event.key === 'Escape' && panel.value) { event.preventDefault(); closePanel(); return }
  if (panel.value) {
    if (event.key === 'Tab') {
      const items = [...document.querySelectorAll('.side-panel button, .side-panel a, .side-panel summary')]
      const first = items[0], last = items.at(-1)
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    return
  }
  if (event.target.closest?.('input, textarea, select, [contenteditable]')) return
  const key = event.key.toLowerCase()
  if (key === 'f' && !event.repeat) { toggleFullscreen(); return }
  if (key === 'm' || key === 'n') { openPanel(key === 'm' ? 'outline' : 'notes', document.activeElement); return }
  const targets = { ArrowLeft: currentIndex.value - 1, PageUp: currentIndex.value - 1, ArrowRight: currentIndex.value + 1, PageDown: currentIndex.value + 1, Home: 0, End: slides.length - 1 }
  if (Object.hasOwn(targets, event.key) || (event.key === ' ' && !event.target.closest?.('button, a, summary'))) {
    event.preventDefault(); go(targets[event.key] ?? currentIndex.value + 1, true)
  }
}
async function showImage(image) {
  zoomed.value = image
  await nextTick()
  imageDialog.value.showModal()
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
        <header v-if="!['cover', 'closing'].includes(slide.layout)" class="slide-header">
          <h1 id="slide-heading" ref="heading" tabindex="-1">{{ slide.title }}</h1>
        </header>

        <div v-if="slide.layout === 'cover'" class="cover">
          <h1 id="slide-heading" ref="heading" tabindex="-1">BÁO CÁO BÀI TẬP LỚN<br>KHAI PHÁ DỮ LIỆU</h1>
          <p class="cover-subtitle">Dự đoán khách hàng rời bỏ<br>dịch vụ viễn thông</p>
          <p class="cover-description">Nhận diện nguy cơ rời bỏ và hỗ trợ ưu tiên chăm sóc khách hàng.</p>
          <dl class="cover-meta">
            <div v-for="(label, i) in slide.tables[0].header" :key="label"><dt>{{ label }}</dt><dd>{{ coverInfo[i] }}</dd></div>
          </dl>
        </div>

        <div v-else-if="slide.layout === 'roster'" class="slide-body">
          <SlideTable :table="slide.tables[0]" class="roster" />
        </div>

        <div v-else-if="slide.layout === 'data'" class="slide-body split data-layout">
          <section class="source-card">
            <h2>Nguồn gốc và quy mô</h2>
            <p>Bộ dữ liệu mẫu <strong>IBM Telco Customer Churn</strong>, mỗi dòng là một hồ sơ khách hàng.</p>
            <div class="data-stats"><div><strong>7.043</strong><span>Khách hàng ban đầu</span></div><div><strong>21</strong><span>Trường dữ liệu</span></div></div>
            <p class="data-clean">Sau làm sạch: <strong>7.032 khách hàng</strong></p>
            <p class="data-rate"><strong>26,58%</strong> tỷ lệ khách rời bỏ</p>
            <p class="small">Nhãn Churn: No = 0, Yes = 1</p>
          </section>
          <section><h2>Các thuộc tính chính</h2><SlideTable :table="slide.tables[0]" /></section>
        </div>

        <div v-else-if="slide.layout === 'attributes'" class="slide-body stack">
          <SlideTable :table="slide.tables[0]" />
          <div class="target-band"><p><strong>Phân loại Churn</strong><span>Decision Tree và Logistic Regression</span></p><p><strong>Hồi quy MonthlyCharges</strong><span>Linear Regression, phân tích bổ sung</span></p></div>
        </div>

        <div v-else-if="slide.layout === 'encoding'" class="slide-body stack">
          <div class="split">
            <section><h2>Làm sạch và mã hóa</h2><SlidePoints :points="slide.points" /></section>
            <section><h2>Bộ đặc trưng điều chỉnh</h2><SlideTable :table="slide.tables[0]" /><p class="small note">Các bộ biến được khai báo theo báo cáo trong schema.</p></section>
          </div>
          <div class="split-diagram"><div><strong>7.032</strong><span>Hồ sơ hợp lệ</span></div><span class="arrow">→</span><div><strong>5.625</strong><span>Train · 80%</span></div><div><strong>1.407</strong><span>Test · 20%</span></div></div>
          <p class="small">Chia phân tầng theo Churn · random_state = 42 · Loại mã khách hàng và nhãn khỏi đầu vào học.</p>
        </div>

        <div v-else-if="slide.layout === 'smote'" class="slide-body split">
          <section class="stack"><h2><Icon :icon="scaleIcon" /> Cân bằng dữ liệu (SMOTE)</h2><p>Khách rời bỏ chiếm <strong>26,58%</strong>. Chỉ nhìn Accuracy có thể che khuất các trường hợp bị bỏ sót.</p><SlidePoints :points="slide.points.slice(3)" /><p class="small">Áp dụng cho Logistic trong pipeline gốc.</p></section>
          <section class="balance-charts" aria-label="Phân bố lớp và cân bằng dữ liệu trên Train">
            <div class="pie-row"><div class="pie" role="img" aria-label="Ở lại 73,42%; rời bỏ 26,58%"></div><div class="legend"><p><i></i>Ở lại <strong>73,42%</strong></p><p><i class="churn"></i>Rời bỏ <strong>26,58%</strong></p></div></div>
            <div class="bar-charts"><figure v-for="phase in smotePhases" :key="phase.label"><figcaption>{{ phase.label }}</figcaption><div class="bars"><div v-for="(value, i) in [phase.stay, phase.churn]" :key="i" class="bar" :class="{ churn: i === 1 }" :style="{ height: value / 4130 * 100 + '%' }"><strong>{{ value.toLocaleString('vi-VN') }}</strong></div></div><div class="bar-labels"><span>Ở lại</span><span>Rời bỏ</span></div></figure></div>
          </section>
        </div>

        <div v-else-if="slide.layout === 'scaling'" class="slide-body stack">
          <div class="split"><section class="stack"><h2>StandardScaler</h2><p>Đưa các đặc trưng về thang đo chuẩn hóa để huấn luyện Logistic Regression.</p><p class="formula">z = (x − μ<sub>train</sub>) / σ<sub>train</sub></p></section><SlidePoints :points="slide.points" /></div>
          <ol class="pipeline"><li>SMOTE</li><li>StandardScaler</li><li>Logistic Regression</li></ol>
          <SlideImage :src="imageUrl(assets.scaling.file)" :alt="assets.scaling.alt" @zoom="showImage(assets.scaling)" />
          <p class="small">Ảnh minh họa chuẩn hóa trên giao diện. Trong pipeline Logistic, scaler được fit trên Train sau SMOTE.</p>
        </div>

        <div v-else-if="slide.layout === 'models'" class="slide-body stack">
          <div class="cards"><section v-for="(name, i) in slide.tables[0].header" :key="name" class="feature-card"><Icon :icon="icons[modelIcons[i]]" /><h2>{{ name }}</h2><p v-for="(row, r) in slide.tables[0].rows" :key="r">{{ row[i] }}</p></section></div>
          <p class="formula logistic-formula">Logistic: score = 1 / (1 + exp(−(β₀ + β₁x₁ + … + βₚxₚ)))</p>
          <p class="small">Hai mô hình phân loại Churn; Linear Regression phân tích riêng phí hàng tháng.</p>
        </div>

        <div v-else-if="slide.layout === 'training'" class="slide-body split">
          <section><h2>Quy trình thực hiện</h2><ol class="numbered-list"><li v-for="step in slide.steps" :key="step">{{ step }}</li></ol><p class="callout">CV Recall Logistic điều chỉnh: <strong>77,53%</strong></p></section>
          <section><h2>Độ đo đánh giá phân loại</h2><SlideTable :table="slide.tables[0]" /><p class="small note">Precision, Recall và F1 tính cho lớp Churn = 1. Test được giữ nguyên khi huấn luyện và cân bằng.</p></section>
        </div>

        <div v-else-if="slide.layout === 'comparison'" class="slide-body stack">
          <dl class="metric-band"><div v-for="(label, i) in comparisonMetrics.header" :key="label"><dd>{{ comparisonMetrics.rows[0][i] }}</dd><dt>{{ label }} · Logistic điều chỉnh</dt></div></dl>
          <SlideTable :table="slide.tables[1]" :best="comparisonBest" />
          <p class="result-summary">Decision Tree đạt Accuracy và Precision cao hơn. Logistic phát hiện nhiều khách rời bỏ hơn; bản điều chỉnh có F1 nhỉnh hơn trong lần đánh giá này.</p>
          <p class="callout">Phân tích phí hàng tháng: OLS điều chỉnh đạt <strong>R² Test = 0,9689</strong> và <strong>RMSE = 5,2402</strong>.</p>
        </div>

        <div v-else-if="slide.layout === 'matrix'" class="slide-body split matrix-layout">
          <section><h2>Các tình huống dự đoán</h2><div v-for="(point, i) in slide.points" :key="point" class="matrix-definition" :class="{ danger: i === 3 }"><SlidePoints :points="[point]" /></div></section>
          <section><h2>Logistic điều chỉnh · 1.407 mẫu Test</h2><SlideTable :table="slide.tables[0]" class="matrix-table"><template #value="{ value }"><strong>{{ value.match(/\d+/)?.[0] }}</strong><span>{{ value.match(/\([A-Z]+\)/)?.[0] }}</span></template></SlideTable><p class="callout">Phát hiện <strong>285/374</strong> khách rời bỏ.<br>Recall <strong>76,20%</strong> · Precision <strong>50,53%</strong></p></section>
        </div>

        <div v-else-if="slide.layout === 'explanation'" class="slide-body split">
          <section class="stack"><h2>Importance trong Decision Tree</h2><ol class="importance-list"><li v-for="([name, value], i) in importance" :key="name"><span class="rank">0{{ i + 1 }}</span><div><p>{{ name }} <strong>{{ value.toLocaleString('vi-VN') }}%</strong></p><div class="importance-track"><span :style="{ width: value + '%' }"></span></div></div></li></ol><h2>Chiều hệ số Logistic</h2><SlidePoints :points="slide.points" /><p class="small">Importance theo độ giảm hỗn tạp của cây. Các quan hệ quan sát được chưa chứng minh nhân quả.</p></section>
          <section><SlideImage :src="imageUrl(assets.explanation.file)" :alt="assets.explanation.alt" @zoom="showImage(assets.explanation)" /><p class="small">Churn theo hợp đồng: theo tháng <strong>42,71%</strong>, một năm <strong>11,28%</strong>, hai năm <strong>2,85%</strong>.</p></section>
        </div>

        <div v-else-if="slide.layout === 'retraining'" class="slide-body split">
          <section><h2>Quy trình huấn luyện lại</h2><ol class="numbered-list"><li v-for="step in slide.steps" :key="step">{{ step }}</li></ol></section>
          <section class="stack"><h2>Quản lý kết quả</h2><SlidePoints :points="slide.points" /><div class="callout"><strong>Người dùng chủ động khởi chạy</strong><p>Xem kết quả, so sánh và chọn mô hình trước khi dùng cho dự đoán.</p></div><p class="small">Dữ liệu mới cần nhãn Churn thực tế. Chưa có lịch huấn luyện tự động.</p></section>
        </div>

        <div v-else-if="slide.layout === 'demo'" class="slide-body stack">
          <div class="cards"><section v-for="(card, i) in demoCards" :key="card.title" class="feature-card demo-card"><Icon :icon="icons[card.icon]" /><h2>{{ card.title }}</h2><p v-for="(row, r) in slide.tables[0].rows" :key="r">{{ row[i] }}</p></section></div>
          <div class="demo-bottom"><div><strong>Đầu ra dự đoán</strong><p>Điểm nguy cơ 0–1 · Nhãn Yes/No · Nhóm Low / Medium / High</p><p class="small">Ngưỡng nhãn mặc định 0,5. Điểm sau SMOTE chưa được hiệu chuẩn xác suất.</p></div><a :href="dashboardUrl" target="_blank" rel="noopener" class="demo-link">Mở demo Streamlit ↗</a></div>
          <ol class="pipeline demo-flow"><li>Dữ liệu</li><li>Tiền xử lý</li><li>Huấn luyện</li><li>So sánh</li><li>Dự đoán</li></ol>
        </div>

        <div v-else-if="slide.layout === 'closing'" class="closing"><h1 id="slide-heading" ref="heading" tabindex="-1">CẢM ƠN!</h1><p>GIẢNG VIÊN VÀ CÁC BẠN ĐÃ LẮNG NGHE</p><div><span>[Tên nhóm] - [Lớp]</span><span>HỎI ĐÁP</span></div></div>
        <footer class="slide-footer">Page {{ currentIndex + 1 }}</footer>
      </article>
      <div class="sr-only" role="status">Slide {{ currentIndex + 1 }} trên {{ slides.length }}. {{ slide.title }}</div>
    </main>

    <nav class="controls" :inert="Boolean(panel)" aria-label="Điều khiển trình chiếu">
      <button aria-label="Slide trước" title="Slide trước (←)" :disabled="currentIndex === 0" @click="go(currentIndex - 1)"><Icon :icon="previousIcon" /></button>
      <span class="page-counter">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      <button aria-label="Slide tiếp theo" title="Slide tiếp theo (→)" :disabled="currentIndex === slides.length - 1" @click="go(currentIndex + 1)"><Icon :icon="nextIcon" /></button>
      <button aria-label="Mục lục" title="Mục lục (M)" @click="openPanel('outline', $event.currentTarget)"><Icon :icon="listIcon" /><span class="control-label">Mục lục</span></button>
      <button aria-label="Ghi chú thuyết trình" title="Ghi chú (N)" @click="openPanel('notes', $event.currentTarget)"><Icon :icon="notesIcon" /><span class="control-label">Ghi chú</span></button>
      <button :aria-label="isFullscreen ? 'Thoát toàn màn hình' : 'Toàn màn hình'" title="Toàn màn hình (F)" @click="toggleFullscreen"><Icon :icon="isFullscreen ? minimizeIcon : maximizeIcon" /></button>
    </nav>
    <div v-if="panel" class="panel-backdrop" @click.self="closePanel()">
      <aside class="side-panel" role="dialog" aria-modal="true" aria-labelledby="panel-title">
        <div class="panel-heading"><h2 id="panel-title">{{ panel === 'outline' ? 'Mục lục' : 'Ghi chú thuyết trình' }}</h2><button ref="closePanelButton" aria-label="Đóng bảng bên" @click="closePanel()"><Icon :icon="closeIcon" /></button></div>
        <ol v-if="panel === 'outline'" class="outline-list"><li v-for="(item, index) in slides" :key="item.title"><button :aria-current="currentIndex === index ? 'step' : undefined" @click="selectSlide(index)"><span>{{ String(index + 1).padStart(2, '0') }}</span>{{ item.title }}</button></li></ol>
        <div v-else class="speaker-notes"><p class="notes-source">Nội dung từ {{ sourceName }}</p><h3>Slide {{ currentIndex + 1 }}. {{ slide.title }}</h3><p v-for="paragraph in slide.notes" :key="paragraph">{{ paragraph }}</p></div>
      </aside>
    </div>
    <dialog ref="imageDialog" class="image-dialog" aria-label="Ảnh phóng to" @click.self="imageDialog.close()"><figure v-if="zoomed"><figcaption>{{ zoomed.alt }}<button autofocus aria-label="Đóng ảnh" @click="imageDialog.close()"><Icon :icon="closeIcon" /></button></figcaption><img :src="imageUrl(zoomed.file)" :alt="zoomed.alt"></figure></dialog>
  </div>
</template>
