<template>
  <div class="machine-parts-management">
    <CommonHeader title="机器零部件管理" />

    <el-card shadow="hover" class="management-card">
      <el-tabs v-model="activeTab" type="card" @tab-change="handleTabChange">
        <el-tab-pane label="机器管理" name="machines">
          <MachineManagement
            :is-admin="isAdmin"
            :has-token="hasToken"
          />
        </el-tab-pane>
        <el-tab-pane label="部件管理" name="parts">
          <PartManagement
            :is-admin="isAdmin"
            :has-token="hasToken"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import CommonHeader from '@/components/CommonHeader.vue'
import MachineManagement from '@/components/MachineManagement.vue'
import PartManagement from '@/components/PartManagement.vue'
import { hasModulePermission, ModuleNames, getCurrentUserRole, hasToken as checkHasToken } from '@/utils/authUtils'

const activeTab = ref('machines')

const handleTabChange = (tabName: string) => {
  // 处理标签切换
}
// 是否已登录（存在token）
const hasToken = computed(() => checkHasToken());
// 计算属性：检查当前用户是否为管理员
const isAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'admin';
});

// 页面挂载时检查登录状态和用户角色
onMounted(() => {
  // 登录状态和用户角色检查现在通过computed属性自动处理
});
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