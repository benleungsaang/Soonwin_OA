<template>
  <div class="redirect-container">
    <p>正在跳转到询盘列表页面...</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

onMounted(() => {
  // 重定向到询盘列表页面，因为所有功能现在都在列表页中以模态框形式实现
  router.push('/inquiries');
});
</script>

<style scoped>
.redirect-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  font-size: 18px;
}
</style>