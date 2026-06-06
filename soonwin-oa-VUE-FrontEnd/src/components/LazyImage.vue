<template>
  <div ref="rootRef" class="lazy-img-wrapper" :style="{ aspectRatio: aspectRatio || undefined }">
    <!-- 占位骨架 -->
    <div v-if="!loaded" class="lazy-img-placeholder">
      <slot name="placeholder">
        <div class="placeholder-shimmer"></div>
      </slot>
    </div>

    <!-- 图片：加载完成后显示 -->
    <img
      v-show="loaded"
      :src="displaySrc"
      :alt="alt"
      :class="imgClass"
      :style="imgStyle"
      @load="onImgLoad"
      @error="onImgError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { enqueueImageLoad } from '@/composables/useLazyImageQueue'

const props = withDefaults(defineProps<{
  src: string
  alt?: string
  /** 宽高比，如 '16/9'、'1'，用于预留空间防 CLS */
  aspectRatio?: string
  /** true = 立即加载（跳过 IntersectionObserver，用于首屏可视区） */
  immediate?: boolean
  /** 图片 class */
  imgClass?: string
  /** 图片 style */
  imgStyle?: string | Record<string, string>
}>(), {
  alt: '',
  immediate: false,
  imgStyle: '',
})

const emit = defineEmits<{
  (e: 'loaded'): void
  (e: 'error'): void
}>()

const rootRef = ref<HTMLElement | null>(null)
const loaded = ref(false)
const displaySrc = ref('')
let observer: IntersectionObserver | null = null

function triggerLoad() {
  if (!props.src) return

  enqueueImageLoad(props.src).then(() => {
    // 图片已被浏览器缓存，直接赋值 src 即为即时展示
    displaySrc.value = props.src
    loaded.value = true
  })
}

function onImgLoad() {
  emit('loaded')
}

function onImgError() {
  emit('error')
}

onMounted(() => {
  if (!rootRef.value) return

  if (props.immediate) {
    // 首屏可视区：跳过 observer，直接加入加载队列
    triggerLoad()
    return
  }

  // IntersectionObserver：距视口底部 200px 时开始加载
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        triggerLoad()
        observer?.disconnect()
        observer = null
      }
    },
    {
      rootMargin: '0px 0px 200px 0px',
      threshold: 0,
    }
  )
  observer.observe(rootRef.value)
})

// src 变化时重新加载（如分页追加内容后原占位获得新 src）
watch(() => props.src, (newSrc) => {
  if (newSrc && !loaded.value) {
    // 已在观察中：等待 observer 触发
    // 未观察但 immediate：直接加载
    if (props.immediate && !observer) {
      triggerLoad()
    }
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.lazy-img-wrapper {
  position: relative;
  overflow: hidden;
  background: #f3f4f6;
  width: 100%;
}

.lazy-img-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.lazy-img-placeholder {
  position: absolute;
  inset: 0;
}

.placeholder-shimmer {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
