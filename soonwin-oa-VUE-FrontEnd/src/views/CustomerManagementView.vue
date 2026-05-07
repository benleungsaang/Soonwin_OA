<template>
  <div class="customer-management-container">
    <CommonHeader title="客户信息管理" />

    <el-card shadow="hover" class="management-card">
      <!-- 搜索筛选 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索公司名/联系人/电话/地区"
          style="width: 300px"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          新增客户
        </el-button>
        <el-button type="success" @click="showImportFromInquiryDialog">
          <el-icon><Download /></el-icon>
          从询盘导入
        </el-button>
        <el-button type="success" @click="showImportFromOrderRecordDialog">
          <el-icon><Download /></el-icon>
          从订单记录导入
        </el-button>
      </div>

      <!-- 客户列表表格 -->
      <el-table
        :data="customers"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        :row-style="{ cursor: 'pointer' }"
        @row-click="handleCustomerRowClick"
      >
        <el-table-column prop="company_name" label="公司名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="contact_person" label="联系人" width="120" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="email" label="邮箱" width="180" show-overflow-tooltip />
        <el-table-column prop="area" label="地区" width="120" />
        <el-table-column prop="customer_type" label="客户类型" width="100">
          <template #default="scope">
            {{ scope.row.customer_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.source === 'inquiry'" type="primary" size="small">询盘</el-tag>
            <el-tag v-else-if="scope.row.source === 'order_record'" type="success" size="small">订单记录</el-tag>
            <el-tag v-else type="info" size="small">手动</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="160" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" @click.stop="viewCustomer(scope.row)">查看</el-button>
            <el-button size="small" type="primary" @click.stop="editCustomer(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="handleDeleteCustomer(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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
    >
      <el-form :model="customerForm" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="公司名称" prop="company_name">
          <el-input v-model="customerForm.company_name" placeholder="请输入公司名称" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_person">
          <el-input v-model="customerForm.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="customerForm.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="customerForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="地区">
          <el-input v-model="customerForm.area" placeholder="请输入地区" />
        </el-form-item>
        <el-form-item label="客户类型">
          <el-select v-model="customerForm.customer_type" placeholder="请选择客户类型" style="width: 100%">
            <el-option label="经销商" value="经销商" />
            <el-option label="终端" value="终端" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="customerForm.remark" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCustomer" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 客户详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="客户详情"
      size="600px"
    >
      <div v-if="currentCustomer" class="customer-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="公司名称">{{ currentCustomer.company_name }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ currentCustomer.contact_person }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ currentCustomer.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ currentCustomer.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="地区">{{ currentCustomer.area || '-' }}</el-descriptions-item>
          <el-descriptions-item label="客户类型">{{ currentCustomer.customer_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="来源" :span="2">
            <el-tag v-if="currentCustomer.source === 'inquiry'" type="primary">询盘</el-tag>
            <el-tag v-else-if="currentCustomer.source === 'order_record'" type="success">订单记录</el-tag>
            <el-tag v-else type="info">手动</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ currentCustomer.remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ currentCustomer.create_time }}</el-descriptions-item>
          <el-descriptions-item label="绑定操作" :span="2">
            <el-button size="small" type="primary" @click.stop="handleBindInquiry(currentCustomer)">绑定询盘</el-button>
            <el-button size="small" type="success" @click.stop="handleBindOrderRecord(currentCustomer)">绑定订单记录</el-button>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 关联记录 -->
        <el-tabs class="related-tabs">
          <el-tab-pane label="关联询盘">
            <el-table :data="relatedInquiries" v-loading="relatedLoading" style="width: 100%" max-height="300" :row-style="{ cursor: 'pointer' }" @row-click="goToInquiry">
              <el-table-column prop="company_name" label="公司名" />
              <el-table-column prop="contact_person" label="联系人" />
              <el-table-column prop="phone" label="电话" />
              <el-table-column prop="create_time" label="创建时间" />
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="scope">
                  <el-button size="small" type="danger" @click.stop="handleUnbindInquiry(scope.row)">解除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="relatedInquiries.length === 0" description="暂无关联询盘" />
          </el-tab-pane>
          <el-tab-pane label="关联订单记录">
            <el-table :data="relatedOrderRecords" v-loading="relatedLoading" style="width: 100%" max-height="300" :row-style="{ cursor: 'pointer' }" @row-click="goToOrderRecord">
              <el-table-column prop="order_no" label="订单号" />
              <el-table-column prop="order_remark_name" label="订单备注名" />
              <el-table-column prop="order_amount_cny" label="订单金额">
                <template #default="scope">
                  ¥{{ formatCurrency(scope.row.order_amount_cny) }}
                </template>
              </el-table-column>
              <el-table-column prop="order_date" label="订单日期" />
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="scope">
                  <el-button size="small" type="danger" @click.stop="handleUnbindOrderRecord(scope.row)">解除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="relatedOrderRecords.length === 0" description="暂无关联订单记录" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-drawer>

    <!-- 从询盘导入对话框 -->
    <el-dialog
      title="从询盘导入客户"
      v-model="importFromInquiryDialogVisible"
      width="700px"
    >
      <p style="color: #909399; margin-bottom: 10px;">选择一个询盘，点击确认填充到新增表单</p>
      <el-table
        :data="inquiries"
        v-loading="inquiriesLoading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        @row-click="handleInquiryRowClick"
        :row-class-name="getInquiryRowClassName"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column width="60" label="选择">
          <template #default="scope">
            <el-radio v-model="selectedInquiryId" :label="scope.row.id" @click.stop>&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="company_name" label="公司名" />
        <el-table-column prop="contact_person" label="联系人" />
        <el-table-column prop="phone" label="电话" />
        <el-table-column prop="area" label="地区" />
      </el-table>
      <el-pagination
        v-model:current-page="inquiriesPage"
        :page-size="inquiriesSize"
        :total="inquiriesTotal"
        layout="prev, pager, next"
        @current-change="loadInquiries"
        style="margin-top: 10px; justify-content: center"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importFromInquiryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmImportFromInquiry" :disabled="!selectedInquiryId">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 从订单记录导入对话框 -->
    <el-dialog
      title="从订单记录导入客户"
      v-model="importFromOrderRecordDialogVisible"
      width="700px"
    >
      <p style="color: #909399; margin-bottom: 10px;">选择一个订单记录，点击确认填充到新增表单</p>
      <el-table
        :data="orderRecords"
        v-loading="orderRecordsLoading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        @row-click="handleOrderRecordRowClick"
        :row-class-name="getOrderRecordRowClassName"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column width="60" label="选择">
          <template #default="scope">
            <el-radio v-model="selectedOrderRecordId" :label="scope.row.id" @click.stop>&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="order_no" label="订单号" />
        <el-table-column prop="order_remark_name" label="订单备注名" />
        <el-table-column prop="order_amount" label="订单金额">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.order_amount) }} ({{ scope.row.currency }})
          </template>
        </el-table-column>
        <el-table-column prop="order_date" label="订单日期" />
      </el-table>
      <el-pagination
        v-model:current-page="orderRecordsPage"
        :page-size="orderRecordsSize"
        :total="orderRecordsTotal"
        layout="prev, pager, next"
        @current-change="loadOrderRecords"
        style="margin-top: 10px; justify-content: center"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importFromOrderRecordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmImportFromOrderRecord" :disabled="!selectedOrderRecordId">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 绑定询盘对话框 -->
    <el-dialog
      title="绑定询盘"
      v-model="bindInquiryDialogVisible"
      width="700px"
    >
      <p style="color: #909399; margin-bottom: 10px;">选择一个询盘进行绑定</p>
      <el-table
        :data="bindableInquiries"
        v-loading="bindableInquiriesLoading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        @row-click="handleBindableInquiryRowClick"
        :row-class-name="getBindableInquiryRowClassName"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column width="60" label="选择">
          <template #default="scope">
            <el-radio v-model="selectedBindableInquiryId" :label="scope.row.id" @click.stop>&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="company_name" label="公司名" />
        <el-table-column prop="contact_person" label="联系人" />
        <el-table-column prop="phone" label="电话" />
        <el-table-column prop="area" label="地区" />
      </el-table>
      <el-pagination
        v-model:current-page="bindableInquiriesPage"
        :page-size="bindableInquiriesSize"
        :total="bindableInquiriesTotal"
        layout="prev, pager, next"
        @current-change="loadBindableInquiries"
        style="margin-top: 10px; justify-content: center"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="bindInquiryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmBindInquiry" :disabled="!selectedBindableInquiryId">确认绑定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 绑定订单记录对话框 -->
    <el-dialog
      title="绑定订单记录"
      v-model="bindOrderRecordDialogVisible"
      width="700px"
    >
      <p style="color: #909399; margin-bottom: 10px;">选择一个订单记录进行绑定</p>
      <el-table
        :data="bindableOrderRecords"
        v-loading="bindableOrderRecordsLoading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        @row-click="handleBindableOrderRecordRowClick"
        :row-class-name="getBindableOrderRecordRowClassName"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column width="60" label="选择">
          <template #default="scope">
            <el-radio v-model="selectedBindableOrderRecordId" :label="scope.row.id" @click.stop>&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="order_no" label="订单号" />
        <el-table-column prop="order_remark_name" label="订单备注名" />
        <el-table-column prop="order_amount" label="订单金额">
          <template #default="scope">
            ¥{{ formatCurrency(scope.row.order_amount) }} ({{ scope.row.currency }})
          </template>
        </el-table-column>
        <el-table-column prop="order_date" label="订单日期" />
      </el-table>
      <el-pagination
        v-model:current-page="bindableOrderRecordsPage"
        :page-size="bindableOrderRecordsSize"
        :total="bindableOrderRecordsTotal"
        layout="prev, pager, next"
        @current-change="loadBindableOrderRecords"
        style="margin-top: 10px; justify-content: center"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="bindOrderRecordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmBindOrderRecord" :disabled="!selectedBindableOrderRecordId">确认绑定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Download } from '@element-plus/icons-vue'
