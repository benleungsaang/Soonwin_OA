<template>
  <div class="order-management-container">
    <el-page-header content="订单管理" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>

    <!-- 费用汇总信息卡片 -->
    <el-card shadow="hover" class="expense-summary-card" style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>年度费用汇总</span>
          <div class="summary-actions">
            <el-select v-model="currentYear" placeholder="选择年份" @change="fetchExpenseSummary" style="width: 120px; margin-right: 10px;">
              <el-option 
                v-for="year in yearOptions" 
                :key="year" 
                :label="year" 
                :value="year"
              ></el-option>
            </el-select>
            <el-button size="small" @click="fetchExpenseSummary">刷新</el-button>
          </div>
        </div>
      </template>
      <div class="summary-content" v-if="expenseSummary">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">订单总数</div>
              <div class="summary-value">{{ expenseSummary.total_orders }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">合同总金额</div>
              <div class="summary-value">¥{{ formatCurrency(expenseSummary.total_contract_amount) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">总毛利</div>
              <div class="summary-value">¥{{ formatCurrency(expenseSummary.total_gross_profit) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">费用分摊总额</div>
              <div class="summary-value" :class="expenseSummary.total_expense_allocation >= 0 ? 'positive' : 'negative'">
                {{ expenseSummary.total_expense_allocation >= 0 ? '+' : '' }}¥{{ formatCurrency(expenseSummary.total_expense_allocation) }}
              </div>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 15px;">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">估算净利</div>
              <div class="summary-value" :class="expenseSummary.net_profit_estimate >= 0 ? 'positive' : 'negative'">
                ¥{{ formatCurrency(expenseSummary.net_profit_estimate) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">最后更新</div>
              <div class="summary-value">{{ expenseSummary.last_updated }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">计算状态</div>
              <div class="summary-value" :class="expenseSummary.calculation_status === 'completed' ? 'success' : 'warning'">
                {{ expenseSummary.calculation_status === 'completed' ? '已完成' : expenseSummary.calculation_status === 'failed' ? '失败' : '未计算' }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item" style="text-align: right;">
              <el-button type="primary" size="small" @click="updateExpenseAllocations">更新费用分摊</el-button>
            </div>
          </el-col>
        </el-row>
      </div>
      <div v-else class="no-summary-data">
        暂无费用汇总数据，请点击"更新费用分摊"按钮进行计算
      </div>
    </el-card>

    <el-card shadow="hover" class="management-card">
      <!-- 搜索筛选区域 -->
      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="客户名称">
          <el-input v-model="searchForm.customerName" placeholder="请输入客户名称" clearable></el-input>
        </el-form-item>
        <el-form-item label="订单编号">
          <el-input v-model="searchForm.orderNo" placeholder="请输入订单编号" clearable></el-input>
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="searchForm.machineName" placeholder="请输入设备名称" clearable></el-input>
        </el-form-item>
        <el-form-item label="地区">
          <el-select v-model="searchForm.area" placeholder="请选择地区" clearable>
            <el-option label="华东" value="华东"></el-option>
            <el-option label="华南" value="华南"></el-option>
            <el-option label="华北" value="华北"></el-option>
            <el-option label="华中" value="华中"></el-option>
            <el-option label="西南" value="西南"></el-option>
            <el-option label="西北" value="西北"></el-option>
            <el-option label="东北" value="东北"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="订单时间">
          <el-date-picker
            v-model="searchForm.orderTimeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          ></el-date-picker>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchOrders">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
          <el-button type="success" @click="refreshData">刷新</el-button>
          <el-button type="primary" @click="showAddDialog">新增订单</el-button>
        </el-form-item>
      </el-form>

      <!-- 订单表格 -->
      <el-table
        :data="orders"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{background: '#f5f7fa', color: '#606266'}"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="order_no" label="订单编号" width="150" />
        <el-table-column prop="customer_name" label="客户名称" width="150" />
        <el-table-column prop="area" label="地区" width="100" />
        <el-table-column prop="machine_name" label="设备名称" width="150" />
        <el-table-column prop="machine_model" label="机型" width="120" />
        <el-table-column prop="machine_count" label="主机数量" width="100" />
        <el-table-column prop="contract_amount" label="合同金额" width="120">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.contract_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="order_time" label="下单时间" width="120" />
        <el-table-column prop="ship_time" label="出货时间" width="120" />
        <el-table-column prop="gross_profit" label="毛利" width="100">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.gross_profit) }}
          </template>
        </el-table-column>
        <el-table-column prop="net_profit" label="净利" width="100">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.net_profit) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="showEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteOrder(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <el-pagination
        v-model="pagination.page"
        :page-size="pagination.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        class="pagination"
      />
    </el-card>

    <!-- 新增/编辑订单对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="60%"
      :before-close="handleDialogClose"
    >
      <el-form
        :model="orderForm"
        :rules="orderRules"
        ref="orderFormRef"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="新旧" prop="is_new">
              <el-select v-model="orderForm.is_new" placeholder="请选择新旧">
                <el-option label="新" :value="1"></el-option>
                <el-option label="旧" :value="0"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地区" prop="area">
              <el-input v-model="orderForm.area" placeholder="请输入地区"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户名称" prop="customer_name">
              <el-input v-model="orderForm.customer_name" placeholder="请输入客户名称"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户类型" prop="customer_type">
              <el-input v-model="orderForm.customer_type" placeholder="请输入客户类型"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="下单时间" prop="order_time">
              <el-date-picker
                v-model="orderForm.order_time"
                type="date"
                placeholder="选择下单时间"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出货时间" prop="ship_time">
              <el-date-picker
                v-model="orderForm.ship_time"
                type="date"
                placeholder="选择出货时间"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发运国家" prop="ship_country">
              <el-input v-model="orderForm.ship_country" placeholder="请输入发运国家"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同编号" prop="contract_no">
              <el-input v-model="orderForm.contract_no" placeholder="请输入合同编号"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="订单编号" prop="order_no">
              <el-input v-model="orderForm.order_no" placeholder="请输入订单编号"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="包装机单号" prop="machine_no">
              <el-input v-model="orderForm.machine_no" placeholder="请输入包装机单号"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备名称" prop="machine_name">
              <el-input v-model="orderForm.machine_name" placeholder="请输入设备名称"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="机型" prop="machine_model">
              <el-input v-model="orderForm.machine_model" placeholder="请输入机型"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主机数量" prop="machine_count">
              <el-input-number v-model="orderForm.machine_count" :min="1" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位" prop="unit">
              <el-input v-model="orderForm.unit" placeholder="请输入单位"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同金额" prop="contract_amount">
              <el-input-number v-model="orderForm.contract_amount" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="定金" prop="deposit">
              <el-input-number v-model="orderForm.deposit" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="尾款" prop="balance">
              <el-input-number v-model="orderForm.balance" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="退税后总金额" prop="tax_refund_amount">
              <el-input-number v-model="orderForm.tax_refund_amount" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="美金/RMB金额" prop="currency_amount">
              <el-input-number v-model="orderForm.currency_amount" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="回款" prop="payment_received">
              <el-input-number v-model="orderForm.payment_received" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="直接成本" prop="direct_cost">
              <el-input-number v-model="orderForm.direct_cost" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佣金" prop="commission">
              <el-input-number v-model="orderForm.commission" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="摊分费用" prop="allocated_cost">
              <el-input-number v-model="orderForm.allocated_cost" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="自定义增收费用" prop="custom_income">
              <el-input-number v-model="orderForm.custom_income" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="自定义减支费用" prop="custom_expense">
              <el-input-number v-model="orderForm.custom_expense" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="毛利" prop="gross_profit">
              <el-input-number v-model="orderForm.gross_profit" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="净利" prop="net_profit">
              <el-input-number v-model="orderForm.net_profit" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="付款方式" prop="pay_type">
              <el-input v-model="orderForm.pay_type" placeholder="请输入付款方式"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最迟装运期" prop="latest_ship_date">
              <el-date-picker
                v-model="orderForm.latest_ship_date"
                type="date"
                placeholder="选择最迟装运期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计交期" prop="expected_delivery">
              <el-date-picker
                v-model="orderForm.expected_delivery"
                type="date"
                placeholder="选择预计交期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="下单部门" prop="order_dept">
              <el-input v-model="orderForm.order_dept" placeholder="请输入下单部门"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="验收要求" prop="check_requirement">
              <el-input
                v-model="orderForm.check_requirement"
                type="textarea"
                :rows="3"
                placeholder="请输入验收要求"
              ></el-input>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button type="primary" @click="saveOrder" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus';
import request from '@/utils/request';

// 路由实例
const router = useRouter();

// 当前年份
const currentYear = ref(new Date().getFullYear());
// 年份选项
const yearOptions = ref<number[]>([]);
for (let i = currentYear.value - 5; i <= currentYear.value + 2; i++) {
  yearOptions.value.push(i);
}

// 费用汇总信息
const expenseSummary = ref<any>(null);

// 分页参数
const pagination = ref({
  page: 1,
  size: 10,
  total: 0
});

// 搜索表单
const searchForm = ref({
  customerName: '',
  orderNo: '',
  machineName: '',
  area: '',
  orderTimeRange: [] as string[],
});

// 订单数据
const orders = ref<any[]>([]);
const loading = ref(false);

// 对话框相关
const dialogVisible = ref(false);
const dialogTitle = ref('');
const isEdit = ref(false);
const orderFormRef = ref<FormInstance | null>(null);
const submitting = ref(false);

// 订单表单
const orderForm = ref({
  id: 0,
  is_new: 1,
  area: '',
  customer_name: '',
  customer_type: '',
  order_time: '',
  ship_time: '',
  ship_country: '',
  contract_no: '',
  order_no: '',
  machine_no: '',
  machine_name: '',
  machine_model: '',
  machine_count: 1,
  unit: '',
  contract_amount: 0,
  deposit: 0,
  balance: 0,
  tax_refund_amount: 0,
  currency_amount: 0,
  payment_received: 0,
  direct_cost: 0,
  commission: 0,
  allocated_cost: 0,
  custom_income: 0,
  custom_expense: 0,
  gross_profit: 0,
  net_profit: 0,
  pay_type: '',
  latest_ship_date: '',
  expected_delivery: '',
  order_dept: '',
  check_requirement: '',
  attachment_imgs: '',
  attachment_videos: ''
});

// 表单校验规则
const orderRules = ref<FormRules>({
  customer_name: [
    { required: true, message: '请输入客户名称', trigger: 'blur' }
  ],
  order_no: [
    { required: true, message: '请输入订单编号', trigger: 'blur' }
  ],
  machine_name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ],
  contract_amount: [
    { required: true, message: '请输入合同金额', trigger: 'blur' }
  ]
});

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      customer_name: searchForm.value.customerName || undefined,
      order_no: searchForm.value.orderNo || undefined,
      machine_name: searchForm.value.machineName || undefined,
      area: searchForm.value.area || undefined,
      start_date: searchForm.value.orderTimeRange?.[0] || undefined,
      end_date: searchForm.value.orderTimeRange?.[1] || undefined
    };

    const response = await request.get('/api/orders', { params });
    orders.value = response.list || [];
    pagination.value.total = response.total || 0;
    pagination.value.page = response.page || 1;
    pagination.value.size = response.size || 10;
  } catch (error) {
    console.error('Error fetching orders:', error);
    ElMessage.error('获取订单列表失败');
  } finally {
    loading.value = false;
  }
};

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    customerName: '',
    orderNo: '',
    machineName: '',
    area: '',
    orderTimeRange: [],
  };
  pagination.value.page = 1;
  fetchOrders();
};

