<template>
  <div class="inquiry-list-container">
    <CommonHeader title="询盘管理" />

    <!-- 搜索和筛选 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :model="searchForm" label-width="100px" style="display: flex; flex-wrap: wrap;">
        <el-form-item label="地区" style="min-width: 200px;">
          <el-input v-model="searchForm.area" placeholder="请输入地区" clearable />
        </el-form-item>
        <el-form-item label="联系人" style="min-width: 200px;">
          <el-input v-model="searchForm.contact_person" placeholder="请输入联系人" clearable />
        </el-form-item>
        <el-form-item label="公司名" style="min-width: 200px;">
          <el-input v-model="searchForm.company_name" placeholder="请输入公司名" clearable />
        </el-form-item>
        <el-form-item label="包装产品" style="min-width: 200px;">
          <el-input v-model="searchForm.packaging_product" placeholder="请输入包装产品" clearable />
        </el-form-item>
        <el-form-item label="机器类型" style="min-width: 200px;">
          <el-input v-model="searchForm.machine_type" placeholder="请输入机器类型" clearable />
        </el-form-item>
        <el-form-item label="询盘来源" style="min-width: 200px;">
          <el-input v-model="searchForm.inquiry_source" placeholder="请输入询盘来源" clearable />
        </el-form-item>
        <el-form-item label="询盘日期" style="min-width: 300px;">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="onDateRangeChange"
          />
        </el-form-item>
        <el-form-item style="margin-left: auto;">
          <el-button type="primary" @click="searchInquiries">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮 -->
    <div style="margin-bottom: 20px;">
      <el-button type="primary" @click="showAddInquiryDialog">新增询盘</el-button>
      <el-button @click="showInquiryLogs" v-if="isCurrentUserAdmin">查看日志</el-button>
      <el-button @click="exportData">导出数据</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="inquiries"
      style="width: 100%"
      v-loading="loading"
      @row-click="viewInquiryById"
    >
      <el-table-column prop="area" label="地区" width="120" />
      <el-table-column prop="inquiry_date" label="询盘日期" width="120" />
      <el-table-column prop="inquiry_source" label="询盘来源" width="120" />
      <el-table-column prop="company_name" label="公司名" width="150" show-overflow-tooltip />
      <el-table-column prop="contact_person" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="email" label="邮箱" width="180" show-overflow-tooltip />
      <el-table-column prop="packaging_product" label="包装产品" width="150" show-overflow-tooltip />
      <el-table-column prop="machine_type" label="需求机器类型" show-overflow-tooltip />
      <el-table-column prop="creator_name" label="创建人" width="120" />
      <el-table-column prop="create_time" label="创建时间" width="150" />
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click.stop="viewInquiry(scope.row.id)">查看详情</el-button>
          <el-button size="small" type="danger" @click.stop="deleteInquiry(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination" style="margin-top: 20px; display: flex; justify-content: center;">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
      />
    </div>

    <!-- 新增/编辑询盘对话框 -->
    <el-dialog :title="inquiryDialogTitle" v-model="inquiryDialogVisible" width="70%" :before-close="handleDialogClose">
      <el-form :model="inquiryForm" :rules="inquiryRules" ref="inquiryFormRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="地区" prop="area">
              <el-autocomplete
                v-model="inquiryForm.area"
                :fetch-suggestions="queryArea"
                placeholder="请输入或选择地区"
                clearable
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="询盘日期" prop="inquiry_date">
              <el-date-picker
                v-model="inquiryForm.inquiry_date"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="询盘来源" prop="inquiry_source">
              <el-autocomplete
                v-model="inquiryForm.inquiry_source"
                :fetch-suggestions="querySource"
                placeholder="请输入或选择询盘来源"
                clearable
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司名" prop="company_name">
              <el-input v-model="inquiryForm.company_name" placeholder="请输入公司名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系人" prop="contact_person">
              <el-input v-model="inquiryForm.contact_person" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话" prop="phone">
              <el-input v-model="inquiryForm.phone" placeholder="请输入电话" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="inquiryForm.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="包装产品" prop="packaging_product">
              <el-input v-model="inquiryForm.packaging_product" placeholder="请输入包装产品" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="需求机器类型" prop="machine_type">
              <el-input
                v-model="inquiryForm.machine_type"
                type="textarea"
                :rows="2"
                placeholder="请输入需求机器类型"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 按钮区域 -->
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="24">
            <el-form-item>
              <el-button @click="cancelInquiry">取消</el-button>
              <el-button
                v-if="inquiryDialogTitle === '查看详情/编辑' || inquiryDialogTitle === '新增询盘'"
                type="primary"
                @click="submitInquiry"
                :loading="submitting"
              >
                提交
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <!-- 沟通记录部分 -->
      <div v-if="inquiryForm.id" class="communication-section">
        <el-divider />
        <div class="communication-header">
          <h3>沟通记录</h3>
          <el-button type="primary" size="large" @click="showAddCommunicationDialog">
            添加沟通记录
            <el-icon style="margin-left: 5px;font-size: 20px;"><ChatLineRound /></el-icon>
          </el-button>
        </div>

        <!-- 沟通记录列表 -->
        <div class="communication-list">
          <el-card
            v-for="comm in communications"
            :key="comm.id"
            class="communication-item"
            shadow="hover"
            body-style="padding:10px"
          >
            <div class="communication-content-header">
              <span class="subject">主题：{{ comm.subject }}</span>
              <div class="communication-footer"><span class="creator">{{ comm.creator_name }}</span>
                <span class="time">{{ comm.create_time }}</span>
                <el-icon @click="editCommunication(comm)" class="el-icon edit"><Edit /></el-icon>
                <el-icon @click="deleteCommunication(comm.id)" class="el-icon delete"><Delete /></el-icon>
              </div>
            </div>
            <div class="communication-content">{{ comm.content }}</div>
          </el-card>
          <div v-if="communications.length === 0" class="no-communications">
            暂无沟通记录
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <!-- 这里不放按钮，按钮已移到表单内部 -->
        </span>
      </template>
    </el-dialog>
          <!-- 新增/编辑沟通记录对话框 -->
          <el-dialog :title="communicationDialogTitle" v-model="addCommunicationDialogVisible" width="50%">
            <el-form :model="communicationForm" :rules="communicationRules" ref="communicationFormRef" label-width="100px">
              <el-form-item label="主题" prop="subject">
                <el-input v-model="communicationForm.subject" placeholder="请输入沟通主题" />
              </el-form-item>
              <el-form-item label="内容" prop="content">
                <el-input
                  v-model="communicationForm.content"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入沟通内容"
                />
              </el-form-item>
              <el-form-item label="沟通日期" prop="communication_date">
                <el-date-picker
                  v-model="communicationForm.communication_date"
                  type="date"
                  placeholder="选择日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%;"
                />
              </el-form-item>
            </el-form>
            <template #footer>
              <span class="dialog-footer">
                <el-button @click="cancelCommunication">取消</el-button>
                <el-button type="primary" @click="submitCommunication" :loading="communicationSubmitting">确定</el-button>
              </span>
            </template>
          </el-dialog>
    <!-- 沟通记录对话框 -->
    <el-dialog title="沟通记录" v-model="communicationDialogVisible" width="70%">
      <div>
        <el-button type="primary" size="small" @click="showAddCommunicationDialog" style="margin-bottom: 20px;"><el-icon><ChatLineRound /></el-icon>添加沟通记录</el-button>

        <el-table :data="communications" style="width: 100%; margin-bottom: 20px;">
          <el-table-column prop="subject" label="主题" width="200" />
          <el-table-column prop="content" label="内容" />
          <el-table-column prop="communication_date" label="沟通日期" width="120" />
          <el-table-column prop="creator_name" label="创建人" width="120" />
          <el-table-column prop="create_time" label="创建时间" width="150" />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button size="small" @click="editCommunication(scope.row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteCommunication(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeCommunicationDialog">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新增/编辑沟通记录对话框 -->
    <el-dialog :title="communicationDialogTitle" v-model="addCommunicationDialogVisible" width="50%">
      <el-form :model="communicationForm" :rules="communicationRules" ref="communicationFormRef" label-width="100px">
        <el-form-item label="主题" prop="subject">
          <el-input v-model="communicationForm.subject" placeholder="请输入沟通主题" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="communicationForm.content"
            type="textarea"
            :rows="4"
            placeholder="请输入沟通内容"
          />
        </el-form-item>
        <el-form-item label="沟通日期" prop="communication_date">
          <el-date-picker
            v-model="communicationForm.communication_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelCommunication">取消</el-button>
          <el-button type="primary" @click="submitCommunication" :loading="communicationSubmitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 日志对话框 -->
    <el-dialog title="询盘操作日志" v-model="logDialogVisible" width="80%" top="5vh">
      <el-table :data="inquiryLogs" style="width: 100%" v-loading="logLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="inquiry_id" label="询盘ID" width="100" />
        <el-table-column prop="operation_type" label="操作类型" width="120" />
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="operator_role" label="角色" width="100" />
        <el-table-column prop="operation_details" label="操作详情" show-overflow-tooltip />
        <el-table-column prop="create_time" label="操作时间" width="160" />
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeLogDialog">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import request from '@/utils/request';
import { Delete, Edit, ChatLineRound } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';