import request from '@/utils/request'
import CommonHeader from '@/components/CommonHeader.vue'
import {
  getCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  getCustomerRecords,
  bindInquiry,
  unbindInquiry,
  bindOrderRecord,
  unbindOrderRecord
} from '@/api/customer'

// ============ 数据列表 ============
const customers = ref<any[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const pagination = ref({ page: 1, size: 10, total: 0 })

// ============ 新增/编辑对话框 ============
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const formRef = ref<FormInstance | null>(null)
const submitting = ref(false)

const customerForm = ref({
  id: 0,
  company_name: '',
  contact_person: '',
  phone: '',
  email: '',
  area: '',
  customer_type: '',
  remark: ''
})

const formRules: FormRules = {
  company_name: [{ required: true, message: '请输入公司名称', trigger: 'blur' }],
  contact_person: [{ required: true, message: '请输入联系人', trigger: 'blur' }]
}

// ============ 详情抽屉 ============
const detailDrawerVisible = ref(false)
const currentCustomer = ref<any>(null)
const relatedInquiries = ref<any[]>([])
const relatedOrderRecords = ref<any[]>([])
const relatedLoading = ref(false)

// ============ 绑定询盘对话框 ============
const bindInquiryDialogVisible = ref(false)
const bindableInquiries = ref<any[]>([])
const bindableInquiriesLoading = ref(false)
const bindableInquiriesPage = ref(1)
const bindableInquiriesSize = ref(10)
const bindableInquiriesTotal = ref(0)
const selectedBindableInquiryId = ref<number | null>(null)
const selectedBindableInquiry = ref<any>(null)

// ============ 绑定订单记录对话框 ============
const bindOrderRecordDialogVisible = ref(false)
const bindableOrderRecords = ref<any[]>([])
const bindableOrderRecordsLoading = ref(false)
const bindableOrderRecordsPage = ref(1)
const bindableOrderRecordsSize = ref(10)
const bindableOrderRecordsTotal = ref(0)
const selectedBindableOrderRecordId = ref<number | null>(null)
const selectedBindableOrderRecord = ref<any>(null)

// ============ 从询盘导入 ============
const importFromInquiryDialogVisible = ref(false)
const inquiries = ref<any[]>([])
const inquiriesLoading = ref(false)
const inquiriesPage = ref(1)
const inquiriesSize = ref(10)
const inquiriesTotal = ref(0)
const selectedInquiryId = ref<number | null>(null)
const selectedInquiry = ref<any>(null)

// ============ 从订单记录导入 ============
const importFromOrderRecordDialogVisible = ref(false)
const orderRecords = ref<any[]>([])
const orderRecordsLoading = ref(false)
const orderRecordsPage = ref(1)
const orderRecordsSize = ref(10)
const orderRecordsTotal = ref(0)
const selectedOrderRecordId = ref<number | null>(null)
const selectedOrderRecord = ref<any>(null)

// ============ 生命周期 ============
onMounted(() => {
  loadCustomers()
})

// ============ 方法 ============
const loadCustomers = async () => {
  try {
    loading.value = true
    const response = await getCustomers({
      page: pagination.value.page,
      size: pagination.value.size,
      search: searchKeyword.value
    })
    customers.value = response.list
    pagination.value.total = response.total
  } catch (error: any) {
    ElMessage.error(error.message || '获取客户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  loadCustomers()
}

const handleSizeChange = (size: number) => {
  pagination.value.size = size
  loadCustomers()
}

const handleCurrentChange = (page: number) => {
  pagination.value.page = page
  loadCustomers()
}

const showAddDialog = () => {
  dialogTitle.value = '新增客户'
  isEdit.value = false
  customerForm.value = {
    id: 0,
    company_name: '',
    contact_person: '',
    phone: '',
    email: '',
    area: '',
    customer_type: '',
    remark: ''
  }
  dialogVisible.value = true
}

const editCustomer = (row: any) => {
  dialogTitle.value = '编辑客户'
  isEdit.value = true
  customerForm.value = {
    id: row.id,
    company_name: row.company_name,
    contact_person: row.contact_person,
    phone: row.phone || '',
    email: row.email || '',
    area: row.area || '',
    customer_type: row.customer_type || '',
    remark: row.remark || ''
  }
  dialogVisible.value = true
}

const saveCustomer = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    if (isEdit.value) {
      await updateCustomer(customerForm.value.id, customerForm.value)
      ElMessage.success('客户更新成功')
    } else {
      await createCustomer(customerForm.value)
      ElMessage.success('客户创建成功')
    }

    dialogVisible.value = false
    loadCustomers()
  } catch (error: any) {
    if (error !== 'validate') {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

const viewCustomer = (row: any) => {
  currentCustomer.value = row
  detailDrawerVisible.value = true
  // 清空关联记录并重新加载
  relatedInquiries.value = []
  relatedOrderRecords.value = []
  loadRelatedRecords()
}

const handleCustomerRowClick = (row: any) => {
  viewCustomer(row)
}

const loadRelatedRecords = async () => {
  if (!currentCustomer.value) return
  try {
    relatedLoading.value = true
    const response = await getCustomerRecords(currentCustomer.value.id)
    let inquiries = response.inquiries || []
    let orderRecords = response.order_records || []

    // 后备操作：检查关联记录是否仍然存在
    let cleanedCount = 0
    for (const inquiry of inquiries) {
      try {
        await request.get(`/api/inquiries/${inquiry.id}`)
      } catch {
        // 询盘已不存在，自动解绑
        await unbindInquiry(currentCustomer.value.id, inquiry.id)
        cleanedCount++
      }
    }
    for (const record of orderRecords) {
      try {
        await request.get(`/api/order-records/${record.id}`)
      } catch {
        // 订单已不存在，自动解绑
        await unbindOrderRecord(currentCustomer.value.id, record.id)
        cleanedCount++
      }
    }

    if (cleanedCount > 0) {
      ElMessage.warning(`有${cleanedCount}条关联记录已不存在，已自动清理`)
      // 重新获取最新数据
      const refreshed = await getCustomerRecords(currentCustomer.value.id)
      relatedInquiries.value = refreshed.inquiries || []
      relatedOrderRecords.value = refreshed.order_records || []
    } else {
      relatedInquiries.value = inquiries
      relatedOrderRecords.value = orderRecords
    }
  } catch (error) {
    console.error('获取关联记录失败:', error)
  } finally {
    relatedLoading.value = false
  }
}

const goToInquiry = (row: any) => {
  window.open(`/#/inquiry/${row.id}`, '_blank')
}

const goToOrderRecord = (row: any) => {
  window.open(`/#/order-record?id=${row.id}`, '_blank')
}

// ============ 绑定询盘 ============
const handleBindInquiry = async (row: any) => {
  currentCustomer.value = row
  selectedBindableInquiryId.value = null
  selectedBindableInquiry.value = null
  bindInquiryDialogVisible.value = true
  await loadBindableInquiries()
}

const showBindInquiryDialog = async () => {
  selectedBindableInquiryId.value = null
  selectedBindableInquiry.value = null
  bindInquiryDialogVisible.value = true
  await loadBindableInquiries()
}

const loadBindableInquiries = async () => {
  try {
    bindableInquiriesLoading.value = true
    const response = await request.get('/api/inquiries', {
      params: { page: bindableInquiriesPage.value, size: bindableInquiriesSize.value }
    })
    // 过滤掉已关联本客户的询盘
    const alreadyRelatedIds = relatedInquiries.value.map((i: any) => i.id)
    bindableInquiries.value = (response.list || []).filter((item: any) =>
      !item.customer_id && !alreadyRelatedIds.includes(item.id)
    )
    bindableInquiriesTotal.value = response.total || 0
  } catch (error) {
    console.error('获取可绑定询盘列表失败:', error)
  } finally {
    bindableInquiriesLoading.value = false
  }
}

const handleBindableInquiryRowClick = (row: any) => {
  selectedBindableInquiryId.value = row.id
  selectedBindableInquiry.value = row
}

const getBindableInquiryRowClassName = ({ row }: { row: any }) => {
  return selectedBindableInquiryId.value === row.id ? 'selected-row' : ''
}

const confirmBindInquiry = async () => {
  if (!selectedBindableInquiryId.value || !currentCustomer.value) return
  try {
    await bindInquiry(currentCustomer.value.id, selectedBindableInquiryId.value)
    ElMessage.success('绑定询盘成功')
    bindInquiryDialogVisible.value = false
    await loadRelatedRecords()
  } catch (error: any) {
    ElMessage.error(error.message || '绑定询盘失败')
  }
}

const handleUnbindInquiry = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要解除与询盘"${row.company_name}"的关联吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await unbindInquiry(currentCustomer.value.id, row.id)
    ElMessage.success('解除关联成功')
    await loadRelatedRecords()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '解除关联失败')
    }
  }
}

