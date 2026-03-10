<template>
  <div class="order-management-container">
    <CommonHeader title="订单管理" />


    <el-card shadow="hover" class="management-card">
      <!-- 操作按钮 -->
      <div style="margin-bottom: 20px;">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          新增订单
        </el-button>
        <el-button @click="showOrderLogs" v-if="isAdmin">
          <el-icon><Document /></el-icon>
          查看日志
        </el-button>
      </div>
      <!-- 内容搜索筛选区域 -->
      <el-form :model="searchForm" :inline="true" class="search-form">
          <el-form-item label="订单搜索">
            <el-input v-model="searchForm.search" placeholder="请输入订单内容..." clearable @keyup.enter="fetchOrdersByContent"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchOrdersByContent"><el-icon style="margin-right: 5px;"><Search /></el-icon>内容查询</el-button>

          <span v-if="hasSearched" class="search-result">搜索结果: {{ orders.length }} 条</span>
          <el-button v-if="hasSearched" type="secondary" @click="resetSearch">重置表单</el-button>
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
        @row-click="viewOrderById"
      :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column prop="customer_name" label="客户名称" width="150" />
        <el-table-column prop="area" label="地区" width="100" />
        <el-table-column prop="contract_amount" label="合同金额" width="120">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.contract_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="order_time" label="下单时间" width="120" />
        <el-table-column prop="ship_time" label="出货时间" width="120" />
        <el-table-column v-if="isAdmin" prop="creator_id" label="创建者ID" width="120" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button size="small" @click.stop="showEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="deleteOrder(scope.row.id)">删除</el-button>
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


    <!-- 费用汇总信息卡片 - 仅管理员可见 -->
    <el-card shadow="hover" class="expense-summary-card" style="margin-bottom: 20px;" v-if="isAdmin">
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
            <el-button size="small" @click="fetchExpenseSummary">手动加载</el-button>
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
        <!-- 显示时间节点 -->
        <div style="margin-top: 15px; padding: 10px; background-color: #f5f7fa; border-radius: 4px; border-left: 4px solid #409eff;">
          <div style="display: flex; flex-direction: column; justify-content: flex-end; align-items: flex-end; gap: 8px; font-size: 0.95em;">
            <div style="color: #606266;">
              <strong>最后费用创建时间:</strong>
              <span>{{ expenseSummary.latest_expense_create_time ? expenseSummary.latest_expense_create_time : '暂无费用记录' }}</span>
            </div>
            <div style="color: #606266;">
              <strong>最后分摊计算时间:</strong>
              <span>{{ expenseSummary.latest_calculation ? expenseSummary.latest_calculation.calculation_time : '暂未计算' }}</span>
            </div>
            <div style="margin-top: 4px;">
              <el-button type="primary" @click="updateOrderProportionateCost">更新订单摊分费用到每个订单</el-button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-summary-data">
        查看费用汇总数据，请点击"手动加载"按钮进行加载
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
            <el-form-item label="新旧" prop="is_new" required>
                <el-select v-model="orderForm.is_new" :disabled="isViewMode" placeholder="请选择新旧">
                  <el-option label="新" :value="1"></el-option>
                  <el-option label="旧" :value="0"></el-option>
                </el-select>
              </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联询盘" prop="inquiry_id" required>
              <el-select
                v-model="orderForm.inquiry_id"
                :disabled="isViewMode"
                filterable
                placeholder="请选择关联询盘"
                style="width: 100%"
                @change="handleInquiryChange"
              >
                <el-option
                  v-for="inquiry in inquiryOptions"
                  :key="inquiry.id"
                  :label="`${inquiry.company_name || '未知公司'} - ${inquiry.contact_person || '未知联系人'} (${inquiry.area || '未知地区'} ${inquiry.inquiry_date || '未知日期'})`"
                  :value="inquiry.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户地区" prop="area" required>
              <el-select
                v-model="orderForm.area"
                  filterable
                  allow-create
                  default-first-option
                  :disabled="isViewMode"
                  placeholder="请选择地区"
                  style="width: 100%">
                <el-option label="印尼" value="印尼"></el-option>
                <el-option label="俄罗斯" value="俄罗斯"></el-option>
                <el-option label="迪拜" value="迪拜"></el-option>
                <el-option label="泰国" value="泰国"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户名称" prop="customer_name">
              <el-input v-model="orderForm.customer_name" :disabled="isViewMode" placeholder="请输入客户名称"></el-input>
            </el-form-item>
          </el-col>
            <el-col :span="12">
              <el-form-item label="客户类型" prop="customer_type">
                <el-select
                  v-model="orderForm.customer_type"
                  :disabled="isViewMode"
                  filterable
                  allow-create
                  default-first-option
                  :reserve-keyword="true"
                  placeholder="经销商，终端 ..."
                  style="width: 100%"
                >
                  <el-option label="经销商" value="经销商" />
                  <el-option label="终端" value="终端" />
                  <el-option label="代理商" value="代理商" />
                </el-select>
              </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="下单时间" prop="order_time">
              <el-date-picker
                v-model="orderForm.order_time"
                :disabled="isViewMode"
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
                :disabled="isViewMode"
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
              <el-select
              v-model="orderForm.ship_country"
              filterable
              allow-create
              default-first-option
              placeholder="请选择发运国家" style="width: 100%">
                <el-option label="印尼" value="印尼"></el-option>
                <el-option label="俄罗斯" value="俄罗斯"></el-option>
                <el-option label="迪拜" value="迪拜"></el-option>
                <el-option label="泰国" value="泰国"></el-option>
              </el-select>
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
            <el-form-item label="设备名称" prop="machine_name">
              <el-input v-model="orderForm.machine_name" placeholder="请输入名称"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="机型" prop="machine_model">
              <el-select
                v-model="orderForm.machine_model"
                multiple
                filterable
                allow-create
                default-first-option
                :reserve-keyword="false"
                placeholder="请选择机型"
                style="width: 100%"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.id"
                  :label="`${machine.model} (${machine.original_model})`"
                  :value="machine.id"
                />
              </el-select>
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
              :disabled="isViewMode"
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
          <el-col :span="12" v-if="isAdmin">
            <el-form-item label="机器成本" prop="machine_cost">
              <el-input-number
              v-model="orderForm.machine_cost"
              :disabled="isViewMode"
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
        <!-- <el-row :gutter="20" v-if="isAdmin">
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
          <el-col :span="12" v-if="isAdmin">
            <el-form-item label="摊分费用" prop="proportionate_cost">
              <el-input-number
              v-model="orderForm.proportionate_cost"
              :disabled="isViewMode || true"
              :precision="2"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
            ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="其它费用" prop="individual_cost">
              <el-input-number
              v-model="orderForm.individual_cost"
              :disabled="isViewMode || true"
              :precision="2"
              style="width: 100%"
              :format="formatNumber"
              :parser="parseNumber"
              @change="calculateProfits"
            ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="isEdit && orderForm.id">
            <el-form-item label="" prop="individual_cost">
              <el-button size="small" @click.stop="showIndividualExpensesDialog(orderForm)">添加其它费用</el-button>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="付款方式" prop="pay_type">
              <el-select
                  filterable
                  allow-create
                  default-first-option
              v-model="orderForm.pay_type" :disabled="isViewMode" placeholder="请选择付款方式" style="width: 100%">
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
              <el-select
                v-model="orderForm.order_dept"
                multiple
                filterable
                allow-create
                default-first-option
                :reserve-keyword="false"
                placeholder="请选择下单部门"
                style="width: 100%"
              >
                <el-option label="立式机事业部" value="立式机事业部"></el-option>
                <el-option label="枕式机事业部" value="枕式机事业部"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12" v-if="isAdmin">
            <el-form-item label="创建者ID" prop="creator_id">
              <el-input v-model="orderForm.creator_id" placeholder="创建者ID" readonly></el-input>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <!-- 毛利和净利显示区域 -->
      <div v-if="isAdmin" style="background-color: #f5f7fa; padding: 15px; border-radius: 4px; margin-top: 20px;">

          <div>
            <span style="font-weight: bold;">毛利：</span>
            <span :class="orderForm.gross_profit >= 0 ? 'positive' : 'negative'">¥{{ formatCurrency(orderForm.gross_profit) }}</span>
          </div>
        <div style="margin-top: 10px; font-size: 14px; color: #606266;">
          <p v-if="isAdmin">合同金额（{{ formatCurrency(orderForm.contract_amount || 0) }}） - 机器成本（{{ formatCurrency(orderForm.machine_cost || 0) }}）</p>
          <p v-else>合同金额 - 成本</p>
        </div>
          <div>
            <span style="font-weight: bold;">净利：</span>
            <span :class="orderForm.net_profit >= 0 ? 'positive' : 'negative'">¥{{ formatCurrency(orderForm.net_profit) }}</span>
          </div>
        <div style="margin-top: 10px; font-size: 14px; color: #606266;">
          <p v-if="isAdmin">毛利（{{ formatCurrency(orderForm.gross_profit || 0) }}） - 摊分费用（{{ formatCurrency(orderForm.proportionate_cost || 0) }}） - 独立费用({{ formatCurrency(orderForm.individual_cost || 0) }}) - 佣金（{{ formatCurrency(orderForm.commission || 0) }}）</p>
          <p v-else>毛利 - 费用</p>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button
            v-if="!isViewMode"
            type="primary"
            @click="saveOrder"
            :loading="submitting"
          >确定</el-button>
          <el-button
            v-if="isViewMode"
            type="primary"
            @click="handleDialogClose"
          >关闭</el-button>
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
        <el-button style="margin-left: 15px;" type="primary" @click.stop="showAddIndividualExpenseDialog">添加费用</el-button>
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
            <el-button size="small" @click.stop="showEditIndividualExpenseDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="deleteIndividualExpense(scope.row.id)">删除</el-button>
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

    <!-- 引入通用日志对话框组件 -->
    <CommonLogDialog
      v-model="logDialogVisible"
      log-type="order"
      :handle-jump="handleLogJump"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus';