// 路由
const router = useRouter();

// 检查当前用户是否为管理员
const isCurrentUserAdmin = ref(false);

// 在组件挂载时检查用户角色
onMounted(async () => {
  try {
    const token = localStorage.getItem('oa_token');
    if (token) {
      // 解码JWT token获取用户角色信息
      const payload = JSON.parse(atob(token.split('.')[1]));
      isCurrentUserAdmin.value = payload.user_role === 'admin';
    }
  } catch (error) {
    console.error('解析用户信息失败:', error);
    isCurrentUserAdmin.value = false;
  }
  loadInquiries();

  // 获取预设地区列表
  try {
    const response = await request.get('/api/inquiries', { page: 1, size: 1000 });
    if (response && response.list) {
      // 提取所有不重复的地区
      const areas = [...new Set(response.list.map((item: any) => item.area).filter((area: any) => area))];
      presetAreas.value = areas;
    }
  } catch (error) {
    console.error('获取地区列表失败:', error);
    // 出错时使用空数组
    presetAreas.value = [];
  }
});

// 分页参数
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 搜索参数
const searchForm = ref({
  area: '',
  contact_person: '',
  company_name: '',
  packaging_product: '',
  machine_type: '',
  inquiry_source: '',
  start_date: '',
  end_date: ''
});

