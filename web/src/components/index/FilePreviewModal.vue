<template>
  <Teleport to="body">
    <div v-if="visible" class="preview-overlay" @mousedown.self="emit('close')">
      <div class="preview-shell">
        <header class="preview-header">
          <div class="preview-title">
            <span class="preview-name" :title="currentFile?.name">{{ currentFile?.name }}</span>
            <span v-if="total > 1" class="preview-counter">{{ currentIndex + 1 }} / {{ total }}</span>
          </div>
          <div class="preview-actions">
            <template v-if="previewKind === 'image'">
              <button type="button" class="preview-icon-btn" title="缩小" @click="zoomOut">-</button>
              <button type="button" class="preview-icon-btn wide" title="适应窗口" @click="resetView">适应</button>
              <button type="button" class="preview-icon-btn" title="放大" @click="zoomIn">+</button>
            </template>
            <button type="button" class="preview-icon-btn wide" title="下载" @click="emit('download', currentFile)">下载</button>
            <button type="button" class="preview-icon-btn" title="关闭" @click="emit('close')">x</button>
          </div>
        </header>

        <main class="preview-stage" :class="`preview-${previewKind}`" @wheel="handleWheel">
          <button
            v-if="total > 1"
            type="button"
            class="preview-nav prev"
            title="上一张"
            @click="emit('previous')"
          >
            &lt;
          </button>

          <div
            v-if="previewKind === 'image'"
            class="preview-image-wrap"
            :class="{ grabbing: dragging }"
            @mousedown="startDrag"
          >
            <div v-if="loading" class="preview-state">
              <span class="preview-spinner"></span>
              <span>正在载入图片</span>
            </div>
            <div v-else-if="loadError" class="preview-state error">
              <span>图片加载失败</span>
              <button type="button" class="preview-state-btn" @click="reloadImage">重试</button>
            </div>
            <img
              v-show="!loadError && mediaUrl"
              :key="imageKey"
              ref="imageRef"
              class="preview-image"
              :src="mediaUrl"
              :alt="currentFile?.name || '图片预览'"
              :style="imageStyle"
              draggable="false"
              @load="handleImageLoad"
              @error="handleImageError"
            >
          </div>

          <div v-else-if="previewKind === 'video'" class="preview-video-wrap">
            <div v-if="loading" class="preview-state">
              <span class="preview-spinner"></span>
              <span>正在载入视频</span>
            </div>
            <div v-else-if="loadError" class="preview-state error">
              <span>浏览器无法直接播放该视频</span>
              <button type="button" class="preview-state-btn" @click="emit('download', currentFile)">下载文件</button>
            </div>
            <video
              v-show="!loadError && mediaUrl"
              :key="mediaKey"
              ref="videoRef"
              class="preview-video"
              :src="mediaUrl"
              controls
              autoplay
              playsinline
              preload="auto"
              @loadedmetadata="handleVideoReady"
              @loadeddata="handleVideoReady"
              @canplay="handleVideoCanPlay"
              @error="handleVideoError"
            ></video>
          </div>

          <div v-else-if="previewKind === 'audio'" class="preview-audio-wrap">
            <div v-if="loading" class="preview-state">
              <span class="preview-spinner"></span>
              <span>正在载入音频</span>
            </div>
            <div v-else-if="loadError" class="preview-state error">
              <span>浏览器无法直接播放该音频</span>
              <button type="button" class="preview-state-btn" @click="emit('download', currentFile)">下载文件</button>
            </div>
            <div v-show="!loadError && mediaUrl" class="preview-audio-panel">
              <div class="preview-audio-cover">
                <span>{{ audioBadgeText }}</span>
              </div>
              <div class="preview-audio-info">
                <div class="preview-audio-name" :title="currentFile?.name">{{ currentFile?.name }}</div>
                <div class="preview-audio-meta">{{ audioMetaText }}</div>
                <audio
                  :key="mediaKey"
                  ref="audioRef"
                  class="preview-audio"
                  :src="mediaUrl"
                  controls
                  autoplay
                  preload="auto"
                  @loadedmetadata="handleAudioReady"
                  @loadeddata="handleAudioReady"
                  @canplay="handleAudioCanPlay"
                  @error="handleAudioError"
                ></audio>
              </div>
            </div>
          </div>

          <div v-else-if="previewKind === 'text'" class="preview-text-wrap">
            <div v-if="loading" class="preview-state">
              <span class="preview-spinner"></span>
              <span>正在载入文本</span>
            </div>
            <div v-else-if="loadError" class="preview-state error">
              <span>{{ textError || '文本加载失败' }}</span>
              <button type="button" class="preview-state-btn" @click="loadTextPreview">重试</button>
            </div>
            <div v-else class="preview-text-panel">
              <div v-if="textTruncated" class="preview-text-notice">
                文件较大，仅显示前 {{ textPreviewBytesText }}
              </div>
              <pre class="preview-text-content">{{ textContent }}</pre>
            </div>
          </div>

          <div v-else-if="previewKind === 'pdf'" class="preview-pdf-wrap">
            <div v-if="loading" class="preview-state">
              <span class="preview-spinner"></span>
              <span>正在载入 PDF</span>
            </div>
            <div v-else-if="loadError" class="preview-state error">
              <span>浏览器无法直接预览该 PDF</span>
              <button type="button" class="preview-state-btn" @click="emit('download', currentFile)">下载文件</button>
            </div>
            <iframe
              v-show="!loadError && mediaUrl"
              :key="mediaKey"
              class="preview-pdf-frame"
              :src="mediaUrl"
              title="PDF 预览"
              @load="handlePdfReady"
              @error="handlePdfError"
            ></iframe>
          </div>

          <button
            v-if="total > 1"
            type="button"
            class="preview-nav next"
            title="下一张"
            @click="emit('next')"
          >
            &gt;
          </button>
        </main>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { getPreviewKind } from '../../utils/fileTypes.js'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  files: {
    type: Array,
    default: () => []
  },
  currentIndex: {
    type: Number,
    default: 0
  },
  accountId: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['close', 'previous', 'next', 'download'])