import request from '@/utils/request';
import { Search, Plus, Document } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';
import CommonLogDialog from '@/components/CommonLogDialog.vue';
import { getCurrentUserRole } from '@/utils/authUtils';

// 检查当前用户是否为管理员
const isAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'admin';
});

// 导入ECharts


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
  search: '', // 内容搜索字段
});

// 订单数据
const orders = ref<any[]>([]);
const loading = ref(false);

// 搜索状态
const hasSearched = ref(false);

// 对话框相关
const dialogVisible = ref(false);
const dialogTitle = ref('');
const isEdit = ref(false);
const isViewMode = ref(false); // 是否为查看模式
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

// 通用日志组件相关
const logDialogVisible = ref(false);

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
  machine_name: '',  // 默认值"包装机"
  machine_model: [] as string[],  // 修改为数组类型以支持多选，使用ID而不是型号
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
  gross_profit: 0,  // 默认0
  pay_type: 'T/T',  // 默认T/T
  commission: 0,  // 默认0
  proportionate_cost: 0,  // 摊分费用
  individual_cost: 0,  // 个别费用
  latest_ship_date: '',
  expected_delivery: '',
  order_dept: [] as string[],  // 修改为数组类型以支持多选
  check_requirement: '',
  attachment_imgs: '',
  attachment_videos: '',
  creator_id: '', // 添加creator_id字段
  inquiry_id: null // 添加关联询盘ID字段
});

