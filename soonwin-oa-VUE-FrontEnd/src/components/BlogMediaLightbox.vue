<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="lightbox-overlay"
      @click="onOverlayClick"
      @keydown="handleKeydown"
    >
      <!-- 控件层：绝对定位，pointer-events: none 让空白处点击穿透到 overlay 触发关闭 -->
      <div class="lightbox-controls">
        <el-button class="lightbox-close" circle @click="close" title="关闭 (Esc)">
          <el-icon :size="20"><Close /></el-icon>
        </el-button>

        <div class="lightbox-counter" v-if="mediaList.length > 1">
          {{ currentIndex + 1 }} / {{ mediaList.length }}
        </div>

        <div class="lightbox-zoom-hint" v-if="scale > 1">
          {{ Math.round(scale * 100) }}%
          <button class="lightbox-zoom-reset" @click="resetView" title="重置">↺</button>
        </div>

        <el-button
          v-if="mediaList.length > 1"
          class="lightbox-arrow left"
          circle
          @click.stop="prev"
          title="上一张 (←)"
        >
          <el-icon :size="22"><ArrowLeft /></el-icon>
        </el-button>

        <el-button
          v-if="mediaList.length > 1"
          class="lightbox-arrow right"
          circle
          @click.stop="next"
          title="下一张 (→)"
        >
          <el-icon :size="22"><ArrowRight /></el-icon>
        </el-button>
      </div>

      <!-- 媒体内容：不铺满全屏，overflow: visible 允许放大后溢出 -->
      <div
        class="lightbox-content"
        @wheel.prevent="onWheel"
        @dblclick.prevent="onDblClick"
      >
        <img
          v-if="currentMedia?.media_type === 'image'"
          ref="imageRef"
          :src="getMediaUrl(currentMedia.file_path)"
          alt=""
          class="lightbox-media"
          :class="{ 'is-dragging': isDragging }"
          :style="imageTransform"
          @load="onImageLoad"
          @mousedown.prevent="onDragStart"
          @mousemove="onDragMove"
          @mouseup="onDragEnd"
          @mouseleave="onDragEnd"
          draggable="false"
        />
        <video
          v-else-if="currentMedia?.media_type === 'video'"
          :src="getMediaUrl(currentMedia.file_path)"
          controls
          autoplay
          class="lightbox-media"
        />
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Close, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import type { BlogMedia } from '@/types/blog'
import { getMediaUrl } from '@/api/blog'

const props = defineProps<{
  visible: boolean
  mediaList: BlogMedia[]
  initialIndex?: number
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const currentIndex = ref(0)
const currentMedia = ref<BlogMedia | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

// ========== 缩放 + 平移 ==========
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const MIN_SCALE = 0.5
const MAX_SCALE = 5
const ZOOM_STEP = 0.25

const imageTransform = computed(() => {
  const parts: string[] = []
  if (panX.value !== 0 || panY.value !== 0) {
    parts.push(`translate(${panX.value}px, ${panY.value}px)`)
  }
  if (scale.value !== 1) {
    parts.push(`scale(${scale.value})`)
  }
  if (parts.length === 0) return {}
  return {
    transform: parts.join(' '),
    transformOrigin: 'center center',
    transition: isDragging.value ? 'none' : 'transform 0.1s ease-out',
  }
})

function resetView() {
  scale.value = 1
  panX.value = 0
  panY.value = 0
}

// ========== 拖动平移 ==========
const isDragging = ref(false)
let dragStartX = 0
let dragStartY = 0
let panStartX = 0
let panStartY = 0

function onDragStart(e: MouseEvent) {
  // 仅放大状态下可拖动（1x 时不需要平移）
  if (scale.value <= 1) return
  isDragging.value = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  panStartX = panX.value
  panStartY = panY.value
}

function onDragMove(e: MouseEvent) {
  if (!isDragging.value) return
  panX.value = panStartX + (e.clientX - dragStartX)
  panY.value = panStartY + (e.clientY - dragStartY)
}

function onDragEnd() {
  isDragging.value = false
}

// 全局 mouseup：防止拖出图片后状态残留
function onGlobalMouseUp() {
  if (isDragging.value) {
    isDragging.value = false
  }
}

/**
 * overlay 点击处理：判断点击是否落在图片的视觉区域内
 *
 * 不能用 @click.self 或 DOM 命中检测，因为 CSS transform: scale()
 * 不改变元素的布局盒 —— 缩放后图片视觉上变小/变大，但 getBoundingClientRect()
 * 返回的始终是 transform 前的原始尺寸。必须用坐标数学计算视觉边界。
 */
function onOverlayClick(e: MouseEvent) {
  // 如果点击目标是按钮/控件，不处理（按钮有自己的 handler + stopPropagation）
  const target = e.target as HTMLElement
  if (target.closest('.lightbox-close, .lightbox-arrow, .lightbox-zoom-reset')) {
    return
  }

  const img = imageRef.value
  if (!img) {
    // 无图片（如视频模式）：点击 overlay 任意位置关闭
    close()
    return
  }

  const rect = img.getBoundingClientRect()   // transform 前的布局盒
  const s = scale.value
  const px = panX.value
  const py = panY.value

  // 视觉尺寸 = 布局盒 × scale
  const vw = rect.width * s
  const vh = rect.height * s
  // 缩放以 transform-origin: center 为中心 → 视觉盒中心 = 布局盒中心
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  // 视觉左上角（平移前）
  let vl = cx - vw / 2
  let vt = cy - vh / 2
  // translate 在 scale 之后应用 → 视觉偏移 = pan × scale（屏幕像素）
  vl += px * s
  vt += py * s

  if (
    e.clientX >= vl &&
    e.clientX <= vl + vw &&
    e.clientY >= vt &&
    e.clientY <= vt + vh
  ) {
    // 点击在图片视觉区域内 → 不关闭
    return
  }
  // 点击在图片外 → 关闭
  close()
}

// ========== 缩放 ==========
function onWheel(e: WheelEvent) {
  const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
  const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale.value + delta))
  scale.value = newScale
  // 回到 1x 时重置平移
  if (newScale <= 1) {
    panX.value = 0
    panY.value = 0
  }
}

