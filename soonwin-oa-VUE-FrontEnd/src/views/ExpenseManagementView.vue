<template>
  <div class="expense-management-container">
    <el-page-header content="运营费用管理" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>

    <el-card shadow="hover" class="management-card">
      <template #header>
        <div class="card-header">
          <span>费用管理</span>
          <div>
            <el-button class="button" type="primary" @click="showCreateDialog = true">
              新增费用
            </el-button>
            <el-button type="success" @click="refreshData">刷新</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索筛选区域 -->
      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="费用名称">
          <el-input v-model="searchForm.name" placeholder="请输入费用名称" clearable></el-input>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="searchForm.targetYear" placeholder="请选择年份" style="width:100px;">
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year"
              :value="year"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchExpenses">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="expenses"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="费用名称" width="150" />
        <el-table-column prop="amount" label="费用金额" width="120">
          <template #default="scope">
            <span :class="scope.row.amount >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(scope.row.amount || 0) }}
              <!-- {{ scope.row.amount >= 0 ? `+${Math.abs(scope.row.amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}` : `-${Math.abs(scope.row.amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}` }} -->
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="target_year" label="目标年份" width="100" />
        <el-table-column prop="remark" label="备注信息" width="200">
          <template #default="scope">
            <span v-if="scope.row.remark && scope.row.remark.length > 30">
              {{ scope.row.remark.substring(0, 30) }}...
              <el-popover
                effect="light"
                trigger="hover"
                placement="top"
                :width="300"
              >
                <template #reference>
                  <el-link type="primary" :underline="false">查看</el-link>
                </template>
                <div>{{ scope.row.remark }}</div>
              </el-popover>
            </span>
            <span v-else>{{ scope.row.remark || '无备注' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="160" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button
              size="small"
              type="info"
              @click="showEditDialog(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteExpense(scope.row)"
            >
              删除
            </el-button>
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

    <!-- 年度费用汇总 -->
    <el-card shadow="hover" class="allocation-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>年度运营费用汇总</span>
        </div>
      </template>


      <!-- 年度汇总信息表格 -->
      <div v-if="yearlySummary" class="summary-info">
        <div style="display: flex; justify-content:flex-start; align-items: center; margin-bottom: 15px;">
          <div>
            <strong>年度目标: </strong>
            <span @click="showAnnualTargetDialog" style="cursor:pointer;"> ¥{{ formatCurrency(yearlySummary.annual_target) }}</span>
          </div>
        </div>
        <el-table :data="[yearlySummary]" style="width: 100%" border>
          <el-table-column prop="year" label="年份" width="100" />
          <el-table-column prop="total_expenditure" label="运营总开支" width="150">
            <template #default="scope">
              <span :class="scope.row.total_expenditure < 0 ? 'negative' : 'positive'">
                {{ formatCurrency(scope.row.total_expenditure || 0) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="total_income" label="运营总收入" width="150">
            <template #default="scope">
              <span :class="scope.row.total_income < 0 ? 'negative' : 'positive'">
                {{ formatCurrency(scope.row.total_income || 0) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="total_expenses" label="合计运营费用" width="150">
            <template #default="scope">
              <span :class="scope.row.total_expenses < 0 ? 'negative' : 'positive'">
                {{ formatCurrency(scope.row.total_expenses) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="最近后创建费用时间" width="180">
            <template #default="scope">
              {{ scope.row.latest_expense_create_time }}
            </template>
          </el-table-column>
          <el-table-column label="最近计算时间" width="180">
            <template #default="scope">
              {{ scope.row.latest_calculation ? scope.row.latest_calculation.calculation_time : '未计算' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 费用分摊计算 - 已移除，由订单管理页面处理 -->

    <!-- 新增费用对话框 -->
    <el-dialog v-model="showCreateDialog" title="新增费用" width="500px">
      <el-form :model="newExpense" :rules="expenseRules" ref="expenseFormRef" label-width="100px">
        <el-form-item label="费用名称" prop="name">
          <el-input v-model="newExpense.name" placeholder="请输入费用名称" />
        </el-form-item>
        <el-form-item label="费用金额" prop="amount">
          <el-input v-model.number="newExpense.amount" placeholder="请输入费用金额" type="number">
            <template #append>元</template>
          </el-input>
          <div class="expense-type-selector">
            <el-radio-group v-model="newExpense.expenseSign" style="margin-top: 5px;">
              <el-radio :label="1">支出</el-radio>
              <el-radio :label="-1">收入</el-radio>
            </el-radio-group>
          </div>
        </el-form-item>
        <el-form-item label="目标年份" prop="targetYear">
          <el-select v-model="newExpense.targetYear" placeholder="请选择年份">
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year"
              :value="year"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注信息">
          <el-input
            v-model="newExpense.remark"
            placeholder="请输入备注信息"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createExpense">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑费用对话框 -->
    <el-dialog v-model="showEditDialogVisible" title="编辑费用" width="500px">
      <el-form :model="editExpense" :rules="expenseRules" ref="editExpenseFormRef" label-width="100px">
        <el-form-item label="费用名称" prop="name">
          <el-input v-model="editExpense.name" placeholder="请输入费用名称" />
        </el-form-item>
        <el-form-item label="费用金额" prop="amount">
          <el-input v-model.number="editExpense.amount" placeholder="请输入费用金额" type="number">
            <template #append>元</template>
          </el-input>
          <div class="expense-type-selector">
            <el-radio-group v-model="editExpense.expenseSign" style="margin-top: 5px;">
              <el-radio :label="1">支出</el-radio>
              <el-radio :label="-1">收入</el-radio>
            </el-radio-group>
          </div>
        </el-form-item>
        <el-form-item label="目标年份" prop="targetYear">
          <el-select v-model="editExpense.targetYear" placeholder="请选择年份">
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year"
              :value="year"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注信息">
          <el-input
            v-model="editExpense.remark"
            placeholder="请输入备注信息"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateExpense">更新</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改年度目标对话框 -->
    <el-dialog title="修改年度目标" v-model="annualTargetDialogVisible" width="500px">
      <el-form :model="annualTargetForm" label-width="120px">
        <el-form-item label="年份">
          <el-input v-model.number="summaryForm.targetYear" disabled />
        </el-form-item>
        <el-form-item label="年度目标金额">
          <el-input v-model.number="annualTargetForm.target_amount" placeholder="请输入年度目标金额" type="number">
            <template #append>元</template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="annualTargetDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateAnnualTarget">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import request from '@/utils/request';

// 路由实例
const router = useRouter();

// 当前年份
const currentYear = new Date().getFullYear();
// 年份选项（过去5年到未来2年）
const yearOptions = ref<number[]>([]);
for (let i = currentYear - 5; i <= currentYear + 2; i++) {
  yearOptions.value.push(i);
}

// 格式化货币显示
const formatCurrency = (value: number) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '0.00';
  }
  const numValue = Number(value);
  if (Number.isNaN(numValue)) {
    return '0.00';
  }
  return Math.abs(numValue).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

// 费用数据
const expenses = ref<any[]>([]);
const loading = ref(false);
const showCreateDialog = ref(false);
const showEditDialogVisible = ref(false);

// 分页参数
const pagination = ref({
  page: 1,
  size: 10,
  total: 0
});

// 搜索表单
const searchForm = ref({
  name: '',
  targetYear: null as number | null,
  expenseType: ''
});

// 分摊表单
const allocationForm = ref({
  targetYear: currentYear
});

// 年度汇总表单
const summaryForm = ref({
  targetYear: currentYear
});

// 年度目标对话框相关
const annualTargetDialogVisible = ref(false);
const annualTargetForm = ref({
  target_amount: 10000000.00  // 默认值
});

// 年度汇总信息
const yearlySummary = ref<any>(null);

// 费用分摊计算结果
const allocationResult = ref<any>(null);

// 新增费用表单
const newExpense = ref({
  name: '',
  amount: 0,
  expenseType: '全面分摊',
  targetYear: currentYear,
  remark: '',
  expenseSign: 1  // 1表示支出，-1表示收入
});

// 编辑费用表单
const editExpense = ref({
  id: 0,
  name: '',
  amount: 0,
  expenseType: '全面分摊',
  targetYear: currentYear,
  remark: '',
  expenseSign: 1  // 1表示支出，-1表示收入
});

// 表单引用
const expenseFormRef = ref();
const editExpenseFormRef = ref();

// 验证规则
const expenseRules = {
  name: [
    { required: true, message: '请输入费用名称', trigger: 'blur' }
  ],
  amount: [
    { required: true, message: '请输入费用金额', trigger: 'blur' },
    { type: 'number', message: '费用金额必须为数字', trigger: 'blur' }
  ],
  targetYear: [
    { required: true, message: '请选择目标年份', trigger: 'change' }
  ]
};

// 获取费用列表
const fetchExpenses = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      name: searchForm.value.name || undefined,
      target_year: searchForm.value.targetYear || undefined,
      expense_type: searchForm.value.expenseType || undefined,
    };

    const response: any = await request.get('/api/expenses', { params });

    // 处理费用列表数据
    expenses.value = response.list || [];
    pagination.value.total = response.total || 0;
    pagination.value.page = response.page || 1;
    pagination.value.size = response.size || 10;

    // 处理年度费用汇总数据（现在包含在同一个响应中）
    if (response.yearly_summary) {
      yearlySummary.value = response.yearly_summary;
      // 更新汇总表单的年份选择
      summaryForm.value.targetYear = response.yearly_summary.year;
    }
  } catch (error) {
    console.error('Error fetching expenses:', error);
    ElMessage.error('获取费用列表失败');
  } finally {
    loading.value = false;
  }
};

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    name: '',
    targetYear: null,
    expenseType: ''
  };
  pagination.value.page = 1;
  fetchExpenses();
};

// 刷新数据
const refreshData = () => {
  fetchExpenses();
};

// 创建新费用
const createExpense = async () => {
  try {
    await expenseFormRef.value.validate();

    // 根据expenseSign调整金额的正负
    const finalAmount = newExpense.value.amount * newExpense.value.expenseSign;

    await request.post('/api/expenses', {
      name: newExpense.value.name,
      amount: finalAmount,
      expense_type: newExpense.value.expenseType,
      target_year: newExpense.value.targetYear,
      remark: newExpense.value.remark
    });

    ElMessage.success('费用创建成功');
    showCreateDialog.value = false;

    // 重置表单
    newExpense.value = {
      name: '',
      amount: 0,
      expenseType: '全面分摊',
      targetYear: currentYear,
      remark: '',
      expenseSign: 1
    };

    // 刷新费用列表
    fetchExpenses();
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      ElMessage.error('费用创建失败');
    }
  }
};

// 删除费用
const deleteExpense = async (expense: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除费用 "${expense.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'danger'
      }
    );

    await request.delete(`/api/expenses/${expense.id}`);
    ElMessage.success('费用删除成功');
    fetchExpenses(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('费用删除失败');
    }
  }
};