const scale = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)
const loading = ref(false)
const loadError = ref(false)
const imageKey = ref(0)
const mediaKey = ref(0)
const imageRef = ref(null)
const videoRef = ref(null)
const audioRef = ref(null)
const videoAutoplayTried = ref(false)
const audioAutoplayTried = ref(false)
const textContent = ref('')
const textError = ref('')
const textTruncated = ref(false)
const textPreviewBytes = ref(0)
const textLoadSeq = ref(0)
const dragging = ref(false)
const dragStart = ref({ x: 0, y: 0, offsetX: 0, offsetY: 0 })

const total = computed(() => props.files.length)
const currentFile = computed(() => props.files[props.currentIndex] || null)
const previewKind = computed(() => getPreviewKind(currentFile.value))

const mediaUrl = computed(() => {
  if (!props.accountId || !currentFile.value?.id) return ''
  const encodedId = encodeURIComponent(currentFile.value.id)
  const userAgent = encodeURIComponent(navigator.userAgent)
  const fileName = encodeURIComponent(currentFile.value.name || '')
  return `/api/files/download/${props.accountId}/${encodedId}?user_agent=${userAgent}&preview=true&file_name=${fileName}`
})

const imageStyle = computed(() => ({
  transform: `translate(${offsetX.value}px, ${offsetY.value}px) scale(${scale.value})`
}))

const textPreviewBytesText = computed(() => {
  const bytes = textPreviewBytes.value || 0
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  if (bytes >= 1024) return `${Math.ceil(bytes / 1024)} KB`
  return `${bytes} B`
})

const audioBadgeText = computed(() => {
  const ext = String(currentFile.value?.name || '').split('.').pop() || '音频'
  return ext.slice(0, 4).toUpperCase()
})

