<template>
  <div class="order-container">
    <el-page-header content="订单管理系统">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-card shadow="hover" class="order-card">
      <!-- 订单筛选区域 -->
      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="客户名称">
          <el-input v-model="searchForm.customerName" placeholder="请输入客户名称" clearable></el-input>
        </el-form-item>
        <el-form-item label="订单状态">
          <el-select v-model="searchForm.orderStatus" placeholder="请选择订单状态" clearable>
            <el-option label="全部" value=""></el-option>
            <el-option label="待出货" value="pending"></el-option>
            <el-option label="已出货" value="shipped"></el-option>
            <el-option label="已完成" value="completed"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="下单时间">
          <el-date-picker v-model="searchForm.orderTime" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"></el-date-picker>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
          <el-button type="success" icon="el-icon-plus" @click="handleAddOrder">新增订单</el-button>
        </el-form-item>
      </el-form>

      <!-- 订单列表区域 -->
      <el-table :data="orderList" border stripe :loading="isLoading">
        <el-table-column label="序号" type="index" width="60"></el-table-column>
        <el-table-column label="订单编号" prop="order_no" min-width="120"></el-table-column>
        <el-table-column label="客户名称" prop="customer_name" min-width="150"></el-table-column>
        <el-table-column label="客户类型" prop="customer_type" width="100"></el-table-column>
        <el-table-column label="设备名称" prop="machine_name" min-width="150"></el-table-column>
        <el-table-column label="订单金额（元）" prop="contract_amount" width="120" align="right"></el-table-column>
        <el-table-column label="下单时间" prop="order_time" width="140"></el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.ship_time ? 'success' : 'warning'">
              {{ scope.row.ship_time ? '已出货' : '待出货' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center">
          <template #default="scope">
            <el-button type="text" size="small" @click="handleViewOrder(scope.row)">查看</el-button>
            <el-button type="text" size="small" @click="handleEditOrder(scope.row)">编辑</el-button>
            <el-button type="text" size="small" text-color="#ff4d4f" @click="handleDeleteOrder(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页区域 -->
      <el-pagination
        v-model:current-page="pageParams.page"
        v-model:page-size="pageParams.size"
        :total="total"
        layout="total, prev, pager, next, jumper, ->, sizes"
        :page-sizes="[10, 20, 50, 100]"
        @size-change="handlePageSizeChange"
        @current-change="handleCurrentPageChange"
        class="pagination"
      ></el-pagination>
    </el-card>

    <!-- 新增/编辑订单弹窗（后续完善，当前仅占位） -->
    <el-dialog v-model="isOrderDialogOpen" :title="isEditMode ? '编辑订单' : '新增订单'" width="80%">
      <div class="dialog-content">
        <el-message type="info">订单表单功能将在「阶段四：订单基础功能」中完善</el-message>
      </div>
      <template #footer>
        <el-button @click="isOrderDialogOpen = false">取消</el-button>
        <el-button type="primary" @click="isOrderDialogOpen = false">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import request from '@/utils/request';
import { OrderList } from '@/types'; // 引用订单类型定义

// 路由实例
const router = useRouter();

// 搜索表单数据
const searchForm = reactive({
  customerName: '',
  orderStatus: '',
  orderTime: [] as Date[],
});

// 分页参数
const pageParams = reactive({
  page: 1,
  size: 10,
});

// 订单列表数据
const orderList = ref<OrderList[]>([]);
const total = ref(0);
const isLoading = ref(false);

// 弹窗控制
const isOrderDialogOpen = ref(false);
const isEditMode = ref(false);
const currentOrder = ref<OrderList | null>(null);

// 初始化加载订单列表
const loadOrderList = async () => {
  isLoading.value = true;
  try {
    // 模拟接口请求（后续替换为真实接口）
    const res = await request.get<{ list: OrderList[], total: number }>('/order/list', {
      params: {
        page: pageParams.page,
        size: pageParams.size,
        customer_name: searchForm.customerName,
        // 其他筛选参数后续补充
      },
    });
    orderList.value = res.list;
    total.value = res.total;
  } catch (error) {
    ElMessage.error('订单数据加载失败');
    console.error('加载订单失败：', error);
  } finally {
    isLoading.value = false;
  }
};

// 页面挂载时加载数据
onMounted(() => {
  loadOrderList();
});

// 搜索订单
const handleSearch = () => {
  pageParams.page = 1; // 重置为第一页
  loadOrderList();
};

// 重置搜索条件
const resetSearch = () => {
  searchForm.customerName = '';
  searchForm.orderStatus = '';
  searchForm.orderTime = [];
  pageParams.page = 1;
  loadOrderList();
};

// 新增订单
const handleAddOrder = () => {
  isEditMode.value = false;
  currentOrder.value = null;
  isOrderDialogOpen.value = true;
};

// 编辑订单
const handleEditOrder = (order: OrderList) => {
  isEditMode.value = true;
  currentOrder.value = { ...order };
  isOrderDialogOpen.value = true;
};

// 查看订单（后续完善）
const handleViewOrder = (order: OrderList) => {
  ElMessage.info(`查看订单：${order.order_no}`);
};

// 删除订单（后续完善）
const handleDeleteOrder = (id: number) => {
  ElMessage.warning(`删除订单ID：${id}（功能待完善）`);
};

// 分页大小改变
const handlePageSizeChange = (size: number) => {
  pageParams.size = size;
  loadOrderList();
};

// 当前页改变
const handleCurrentPageChange = (page: number) => {
  pageParams.page = page;
  loadOrderList();
};

// 退出登录
const logout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    // 清除本地存储的token
    localStorage.removeItem('oa_token');
    // 提示用户
    ElMessage.success('已退出登录');
    // 跳转到登录页
    router.push('/login');
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('退出登录失败：', error);
    }
  }
};
</script>

<style scoped>
.order-container {
  padding: 20px;
}

.order-card {
  margin-top: 10px;
}

.search-form {
  margin-bottom: 15px;
}

.pagination {
  margin-top: 15px;
  text-align: right;
}

.dialog-content {
  padding: 20px;
}
</style>