// 显示编辑对话框
const showEditDialog = (expense: any) => {
  editExpense.value = {
    id: expense.id,
    name: expense.name,
    amount: Math.abs(expense.amount),  // 使用绝对值
    expenseType: expense.expense_type,
    targetYear: expense.target_year,
    remark: expense.remark || '',
    expenseSign: expense.amount >= 0 ? 1 : -1  // 正数为支出(-1)，负数为收入(1)
  };
  showEditDialogVisible.value = true;
};

// 更新费用信息
const updateExpense = async () => {
  try {
    await editExpenseFormRef.value.validate();

    // 根据expenseSign调整金额的正负
    const finalAmount = editExpense.value.amount * editExpense.value.expenseSign;

    await request.put(`/api/expenses/${editExpense.value.id}`, {
      name: editExpense.value.name,
      amount: finalAmount,
      expense_type: editExpense.value.expenseType,
      target_year: editExpense.value.targetYear,
      remark: editExpense.value.remark
    });

    ElMessage.success('费用信息更新成功');
    showEditDialogVisible.value = false;
    fetchExpenses(); // 刷新列表
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      ElMessage.error('费用信息更新失败');
    }
  }
};

// 计算费用分摊
const calculateAllocations = async () => {
  if (!allocationForm.value.targetYear) {
    ElMessage.warning('请选择要计算的年份');
    return;
  }

  try {
    const response: any = await request.post('/api/calculate-expense-allocations', {
      target_year: allocationForm.value.targetYear
    });

    // request.ts会自动解包data部分，所以response直接就是所需的数据
    ElMessage.success('费用分摊计算完成');
    // 存储费用分摊计算结果
    allocationResult.value = response;
    // 不再调用getYearlySummary()，避免额外API请求
    // 年度汇总信息已经包含在response中

    // 刷新费用列表，以显示最新计算结果
    fetchExpenses();
  } catch (error: any) {
    ElMessage.error(error.message || '费用分摊计算失败');
  }
};