// 刷新数据
const refreshData = () => {
  fetchOrders();
};

// 处理分页大小改变
const handleSizeChange = (newSize: number) => {
  pagination.value.size = newSize;
  pagination.value.page = 1;
  fetchOrders();
};

// 处理当前页改变
const handleCurrentChange = (newPage: number) => {
  pagination.value.page = newPage;
  fetchOrders();
};

// 显示新增对话框
const showAddDialog = () => {
  dialogTitle.value = '新增订单';
  isEdit.value = false;
  resetForm();
  dialogVisible.value = true;
};

// 显示编辑对话框
const showEditDialog = (order: any) => {
  dialogTitle.value = '编辑订单';
  isEdit.value = true;
  // 深拷贝订单数据到表单
  Object.assign(orderForm.value, order);
  dialogVisible.value = true;
};

// 重置表单
const resetForm = () => {
  orderForm.value = {
    id: 0,
    is_new: 1,
    area: '',
    customer_name: '',
    customer_type: '',
    order_time: '',
    ship_time: '',
    ship_country: '',
    contract_no: '',
    order_no: '',
    machine_no: '',
    machine_name: '',
    machine_model: '',
    machine_count: 1,
    unit: '',
    contract_amount: 0,
    deposit: 0,
    balance: 0,
    tax_refund_amount: 0,
    currency_amount: 0,
    payment_received: 0,
    direct_cost: 0,
    commission: 0,
    allocated_cost: 0,
    custom_income: 0,
    custom_expense: 0,
    gross_profit: 0,
    net_profit: 0,
    pay_type: '',
    latest_ship_date: '',
    expected_delivery: '',
    order_dept: '',
    check_requirement: '',
    attachment_imgs: '',
    attachment_videos: ''
  };
};

