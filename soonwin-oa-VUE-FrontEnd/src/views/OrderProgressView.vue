<template>
  <div class="order-progress-container">
    <CommonHeader title="订单进度跟踪" />

    <!-- 订单列表 -->
    <div class="order-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>订单列表</span>
          </div>
        </template>

        <el-table
          :data="orders"
          style="width: 100%"
          @row-click="showOrderDetails"
          v-loading="loading"
          :row-style="{ cursor: 'pointer' }"
        >
          <el-table-column prop="contract_no" label="合同编号" width="150" />
          <el-table-column prop="machine_name" label="名称" width="150" />
          <el-table-column prop="machine_model" label="机型" width="120" />
          <el-table-column prop="order_time" label="下单时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.order_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="ship_time" label="出货时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.ship_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="current_status" label="当前进度" width="120">
            <template #default="scope">
              <el-tag :type="getStatusTagType(scope.row.current_status)">
                {{ scope.row.current_status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="showOrderDetails(scope.row)"
              >
                <el-icon style="margin-right: 5px;"><Search /></el-icon> 查看进度
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          class="pagination"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import { Search } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';
import { getOrderList } from '@/api/progress';

const router = useRouter();

// 响应式数据
const orders = ref<any[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const response: any = await getOrderList({
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    });

    orders.value = response.list || [];
    total.value = response.total || 0;
  } catch (error) {
    console.error('获取订单列表失败:', error);
    ElMessage.error('获取订单列表失败');
  } finally {
    loading.value = false;
  }
};

// 分页相关方法
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchOrders();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchOrders();
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
};

// 状态标签类型映射
const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    下单: 'info',
    采购: 'warning',
    排产: 'warning',
    生产: 'primary',
    发货: 'success',
    完成: 'success'
  };
  return typeMap[status] || 'info';
};

// 显示订单详情
const showOrderDetails = (row: any) => {
  router.push(`/order-progress/${row.id}`);
};

onMounted(() => {
  fetchOrders();
});
</script>

<style scoped>
.order-progress-container {
  padding: 0;
}

.order-list-section {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.progress-text {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}
</style>