// 获取年度摊分费用汇总信息
const getYearlySummary = async () => {
  if (!summaryForm.value.targetYear) {
    ElMessage.warning('请选择要查看的年份');
    return;
  }

  try {
    const response: any = await request.get(`/api/get-yearly-expense-summary/${summaryForm.value.targetYear}`);
    // request.ts会自动解包data部分，所以response直接就是所需的数据
    if (response) {
      yearlySummary.value = response;
      ElMessage.success('年度摊分费用汇总更新成功');
    } else {
      ElMessage.error('获取年度摊分费用汇总数据失败');
    }
  } catch (error: any) {
    console.error('获取年度摊分费用汇总失败:', error);
    ElMessage.error(error.message || '获取年度摊分费用汇总失败');
  }
};

// 年份选择改变时同时更新费用汇总和年度目标
const onYearChange = async () => {
  await getYearlySummary();
};

// 显示年度目标修改对话框
const showAnnualTargetDialog = async () => {
  try {
    const response: any = await request.get(`/api/annual-targets/year/${summaryForm.value.targetYear}`);
    // request.ts会自动解包data部分，所以response就是annual target对象
    annualTargetForm.value.target_amount = response.target_amount || 10000000.00;
    annualTargetDialogVisible.value = true;
  } catch (error) {
    console.error('获取年度目标失败:', error);
    // 如果获取失败，使用默认值
    annualTargetForm.value.target_amount = 10000000.00;
    annualTargetDialogVisible.value = true;
  }
};