// ============ 绑定订单记录 ============
const handleBindOrderRecord = async (row: any) => {
  currentCustomer.value = row
  selectedBindableOrderRecordId.value = null
  selectedBindableOrderRecord.value = null
  bindOrderRecordDialogVisible.value = true
  await loadBindableOrderRecords()
}

const showBindOrderRecordDialog = async () => {
  selectedBindableOrderRecordId.value = null
  selectedBindableOrderRecord.value = null
  bindOrderRecordDialogVisible.value = true
  await loadBindableOrderRecords()
}

const loadBindableOrderRecords = async () => {
  try {
    bindableOrderRecordsLoading.value = true
    const response = await request.get('/api/order-records', {
      params: { page: bindableOrderRecordsPage.value, size: bindableOrderRecordsSize.value }
    })
    // 过滤掉已关联本客户的订单记录
    const alreadyRelatedIds = relatedOrderRecords.value.map((o: any) => o.id)
    bindableOrderRecords.value = (response.list || []).filter((item: any) =>
      !item.customer_id && !alreadyRelatedIds.includes(item.id)
    )
    bindableOrderRecordsTotal.value = response.total || 0
  } catch (error) {
    console.error('获取可绑定订单记录列表失败:', error)
  } finally {
    bindableOrderRecordsLoading.value = false
  }
}