// 保存订单
const saveOrder = async () => {
  try {
    await orderFormRef.value?.validate();
    submitting.value = true;

    if (isEdit.value) {
      // 更新订单
      await request.put(`/api/orders/${orderForm.value.id}`, orderForm.value);
      ElMessage.success('订单更新成功');
    } else {
      // 创建订单
      await request.post('/api/orders', orderForm.value);
      ElMessage.success('订单创建成功');
    }

    dialogVisible.value = false;
    fetchOrders();
  } catch (error: any) {
    if (error.message && error.message !== 'Validation failed') {
      ElMessage.error(error.message || (isEdit.value ? '更新订单失败' : '创建订单失败'));
    }
  } finally {
    submitting.value = false;
  }
};

// 删除订单
const deleteOrder = async (id: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个订单吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    await request.delete(`/api/orders/${id}`);
    ElMessage.success('订单删除成功');
    fetchOrders();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除订单失败：', error);
      ElMessage.error('删除订单失败');
    }
  }
};

// 处理对话框关闭
const handleDialogClose = () => {
  dialogVisible.value = false;
  resetForm();
};

// 格式化货币显示
const formatCurrency = (value: number) => {
  if (value === null || value === undefined) return '0.00';
  return Number(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 组件挂载时获取数据
onMounted(() => {
  fetchOrders();
  fetchExpenseSummary(); // 获取费用汇总信息
});

// 获取费用汇总信息
const fetchExpenseSummary = async () => {
  try {
    const response: any = await request.get('/api/orders/expense-summary', {
      params: {
        year: currentYear.value
      }
    });
    expenseSummary.value = response.data;
  } catch (error) {
    console.error('获取费用汇总失败：', error);
    ElMessage.error('获取费用汇总失败');
    // 即使失败也设置为null，显示提示信息
    expenseSummary.value = null;
  }
};

// 更新费用分摊
const updateExpenseAllocations = async () => {
  try {
    const response: any = await request.post('/api/calculate-expense-allocations', {
      target_year: currentYear.value
    });
    ElMessage.success(response.msg || '费用分摊更新成功');
    // 更新费用汇总信息
    fetchExpenseSummary();
    // 刷新订单列表，以便显示更新后的净利
    fetchOrders();
  } catch (error: any) {
    ElMessage.error(error.message || '费用分摊更新失败');
  }
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
.order-management-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.management-card {
  margin-top: 20px;
}

.expense-summary-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-content {
  padding: 10px 0;
}

.summary-item {
  text-align: center;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fafafa;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.summary-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.summary-value.positive {
  color: #67c23a;
}

.summary-value.negative {
  color: #f56c6c;
}

.summary-value.success {
  color: #67c23a;
}

.summary-value.warning {
  color: #e6a23c;
}

.no-summary-data {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>