// 日期范围
const dateRange = ref<[string, string] | null>(null);

// 数据
const inquiries = ref<any[]>([]);
const loading = ref(false);

// 预设地区和来源
const presetAreas = ref<string[]>([]);
const presetSources = ref(['官网', '阿里', '展会']);
// 用于存储打开对话框时的初始表单值
const initialInquiryForm = ref<any>(null);

// 询盘表单相关
const inquiryDialogVisible = ref(false);
const inquiryDialogTitle = ref('');
const editingInquiryId = ref<number | null>(null);
const submitting = ref(false);

const inquiryForm = ref({
  id: null as number | null,
  area: '',
  inquiry_date: '',
  inquiry_source: '',
  company_name: '',
  contact_person: '',
  phone: '',
  email: '',
  packaging_product: '',
  machine_type: ''
});

// 沟通记录相关
const communicationDialogVisible = ref(false);
const communications = ref<any[]>([]);
const currentInquiryId = ref<number | null>(null);

const addCommunicationDialogVisible = ref(false);
const communicationDialogTitle = ref('');
const editingCommunicationId = ref<number | null>(null);
const communicationSubmitting = ref(false);

const communicationForm = ref({
  id: null as number | null,
  subject: '',
  content: '',
  communication_date: ''
});

// 日志相关
const logDialogVisible = ref(false);
const inquiryLogs = ref<any[]>([]);
const logLoading = ref(false);

// 表单引用
const inquiryFormRef = ref();
const communicationFormRef = ref();

// 表单验证规则
const inquiryRules = {
  contact_person: [
    { required: true, message: '请输入联系人', trigger: 'blur' }
  ],
  packaging_product: [
    { required: true, message: '请输入包装产品', trigger: 'blur' }
  ],
  machine_type: [
    { required: true, message: '请输入需求机器类型', trigger: 'blur' }
  ],
  email: [
    {
      type: 'email',
      message: '请输入正确的邮箱格式',
      trigger: 'blur'
    }
  ]
};

