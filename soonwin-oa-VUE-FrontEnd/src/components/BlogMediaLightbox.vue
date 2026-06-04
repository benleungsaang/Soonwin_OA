<template>
  <teleport to="body">
    <div v-if="visible" class="lightbox-overlay" @click.self="close" @keydown="handleKeydown">
      <div class="lightbox-container">
        <!-- 关闭按钮 -->
        <el-button class="lightbox-close" circle @click="close">
          <el-icon><Close /></el-icon>
        </el-button>

        <!-- 计数器 -->
        <div class="lightbox-counter" v-if="mediaList.length > 1">
          {{ currentIndex + 1 }} / {{ mediaList.length }}
        </div>

        <!-- 左箭头 -->
        <el-button
          v-if="mediaList.length > 1"
          class="lightbox-arrow left"
          circle
          @click="prev"
        >
          <el-icon><ArrowLeft /></el-icon>
        </el-button>

        <!-- 媒体内容 -->
        <div class="lightbox-content">
          <img
            v-if="currentMedia?.media_type === 'image'"
            :src="getMediaUrl(currentMedia.file_path)"
            alt=""
            class="lightbox-media"
          />
          <video
            v-else-if="currentMedia?.media_type === 'video'"
            :src="getMediaUrl(currentMedia.file_path)"
            controls
            autoplay
            class="lightbox-media"
          />
        </div>

        <!-- 右箭头 -->
        <el-button
          v-if="mediaList.length > 1"
          class="lightbox-arrow right"
          circle
          @click="next"
        >
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
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

watch(() => props.visible, (val) => {
  if (val) {
    currentIndex.value = props.initialIndex || 0
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

watch(currentIndex, (idx) => {
  currentMedia.value = props.mediaList[idx] || null
}, { immediate: true })

watch(() => props.mediaList, () => {
  currentMedia.value = props.mediaList[currentIndex.value] || null
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
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-close {
  position: absolute;
  top: -50px;
  right: 0;
  z-index: 10;
}

.lightbox-counter {
  position: absolute;
  top: -50px;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-size: 15px;
  z-index: 10;
}

.lightbox-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
}

.lightbox-arrow.left {
  left: -50px;
}

.lightbox-arrow.right {
  right: -50px;
}

.lightbox-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-media {
  max-width: 85vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 4px;
}
</style>