const handleBindableOrderRecordRowClick = (row: any) => {
  selectedBindableOrderRecordId.value = row.id
  selectedBindableOrderRecord.value = row
}

const getBindableOrderRecordRowClassName = ({ row }: { row: any }) => {
  return selectedBindableOrderRecordId.value === row.id ? 'selected-row' : ''
}

const confirmBindOrderRecord = async () => {
  if (!selectedBindableOrderRecordId.value || !currentCustomer.value) return
  try {
    await bindOrderRecord(currentCustomer.value.id, selectedBindableOrderRecordId.value)
    ElMessage.success('绑定订单记录成功')
    bindOrderRecordDialogVisible.value = false
    await loadRelatedRecords()
  } catch (error: any) {
    ElMessage.error(error.message || '绑定订单记录失败')
  }
}

const handleUnbindOrderRecord = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要解除与订单记录"${row.order_no}"的关联吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await unbindOrderRecord(currentCustomer.value.id, row.id)
    ElMessage.success('解除关联成功')
    await loadRelatedRecords()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '解除关联失败')
    }
  }
}

const handleDeleteCustomer = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个客户吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await deleteCustomer(id)
    ElMessage.success('客户删除成功')
    loadCustomers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除客户失败')
    }
  }
}

// ============ 从询盘导入 ============
const showImportFromInquiryDialog = () => {
  selectedInquiryId.value = null
  selectedInquiry.value = null
  importFromInquiryDialogVisible.value = true
  loadInquiries()
}