const communicationRules = {
  subject: [
    { required: true, message: '请输入沟通主题', trigger: 'blur' }
  ]
};

// 显示新增询盘对话框
const showAddInquiryDialog = () => {
  inquiryDialogTitle.value = '新增询盘';
  editingInquiryId.value = null;
  const emptyForm = {
    id: null,
    area: '',
    inquiry_date: '',
    inquiry_source: '',
    company_name: '',
    contact_person: '',
    phone: '',
    email: '',
    packaging_product: '',
    machine_type: ''
  };
  inquiryForm.value = { ...emptyForm };
  // 保存初始表单值用于比较
  initialInquiryForm.value = JSON.parse(JSON.stringify(emptyForm));
  inquiryDialogVisible.value = true;
  resetFormChangedFlag(); // 重置更改标记
};



// 查看询盘详情（支持编辑）
const viewInquiry = async (id: number) => {
  try {
    const response = await request.get(`/api/inquiries/${id}`);
    inquiryForm.value = { ...response };
    // 保存初始表单值用于比较
    initialInquiryForm.value = JSON.parse(JSON.stringify(response));
    editingInquiryId.value = id;
    inquiryDialogTitle.value = '查看详情/编辑';
    // 加载沟通记录
    await loadCommunications(id);
    inquiryDialogVisible.value = true;
  } catch (error) {
    console.error('加载询盘详情失败:', error);
    ElMessage.error('加载询盘详情失败');
  }
};

// 通过行点击查看详情
const viewInquiryById = (row: any) => {
  viewInquiry(row.id);
};

// 提交询盘
const submitInquiry = async () => {
  if (!inquiryFormRef.value) return;

  await inquiryFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true;
      try {
        let response;
        if (editingInquiryId.value) {
          // 更新现有询盘
          response = await request.put(`/api/inquiries/${editingInquiryId.value}`, inquiryForm.value);
          ElMessage.success('询盘更新成功');
        } else {
          // 创建新询盘
          response = await request.post('/api/inquiries', inquiryForm.value);
          ElMessage.success('询盘创建成功');
        }

        // 关闭对话框并重新加载列表
        inquiryDialogVisible.value = false;
        loadInquiries();
      } catch (error) {
        console.error('提交询盘失败:', error);
        ElMessage.error('提交询盘失败');
      } finally {
        submitting.value = false;
      }
    } else {
      ElMessage.error('请填写必填项');
    }
  });
};
// 取消询盘操作
const cancelInquiry = () => {
  // 如果表单没有被修改过，直接关闭
  if (!isFormChanged()) {
    inquiryDialogVisible.value = false;
    return;
  }

  ElMessageBox.confirm('表单内容已修改，确认取消？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  .then(() => {
    inquiryDialogVisible.value = false;
  })
  .catch(() => {
    // 取消操作
  });
};



// 删除询盘
const deleteInquiry = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条询盘记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await request.delete(`/api/inquiries/${id}`);
    ElMessage.success('询盘删除成功');
    loadInquiries();
  } catch (error) {
    console.error('删除询盘失败:', error);
    if (error !== 'cancel') {
      ElMessage.error('删除询盘失败');
    }
  }
};

// 日期范围变化处理
const onDateRangeChange = (value: [string, string] | null) => {
  if (value) {
    searchForm.value.start_date = value[0];
    searchForm.value.end_date = value[1];
  } else {
    searchForm.value.start_date = '';
    searchForm.value.end_date = '';
  }
};

// 搜索询盘
const searchInquiries = () => {
  currentPage.value = 1;
  loadInquiries();
};

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    area: '',
    contact_person: '',
    company_name: '',
    packaging_product: '',
    machine_type: '',
    inquiry_source: '',
    start_date: '',
    end_date: ''
  };
  dateRange.value = null;
  currentPage.value = 1;
  loadInquiries();
};

