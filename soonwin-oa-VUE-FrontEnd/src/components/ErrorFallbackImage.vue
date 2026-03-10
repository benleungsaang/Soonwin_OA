<template>
  <el-image
    :src="currentSrc"
    :preview-src-list="previewSrcList"
    :alt="alt"
    :fit="fit"
    :preview-teleported="previewTeleported"
    :hide-on-click-modal="hideOnClickModal"
    @error="handleError"
    @click="handleClick"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ElImage } from 'element-plus';

// 定义组件属性
const props = withDefaults(defineProps<{
  src: string;  // 优先加载的缩略图路径
  fallbackSrc: string;  // 降级的原始图片路径
  alt?: string;  // 图片描述
  previewSrcList?: string[]; // 预览图片列表
  fit?: 'fill' | 'contain' | 'cover' | 'none' | 'scale-down'; // 图片适应容器的方式
  previewTeleported?: boolean; // 是否将预览弹窗放置于 body 内
  hideOnClickModal?: boolean; // 是否点击遮罩关闭预览
}>(), {
  alt: '图片',
  previewSrcList: () => [],
  fit: 'cover',
  previewTeleported: true,
  hideOnClickModal: true
});

// 当前显示的图片路径
const currentSrc = ref(props.src);

// 监听 src 变化，确保组件响应 props 变化
watch(() => props.src, (newSrc) => {
  // 立即更新为新的缩略图路径，以防止显示旧图片
  currentSrc.value = newSrc;
});

// 监听 fallbackSrc 变化，确保组件响应 props 变化
watch(() => props.fallbackSrc, (newFallbackSrc) => {
  // 如果当前显示的是旧的 fallbackSrc，则更新为新的 fallbackSrc
  if (currentSrc.value === props.fallbackSrc) {
    currentSrc.value = newFallbackSrc;
  }
});

// 加载失败处理
const handleError = () => {
  // 仅切换一次，避免循环
  if (currentSrc.value === props.fallbackSrc) return;

  currentSrc.value = props.fallbackSrc;
  console.log(`图片 ${props.src} 加载失败，已切换为 ${props.fallbackSrc}`);
};

// 点击处理，阻止事件冒泡
const handleClick = (event: Event) => {
  // 如果需要阻止事件冒泡，可以在父组件中处理
};
</script>

<style scoped>
/* 这里可以添加通用样式 */
</style>