const handleInquiryRowClick = (row: any) => {
  selectedInquiryId.value = row.id
  selectedInquiry.value = row
}

const getInquiryRowClassName = ({ row }: { row: any }) => {
  return selectedInquiryId.value === row.id ? 'selected-row' : ''
}

const confirmImportFromInquiry = () => {
  if (!selectedInquiryId.value || !selectedInquiry.value) return
  const row = selectedInquiry.value
  importFromInquiryDialogVisible.value = false
  showAddDialog()
  customerForm.value = {
    id: 0,
    company_name: row.company_name || '',
    contact_person: row.contact_person || '',
    phone: row.phone || '',
    email: row.email || '',
    area: row.area || '',
    customer_type: '',
    remark: `来源：询盘（ID:${row.id}）`
  }
}

const loadInquiries = async () => {
  try {
    inquiriesLoading.value = true
    const response = await request.get('/api/inquiries', {
      params: { page: inquiriesPage.value, size: inquiriesSize.value }
    })
    inquiries.value = response.list || []
    inquiriesTotal.value = response.total || 0
  } catch (error) {
    console.error('获取询盘列表失败:', error)
  } finally {
    inquiriesLoading.value = false
  }
}

// ============ 从订单记录导入 ============
const showImportFromOrderRecordDialog = () => {
  selectedOrderRecordId.value = null
  selectedOrderRecord.value = null
  importFromOrderRecordDialogVisible.value = true
  loadOrderRecords()
}