// 加载询盘列表
const loadInquiries = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      ...searchForm.value
    };

    const response = await request.get('/api/inquiries', params);
    inquiries.value = response.list || [];
    total.value = response.total || 0;
  } catch (error) {
    console.error('加载询盘列表失败:', error);
    ElMessage.error('加载询盘列表失败');
  } finally {
    loading.value = false;
  }
};

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  loadInquiries();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadInquiries();
};

// 导出数据
const exportData = () => {
  ElMessage.info('数据导出功能待实现');
};

// 地区自动完成查询
const queryArea = (queryString: string, cb: (arg: any) => void) => {
  const results = queryString
    ? presetAreas.value.filter(area => area.toLowerCase().indexOf(queryString.toLowerCase()) === 0)
    : presetAreas.value;

  // 添加输入的值作为选项
  if (queryString && !results.includes(queryString)) {
    results.unshift(queryString);
  }

  cb(results.map(area => ({ value: area })));
};

// 来源自动完成查询
const querySource = (queryString: string, cb: (arg: any) => void) => {
  let results = queryString
    ? presetSources.value.filter(source => source.toLowerCase().indexOf(queryString.toLowerCase()) === 0)
    : presetSources.value;

  // 添加输入的值作为选项
  if (queryString && !results.includes(queryString)) {
    results.unshift(queryString);
  }

  // 同时包含预设值和用户输入
  results = [...new Set(results)]; // 去重

  cb(results.map(source => ({ value: source })));
};

// 比较表单值是否发生变化
const isFormChanged = (): boolean => {
  if (!initialInquiryForm.value) return false;

  // 比较所有字段
  return JSON.stringify(inquiryForm.value) !== JSON.stringify(initialInquiryForm.value);
};

// 对话框关闭处理
const handleDialogClose = (done: () => void) => {
  // 如果表单没有被修改过，直接关闭
  if (!isFormChanged()) {
    done();
    return;
  }

  ElMessageBox.confirm('表单内容已修改，确认关闭？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  .then(() => {
    done();
  })
  .catch(() => {
    // 取消操作
  });
};
// 加载沟通记录
const loadCommunications = async (inquiryId: number) => {
  try {
    const response = await request.get(`/api/inquiries/${inquiryId}/communications`);
    communications.value = response.list || [];
  } catch (error) {
    console.error('加载沟通记录失败:', error);
    ElMessage.error('加载沟通记录失败');
  }
};

// 显示沟通记录对话框
const showCommunicationDialog = async (inquiryId: number) => {
  currentInquiryId.value = inquiryId;
  await loadCommunications(inquiryId);
  communicationDialogVisible.value = true;
};

// 关闭沟通记录对话框
const closeCommunicationDialog = () => {
  communicationDialogVisible.value = false;
  communications.value = [];
  currentInquiryId.value = null;
};

// 显示添加沟通记录对话框
const showAddCommunicationDialog = () => {
  communicationDialogTitle.value = '添加沟通记录';
  editingCommunicationId.value = null;
  communicationForm.value = {
    id: null,
    subject: '',
    content: '',
    communication_date: ''
  };
  addCommunicationDialogVisible.value = true;
};

// 编辑沟通记录
const editCommunication = (comm: any) => {
  communicationDialogTitle.value = '编辑沟通记录';
  editingCommunicationId.value = comm.id;
  communicationForm.value = {
    id: comm.id,
    subject: comm.subject,
    content: comm.content,
    communication_date: comm.communication_date
  };
  addCommunicationDialogVisible.value = true;
};

// 提交沟通记录
const submitCommunication = async () => {
  if (!communicationFormRef.value) return;

  await communicationFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      if (!editingInquiryId.value) {
        ElMessage.error('请先保存询盘信息');
        return;
      }

      communicationSubmitting.value = true;
      try {
        let response;
        if (editingCommunicationId.value) {
          // 更新沟通记录
          response = await request.put(
            `/api/inquiries/${editingInquiryId.value}/communications/${editingCommunicationId.value}`,
            communicationForm.value
          );
          ElMessage.success('沟通记录更新成功');
        } else {
          // 创建沟通记录
          response = await request.post(
            `/api/inquiries/${editingInquiryId.value}/communications`,
            communicationForm.value
          );
          ElMessage.success('沟通记录创建成功');
        }

        // 关闭对话框并重新加载列表
        addCommunicationDialogVisible.value = false;
        await loadCommunications(editingInquiryId.value);

        // 重置表单
        communicationForm.value = {
          id: null,
          subject: '',
          content: '',
          communication_date: ''
        };
        editingCommunicationId.value = null;
      } catch (error) {
        console.error('提交沟通记录失败:', error);
        ElMessage.error('提交沟通记录失败');
      } finally {
        communicationSubmitting.value = false;
      }
    } else {
      ElMessage.error('请填写必填项');
    }
  });
};

