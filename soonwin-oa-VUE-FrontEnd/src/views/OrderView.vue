<template>
  <div class="order-management-container">
    <el-page-header content="订单管理" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>


    <el-card shadow="hover" class="management-card">
      <!-- 搜索筛选区域 -->
      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="订单搜索">
          <el-input v-model="searchForm.customerName" placeholder="请输入订单内容..." clearable></el-input>
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
          <el-button type="warning" @click="showAddDialog">新增订单</el-button>
        </el-form-item>
      </el-form>

      <!-- 订单表格 -->
      <el-table
        :data="orders"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
      >
        <!-- <el-table-column prop="id" label="ID" width="80" /> -->
        <!-- <el-table-column prop="order_no" label="订单编号" width="150" /> -->
        <el-table-column prop="customer_name" label="客户名称" width="150" />
        <el-table-column prop="area" label="地区" width="100" />
        <el-table-column prop="machine_name" label="名称" width="150" />
        <el-table-column prop="machine_model" label="机型" width="120" />
        <el-table-column prop="machine_count" label="主机数量" width="100" />
        <el-table-column prop="contract_amount" label="合同金额" width="120">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.contract_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="machine_cost" label="机器成本" width="100">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.machine_cost) }}
          </template>
        </el-table-column>
        <el-table-column prop="gross_profit" label="毛利" width="100">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.gross_profit) }}
          </template>
        </el-table-column>
        <el-table-column prop="proportionate_cost" label="摊分费用" width="100">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.proportionate_cost) }}
          </template>
        </el-table-column>
        <el-table-column prop="individual_cost" label="个别费用" width="100">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.individual_cost) }}
          </template>
        </el-table-column>
        <el-table-column prop="net_profit" label="净利" width="100">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.net_profit) }}
          </template>
        </el-table-column>
        <el-table-column prop="order_time" label="下单时间" width="120" />
        <el-table-column prop="ship_time" label="出货时间" width="120" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="showEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" @click="showIndividualExpensesDialog(scope.row)">添加费用</el-button>
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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
          <div>
            <strong>{{ expenseSummary.year }}年度 - 设定目标: </strong>
            <span @click="showAnnualTargetDialog" style="cursor: pointer;">￥ {{ formatCurrency(expenseSummary.annual_target) }}</span>
          </div>
        </div>
        <el-table
        :data="[expenseSummary]"
        style="width: 100%"
        border
        :header-cell-style="{background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        >
          <el-table-column prop="year" label="年份" width="100" />
          <el-table-column prop="total_orders" label="订单数量" width="90">
            <template #default="scope">
                {{ scope.row.total_orders }}
            </template>
          </el-table-column>
          <el-table-column prop="total_order_amount" label="总合同金额" width="110">
            <template #default="scope">
              <span :class="scope.row.total_order_amount >= 0 ? 'negative' : 'positive'">
                {{ formatCurrency(scope.row.total_order_amount) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="machine_cost_amount" label="机器成本" width="110">
            <template #default="scope">
                {{ formatCurrency(scope.row.machine_cost_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="total_expenses" label="运营成本" width="110">
            <template #default="scope">
                {{ formatCurrency(scope.row.total_expenses) }}
            </template>
          </el-table-column>
          <el-table-column prop="individual_cost_amount" label="独立费用汇总" width="110">
            <template #default="scope">
                {{ formatCurrency(scope.row.individual_cost_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="net_profit" label="净利" width="110">
            <template #default="scope">
              <span :class="scope.row.net_profit < 0 ? 'positive' : 'negative'">
                {{ formatCurrency(scope.row.net_profit) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <!-- 饼图显示 -->
        <div v-if="expenseSummary" style="margin-top: 20px; height: 400px;">
          <div id="expense-pie-chart" style="width: 100%; height: 100%;"></div>
        </div>
        <!-- <div style="margin-top: 10px; text-align: right;">
          <el-button type="primary" @click="updateOrderProportionateCost">更新订单摊分费用到每个订单</el-button>
        </div> -->
      </div>
      <div v-else class="no-summary-data">
        暂无费用汇总数据，请点击"刷新"按钮进行加载
      </div>
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
              <el-input v-model="orderForm.customer_type" placeholder="经销商，终端 ..."></el-input>
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
              <el-input v-model="orderForm.contract_no" placeholder="请输入合同编号" @blur="checkContractNoDuplicate"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="订单编号" prop="order_no">
              <el-input v-model="orderForm.order_no" placeholder="请输入订单编号（可选）"></el-input>
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
            <el-form-item label="名称" prop="machine_name">
              <el-input v-model="orderForm.machine_name" placeholder="请输入名称"></el-input>
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
              <el-input-number
              v-model="orderForm.contract_amount"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
            ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="定金" prop="deposit">
              <el-input-number
              v-model="orderForm.deposit"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
            ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="尾款" prop="balance">
              <el-input-number
              v-model="orderForm.balance"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
            ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税费(%)" prop="tax_rate">
              <el-input-number v-model="orderForm.tax_rate" :precision="2" :min="0" style="width: 100%"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="退税后总金额" prop="tax_refund_amount">
              <el-input-number
              v-model="orderForm.tax_refund_amount"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
            ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原始发票价" prop="currency_amount">
              <el-input-number
              v-model="orderForm.currency_amount"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
            ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="回款" prop="payment_received">
              <el-input-number
              v-model="orderForm.payment_received"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
            ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="机器成本" prop="machine_cost">
              <el-input-number
              v-model="orderForm.machine_cost"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
            ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <!-- <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佣金" prop="commission">
              <el-input-number
              v-model="orderForm.commission"
              :precision="2"
              :min="0"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
            ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row> -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="摊分费用" prop="proportionate_cost">
              <el-input-number
              v-model="orderForm.proportionate_cost"
              :precision="2"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
              disabled
            ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="独立费用" prop="individual_cost">
              <el-input-number
              v-model="orderForm.individual_cost"
              :precision="2"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
              disabled
            ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="付款方式" prop="pay_type">
              <el-select v-model="orderForm.pay_type" placeholder="请选择付款方式" style="width: 100%">
                <el-option label="T/T" value="T/T"></el-option>
                <el-option label="L/C" value="L/C"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
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
        </el-row>
        <el-row :gutter="20">
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
          <el-col :span="12">
            <el-form-item label="下单部门" prop="order_dept">
              <el-input v-model="orderForm.order_dept" placeholder="请输入下单部门"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <!-- 毛利和净利显示区域 -->
      <div style="background-color: #f5f7fa; padding: 15px; border-radius: 4px; margin-top: 20px;">

          <div>
            <span style="font-weight: bold;">毛利：</span>
            <span :class="orderForm.gross_profit >= 0 ? 'positive' : 'negative'">¥{{ formatCurrency(orderForm.gross_profit) }}</span>
          </div>
        <div style="margin-top: 10px; font-size: 14px; color: #606266;">
          <p>合同金额（{{ formatCurrency(orderForm.contract_amount || 0) }}） - 机器成本（{{ formatCurrency(orderForm.machine_cost || 0) }}）</p>
        </div>
          <div>
            <span style="font-weight: bold;">净利：</span>
            <span :class="orderForm.net_profit >= 0 ? 'positive' : 'negative'">¥{{ formatCurrency(orderForm.net_profit) }}</span>
          </div>
        <div style="margin-top: 10px; font-size: 14px; color: #606266;">
          <p>毛利（{{ formatCurrency(orderForm.gross_profit || 0) }}） - 摊分费用（{{ formatCurrency(orderForm.proportionate_cost || 0) }}） - 独立费用({{ formatCurrency(orderForm.individual_cost || 0) }}) - 佣金（{{ formatCurrency(orderForm.commission || 0) }}）</p>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button type="primary" @click="saveOrder" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改年度目标对话框 -->
    <el-dialog title="修改年度目标" v-model="annualTargetDialogVisible" width="500px">
      <el-form :model="annualTargetForm" label-width="120px">
        <el-form-item label="年份">
          <el-input v-model.number="currentYear" disabled />
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

    <!-- 个别费用管理对话框 -->
    <el-dialog
      :title="`订单 ${currentOrder.customer_name} - 个别费用管理`"
      v-model="individualExpensesDialogVisible"
      width="70%"
      :before-close="handleIndividualExpensesDialogClose"
    >
      <div class="individual-expenses-header" style="display: flex; align-items: center;">
        <h4>订单信息： - {{ currentOrder.customer_name }} - (合同金额: ¥{{ formatCurrency(currentOrder.contract_amount) }})</h4>
        <el-button style="margin-left: 15px;" type="primary" @click="showAddIndividualExpenseDialog">添加费用</el-button>
      </div>

      <el-table
        :data="individualExpenses"
        v-loading="individualExpensesLoading"
        style="width: 100%"
        stripe
        border
        :cell-style="{ textAlign: 'center' }"
        :header-cell-style="{ textAlign: 'center' }"
      >
        <el-table-column prop="id" label="ID" width="50" />
        <el-table-column prop="name" label="费用名称" width="100" />
        <el-table-column prop="amount" label="费用金额" width="120">
          <template #default="scope">
            <span :class="scope.row.amount >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(scope.row.amount || 0) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" width="150" />
        <el-table-column prop="create_time" label="创建时间" width="160" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="showEditIndividualExpenseDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteIndividualExpense(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="individual-expenses-total" style="margin-top: 20px; padding: 15px; background-color: #f5f7fa; border-radius: 4px;">
        <strong>个别费用总计：¥{{ formatCurrency(individualExpensesTotal) }}</strong>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleIndividualExpensesDialogClose">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加/编辑个别费用对话框 -->
    <el-dialog
      :title="individualExpenseDialogTitle"
      v-model="individualExpenseDialogVisible"
      width="500px"
      :before-close="handleIndividualExpenseDialogClose"
    >
      <el-form :model="individualExpenseForm" :rules="individualExpenseRules" ref="individualExpenseFormRef" label-width="100px">
        <el-form-item label="费用名称" prop="name">
          <el-input v-model="individualExpenseForm.name" placeholder="请输入费用名称" />
        </el-form-item>
        <el-form-item label="费用金额" prop="amount">
          <el-input v-model.number="individualExpenseForm.amount" placeholder="请输入费用金额" type="number">
            <template #append>元</template>
          </el-input>
          <div class="expense-type-selector">
            <el-radio-group v-model="individualExpenseForm.expenseSign" style="margin-top: 5px;">
              <el-radio :label="1">支出</el-radio>
              <el-radio :label="-1">收入</el-radio>
            </el-radio-group>
          </div>
        </el-form-item>
        <el-form-item label="备注信息">
          <el-input
            v-model="individualExpenseForm.remark"
            placeholder="请输入备注信息"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleIndividualExpenseDialogClose">取消</el-button>
          <el-button type="primary" @click="saveIndividualExpense" :loading="individualExpenseSubmitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus';
import request from '@/utils/request';
import { Pointer } from '@element-plus/icons-vue';

// 导入ECharts
import * as echarts from 'echarts';

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

// 个别费用对话框相关
const individualExpensesDialogVisible = ref(false);
const individualExpenseDialogVisible = ref(false);
const individualExpenseDialogTitle = ref('');
const individualExpenseSubmitting = ref(false);
const currentOrder = ref<any>({});
const individualExpenses = ref<any[]>([]);
const individualExpensesTotal = ref(0);
const individualExpensesLoading = ref(false);
const individualExpenseFormRef = ref<FormInstance | null>(null);

// 个别费用表单
const individualExpenseForm = ref({
  id: 0,
  name: '',
  amount: 0,
  remark: '',
  expenseSign: 1  // 1表示正数（收入/加费用），-1表示负数（支出/减费用）
});

// 个别费用表单校验规则
const individualExpenseRules = ref<FormRules>({
  name: [
    { required: true, message: '请输入费用名称', trigger: 'blur' }
  ],
  amount: [
    { required: true, message: '请输入费用金额', trigger: 'blur' },
    { type: 'number', message: '费用金额必须为数字', trigger: 'blur' }
  ]
});

// 年度目标对话框相关
const annualTargetDialogVisible = ref(false);
const annualTargetForm = ref({
  target_amount: 10000000.00  // 默认值
});

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
  order_no: '',  // X标记表示非必填，所以默认为空
  machine_no: '',
  machine_name: '包装机',  // 默认值"包装机"
  machine_model: '',
  machine_count: 1,  // 默认值1
  unit: 'set',  // 默认值"set"
  contract_amount: 0,
  deposit: 0,  // 默认0
  balance: 0,  // 默认0
  tax_rate: 13.0,  // 新增字段，默认13
  tax_refund_amount: 0,  // 默认0
  currency_amount: 0,  // 默认0
  payment_received: 0,  // 默认0
  machine_cost: 0,  // 新字段，原direct_cost
  net_profit: 0,  // 默认0
  operational_cost: 0,  // 新增字段，默认0
  gross_profit: 0,  // 默认0
  pay_type: 'T/T',  // 默认T/T
  commission: 0,  // 默认0
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
  customer_type: [
    { required: true, message: '请输入客户类型', trigger: 'blur' }
  ],
  order_time: [
    { required: true, message: '请选择下单时间', trigger: 'change' }
  ],
  contract_no: [
    { required: true, message: '请输入合同编号', trigger: 'blur' }
  ],
  machine_name: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ],
  machine_model: [
    { required: true, message: '请输入机型', trigger: 'blur' }
  ],
  machine_count: [
    { required: true, message: '请输入主机数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '主机数量至少为1', trigger: 'blur' }
  ],
  unit: [
    { required: true, message: '请输入单位', trigger: 'blur' }
  ],
  contract_amount: [
    { required: true, message: '请输入合同金额', trigger: 'blur' },
    { type: 'number', message: '合同金额必须为数字', trigger: 'blur' }
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
  // 深拷贝订单数据到表单，确保所有字段都被正确复制
  orderForm.value = {
    ...orderForm.value, // 保持默认值
    ...order // 覆盖为实际订单值
  };
  // 编辑时自动计算利润
  setTimeout(() => {
    calculateProfits();
  }, 100); // 延迟执行以确保数据已更新
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
    order_no: '',  // X标记表示非必填，所以默认为空
    machine_no: '',
    machine_name: '包装机',  // 默认值"包装机"
    machine_model: '',
    machine_count: 1,  // 默认值1
    unit: 'set',  // 默认值"set"
    contract_amount: 0,
    deposit: 0,  // 默认0
    balance: 0,  // 默认0
    tax_rate: 13.0,  // 新增字段，默认13
    tax_refund_amount: 0,  // 默认0
    currency_amount: 0,  // 默认0
    payment_received: 0,  // 默认0
    machine_cost: 0,  // 新字段，原direct_cost
    net_profit: 0,  // 默认0，将在calculateProfits中更新
    proportionate_cost: 0,  // 摊分费用
    individual_cost: 0,  // 个别费用
    gross_profit: 0,  // 默认0，将在calculateProfits中更新
    pay_type: 'T/T',  // 默认T/T
    commission: 0,  // 默认0
    latest_ship_date: '',
    expected_delivery: '',
    order_dept: '',
    check_requirement: '',
    attachment_imgs: '',
    attachment_videos: ''
  };
  // 重置表单后计算利润
  setTimeout(() => {
    calculateProfits();
  }, 100);
};

// 保存订单
const saveOrder = async () => {
  try {
    await orderFormRef.value?.validate();
    submitting.value = true;

    // 在发送到后端前计算毛利和净利
    const updatedOrderForm = { ...orderForm.value };

    // 毛利 = 合同金额 - 机器成本
    updatedOrderForm.gross_profit = (updatedOrderForm.contract_amount || 0) - (updatedOrderForm.machine_cost || 0);

    // 净利 = 合同金额 - 机器成本 - 摊分费用 - 个别费用 - 佣金
    updatedOrderForm.net_profit = (updatedOrderForm.contract_amount || 0) -
                                 (updatedOrderForm.machine_cost || 0) -
                                 (updatedOrderForm.proportionate_cost || 0) -
                                 (updatedOrderForm.individual_cost || 0) -
                                 (updatedOrderForm.commission || 0);

    if (isEdit.value) {
      // 更新订单
      await request.put(`/api/orders/${updatedOrderForm.id}`, updatedOrderForm);
      ElMessage.success('订单更新成功');
    } else {
      // 创建订单
      await request.post('/api/orders', updatedOrderForm);
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

// 检查合同编号是否重复
const checkContractNoDuplicate = async () => {
  if (!orderForm.value.contract_no) {
    return;
  }

  try {
    // 查询所有订单中是否有相同的合同编号
    const params = {
      contract_no: orderForm.value.contract_no,
      page: 1,
      size: 100  // 获取前100条记录检查重复
    };

    const response = await request.get('/api/orders', { params });

    if (response.list) {
      // 过滤掉当前编辑的订单（如果是编辑模式）
      const duplicateOrders = isEdit.value
        ? response.list.filter((order: any) => order.contract_no === orderForm.value.contract_no && order.id !== orderForm.value.id)
        : response.list.filter((order: any) => order.contract_no === orderForm.value.contract_no);

      if (duplicateOrders.length > 0) {
        ElMessage.warning(`合同编号 "${orderForm.value.contract_no}" 已存在，允许重复但请注意确认！`);
      }
    }
  } catch (error) {
    console.error('检查合同编号重复失败：', error);
  }
};;

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

// 格式化数字为千分位格式（用于显示）
const formatNumber = (val: number | null | undefined) => {
  if (!val && val !== 0) return '';
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// 解析千分位格式的字符串为数字（用于绑定值）
const parseNumber = (val: string | number | null | undefined) => {
  if (!val && val !== 0) return 0;
  if (typeof val === 'number') return val;
  // 去掉所有逗号和空格，转回数字
  return Number(val.toString().replace(/[,，\s]/g, ''));
};

// 计算毛利和净利
const calculateProfits = () => {
  // 毛利 = 合同金额 - 机器成本
  const grossProfit = (orderForm.value.contract_amount || 0) - (orderForm.value.machine_cost || 0);
  orderForm.value.gross_profit = grossProfit;

  // 净利 = 合同金额 - 机器成本 - 摊分费用 - 个别费用 - 佣金
  const netProfit = (orderForm.value.contract_amount || 0) -
                   (orderForm.value.machine_cost || 0) -
                   (orderForm.value.proportionate_cost || 0) -
                   (orderForm.value.individual_cost || 0) -
                   (orderForm.value.commission || 0);
  orderForm.value.net_profit = netProfit;
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
    const response: any = await request.get(`/api/get-yearly-expense-summary/${currentYear.value}`);
    // request.ts会自动解包data部分，所以response直接就是所需的数据
    expenseSummary.value = response;

    // 延迟生成饼图，确保DOM已更新
    setTimeout(() => {
      generatePieChart();
    }, 100);
  } catch (error) {
    console.error('获取费用汇总失败：', error);
    ElMessage.error('获取费用汇总失败');
    // 即使失败也设置为null，显示提示信息
    expenseSummary.value = null;
  }
};

// 生成饼图
const generatePieChart = () => {
  if (!expenseSummary.value) return;

  // 获取DOM元素
  const chartDom = document.getElementById('expense-pie-chart');
  if (!chartDom) return;

  // 如果已有实例，先销毁
  if (chartInstance) {
    chartInstance.dispose();
  }

  // 初始化ECharts实例
  chartInstance = echarts.init(chartDom);

  // 获取总合同金额作为分母
  const totalOrderAmount = parseFloat(expenseSummary.value.total_order_amount || 0);

  // 准备饼图数据，以各项占总合同金额的比例来显示
  const pieData = [];

  // 添加机器成本（如果非零）
  const machineCost = parseFloat(expenseSummary.value.machine_cost_amount || 0);
  if (machineCost !== 0) {
    pieData.push({
      value: Math.abs(machineCost),
      name: `机器成本 ${(totalOrderAmount !== 0 ? (Math.abs(machineCost) / Math.abs(totalOrderAmount) * 100).toFixed(2) : 0)}%`
    });
  }

  // 添加运营成本（如果非零）
  const totalExpenses = parseFloat(expenseSummary.value.total_expenses || 0);
  if (totalExpenses !== 0) {
    pieData.push({
      value: Math.abs(totalExpenses),
      name: `运营成本 ${(totalOrderAmount !== 0 ? (Math.abs(totalExpenses) / Math.abs(totalOrderAmount) * 100).toFixed(2) : 0)}%`
    });
  }

  // 添加独立费用汇总（如果非零）
  const individualCost = parseFloat(expenseSummary.value.individual_cost_amount || 0);
  if (individualCost !== 0) {
    pieData.push({
      value: Math.abs(individualCost),
      name: `独立费用汇总 ${(totalOrderAmount !== 0 ? (Math.abs(individualCost) / Math.abs(totalOrderAmount) * 100).toFixed(2) : 0)}%`
    });
  }

  // 添加净利（如果非零）
  const netProfit = parseFloat(expenseSummary.value.net_profit || 0);
  if (netProfit !== 0) {
    pieData.push({
      value: Math.abs(netProfit),
      name: `净利 ${(totalOrderAmount !== 0 ? (Math.abs(netProfit) / Math.abs(totalOrderAmount) * 100).toFixed(2) : 0)}%`
    });
  }

  // 饼图配置项
  const option = {
    title: {
      text: `${expenseSummary.value.year}年度费用构成 - 基于总合同金额`,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ￥{c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: '费用构成',
        type: 'pie',
        radius: '50%',
        data: pieData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          formatter: '{b|{b}}\n{c|￥{c}}',
          rich: {
            b: {
              fontSize: 12,
              lineHeight: 16
            },
            c: {
              fontSize: 10,
              color: '#999'
            }
          }
        }
      }
    ]
  };

  // 设置配置项并渲染图表
  chartInstance.setOption(option);

  // 监听窗口大小变化，自动调整图表大小
  window.addEventListener('resize', () => {
    chartInstance?.resize();
  });
};// 更新年度分摊费用
const updateExpenseAllocations = async () => {
  try {
    const response: any = await request.get(`/api/get-yearly-expense-summary/${currentYear.value}`);
    ElMessage.success(response.msg || '年度分摊费用更新成功');
    // 更新费用汇总信息
    fetchExpenseSummary();
    // 刷新订单列表，以便显示更新后的净利
    fetchOrders();
  } catch (error: any) {
    ElMessage.error(error.message || '年度分摊费用更新失败');
  }
};

// 显示个别费用管理对话框
const showIndividualExpensesDialog = async (order: any) => {
  currentOrder.value = order;
  individualExpensesDialogVisible.value = true;
  await fetchIndividualExpenses(order.id);
};

// 获取个别费用列表
const fetchIndividualExpenses = async (orderId: number) => {
  individualExpensesLoading.value = true;
  try {
    const response: any = await request.get(`/api/orders/${orderId}/individual-expenses`);
    individualExpenses.value = response.list || [];
    individualExpensesTotal.value = response.total_individual_cost || 0;
  } catch (error) {
    console.error('获取个别费用列表失败:', error);
    ElMessage.error('获取个别费用列表失败');
  } finally {
    individualExpensesLoading.value = false;
  }
};

// 显示添加个别费用对话框
const showAddIndividualExpenseDialog = () => {
  individualExpenseDialogTitle.value = '添加费用';
  individualExpenseForm.value = {
    id: 0,
    name: '',
    amount: 0,
    remark: '',
    expenseSign: 1
  };
  individualExpenseDialogVisible.value = true;
};

// 显示编辑个别费用对话框
const showEditIndividualExpenseDialog = (expense: any) => {
  individualExpenseDialogTitle.value = '编辑个别费用';
  individualExpenseForm.value = {
    id: expense.id,
    name: expense.name,
    amount: Math.abs(expense.amount), // 使用绝对值
    remark: expense.remark || '',
    expenseSign: expense.amount >= 0 ? -1 : 1 // 正数为收入/加费用，负数为支出/减费用
  };
  individualExpenseDialogVisible.value = true;
};

// 保存个别费用
const saveIndividualExpense = async () => {
  try {
    await individualExpenseFormRef.value?.validate();
    individualExpenseSubmitting.value = true;

    // 根据expenseSign调整金额的正负
    const finalAmount = individualExpenseForm.value.amount * individualExpenseForm.value.expenseSign;

    if (individualExpenseForm.value.id) {
      // 更新个别费用
      await request.put(`/api/individual-expenses/${individualExpenseForm.value.id}`, {
        name: individualExpenseForm.value.name,
        amount: finalAmount,
        remark: individualExpenseForm.value.remark
      });
      ElMessage.success('个别费用更新成功');
    } else {
      // 创建个别费用
      await request.post('/api/individual-expenses', {
        order_id: currentOrder.value.id,
        name: individualExpenseForm.value.name,
        amount: finalAmount,
        remark: individualExpenseForm.value.remark
      });
      ElMessage.success('个别费用创建成功');
    }

    individualExpenseDialogVisible.value = false;
    // 重新获取个别费用列表
    await fetchIndividualExpenses(currentOrder.value.id);
    // 重新获取订单列表，以显示更新后的费用
    fetchOrders();
  } catch (error: any) {
    if (error.message && error.message !== 'Validation failed') {
      ElMessage.error(error.message || (individualExpenseForm.value.id ? '更新个别费用失败' : '创建个别费用失败'));
    }
  } finally {
    individualExpenseSubmitting.value = false;
  }
};

// 删除个别费用
const deleteIndividualExpense = async (id: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个个别费用吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    await request.delete(`/api/individual-expenses/${id}`);
    ElMessage.success('个别费用删除成功');
    // 重新获取个别费用列表
    await fetchIndividualExpenses(currentOrder.value.id);
    // 重新获取订单列表，以显示更新后的费用
    fetchOrders();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除个别费用失败：', error);
      ElMessage.error('删除个别费用失败');
    }
  }
};

// 处理个别费用对话框关闭
const handleIndividualExpensesDialogClose = () => {
  individualExpensesDialogVisible.value = false;
  individualExpenses.value = [];
  individualExpensesTotal.value = 0;
  currentOrder.value = {};
};

// 处理个别费用编辑对话框关闭
const handleIndividualExpenseDialogClose = () => {
  individualExpenseDialogVisible.value = false;
  individualExpenseForm.value = {
    id: 0,
    name: '',
    amount: 0,
    remark: '',
    expenseSign: 1
  };
};

// 显示年度目标修改对话框
const showAnnualTargetDialog = async () => {
  try {
    const response: any = await request.get(`/api/annual-targets/year/${currentYear.value}`);
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
    await request.put(`/api/annual-targets/year/${currentYear.value}`, {
      target_amount: annualTargetForm.value.target_amount
    });
    ElMessage.success('年度目标更新成功');
    annualTargetDialogVisible.value = false;
    // 重新获取费用汇总信息以显示新的年度目标
    fetchExpenseSummary();
  } catch (error: any) {
    ElMessage.error(error.message || '年度目标更新失败');
  }
};

// 更新订单摊分费用
const updateOrderProportionateCost = async () => {
  try {
    const response: any = await request.post('/api/orders/update-proportionate-cost', {
      target_year: currentYear.value
    });
    ElMessage.success(response.msg || '订单摊分费用更新成功');
    // 重新获取费用汇总信息
    fetchExpenseSummary();
    // 刷新订单列表，以便显示更新后的摊分费用
    fetchOrders();
  } catch (error: any) {
    ElMessage.error(error.message || '订单摊分费用更新失败');
  }
};

// 用于存储ECharts实例
let chartInstance: echarts.ECharts | null = null;

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

// 组件卸载时清理ECharts实例
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
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

/* 表格中金额显示的正负数样式 */
.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
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