const handleOrderRecordRowClick = (row: any) => {
  selectedOrderRecordId.value = row.id
  selectedOrderRecord.value = row
}

const getOrderRecordRowClassName = ({ row }: { row: any }) => {
  return selectedOrderRecordId.value === row.id ? 'selected-row' : ''
}

const confirmImportFromOrderRecord = () => {
  if (!selectedOrderRecordId.value || !selectedOrderRecord.value) return
  const row = selectedOrderRecord.value
  importFromOrderRecordDialogVisible.value = false
  showAddDialog()
  customerForm.value = {
    id: 0,
    company_name: row.order_remark_name || row.order_no || '',
    contact_person: '',
    phone: '',
    email: '',
    area: '',
    customer_type: '',
    remark: `来源：订单记录（${row.order_no}）`
  }
}

const loadOrderRecords = async () => {
  try {
    orderRecordsLoading.value = true
    const response = await request.get('/api/order-records', {
      params: { page: orderRecordsPage.value, size: orderRecordsSize.value }
    })
    orderRecords.value = response.list || []
    orderRecordsTotal.value = response.total || 0
  } catch (error) {
    console.error('获取订单记录列表失败:', error)
  } finally {
    orderRecordsLoading.value = false
  }
}

const formatCurrency = (value: number) => {
  if (!value) return '0.00'
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped>
.customer-management-container {
  padding: 20px;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.customer-detail {
  padding: 0 10px;
}

.related-tabs {
  margin-top: 20px;
}

:deep(.selected-row) {
  background-color: #ecf5ff !important;
}

:deep(.el-radio) {
  margin-right: 0;
}
</style>
