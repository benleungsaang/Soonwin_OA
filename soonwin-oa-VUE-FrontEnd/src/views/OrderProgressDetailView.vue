<template>
  <div class="order-progress-detail">
    <CommonHeader :title="'订单进度详情'" />
    <ProgressDetail :order-id="orderId" />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import CommonHeader from '@/components/CommonHeader.vue'; // 引入CommonHeader组件
import ProgressDetail from '@/components/ProgressDetail.vue';

const route = useRoute();
const orderId = route.params.id as string;
</script>

<style scoped>
.order-progress-detail {
  padding: 0;
}
</style>