// 取消沟通记录操作
const cancelCommunication = () => {
  addCommunicationDialogVisible.value = false;
  communicationForm.value = {
    id: null,
    subject: '',
    content: '',
    communication_date: ''
  };
  editingCommunicationId.value = null;
};

// 删除沟通记录
const deleteCommunication = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条沟通记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    if (!editingInquiryId.value) return;

    await request.delete(`/api/inquiries/${editingInquiryId.value}/communications/${id}`);
    ElMessage.success('沟通记录删除成功');
    await loadCommunications(editingInquiryId.value);
  } catch (error) {
    console.error('删除沟通记录失败:', error);
    if (error !== 'cancel') {
      ElMessage.error('删除沟通记录失败');
    }
  }
};
// 显示日志对话框
const showInquiryLogs = async () => {
  if (!isCurrentUserAdmin.value) {
    ElMessage.error('您没有权限查看日志');
    return;
  }

  try {
    logLoading.value = true;
    const response = await request.get('/api/inquiry-logs', {
      page: 1,
      size: 100
    });
    inquiryLogs.value = response.list || [];
    logDialogVisible.value = true;
  } catch (error) {
    console.error('加载询盘日志失败:', error);
    ElMessage.error('加载询盘日志失败');
  } finally {
    logLoading.value = false;
  }
};

// 关闭日志对话框
const closeLogDialog = () => {
  logDialogVisible.value = false;
  inquiryLogs.value = [];
};

// 初始化
onMounted(async () => {
  try {
    const token = localStorage.getItem('oa_token');
    if (token) {
      // 解码JWT token获取用户角色信息
      const payload = JSON.parse(atob(token.split('.')[1]));
      isCurrentUserAdmin.value = payload.user_role === 'admin';
    }
  } catch (error) {
    console.error('解析用户信息失败:', error);
    isCurrentUserAdmin.value = false;
  }

  loadInquiries();

  // 获取预设地区列表
  try {
    const response = await request.get('/api/inquiries', { page: 1, size: 1000 });
    if (response && response.list) {
      // 提取所有不重复的地区
      const areas = [...new Set(response.list.map((item: any) => item.area).filter((area: any) => area))];
      presetAreas.value = areas;
    }
  } catch (error) {
    console.error('获取地区列表失败:', error);
    // 出错时使用空数组
    presetAreas.value = [];
  }
});
</script>

<style scoped>
.inquiry-list-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.filter-card {
  margin-bottom: 20px;
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.communication-section {
  margin-top: 20px;
}

.communication-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.communication-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: bold;
}

.communication-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;
}

.communication-item {
  margin-bottom: 10px;
  padding: 0;
  border-radius: 15px;
}

.communication-content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.subject {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  margin-left: 20px;
}

.communication-actions {
  display: flex;
  gap: 5px;
}

.communication-content {
  margin-left: 10px;
  margin-bottom: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.5;
  padding: 15px 50px;
}

.communication-footer {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  font-size: 12px;
  color: #909399;
}

.date, .creator, .time {
  margin-right: 10px;
}

.no-communications {
  text-align: center;
  color: #909399;
  font-style: italic;
  padding: 20px;
}

.el-icon {
  font-size: 16px;
  cursor: pointer;
  margin-left: 10px;
}
.el-icon.edit {
  background-color: #317050;
  color: #FFFFFF;
  padding: 4px;
  border-radius: 3px;
}
.el-icon.delete {
  background-color: #c76767;
  color: #FFFFFF;
  padding: 4px;
  border-radius: 3px;
}
</style>