// 表单校验规则
const orderRules = ref<FormRules>({
  customer_name: [
    { required: true, message: '请输入客户名称', trigger: 'blur' }
  ],
  area: [
    { required: true, message: '请输入地区信息', trigger: 'blur' }
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
    { required: false, message: '请选择机型', trigger: 'change' }
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
  ],
  inquiry_id: [
    { required: true, message: '请选择关联询盘', trigger: 'change' }
  ]
});

// 机器选项
const machineOptions = ref<{ id: number; model: string; original_model: string }[]>([]);
// 标记是否已经尝试加载过机器选项
const hasLoadedMachineOptions = ref(false);

// 询盘选项
const inquiryOptions = ref<{ id: number; company_name: string; contact_person: string; area: string; machine_type: string; inquiry_date: string }[]>([]);
// 标记是否已经尝试加载过询盘选项
const hasLoadedInquiryOptions = ref(false);

// 从本地缓存获取询盘选项
const getInquiryOptionsFromCache = (): { id: number; company_name: string; contact_person: string; area: string; machine_type: string; inquiry_date: string }[] => {
  try {
    const cachedData = localStorage.getItem('inquiryOptions');
    if (cachedData) {
      return JSON.parse(cachedData);
    }
  } catch (error) {
    console.error('读取本地询盘选项缓存失败:', error);
  }
  return [];
};

