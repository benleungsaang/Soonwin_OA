<template>
  <teleport to="body">
    <div v-if="visible" class="lightbox-overlay" @click.self="close" @keydown="handleKeydown">
      <div class="lightbox-container">
        <!-- 控件层：z-index 高于图片，缩放时始终在图片上方 -->
        <div class="lightbox-controls">
          <!-- 关闭按钮 -->
          <el-button class="lightbox-close" circle @click="close" title="关闭 (Esc)">
            <el-icon :size="20"><Close /></el-icon>
          </el-button>

          <!-- 计数器 -->
          <div class="lightbox-counter" v-if="mediaList.length > 1">
            {{ currentIndex + 1 }} / {{ mediaList.length }}
          </div>

          <!-- 缩放提示 -->
          <div class="lightbox-zoom-hint" v-if="scale > 1">
            {{ Math.round(scale * 100) }}%
            <button class="lightbox-zoom-reset" @click="resetZoom" title="重置缩放">↺</button>
          </div>

          <!-- 左箭头 -->
          <el-button
            v-if="mediaList.length > 1"
            class="lightbox-arrow left"
            circle
            @click.stop="prev"
            title="上一张 (←)"
          >
            <el-icon :size="22"><ArrowLeft /></el-icon>
          </el-button>

          <!-- 右箭头 -->
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

        <!-- 媒体内容（可缩放） -->
        <div
          class="lightbox-content"
          @wheel.prevent="onWheel"
          @dblclick="onDblClick"
        >
          <img
            v-if="currentMedia?.media_type === 'image'"
            ref="imageRef"
            :src="getMediaUrl(currentMedia.file_path)"
            alt=""
            class="lightbox-media"
            :style="imageTransform"
            @load="onImageLoad"
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

// ========== 缩放状态 ==========
const scale = ref(1)
const MIN_SCALE = 0.5
const MAX_SCALE = 5
const ZOOM_STEP = 0.25

const imageTransform = computed(() => {
  if (scale.value === 1) return ''
  return {
    transform: `scale(${scale.value})`,
    transformOrigin: 'center center',
    transition: 'transform 0.1s ease-out',
  }
})

function resetZoom() {
  scale.value = 1
}

function onWheel(e: WheelEvent) {
  const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
  const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale.value + delta))
  scale.value = newScale
}

function onDblClick() {
  if (scale.value > 1) {
    resetZoom()
  } else {
    scale.value = 2
  }
}

function onImageLoad() {
  // 切换图片时重置缩放
  resetZoom()
}

// ========== 导航 ==========

watch(() => props.visible, (val) => {
  if (val) {
    currentIndex.value = props.initialIndex || 0
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
    resetZoom()
  }
})

watch(currentIndex, (idx) => {
  currentMedia.value = props.mediaList[idx] || null
}, { immediate: true })

watch(() => props.mediaList, () => {
  currentMedia.value = props.mediaList[currentIndex.value] || null
})

watch(currentMedia, () => {
  resetZoom()
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
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.lightbox-overlay {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ====== 控件层：z-index: 100 确保在缩放图片上方 ====== */
.lightbox-controls {
  position: absolute;
  inset: 0;
  z-index: 100;
  pointer-events: none;  /* 让点击穿透到图片，但按钮自身恢复 pointer-events */
}

.lightbox-controls > * {
  pointer-events: auto;
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

.lightbox-arrow.left {
  left: 12px;
}

.lightbox-arrow.right {
  right: 12px;
}

/* ====== 媒体内容层：z-index 低于控件 ====== */
.lightbox-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 允许缩放后的图片溢出可视区、可滚动查看 */
  overflow: auto;
  max-width: 100%;
  max-height: 100%;
}

.lightbox-media {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 4px;
  /* 让缩放动画平滑 */
  will-change: transform;
  user-select: none;
  -webkit-user-drag: none;
}
</style>
