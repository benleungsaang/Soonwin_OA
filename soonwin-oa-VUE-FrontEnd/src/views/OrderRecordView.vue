<template>
  <div class="order-record-container">
    <CommonHeader title="订单记录" />

    <el-card shadow="hover" class="management-card">
      <!-- 操作按钮 -->
      <div style="margin-bottom: 20px">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          新增订单记录
        </el-button>
      </div>

      <!-- 订单记录表格 -->
      <el-table
        :data="orderRecords"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        :row-style="{ cursor: 'pointer' }"
        :row-class-name="getRowClassName"
        @row-click="showDetailModal"
      >
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column prop="order_remark_name" label="订单备注名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="order_amount_cny" label="订单金额" width="150">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.order_amount_cny) }} ({{ scope.row.currency }})
          </template>
        </el-table-column>
        <el-table-column prop="is_completed" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_completed ? 'success' : 'info'" size="small">
              {{ scope.row.is_completed ? '已完成' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_id" label="订单创建人" width="120" />
        <el-table-column prop="order_date" label="订单创建日期" width="120" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" @click.stop="editOrderRecord(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="deleteOrderRecord(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        class="pagination"
      />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
      :before-close="handleDialogClose"
    >
      <el-form :model="orderRecordForm" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="订单号" prop="order_no">
          <el-input v-model="orderRecordForm.order_no" placeholder="请输入订单号" />
        </el-form-item>
        <el-form-item label="订单备注名" prop="order_remark_name">
          <el-input v-model="orderRecordForm.order_remark_name" placeholder="请输入订单备注名" />
        </el-form-item>
        <el-form-item label="订单金额" prop="order_amount">
          <el-input-number v-model="orderRecordForm.order_amount" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="币种">
          <el-select v-model="orderRecordForm.currency" placeholder="请选择币种" filterable allow-create default-first-option style="width: 100%" @change="onOrderCurrencyChange">
            <el-option label="人民币 (CNY)" value="CNY" />
            <el-option label="美元 (USD)" value="USD" />
            <el-option label="欧元 (EUR)" value="EUR" />
            <el-option label="日元 (JPY)" value="JPY" />
          </el-select>
        </el-form-item>
        <el-form-item label="汇率">
          <el-input-number v-model="orderRecordForm.exchange_rate" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="订单日期" prop="order_date">
          <el-date-picker
            v-model="orderRecordForm.order_date"
            type="date"
            placeholder="选择订单日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="是否完成">
          <el-switch v-model="orderRecordForm.is_completed" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button type="primary" @click="saveOrderRecord" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 订单详情模态框 -->
    <el-dialog
      v-model="detailModalVisible"
      width="1000px"
      :before-close="handleDetailModalClose"
    >
      <template #header>
        <div class="detail-dialog-header" v-if="currentRecord">
          <span>订单详情</span>
          <el-dropdown trigger="click" @command="handleCustomerDropdownCommand" style="margin-left: 20px">
            <el-button type="success" size="small">
              登记客户信息
              <el-icon style="margin-left: 5px;"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="create">创建新客户</el-dropdown-item>
                <el-dropdown-item command="bind">绑定到现有客户</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-switch
            v-model="currentRecord.is_completed"
            active-text="已完成"
            inactive-text="进行中"
            :loading="updatingStatus"
            @change="handleStatusChange"
            style="margin-left: 20px"
          />
        </div>
        <span v-else>订单详情</span>
      </template>
      <!-- 汇总信息头部 -->
      <div class="summary-header" v-if="currentRecord">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">订单号</div>
              <div class="summary-value">{{ currentRecord.order_no }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">订单备注名</div>
              <div class="summary-value">{{ currentRecord.order_remark_name || '-' }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">订单金额(CNY)</div>
              <div class="summary-value">¥{{ formatCurrency(currentRecord.order_amount_cny) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">订单日期</div>
              <div class="summary-value">{{ currentRecord.order_date }}</div>
            </div>
          </el-col>
          <!-- <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">创建人</div>
              <div class="summary-value">{{ currentRecord.creator_id || '-' }}</div>
            </div>
          </el-col> -->
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="6">
            <div class="summary-item highlight">
              <div class="summary-label">当前总收入</div>
              <div class="summary-value income">¥{{ formatCurrency(currentRecord.total_income) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item highlight">
              <div class="summary-label">当前总支出</div>
              <div class="summary-value expense">¥{{ formatCurrency(currentRecord.total_expense) }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item highlight">
              <div class="summary-label">订单预期利润</div>
              <div class="summary-value" :class="currentRecord.order_profit >= 0 ? 'income' : 'expense'">
                ¥{{ formatCurrency(currentRecord.order_profit) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item highlight">
              <div class="summary-label">当前实际利润</div>
              <div class="summary-value" :class="currentRecord.actual_profit >= 0 ? 'income' : 'expense'">
                ¥{{ formatCurrency(currentRecord.actual_profit) }}
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 左右分列：收入和支出 -->
      <el-row :gutter="20" style="margin-top: 20px">
        <!-- 左侧：收入记录 -->
        <el-col :span="12">
          <el-card shadow="hover" class="record-card income-card">
            <template #header>
              <div class="card-header">
                <span>收入记录</span>
                <el-button size="small" type="primary" @click="showAddIncomeDialog">添加收入</el-button>
              </div>
            </template>
            <el-table :data="incomes" style="width: 100%" stripe border size="small"
              :row-style="{ cursor: 'pointer' }" @row-click="(row) => editIncome(row)">
              <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip>
                <template #default="scope">
                  <span :title="scope.row.remark">{{ scope.row.remark || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="record_date" label="日期" width="100" />
              <el-table-column label="金额(CNY)" width="100">
                <template #default="scope">
                  <span class="income-text">
                    ¥{{ formatCurrency(scope.row.amount_cny) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="图片" width="70">
                <template #default="scope">
                  <el-image
                    v-if="scope.row.first_screenshot"
                    :src="getImageUrl(scope.row.first_screenshot)"
                    style="width: 40px; height: 40px; cursor: pointer"
                    :preview-src-list="scope.row.screenshots?.map((s: string) => getImageUrl(s))"
                    fit="cover"
                    preview-teleported
                    close-on-press-esc
                    hide-on-click-modal
                    @click.stop
                  />
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60" fixed="right">
                <template #default="scope">
                  <el-dropdown trigger="click" @command="(cmd: string) => handleIncomeCommand(cmd, scope.row)">
                    <el-button size="small" type="primary" link @click.stop>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="edit">修改</el-dropdown-item>
                        <el-dropdown-item command="delete" style="color: #f56c6c;">删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="incomes.length === 0" description="暂无收入记录" :image-size="60" />
          </el-card>
        </el-col>

        <!-- 右侧：支出记录 -->
        <el-col :span="12">
          <el-card shadow="hover" class="record-card expense-card">
            <template #header>
              <div class="card-header">
                <span>支出记录</span>
                <el-button size="small" type="primary" @click="showAddExpenseDialog">添加支出</el-button>
              </div>
            </template>
            <el-table :data="expenses" style="width: 100%" stripe border size="small"
              :row-style="{ cursor: 'pointer' }" @row-click="(row) => editExpense(row)">
              <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip>
                <template #default="scope">
                  <span :title="scope.row.remark">{{ scope.row.remark || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="record_date" label="日期" width="100" />
              <el-table-column label="金额(CNY)" width="100">
                <template #default="scope">
                  <span class="expense-text">
                    ¥{{ formatCurrency(scope.row.amount_cny) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="图片" width="70">
                <template #default="scope">
                  <el-image
                    v-if="scope.row.first_screenshot"
                    :src="getImageUrl(scope.row.first_screenshot)"
                    style="width: 40px; height: 40px; cursor: pointer"
                    :preview-src-list="scope.row.screenshots?.map((s: string) => getImageUrl(s))"
                    fit="cover"
                    preview-teleported
                    close-on-press-esc
                    hide-on-click-modal
                    @click.stop
                  />
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60" fixed="right">
                <template #default="scope">
                  <el-dropdown trigger="click" @command="(cmd: string) => handleExpenseCommand(cmd, scope.row)">
                    <el-button size="small" type="primary" link @click.stop>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="edit">修改</el-dropdown-item>
                        <el-dropdown-item command="delete" style="color: #f56c6c;">删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="expenses.length === 0" description="暂无支出记录" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDetailModalClose">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 收入/支出编辑对话框 -->
    <el-dialog
      :title="recordDialogTitle"
      v-model="recordDialogVisible"
      width="500px"
    >
      <el-form :model="recordForm" ref="recordFormRef" label-width="100px">
        <el-form-item label="备注信息">
          <el-input v-model="recordForm.remark" placeholder="如：订金收入、买XX机器支出" />
        </el-form-item>
        <el-form-item label="记录日期">
          <el-date-picker
            v-model="recordForm.record_date"
            type="date"
            placeholder="选择记录日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number v-model="recordForm.amount" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="币种">
          <el-select
            v-model="recordForm.currency"
            placeholder="请选择或输入币种"
            filterable
            allow-create
            default-first-option
            style="width: 100%"
            @change="onRecordCurrencyChange"
          >
            <el-option label="人民币 (CNY)" value="CNY" />
            <el-option label="美元 (USD)" value="USD" />
            <el-option label="欧元 (EUR)" value="EUR" />
            <el-option label="日元 (JPY)" value="JPY" />
          </el-select>
        </el-form-item>
        <el-form-item label="汇率">
          <el-input-number
            v-model="recordForm.exchange_rate"
            :precision="4"
            :min="0"
            style="width: 100%"
            @change="onExchangeRateChange"
          />
        </el-form-item>
        <el-form-item label="佐证截图">
          <div class="screenshot-upload-wrapper">
            <ImageUploadPreview
              ref="imageUploadRef"
              :upload-path="uploadPath"
              :upload-immediately="false"
              :order-id="currentRecord?.id"
              :record-type="recordForm.type"
              :remark="recordForm.remark"
              @upload-success="handleUploadSuccess"
              @upload-failure="handleUploadFailure"
            />
            <el-input
              style="margin-top: 10px; width: 100%"
              @paste="handleInputPaste"
              placeholder="粘贴图片(Ctrl+V)"
            />
            <!-- 已保存的截图列表（编辑时显示多张） -->
            <div v-if="recordForm.screenshots && recordForm.screenshots.length > 0" class="existing-screenshots">
              <div v-for="(screenshot, index) in recordForm.screenshots" :key="index" class="screenshot-item">
                <el-image
                  :src="getImageUrl(screenshot)"
                  style="width: 80px; height: 80px"
                  fit="cover"
                  :preview-src-list="recordForm.screenshots.map((s: string) => getImageUrl(s))"
                  :initial-index="index"
                  preview-teleported
                  close-on-press-esc
                  hide-on-click-modal
                />
                <el-button size="small" type="danger" class="delete-screenshot-btn" @click="removeScreenshot(index)">删除</el-button>
              </div>
            </div>
            <!-- 待上传的本地预览文件 -->
            <div v-if="localPreviewFiles.length > 0" class="local-preview-files">
              <div class="local-preview-title">待上传文件 ({{ localPreviewFiles.length }}张)</div>
              <div class="local-preview-list">
                <div v-for="(preview, index) in localPreviewFiles" :key="index" class="screenshot-item local-preview-item">
                  <el-image
                    :src="preview.url"
                    style="width: 80px; height: 80px"
                    fit="cover"
                    :preview-src-list="localPreviewFiles.map((p: { url: string }) => p.url)"
                    :initial-index="index"
                    preview-teleported
                    close-on-press-esc
                    hide-on-click-modal
                  />
                  <el-button size="small" type="danger" class="delete-screenshot-btn" @click="removeLocalPreviewByIndex(index)">删除</el-button>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleRecordDialogClose">取消</el-button>
          <el-button type="primary" @click="saveRecord" :loading="recordSubmitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 创建客户对话框 -->
    <el-dialog
      title="创建客户"
      v-model="createCustomerDialogVisible"
      width="500px"
    >
      <el-form :model="createCustomerForm" label-width="100px">
        <el-form-item label="公司名称">
          <el-input v-model="createCustomerForm.company_name" placeholder="请输入公司名称" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="createCustomerForm.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="createCustomerForm.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="地区">
          <el-input v-model="createCustomerForm.area" placeholder="请输入地区" />
        </el-form-item>
        <el-form-item label="客户类型">
          <el-select v-model="createCustomerForm.customer_type" placeholder="请选择客户类型" style="width: 100%">
            <el-option label="经销商" value="经销商" />
            <el-option label="终端" value="终端" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createCustomerForm.remark" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createCustomerDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreateCustomer" :loading="createCustomerSubmitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 绑定客户对话框 -->
    <el-dialog
      title="绑定客户"
      v-model="bindCustomerDialogVisible"
      width="700px"
    >
      <p style="color: #909399; margin-bottom: 10px;">选择一个客户进行绑定</p>
      <el-table
        :data="bindableCustomers"
        v-loading="bindableCustomersLoading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        @row-click="handleBindableCustomerRowClick"
        :row-class-name="getBindableCustomerRowClassName"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column width="60" label="选择">
          <template #default="scope">
            <el-radio v-model="selectedBindableCustomerId" :label="scope.row.id" @click.stop>&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="company_name" label="公司名" />
        <el-table-column prop="contact_person" label="联系人" />
        <el-table-column prop="phone" label="电话" />
        <el-table-column prop="area" label="地区" />
      </el-table>
      <el-pagination
        v-model:current-page="bindableCustomersPage"
        :page-size="bindableCustomersSize"
        :total="bindableCustomersTotal"
        layout="prev, pager, next"
        @current-change="loadBindableCustomers"
        style="margin-top: 10px; justify-content: center"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="bindCustomerDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmBindCustomer" :disabled="!selectedBindableCustomerId">确认绑定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, MoreFilled, User, ArrowDown } from '@element-plus/icons-vue'
import request, { multipartRequest } from '@/utils/request'
import CommonHeader from '@/components/CommonHeader.vue'
import ImageUploadPreview from '@/components/ImageUploadPreview.vue'
import { createCustomerFromOrderRecord, bindOrderRecord } from '@/api/customer'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 路由
const router = useRouter()

// 跳转到客户详情
const goToCustomer = (customerId: number) => {
  router.push(`/customer-management`)
}

// ============ 数据列表 ============
const orderRecords = ref<any[]>([])
const loading = ref(false)
const pagination = ref({ page: 1, size: 10, total: 0 })

// ============ 详情相关 ============
const detailModalVisible = ref(false)
const currentRecord = ref<any>(null)
const incomes = ref<any[]>([])
const expenses = ref<any[]>([])
const updatingStatus = ref(false)

// ============ 创建客户 ============
const createCustomerDialogVisible = ref(false)
const createCustomerForm = ref({
  company_name: '',
  contact_person: '',
  phone: '',
  area: '',
  customer_type: '',
  remark: ''
})
const createCustomerSubmitting = ref(false)
const currentRecordForCustomer = ref<any>(null)

// 绑定客户相关
const bindCustomerDialogVisible = ref(false)
const bindableCustomers = ref<any[]>([])
const bindableCustomersLoading = ref(false)
const bindableCustomersPage = ref(1)
const bindableCustomersSize = ref(10)
const bindableCustomersTotal = ref(0)
const selectedBindableCustomerId = ref<number | null>(null)
const selectedBindableCustomer = ref<any>(null)

const createCustomer = async (row: any) => {
  createCustomerForm.value = {
    company_name: row.order_remark_name || row.order_no,
    contact_person: '',
    phone: '',
    area: '',
    customer_type: '',
    remark: ''
  }
  createCustomerDialogVisible.value = true
}

const submitCreateCustomer = async () => {
  try {
    createCustomerSubmitting.value = true
    const result = await createCustomerFromOrderRecord(currentRecordForCustomer.value?.id, createCustomerForm.value)
    ElMessage.success('创建客户成功')
    createCustomerDialogVisible.value = false
    fetchOrderRecords()
    // 跳转到客户信息页面
    if (result && result.id) {
      router.push(`/customer-management`)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '创建客户失败')
  } finally {
    createCustomerSubmitting.value = false
  }
}

// 绑定客户相关
const showBindCustomerDialog = async () => {
  // 设置当前订单记录用于后续创建客户时关联
  currentRecordForCustomer.value = currentRecord.value
  // 先创建客户表单填充当前订单信息
  createCustomerForm.value = {
    company_name: currentRecord.value?.order_remark_name || currentRecord.value?.order_no || '',
    contact_person: '',
    phone: '',
    area: '',
    customer_type: '',
    remark: ''
  }
  createCustomerDialogVisible.value = true
}

const showBindToExistingCustomerDialog = async () => {
  selectedBindableCustomerId.value = null
  selectedBindableCustomer.value = null
  bindCustomerDialogVisible.value = true
  await loadBindableCustomers()
}

const handleCustomerDropdownCommand = (command: string) => {
  if (command === 'create') {
    showBindCustomerDialog()
  } else if (command === 'bind') {
    showBindToExistingCustomerDialog()
  }
}

const loadBindableCustomers = async () => {
  try {
    bindableCustomersLoading.value = true
    const response: any = await request.get('/api/customers', {
      params: { page: bindableCustomersPage.value, size: bindableCustomersSize.value }
    })
    // 过滤掉当前订单记录已关联的客户
    bindableCustomers.value = (response.list || []).filter((item: any) =>
      item.id !== currentRecord.value?.customer_id
    )
    bindableCustomersTotal.value = response.total || 0
  } catch (error) {
    console.error('获取可绑定客户列表失败:', error)
  } finally {
    bindableCustomersLoading.value = false
  }
}

const handleBindableCustomerRowClick = (row: any) => {
  selectedBindableCustomerId.value = row.id
  selectedBindableCustomer.value = row
}

const getBindableCustomerRowClassName = ({ row }: { row: any }) => {
  return selectedBindableCustomerId.value === row.id ? 'selected-row' : ''
}

const confirmBindCustomer = async () => {
  if (!selectedBindableCustomerId.value || !currentRecord.value) return
  try {
    await bindOrderRecord(selectedBindableCustomerId.value, currentRecord.value.id)
    ElMessage.success('绑定客户成功')
    bindCustomerDialogVisible.value = false
    fetchOrderRecords()
    // 如果当前正在查看订单记录详情，刷新当前数据
    if (currentRecord.value) {
      await fetchRecordDetail(currentRecord.value.id)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '绑定客户失败')
  }
}

// ============ 新增/编辑对话框 ============
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const formRef = ref<FormInstance | null>(null)
const submitting = ref(false)

const orderRecordForm = ref({
  id: 0,
  order_no: '',
  order_remark_name: '',
  order_amount: 0,
  currency: 'CNY',
  exchange_rate: 1.0,
  order_date: '',
  is_completed: false
})

const formRules: FormRules = {
  order_no: [{ required: true, message: '请输入订单号', trigger: 'blur' }],
  order_date: [{ required: true, message: '请选择订单日期', trigger: 'change' }]
}

// ============ 收入/支出对话框 ============
const recordDialogVisible = ref(false)
const recordDialogTitle = ref('')
const recordFormRef = ref<FormInstance | null>(null)
const recordSubmitting = ref(false)
const imageUploadRef = ref<any>(null)
const uploadPath = '/api/order-records/upload-screenshot'

// 本地预览的文件（待上传的多张图片）
const localPreviewFiles = ref<{ file: File; url: string }[]>([])

const recordForm = ref({
  id: 0,
  remark: '',
  amount: 0,
  currency: 'CNY',
  exchange_rate: 1.0,
  screenshots: [] as string[],  // 多图数组
  type: 'income' as 'income' | 'expense',
  record_date: ''
})

// 预设参考汇率
const EXCHANGE_RATES: Record<string, number> = {
  CNY: 1.0,
  USD: 7.2,
  EUR: 7.8,
  JPY: 0.048
}

// ============ API 调用 ============
const fetchOrderRecords = async () => {
  loading.value = true
  try {
    const response: any = await request.get('/api/order-records', {
      params: { page: pagination.value.page, size: pagination.value.size }
    })
    orderRecords.value = response.list || []
    pagination.value.total = response.total || 0
  } catch (error) {
    console.error('获取订单记录列表失败:', error)
    ElMessage.error('获取订单记录列表失败')
  } finally {
    loading.value = false
  }
}

const fetchRecordDetail = async (id: number) => {
  try {
    const response: any = await request.get(`/api/order-records/${id}`)
    currentRecord.value = response
    incomes.value = response.incomes || []
    expenses.value = response.expenses || []
  } catch (error) {
    console.error('获取订单记录详情失败:', error)
    ElMessage.error('获取订单记录详情失败')
  }
}

// ============ 列表操作 ============
const showDetailModal = async (row: any) => {
  await fetchRecordDetail(row.id)
  detailModalVisible.value = true
}

const showAddDialog = () => {
  dialogTitle.value = '新增订单记录'
  isEdit.value = false
  orderRecordForm.value = { id: 0, order_no: '', order_remark_name: '', order_amount: 0, currency: 'CNY', exchange_rate: 1.0, order_date: '', is_completed: false }
  dialogVisible.value = true
}

const editOrderRecord = async (row: any) => {
  const response: any = await request.get(`/api/order-records/${row.id}`)
  orderRecordForm.value = {
    id: response.id,
    order_no: response.order_no,
    order_remark_name: response.order_remark_name || '',
    order_amount: response.order_amount,
    currency: response.currency || 'CNY',
    exchange_rate: response.exchange_rate || 1.0,
    order_date: response.order_date,
    is_completed: response.is_completed || false
  }
  dialogTitle.value = '编辑订单记录'
  isEdit.value = true
  dialogVisible.value = true
}

const saveOrderRecord = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    if (isEdit.value) {
      await request.put(`/api/order-records/${orderRecordForm.value.id}`, orderRecordForm.value)
      ElMessage.success('订单记录更新成功')
    } else {
      await request.post('/api/order-records', orderRecordForm.value)
      ElMessage.success('订单记录创建成功')
    }

    dialogVisible.value = false
    fetchOrderRecords()
  } catch (error: any) {
    if (error.message !== 'Validation failed') {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

const deleteOrderRecord = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个订单记录吗？', '确认删除', { type: 'warning' })

    // 删除整个订单文件夹
    try {
      await request.post('/api/order-records/delete-order-folder', { order_id: id })
    } catch (e) {
      console.error('删除订单文件夹失败:', e)
    }

    await request.delete(`/api/order-records/${id}`)
    ElMessage.success('订单记录删除成功')
    fetchOrderRecords()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 订单详情中更新完成状态
const handleStatusChange = async (val: boolean) => {
  if (!currentRecord.value) return
  updatingStatus.value = true
  try {
    await request.put(`/api/order-records/${currentRecord.value.id}`, {
      is_completed: val
    })
    ElMessage.success(val ? '订单已标记为完成' : '订单已标记为进行中')
    fetchOrderRecords()
  } catch (error) {
    ElMessage.error('更新状态失败')
    // 恢复原状态
    currentRecord.value.is_completed = !val
  } finally {
    updatingStatus.value = false
  }
}

// 收入操作
// ============ 收入操作 ============
const showAddIncomeDialog = () => {
  recordDialogTitle.value = '添加收入记录'
  recordForm.value = { id: 0, remark: '', amount: 0, currency: 'CNY', exchange_rate: 1.0, screenshots: [], type: 'income', record_date: '' }
  recordDialogVisible.value = true
}

const handleIncomeCommand = (command: string, row: any) => {
  if (command === 'edit') {
    editIncome(row)
  } else if (command === 'delete') {
    deleteIncome(row.id, row.screenshots)
  }
}

const editIncome = (row: any) => {
  recordDialogTitle.value = '修改收入记录'
  localPreviewFiles.value = []  // 重置本地预览
  recordForm.value = { ...row, type: 'income' }
  recordDialogVisible.value = true
}

const deleteIncome = async (id: number, screenshots?: string[]) => {
  try {
    await ElMessageBox.confirm('确定要删除这条收入记录吗？', '确认删除', { type: 'warning' })
    // 如果有截图，先删除截图文件
    if (screenshots && screenshots.length > 0) {
      for (const screenshot of screenshots) {
        try {
          await request.post('/api/order-records/delete-screenshot', { path: screenshot })
        } catch (e) {
          console.error('删除截图失败:', e)
        }
      }
    }
    await request.delete(`/api/order-records/incomes/${id}`)
    ElMessage.success('收入记录删除成功')
    if (currentRecord.value) {
      await fetchRecordDetail(currentRecord.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// ============ 支出操作 ============
const showAddExpenseDialog = () => {
  recordDialogTitle.value = '添加支出记录'
  recordForm.value = { id: 0, remark: '', amount: 0, currency: 'CNY', exchange_rate: 1.0, screenshots: [], type: 'expense', record_date: '' }
  recordDialogVisible.value = true
}

const handleExpenseCommand = (command: string, row: any) => {
  if (command === 'edit') {
    editExpense(row)
  } else if (command === 'delete') {
    deleteExpense(row.id, row.screenshots)
  }
}

const editExpense = (row: any) => {
  recordDialogTitle.value = '修改支出记录'
  localPreviewFiles.value = []  // 重置本地预览
  recordForm.value = { ...row, type: 'expense' }
  recordDialogVisible.value = true
}

const deleteExpense = async (id: number, screenshots?: string[]) => {
  try {
    await ElMessageBox.confirm('确定要删除这条支出记录吗？', '确认删除', { type: 'warning' })
    // 如果有截图，先删除截图文件
    if (screenshots && screenshots.length > 0) {
      for (const screenshot of screenshots) {
        try {
          await request.post('/api/order-records/delete-screenshot', { path: screenshot })
        } catch (e) {
          console.error('删除截图失败:', e)
        }
      }
    }
    await request.delete(`/api/order-records/expenses/${id}`)
    ElMessage.success('支出记录删除成功')
    if (currentRecord.value) {
      await fetchRecordDetail(currentRecord.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

// ============ 保存收入/支出 ============
const saveRecord = async () => {
  try {
    recordSubmitting.value = true

    // 如果有待上传的本地预览文件，全部上传
    if (localPreviewFiles.value.length > 0) {
      try {
        const formData = new FormData()
        // 添加所有文件
        for (const preview of localPreviewFiles.value) {
          formData.append('files', preview.file)
        }
        if (currentRecord.value) {
          formData.append('order_id', currentRecord.value.id.toString())
        }
        formData.append('record_type', recordForm.value.type)
        formData.append('remark', recordForm.value.remark || '')

        // 使用 multipartRequest（不会手动设置 Content-Type，让浏览器自动添加 boundary）
        const response: any = await multipartRequest.post(uploadPath, formData)

        // 处理多文件上传响应
        if (response && response.path) {
          recordForm.value.screenshots.push(response.path)
        } else if (response && Array.isArray(response)) {
          for (const item of response) {
            if (item.path) {
              recordForm.value.screenshots.push(item.path)
            }
          }
        }
      } catch (uploadError) {
        console.error('图片上传失败:', uploadError)
        ElMessage.error('图片上传失败，记录将保存但不含截图')
      }
    }

    const { id, type, ...postData } = recordForm.value

    if (id) {
      const endpoint = type === 'income' ? `/api/order-records/incomes/${id}` : `/api/order-records/expenses/${id}`
      await request.put(endpoint, postData)
      ElMessage.success(`${type === 'income' ? '收入' : '支出'}记录更新成功`)
    } else {
      const endpoint = `/api/order-records/${currentRecord.value.id}/${type === 'income' ? 'incomes' : 'expenses'}`
      await request.post(endpoint, postData)
      ElMessage.success(`${type === 'income' ? '收入' : '支出'}记录添加成功`)
    }

    // 清理本地预览
    for (const preview of localPreviewFiles.value) {
      URL.revokeObjectURL(preview.url)
    }
    localPreviewFiles.value = []

    recordDialogVisible.value = false
    if (currentRecord.value) {
      await fetchRecordDetail(currentRecord.value.id)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    recordSubmitting.value = false
  }
}

// 处理图片上传成功（延迟上传模式，将路径添加到screenshots数组）
const handleUploadSuccess = (files: File[], mediaFiles: any[]) => {
  if (mediaFiles && mediaFiles.length > 0) {
    // 立即上传模式：从返回的mediaFiles中提取path并添加到screenshots数组
    for (const media of mediaFiles) {
      if (media.path) {
        recordForm.value.screenshots.push(media.path)
      }
    }
  } else if (files && files.length > 0) {
    // 延迟上传模式：保存文件到本地预览列表
    for (const file of files) {
      const previewUrl = URL.createObjectURL(file)
      localPreviewFiles.value.push({ file, url: previewUrl })
    }
  }
}

// 删除指定截图
const removeScreenshot = async (index: number) => {
  const screenshot = recordForm.value.screenshots[index]
  if (screenshot) {
    try {
      await ElMessageBox.confirm('确定要删除该截图吗？', '确认删除', { type: 'warning' })
      // 如果是编辑已有记录，尝试删除服务器上的文件
      if (recordForm.value.id) {
        try {
          await request.post('/api/order-records/delete-screenshot', { path: screenshot })
        } catch (e: any) {
          // 404表示文件已不存在，直接删除记录即可
          if (e?.message?.includes('404') || e?.response?.status === 404) {
            console.log('截图文件已不存在，直接删除记录')
          } else {
            console.error('删除截图文件失败:', e)
          }
        }
      }
      // 从数组中移除
      recordForm.value.screenshots.splice(index, 1)
    } catch {
      // 用户取消删除
    }
  }
}

// 处理图片上传失败
const handleUploadFailure = (error: any) => {
  console.error('上传失败:', error)
  ElMessage.error('图片上传失败')
}

// 处理粘贴图片
const handleInputPaste = async (e: ClipboardEvent) => {
  const items = e.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      e.preventDefault()
      const file = item.getAsFile()
      if (file && imageUploadRef.value) {
        imageUploadRef.value.addClipboardMedia(file)
      }
      break
    }
  }
}

// 删除本地预览（兼容旧代码）
const removeLocalPreview = () => {
  for (const preview of localPreviewFiles.value) {
    URL.revokeObjectURL(preview.url)
  }
  localPreviewFiles.value = []
}

// 删除指定索引的本地预览文件
const removeLocalPreviewByIndex = (index: number) => {
  if (index >= 0 && index < localPreviewFiles.value.length) {
    URL.revokeObjectURL(localPreviewFiles.value[index].url)
    localPreviewFiles.value.splice(index, 1)
  }
}

// ============ 辅助方法 ============
const onExchangeRateChange = (val: number) => {
  // 用户手动输入汇率时不做任何限制
}

const onRecordCurrencyChange = (val: string) => {
  // 当选择币种时，设置默认汇率（仅针对预设币种）
  if (EXCHANGE_RATES[val]) {
    recordForm.value.exchange_rate = EXCHANGE_RATES[val]
  }
}

const onOrderCurrencyChange = (val: string) => {
  // 当选择币种时，设置默认汇率（仅针对预设币种）
  if (EXCHANGE_RATES[val]) {
    orderRecordForm.value.exchange_rate = EXCHANGE_RATES[val]
  }
}

const getImageUrl = (path: string) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  // path 格式为 xxx/file.jpg，需要补全为 assets/OrderRecords/xxx/file.jpg
  return `${BASE_URL}/assets/OrderRecords/${path}`
}

// ============ 表格样式 ============
const getRowClassName = ({ row }: { row: any }) => {
  return row.is_completed ? 'completed-row' : ''
}

const formatCurrency = (value: number) => {
  if (!value && value !== 0) return '0.00'
  return Math.abs(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// ============ 分页 ============
const handleSizeChange = (newSize: number) => {
  pagination.value.size = newSize
  pagination.value.page = 1
  fetchOrderRecords()
}

const handleCurrentChange = (newPage: number) => {
  pagination.value.page = newPage
  fetchOrderRecords()
}

// ============ 关闭对话框 ============
const handleDialogClose = () => {
  dialogVisible.value = false
  formRef.value?.resetFields()
}

const handleDetailModalClose = () => {
  detailModalVisible.value = false
  currentRecord.value = null
  incomes.value = []
  expenses.value = []
}

const handleRecordDialogClose = () => {
  // 清理本地预览
  for (const preview of localPreviewFiles.value) {
    URL.revokeObjectURL(preview.url)
  }
  localPreviewFiles.value = []
  recordDialogVisible.value = false
}

onMounted(async () => {
  const route = useRoute()
  const idParam = route.query.id ? Number(route.query.id) : null

  await fetchOrderRecords()

  if (idParam) {
    const record = orderRecords.value.find(r => r.id === idParam)
    if (record) {
      showDetailModal(record)
    } else {
      // 不在当前页，直接通过ID打开详情
      await fetchRecordDetail(idParam)
      detailModalVisible.value = true
    }
  }
})
</script>

<style scoped>
.order-record-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.detail-dialog-header {
  display: flex;
  align-items: center;
}

.management-card {
  margin-top: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.summary-header {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.summary-item {
  text-align: center;
}

.summary-item.highlight {
  background-color: #fff;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
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

.summary-value.income {
  color: #f56c6c;
}

.summary-value.expense {
  color: #67c23a;
}

.record-card {
  height: 100%;
}

.income-card {
  background-color: #fef0f0;
}

.expense-card {
  background-color: #f0f9eb;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.income-text {
  color: #f56c6c;
}

.expense-text {
  color: #67c23a;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.screenshot-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.local-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.existing-screenshot {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background-color: #f0f9eb;
  border-radius: 4px;
}

.existing-screenshots {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.screenshot-item {
  position: relative;
  display: inline-block;
}

.screenshot-item .delete-screenshot-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  padding: 2px 5px;
  font-size: 10px;
}

.preview-file-name {
  font-size: 12px;
  color: #909399;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 已完成订单行样式 */
:deep(.completed-row) {
  background-color: #f0f9eb !important;
}

/* 待上传文件样式 */
.local-preview-files {
  margin-top: 10px;
  padding: 8px;
  background-color: #f0f9eb;
  border-radius: 4px;
}

.local-preview-title {
  font-size: 12px;
  color: #67c23a;
  margin-bottom: 8px;
  font-weight: bold;
}

.local-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.local-preview-item {
  border: 2px dashed #67c23a;
}
</style>