// 将询盘选项保存到本地缓存
const saveInquiryOptionsToCache = (options: { id: number; company_name: string; contact_person: string; area: string; machine_type: string; inquiry_date: string }[]) => {
  try {
    localStorage.setItem('inquiryOptions', JSON.stringify(options));
  } catch (error) {
    console.error('保存询盘选项到本地缓存失败:', error);
  }
};

// 获取机器选项
const fetchMachineOptions = async () => {
  try {
    // 直接发起API请求获取最新数据，参考VideoManagementView.vue的fetchMachines方法
    const response: any = await request.get('/api/machines_new');
    
    // 由于request.ts会自动解包data，所以response直接就是数组
    if (response && response.machines && Array.isArray(response.machines)) {
      // 直接使用API返回的机器数据
      machineOptions.value = response.machines;
    } else {
      console.warn('API返回的机器数据格式不正确:', response);
      machineOptions.value = [];
    }
  } catch (error) {
    console.error('获取机器选项失败:', error);
    ElMessage.error('获取机器选项失败');
    machineOptions.value = [];
  }
};

// 处理询盘选择变化
const handleInquiryChange = (inquiryId: number) => {
  if (!inquiryId) return;

  // 找到对应的询盘对象
  const selectedInquiry = inquiryOptions.value.find(inquiry => inquiry.id === inquiryId);
  if (selectedInquiry) {
    // 自动填充询盘信息到订单表单（仅当表单字段为空时）
    if (!orderForm.value.area) {
      orderForm.value.area = selectedInquiry.area;
    }
    if (!orderForm.value.ship_country) {
      orderForm.value.ship_country = selectedInquiry.area;
    }
    if (!orderForm.value.machine_name) {
      if (selectedInquiry.machine_type) {
        orderForm.value.machine_name = selectedInquiry.machine_type;
      }
    }
    if (!orderForm.value.customer_name) {
      orderForm.value.customer_name = `${selectedInquiry.company_name} - ${selectedInquiry.contact_person}`;
    }
  }
};

// 获取询盘选项
const fetchInquiryOptions = async () => {
  try {
    // 首先尝试从本地缓存获取数据
    const cachedOptions = getInquiryOptionsFromCache();
    if (cachedOptions.length > 0) {
      // 如果有缓存数据，先使用缓存数据
      inquiryOptions.value = cachedOptions;
    }

    // 然后发起API请求获取最新数据，排除已关联订单的询盘
    const response: any = await request.get('/api/inquiries?include_associated=false');

    // 由于request.ts会自动解包data，所以response直接就是数据对象
    // 后端返回格式为 { list: [...], total: ..., page: ..., size: ... }
        if (response && response.list && Array.isArray(response.list)) {
          const newInquiryOptions = response.list.map((inquiry: any) => {
            if (typeof inquiry === 'object' && inquiry !== null) {
              return {
                id: inquiry.id,
                company_name: inquiry.company_name || '',
                contact_person: inquiry.contact_person || '',
                area: inquiry.area || '',
                machine_type: inquiry.machine_type || '',  // 添加machine_type字段
                inquiry_date: inquiry.inquiry_date || ''
              };
            } else {
              // 如果不是对象，返回空选项
              return { id: 0, company_name: '', contact_person: '', area: '', machine_type: '', inquiry_date: ''};
            }
          }).filter(item => item.id !== 0); // 过滤掉无效的询盘
      // 更新本地缓存和当前值
      inquiryOptions.value = newInquiryOptions;
      saveInquiryOptionsToCache(newInquiryOptions);
    } else {
      console.warn('API返回的询盘数据格式不正确:', response);
      // 如果API返回的数据格式不正确，但有缓存数据，则使用缓存数据
      if (cachedOptions.length > 0) {
        inquiryOptions.value = cachedOptions;
      } else {
        inquiryOptions.value = [];
      }
    }
  } catch (error) {
    console.error('获取询盘选项失败:', error);
    // 获取失败时，尝试使用缓存数据
    const cachedOptions = getInquiryOptionsFromCache();
    if (cachedOptions.length > 0) {
      inquiryOptions.value = cachedOptions;
      ElMessage.warning('获取最新询盘选项失败，已使用缓存数据');
    } else {
      ElMessage.error('获取询盘选项失败');
      inquiryOptions.value = [];
    }
  }
};// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    // 根据用户权限决定请求的字段
    let fields = 'id,customer_name,area,contract_amount,order_time,ship_time';
    if (isAdmin.value) {
      // 管理员可以查看creator_id字段
      fields += ',creator_id';
    }

    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      fields: fields // 显式请求ID和所需字段
    };

    const response: any = await request.get('/api/orders', { params });

    // 由于request.ts会自动解包data，所以response直接就是订单数据
    // 标准响应结构：{ list: [...], total: ..., page: ..., size: ... }
    const ordersData = response || { list: [], total: 0, page: 1, size: 10 };

    // 处理返回的订单数据
    const processedOrders = (ordersData.list || []);
    orders.value = processedOrders;
    pagination.value.total = ordersData.total || 0;
    pagination.value.page = ordersData.page || 1;
    pagination.value.size = ordersData.size || 10;
  } catch (error) {
    console.error('Error fetching orders:', error);
    ElMessage.error('获取订单列表失败');
  } finally {
    loading.value = false;
  }
};

