<template>
  <div class="machine-parts-management">
    <CommonHeader title="机器零部件管理" />
    
    <el-card shadow="hover" class="management-card">
      <el-tabs v-model="activeTab" type="card" @tab-change="handleTabChange">
        <el-tab-pane label="机器管理" name="machines">
          <MachineManagement />
        </el-tab-pane>
        <el-tab-pane label="部件管理" name="parts">
          <PartManagement />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CommonHeader from '@/components/CommonHeader.vue'
import MachineManagement from '@/components/MachineManagement.vue'
import PartManagement from '@/components/PartManagement.vue'

const activeTab = ref('machines')

const handleTabChange = (tabName: string) => {
  // 处理标签切换
}
</script>

<style scoped>
.machine-parts-management {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.management-card {
  margin-top: 20px;
}

:deep(.el-tabs__content) {
  padding: 20px;
  min-height: 500px;
}
</style>