function onDblClick() {
  if (scale.value > 1) {
    resetView()
  } else {
    scale.value = 2
  }
}

function onImageLoad() {
  resetView()
}

// ========== 导航 ==========
watch(() => props.visible, (val) => {
  if (val) {
    currentIndex.value = props.initialIndex || 0
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    resetView()
  }
})

watch(currentIndex, (idx) => {
  currentMedia.value = props.mediaList[idx] || null
}, { immediate: true })

watch(() => props.mediaList, () => {
  currentMedia.value = props.mediaList[currentIndex.value] || null
})

watch(currentMedia, () => {
  resetView()
})

function close() {
  emit('update:visible', false)
}

function prev() {
  currentIndex.value = (currentIndex.value - 1 + props.mediaList.length) % props.mediaList.length
}

function next() {
  currentIndex.value = (currentIndex.value + 1) % props.mediaList.length
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('mouseup', onGlobalMouseUp)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mouseup', onGlobalMouseUp)
  document.body.style.overflow = ''
})
</script>

<style scoped>
/* ====== 遮罩层：满屏暗背景，点击空白处关闭 ====== */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ====== 控件层：绝对定位在 overlay 之上，不阻挡 overlay 点击关闭 ====== */
.lightbox-controls {
  position: fixed;
  inset: 0;
  z-index: 100;
  pointer-events: none;  /* 透明区域点击穿透 → overlay @click.self → 关闭 */
}

.lightbox-controls > * {
  pointer-events: auto;  /* 按钮自身可点击 */
}

.lightbox-close {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(0, 0, 0, 0.55) !important;
  color: #fff !important;
  border: none !important;
  width: 40px;
  height: 40px;
}
.lightbox-close:hover {
  background: rgba(0, 0, 0, 0.8) !important;
}

.lightbox-counter {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.45);
  padding: 4px 14px;
  border-radius: 20px;
}

.lightbox-zoom-hint {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-size: 13px;
  background: rgba(0, 0, 0, 0.55);
  padding: 4px 12px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.lightbox-zoom-reset {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lightbox-zoom-reset:hover {
  background: rgba(255, 255, 255, 0.4);
}

.lightbox-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.5) !important;
  color: #fff !important;
  border: none !important;
  width: 44px;
  height: 44px;
}
.lightbox-arrow:hover {
  background: rgba(0, 0, 0, 0.75) !important;
}

.lightbox-arrow.left  { left: 12px; }
.lightbox-arrow.right { right: 12px; }

/* ====== 内容层：overflow: visible 允许放大后不裁剪 ====== */
.lightbox-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;           /* 关键：放大后不被裁剪 */
  max-width: 90vw;
  max-height: 90vh;
}

.lightbox-media {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 4px;
  will-change: transform;
  user-select: none;
  -webkit-user-drag: none;
}

/* 默认：手掌图标（可拖拽/交互） */
.lightbox-media:not(.is-dragging) {
  cursor: grab;
}

/* 拖拽中：握拳图标 */
.lightbox-media.is-dragging {
  cursor: grabbing;
}
</style>