// 按内容搜索订单（使用search_field）
const fetchOrdersByContent = async () => {
  loading.value = true;
  try {
    // 根据用户权限决定请求的字段
    let fields = 'id,customer_name,area,contract_amount,order_time,ship_time';
    if (isAdmin.value) {
      // 管理员可以查看creator_id字段
      fields += ',creator_id';
    }

    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      search: searchForm.value.search || undefined, // 使用search参数进行搜索
      fields: fields // 显式请求ID和所需字段
    };

    const response: any = await request.get('/api/orders', { params });

    // 由于request.ts会自动解包data，所以response直接就是订单数据
    // 标准响应结构：{ list: [...], total: ..., page: ..., size: ... }
    const ordersData = response || { list: [], total: 0, page: 1, size: 10 };

    // 处理返回的订单数据
    const processedOrders = (ordersData.list || []);
    orders.value = processedOrders;
    pagination.value.total = ordersData.total || 0;
    pagination.value.page = ordersData.page || 1;
    pagination.value.size = ordersData.size || 10;
    hasSearched.value = true; // 设置已搜索状态
  } catch (error) {
    console.error('Error fetching orders by content:', error);
    ElMessage.error('按内容搜索订单失败');
  } finally {
    loading.value = false;
  }
};



// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    search: '',
  };
  pagination.value.page = 1;
  hasSearched.value = false; // 重置搜索状态
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
const showAddDialog = async () => {
  dialogTitle.value = '新增订单';
  isEdit.value = false;
  isViewMode.value = false; // 新增模式不是查看模式
  resetForm();

  // 确保机器选项数据已加载
  if (!hasLoadedMachineOptions.value || machineOptions.value.length === 0) {
    // 如果还没有尝试加载过机器选项，或机器选项为空，先加载数据
    await fetchMachineOptions();
    hasLoadedMachineOptions.value = true;
  }

  // 确保询盘选项数据已加载
  if (!hasLoadedInquiryOptions.value || inquiryOptions.value.length === 0) {
    // 如果还没有尝试加载过询盘选项，或询盘选项为空，先加载数据
    await fetchInquiryOptions();
    hasLoadedInquiryOptions.value = true;
  }

  dialogVisible.value = true;
};