const audioMetaText = computed(() => {
  const size = Number(currentFile.value?.size || 0)
  if (!size) return '音频预览'
  if (size >= 1024 * 1024 * 1024) return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`
  if (size >= 1024) return `${Math.ceil(size / 1024)} KB`
  return `${size} B`
})

const resetView = () => {
  scale.value = 1
  offsetX.value = 0
  offsetY.value = 0
}

const zoomIn = () => {
  scale.value = Math.min(5, Number((scale.value + 0.2).toFixed(2)))
}

const zoomOut = () => {
  scale.value = Math.max(0.2, Number((scale.value - 0.2).toFixed(2)))
  if (scale.value === 1) {
    offsetX.value = 0
    offsetY.value = 0
  }
}

const handleWheel = event => {
  if (previewKind.value !== 'image') return
  event.preventDefault()

  if (event.deltaY < 0) {
    zoomIn()
  } else {
    zoomOut()
  }
}

const startDrag = event => {
  if (event.button !== 0 || loading.value || loadError.value) return
  dragging.value = true
  dragStart.value = {
    x: event.clientX,
    y: event.clientY,
    offsetX: offsetX.value,
    offsetY: offsetY.value
  }
}

const handleMouseMove = event => {
  if (!dragging.value) return
  offsetX.value = dragStart.value.offsetX + event.clientX - dragStart.value.x
  offsetY.value = dragStart.value.offsetY + event.clientY - dragStart.value.y
}

const stopDrag = () => {
  dragging.value = false
}

const handleImageLoad = () => {
  if (previewKind.value !== 'image') return
  loading.value = false
  loadError.value = false
}

const handleImageError = () => {
  if (previewKind.value !== 'image') return
  loading.value = false
  loadError.value = true
}

const reloadImage = () => {
  loading.value = true
  loadError.value = false
  imageKey.value += 1
}

const handleVideoReady = () => {
  if (previewKind.value !== 'video') return
  loading.value = false
  loadError.value = false
}

const handleVideoCanPlay = () => {
  handleVideoReady()
  if (videoAutoplayTried.value) return
  videoAutoplayTried.value = true
  videoRef.value?.play?.().catch(() => {})
}

const handleVideoError = () => {
  if (previewKind.value !== 'video') return
  loading.value = false
  loadError.value = true
}

const handleAudioReady = () => {
  if (previewKind.value !== 'audio') return
  loading.value = false
  loadError.value = false
}

const handleAudioCanPlay = () => {
  handleAudioReady()
  if (audioAutoplayTried.value) return
  audioAutoplayTried.value = true
  audioRef.value?.play?.().catch(() => {})
}

const handleAudioError = () => {
  if (previewKind.value !== 'audio') return
  loading.value = false
  loadError.value = true
}

const handlePdfReady = () => {
  if (previewKind.value !== 'pdf') return
  loading.value = false
  loadError.value = false
}

const handlePdfError = () => {
  if (previewKind.value !== 'pdf') return
  loading.value = false
  loadError.value = true
}

const loadTextPreview = async () => {
  if (!props.visible || previewKind.value !== 'text' || !props.accountId || !currentFile.value?.id) return

  const seq = textLoadSeq.value + 1
  textLoadSeq.value = seq
  loading.value = true
  loadError.value = false
  textError.value = ''
  textContent.value = ''
  textTruncated.value = false
  textPreviewBytes.value = 0

  try {
    const encodedId = encodeURIComponent(currentFile.value.id)
    const userAgent = encodeURIComponent(navigator.userAgent)
    const response = await fetch(
      `/api/files/preview-text/${props.accountId}/${encodedId}?user_agent=${userAgent}`,
      { credentials: 'same-origin' }
    )
    const result = await response.json()
    if (seq !== textLoadSeq.value) return
    if (!response.ok || !result.success) {
      throw new Error(result.message || '文本加载失败')
    }
    textContent.value = result.data?.content || ''
    textTruncated.value = Boolean(result.data?.truncated)
    textPreviewBytes.value = Number(result.data?.preview_bytes || 0)
    loading.value = false
  } catch (error) {
    if (seq !== textLoadSeq.value) return
    loading.value = false
    loadError.value = true
    textError.value = error.message || '文本加载失败'
  }
}

const resetPreviewState = async () => {
  if (!props.visible || !currentFile.value || !mediaUrl.value) return
  if (videoRef.value) {
    videoRef.value.pause()
  }
  if (audioRef.value) {
    audioRef.value.pause()
  }
  loading.value = true
  loadError.value = false
  videoAutoplayTried.value = false
  audioAutoplayTried.value = false
  textContent.value = ''
  textError.value = ''
  textTruncated.value = false
  textPreviewBytes.value = 0
  if (previewKind.value === 'image') {
    imageKey.value += 1
  } else if (previewKind.value === 'video' || previewKind.value === 'audio' || previewKind.value === 'pdf') {
    mediaKey.value += 1
  }
  resetView()
  if (previewKind.value === 'text') {
    loadTextPreview()
    return
  }
  await nextTick()
  if (previewKind.value === 'image' && imageRef.value?.complete && imageRef.value.naturalWidth > 0) {
    handleImageLoad()
  }
}

const handleKeydown = event => {
  if (!props.visible) return
  if (event.key === 'Escape') emit('close')
  if (event.key === 'ArrowLeft') emit('previous')
  if (event.key === 'ArrowRight') emit('next')
  if (previewKind.value !== 'image') return
  if ((event.metaKey || event.ctrlKey) && ['+', '='].includes(event.key)) {
    event.preventDefault()
    zoomIn()
  }
  if ((event.metaKey || event.ctrlKey) && event.key === '-') {
    event.preventDefault()
    zoomOut()
  }
  if ((event.metaKey || event.ctrlKey) && event.key === '0') {
    event.preventDefault()
    resetView()
  }
}

watch(
  () => [props.visible, currentFile.value?.id, previewKind.value, mediaUrl.value],
  () => {
    resetPreviewState()
  },
  { immediate: true, flush: 'post' }
)

watch(() => props.visible, visible => {
  if (!visible) {
    videoRef.value?.pause()
    audioRef.value?.pause()
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopDrag)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopDrag)
})
</script>

<style scoped>
.preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 100200;
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: stretch;
  justify-content: stretch;
}

.preview-shell {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  color: #f8fafc;
}

.preview-header {
  height: 62px;
  padding: 0 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0));
  flex-shrink: 0;
}

.preview-title {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-name {
  max-width: min(56vw, 860px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 15px;
  font-weight: 600;
}

.preview-counter {
  color: rgba(226, 232, 240, 0.72);
  font-size: 13px;
}

.preview-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-icon-btn,
.preview-state-btn {
  height: 34px;
  min-width: 34px;
  border: 1px solid rgba(226, 232, 240, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.preview-icon-btn:hover,
.preview-state-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(226, 232, 240, 0.32);
}

.preview-icon-btn.wide {
  min-width: 50px;
  padding: 0 12px;
}

.preview-stage {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.preview-video {
  background: rgba(2, 6, 23, 0.74);
}

.preview-image-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  cursor: grab;
}

.preview-video-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 20px 96px 44px;
  box-sizing: border-box;
}

.preview-audio-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 20px 76px 42px;
  box-sizing: border-box;
}

.preview-text-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 20px 76px 42px;
  box-sizing: border-box;
}

.preview-pdf-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 12px 76px 34px;
  box-sizing: border-box;
}

.preview-image-wrap.grabbing {
  cursor: grabbing;
}

.preview-image {
  max-width: calc(100vw - 112px);
  max-height: calc(100vh - 112px);
  object-fit: contain;
  user-select: none;
  opacity: 1;
  transition: transform 0.08s ease-out;
  transform-origin: center center;
}

.preview-video {
  display: block;
  width: min(1280px, 78vw);
  max-width: calc(100vw - 220px);
  height: auto;
  max-height: calc(100vh - 156px);
  margin: auto;
  border-radius: 8px;
  outline: none;
  object-fit: contain;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.24);
}

.preview-audio-panel {
  width: min(680px, calc(100vw - 152px));
  display: grid;
  grid-template-columns: 128px minmax(0, 1fr);
  gap: 22px;
  align-items: center;
  padding: 26px;
  border: 1px solid rgba(226, 232, 240, 0.14);
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.84);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.24);
}

.preview-audio-cover {
  width: 128px;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(76, 116, 223, 0.95), rgba(2, 166, 240, 0.88));
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0;
}

.preview-audio-info {
  min-width: 0;
}

.preview-audio-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #f8fafc;
  font-size: 17px;
  font-weight: 700;
}

.preview-audio-meta {
  margin-top: 8px;
  color: rgba(226, 232, 240, 0.64);
  font-size: 13px;
}

.preview-audio {
  width: 100%;
  margin-top: 22px;
}

.preview-text-panel {
  width: min(1120px, calc(100vw - 152px));
  height: min(720px, calc(100vh - 144px));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.14);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.84);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.24);
}

.preview-text-notice {
  flex-shrink: 0;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.1);
  color: rgba(226, 232, 240, 0.74);
  font-size: 13px;
}

.preview-text-content {
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 18px 20px;
  overflow: auto;
  color: rgba(248, 250, 252, 0.94);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.preview-pdf-frame {
  width: min(1180px, calc(100vw - 152px));
  height: min(780px, calc(100vh - 124px));
  border: 1px solid rgba(226, 232, 240, 0.14);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.24);
}

.preview-state {
  position: absolute;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.64);
  color: rgba(248, 250, 252, 0.92);
  font-size: 14px;
}

.preview-state.error {
  flex-direction: column;
  gap: 10px;
}

.preview-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.28);
  border-top-color: #fff;
  border-radius: 50%;
  animation: previewSpin 0.8s linear infinite;
}

.preview-nav {
  position: absolute;
  top: 50%;
  z-index: 3;
  width: 42px;
  height: 58px;
  transform: translateY(-50%);
  border: 1px solid rgba(226, 232, 240, 0.16);
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.36);
  color: #f8fafc;
  font-size: 26px;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.preview-nav:hover {
  background: rgba(15, 23, 42, 0.62);
  border-color: rgba(226, 232, 240, 0.34);
}

.preview-nav.prev {
  left: 22px;
}

.preview-nav.next {
  right: 22px;
}

@keyframes previewSpin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .preview-header {
    height: auto;
    min-height: 58px;
    padding: 10px 12px;
    align-items: flex-start;
    flex-direction: column;
  }

  .preview-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .preview-name {
    max-width: calc(100vw - 24px);
  }

  .preview-image {
    max-width: calc(100vw - 28px);
    max-height: calc(100vh - 150px);
  }

  .preview-video-wrap {
    padding: 16px 14px 28px;
  }

  .preview-video {
    width: calc(100vw - 28px);
    max-width: calc(100vw - 28px);
    max-height: calc(100vh - 178px);
  }

  .preview-audio-wrap {
    padding: 16px 14px 28px;
  }

  .preview-audio-panel {
    width: calc(100vw - 28px);
    grid-template-columns: 1fr;
    justify-items: center;
    padding: 22px;
  }

  .preview-audio-info {
    width: 100%;
  }

  .preview-text-wrap {
    padding: 16px 14px 28px;
  }

  .preview-text-panel {
    width: calc(100vw - 28px);
    height: calc(100vh - 178px);
  }

  .preview-pdf-wrap {
    padding: 12px 14px 28px;
  }

  .preview-pdf-frame {
    width: calc(100vw - 28px);
    height: calc(100vh - 178px);
  }

  .preview-nav {
    width: 34px;
    height: 48px;
  }

  .preview-nav.prev {
    left: 8px;
  }

  .preview-nav.next {
    right: 8px;
  }
}
</style>