// 更新年度目标
const updateAnnualTarget = async () => {
  try {
    await request.put(`/api/annual-targets/year/${summaryForm.value.targetYear}`, {
      target_amount: annualTargetForm.value.target_amount
    });
    ElMessage.success('年度目标更新成功');
    annualTargetDialogVisible.value = false;
    // 重新获取费用汇总信息以显示新的年度目标
    await getYearlySummary();
  } catch (error: any) {
    ElMessage.error(error.message || '年度目标更新失败');
  }
};

// 处理分页大小改变
const handleSizeChange = (newSize: number) => {
  pagination.value.size = newSize;
  pagination.value.page = 1;
  fetchExpenses();
};

// 处理当前页改变
const handleCurrentChange = (newPage: number) => {
  pagination.value.page = newPage;
  fetchExpenses();
};

// 组件挂载时获取数据
onMounted(async () => {
  fetchExpenses();
  // fetchExpenses现在会同时获取费用列表和年度汇总数据，所以不需要单独调用getYearlySummary()
  // 从年度汇总信息中提取费用分摊计算结果
  if (yearlySummary.value) {
    // 从年度汇总中构造费用分摊计算结果
    allocationResult.value = {
      target_year: yearlySummary.value.year,
      total_orders: yearlySummary.value.total_orders,
      total_order_amount: yearlySummary.value.total_order_amount,
      total_net_profit: 0, // 从年度汇总中无法直接获取，设为0
      total_gross_profit: 0, // 从年度汇总中无法直接获取，设为0
      total_direct_cost: 0, // 从年度汇总中无法直接获取，设为0
      total_expense_amount: yearlySummary.value.total_expenses,
      calculation_time: yearlySummary.value.latest_calculation ? yearlySummary.value.latest_calculation.calculation_time : null
    };
  }
});

// 返回上一页
const goBack = () => {
  router.go(-1);
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

// 金额正负样式
const positiveAmountStyle = (amount: number) => {
  return amount >= 0 ? 'positive' : 'negative';
};
</script>

<style scoped>
.expense-management-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.management-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.positive {
  color: #67c23a; /* 绿色表示收入 */
}

.negative {
  color: #f56c6c; /* 红色表示支出 */
}

.allocation-form {
  margin-bottom: 20px;
}

.summary-info {
  margin-top: 20px;
}

.allocation-result {
  margin-top: 20px;
}

.expense-type-selector {
  margin-top: 5px;
}
</style>