// 显示编辑对话框
const showEditDialog = async (order: any) => {
  try {
    // 获取完整的订单数据，而不是只使用表格中显示的部分数据
    const response: any = await request.get(`/api/orders/${order.id}`);

    // 由于request.ts会自动解包data，所以response直接就是订单数据
    const fullOrderData = response || {};

    dialogTitle.value = '编辑订单';
    isEdit.value = true;
    isViewMode.value = false; // 确保编辑模式不是查看模式

    // 确保机器选项数据已加载
    if (!hasLoadedMachineOptions.value || machineOptions.value.length === 0) {
      // 如果还没有尝试加载过机器选项，或机器选项为空，先加载数据
      await fetchMachineOptions();
      hasLoadedMachineOptions.value = true;
    }

    // 确保询盘选项数据已加载
    // if (!hasLoadedInquiryOptions.value || inquiryOptions.value.length === 0) {
    //   // 如果还没有尝试加载过询盘选项，或询盘选项为空，先加载数据
    //   await fetchInquiryOptions();
    //   hasLoadedInquiryOptions.value = true;
    // }

    // 如果返回的订单数据中包含询盘信息，需要将该询盘添加到选项列表中
    // （这样可以避免重复请求询盘数据，直接使用已有的询盘信息）
    if (fullOrderData.inquiry && fullOrderData.inquiry.id) {
      // 检查该询盘是否已存在于选项列表中
      const existingInquiryIndex = inquiryOptions.value.findIndex(inquiry => inquiry.id === fullOrderData.inquiry.id);
      if (existingInquiryIndex === -1) {
        // 如果不存在，则添加到选项列表中
        const inquiryOption = {
          id: fullOrderData.inquiry.id,
          company_name: fullOrderData.inquiry.company_name || '',
          contact_person: fullOrderData.inquiry.contact_person || '',
          area: fullOrderData.inquiry.area || '',
          machine_type: fullOrderData.inquiry.machine_type || '',
          inquiry_date: fullOrderData.inquiry.inquiry_date || ''
        };
        inquiryOptions.value.unshift(inquiryOption); // 添加到列表开头
      }
    } else if (fullOrderData.inquiry_id && !inquiryOptions.value.some(inquiry => inquiry.id === fullOrderData.inquiry_id)) {
      // 作为备选方案，如果订单数据中没有包含询盘对象，但有询盘ID，则请求该询盘信息
      try {
        // 获取特定询盘信息
        const inquiryResponse: any = await request.get(`/api/inquiries/${fullOrderData.inquiry_id}`);
        if (inquiryResponse && inquiryResponse.id) {
          // 添加到询盘选项列表
          const inquiryOption = {
            id: inquiryResponse.id,
            company_name: inquiryResponse.company_name || '',
            contact_person: inquiryResponse.contact_person || '',
            area: inquiryResponse.area || '',
            machine_type: inquiryResponse.machine_type || '',
            inquiry_date: inquiryResponse.inquiry_date || ''
          };
          inquiryOptions.value.unshift(inquiryOption); // 添加到列表开头
        }
      } catch (error) {
        console.error('获取关联询盘信息失败:', error);
        // 即使获取失败也不影响编辑订单功能
      }
    }

    // 处理机器型号到ID的转换
    let processedMachineModel: string[] = [];
    if (fullOrderData.machine_model) {
      if (Array.isArray(fullOrderData.machine_model)) {
        // 如果是ID数组，直接使用
        if (fullOrderData.machine_model.length > 0 && typeof fullOrderData.machine_model[0] === 'number') {
          processedMachineModel = fullOrderData.machine_model.map(id => id.toString());
        } else {
          // 如果是型号数组，需要转换为ID
          processedMachineModel = fullOrderData.machine_model.map(model => {
            const machine = machineOptions.value.find(m => m.model === model || m.original_model === model);
            return machine ? machine.id.toString() : '';
          }).filter(id => id !== '');
        }
      } else {
        // 如果是单个值，判断是ID还是型号
        if (typeof fullOrderData.machine_model === 'number') {
          processedMachineModel = [fullOrderData.machine_model.toString()];
        } else {
          const machine = machineOptions.value.find(m => m.model === fullOrderData.machine_model || m.original_model === fullOrderData.machine_model);
          if (machine) {
            processedMachineModel = [machine.id.toString()];
          }
        }
      }
    }

    // 在所有选项都加载完成后，再设置表单数据
    // 深拷贝完整订单数据到表单，确保所有字段都被正确复制
    orderForm.value = {
      id: fullOrderData.id || 0,
      is_new: fullOrderData.is_new || 1,
      area: fullOrderData.area || '',
      customer_name: fullOrderData.customer_name || '',
      customer_type: fullOrderData.customer_type || '',
      order_time: fullOrderData.order_time || '',
      ship_time: fullOrderData.ship_time || '',
      ship_country: fullOrderData.ship_country || '',
      contract_no: fullOrderData.contract_no || '',
      order_no: fullOrderData.order_no || '',
      machine_no: fullOrderData.machine_no || '',
      machine_name: fullOrderData.machine_name || '包装机',
      machine_model: processedMachineModel as string[],  // 类型断言确保类型匹配
      machine_count: fullOrderData.machine_count || 1,
      unit: fullOrderData.unit || 'set',
      contract_amount: fullOrderData.contract_amount || 0,
      deposit: fullOrderData.deposit || 0,
      balance: fullOrderData.balance || 0,
      tax_rate: fullOrderData.tax_rate || 13.0,
      tax_refund_amount: fullOrderData.tax_refund_amount || 0,
      currency_amount: fullOrderData.currency_amount || 0,
      payment_received: fullOrderData.payment_received || 0,
      machine_cost: fullOrderData.machine_cost || 0,
      net_profit: fullOrderData.net_profit || 0,
      gross_profit: fullOrderData.gross_profit || 0,
      pay_type: fullOrderData.pay_type || 'T/T',
      commission: fullOrderData.commission || 0,
      proportionate_cost: fullOrderData.proportionate_cost || 0,
      individual_cost: fullOrderData.individual_cost || 0,
      latest_ship_date: fullOrderData.latest_ship_date || '',
      expected_delivery: fullOrderData.expected_delivery || '',
      order_dept: Array.isArray(fullOrderData.order_dept) ? fullOrderData.order_dept : fullOrderData.order_dept ? [fullOrderData.order_dept] : [],
      check_requirement: fullOrderData.check_requirement || '',
      attachment_imgs: fullOrderData.attachment_imgs || '',
      attachment_videos: fullOrderData.attachment_videos || '',
      creator_id: fullOrderData.creator_id || '', // 添加creator_id字段
      inquiry_id: fullOrderData.inquiry_id || null // 添加关联询盘ID
    };
    // 编辑时自动计算利润
    setTimeout(() => {
      calculateProfits();
    }, 100); // 延迟执行以确保数据已更新

    dialogVisible.value = true;
  } catch (error) {
    console.error('加载订单详情失败:', error);
    ElMessage.error('加载订单详情失败');
  }
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
    machine_name: '',  // 默认值"包装机"
    machine_model: [],  // 修改为数组类型以支持多选，使用ID而不是型号
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
    gross_profit: 0,  // 默认0，将在calculateProfits中更新
    pay_type: 'T/T',  // 默认T/T
    commission: 0,  // 默认0
    proportionate_cost: 0,  // 摊分费用
    individual_cost: 0,  // 个别费用
    latest_ship_date: '',
    expected_delivery: '',
    order_dept: [],  // 修改为数组类型以支持多选
    check_requirement: '',
    attachment_imgs: '',
    attachment_videos: '',
    creator_id: '',
    inquiry_id: null // 添加关联询盘ID
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

    // 处理多选字段，将数组转换为逗号分隔的字符串
    let processedMachineModel: string;
    const machineModelValue = updatedOrderForm.machine_model;
    
    // 由于orderForm.machine_model是string[]类型，我们需要处理它
    if (Array.isArray(machineModelValue)) {
      // 如果是ID数组，转换为逗号分隔的字符串
      processedMachineModel = machineModelValue.join(',');
    } else if (typeof machineModelValue === 'string') {
      processedMachineModel = machineModelValue;
    } else {
      // 处理其他情况，使用类型断言
      processedMachineModel = String(machineModelValue) || '';
    }

    let processedOrderDept: string;
    if (Array.isArray(updatedOrderForm.order_dept)) {
      processedOrderDept = updatedOrderForm.order_dept.join(',');
    } else if (typeof updatedOrderForm.order_dept === 'string') {
      processedOrderDept = updatedOrderForm.order_dept;
    } else {
      processedOrderDept = '';
    }

    // 最终发送到后端的数据
    const finalOrderData = {
      ...updatedOrderForm,
      machine_model: processedMachineModel,
      order_dept: processedOrderDept
    };

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
      await request.put(`/api/orders/${updatedOrderForm.id}`, finalOrderData);
      ElMessage.success('订单更新成功');
    } else {
      // 创建订单
      await request.post('/api/orders', finalOrderData);
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

// 查看订单详情
const viewOrder = async (id: number) => {
  try {
    const response: any = await request.get(`/api/orders/${id}`);

    // 由于request.ts会自动解包data，所以response直接就是订单数据
    const orderData = response || {};

    // 如果返回的订单数据中包含询盘信息，需要将该询盘添加到选项列表中
    if (orderData.inquiry && orderData.inquiry.id) {
      // 检查该询盘是否已存在于选项列表中
      const existingInquiryIndex = inquiryOptions.value.findIndex(inquiry => inquiry.id === orderData.inquiry.id);
      if (existingInquiryIndex === -1) {
        // 如果不存在，则添加到选项列表中
        const inquiryOption = {
          id: orderData.inquiry.id,
          company_name: orderData.inquiry.company_name || '',
          contact_person: orderData.inquiry.contact_person || '',
          area: orderData.inquiry.area || '',
          machine_type: orderData.inquiry.machine_type || '',
          inquiry_date: orderData.inquiry.inquiry_date || ''
        };
        inquiryOptions.value.unshift(inquiryOption); // 添加到列表开头
      }
    }

    // 用获取到的数据填充表单
    orderForm.value = {
      ...orderData,
      creator_id: orderData.creator_id || '', // 确保creator_id字段被正确设置
      inquiry_id: orderData.inquiry_id || null // 添加关联询盘ID
    };
    dialogTitle.value = '查看订单详情';
    isEdit.value = true; // 设置为编辑模式，但不显示保存按钮或禁用编辑功能
    isViewMode.value = true; // 设置为查看模式
    dialogVisible.value = true;
  } catch (error) {
    console.error('加载订单详情失败:', error);
    ElMessage.error('加载订单详情失败');
  }
};

// 通过行点击查看详情
const viewOrderById = async (row: any) => {
  try {
    const response: any = await request.get(`/api/orders/${row.id}`);

    // 由于request.ts会自动解包data，所以response直接就是订单数据
    const orderData = response || {};

    // 如果返回的订单数据中包含询盘信息，需要将该询盘添加到选项列表中
    if (orderData.inquiry && orderData.inquiry.id) {
      // 检查该询盘是否已存在于选项列表中
      const existingInquiryIndex = inquiryOptions.value.findIndex(inquiry => inquiry.id === orderData.inquiry.id);
      if (existingInquiryIndex === -1) {
        // 如果不存在，则添加到选项列表中
        const inquiryOption = {
          id: orderData.inquiry.id,
          company_name: orderData.inquiry.company_name || '',
          contact_person: orderData.inquiry.contact_person || '',
          area: orderData.inquiry.area || '',
          machine_type: orderData.inquiry.machine_type || '',
          inquiry_date: orderData.inquiry.inquiry_date || ''
        };
        inquiryOptions.value.unshift(inquiryOption); // 添加到列表开头
      }
    }

    // 用获取到的完整数据填充表单
    orderForm.value = {
      ...orderData,
      creator_id: orderData.creator_id || '', // 确保creator_id字段被正确设置
      inquiry_id: orderData.inquiry_id || null // 添加关联询盘ID
    };
    dialogTitle.value = '查看订单详情';
    isEdit.value = true; // 设置为编辑模式，但不显示保存按钮或禁用编辑功能
    isViewMode.value = true; // 设置为查看模式
    dialogVisible.value = true;
  } catch (error) {
    console.error('加载订单详情失败:', error);
    ElMessage.error('加载订单详情失败');
  }
};

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

// 组件挂载时获取数据
onMounted(async () => {
  // 在组件挂载时获取数据
  await fetchMachineOptions(); // 获取并缓存机器选项
  hasLoadedMachineOptions.value = true; // 标记已经加载过机器选项
  // 不在页面加载时获取询盘选项，只在需要时获取
  fetchOrders();
  if(!isAdmin){fetchExpenseSummary()}; // 获取费用汇总信息
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
const generatePieChart = async () => {
  if (!expenseSummary.value) return;

  // 获取DOM元素
  const chartDom = document.getElementById('expense-pie-chart');
  if (!chartDom) return;

  // 动态导入ECharts
  const echarts = await import('echarts');

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
let chartInstance: any = null;

// 添加专门的日志跳转处理函数
const handleLogJump = (id: number) => {
  viewOrder(id);
};

// 显示日志对话框
const showOrderLogs = () => {
  if (!isAdmin.value) {
    ElMessage.error('您没有权限查看日志');
    return;
  }
  // 先重置日志组件的状态，再显示对话框
  logDialogVisible.value = false;
  // 使用nextTick确保状态更新后再显示
  setTimeout(() => {
    logDialogVisible.value = true;
  }, 100);
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

.search-result{
  font-size: 14px;
  color: #606266;
  margin-left: 30px;
  margin-right:15px;
}

.create-order-btn {
  background-color: green;
  color: white;
  margin-left: 30px;
}
</style>