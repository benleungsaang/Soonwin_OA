<template>
  <div class="employee-management-container">
    <el-page-header content="员工管理" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>

    <el-card shadow="hover" class="management-card">
      <template #header>
        <div class="card-header">
          <span>员工管理</span>
          <el-button class="button" type="primary" @click="showCreateDialog = true">
            新增员工
          </el-button>
        </div>
      </template>

      <el-table 
        :data="employees" 
        v-loading="loading"
        style="width: 100%"
        stripe
        border
      >
        <el-table-column prop="emp_id" label="员工ID" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="dept" label="部门" width="120" />
        <el-table-column prop="is_temp" label="类型" width="80">
          <template #default="scope">
            <el-tag v-if="isTempEmployee(scope.row.emp_id)" type="warning">临时</el-tag>
            <el-tag v-else type="success">正式</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_role" label="角色" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.user_role === 'admin' ? 'danger' : 'success'">
              {{ scope.row.user_role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag 
              :type="getStatusType(scope.row.status)"
            >
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录时间" width="180">
          <template #default="scope">
            {{ scope.row.last_login_time ? formatDateTime(scope.row.last_login_time) : '无记录' }}
          </template>
        </el-table-column>
        <el-table-column prop="login_device" label="登录设备" width="180" />
        <el-table-column prop="create_time" label="创建时间" width="160" />
        <el-table-column prop="remarks" label="备注信息" width="200">
          <template #default="scope">
            <span v-if="scope.row.remarks && scope.row.remarks.length > 50">
              {{ scope.row.remarks.substring(0, 50) }}...
              <el-popover
                effect="light"
                trigger="hover"
                placement="top"
                :width="300"
              >
                <template #reference>
                  <el-link type="primary" :underline="false">查看</el-link>
                </template>
                <div>{{ scope.row.remarks }}</div>
              </el-popover>
            </span>
            <span v-else>{{ scope.row.remarks || '无备注' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="380">
          <template #default="scope">
            <el-button 
              size="small" 
              type="primary"
              :disabled="scope.row.status !== 'pending_approval'"
              @click="approveEmployee(scope.row)"
            >
              审批
            </el-button>
            <el-button 
              size="small" 
              type="info"
              @click="showEditDialog(scope.row)"
            >
              编辑
            </el-button>
            <template v-if="isTempEmployee(scope.row.emp_id)">
              <!-- 临时员工的操作：替换设备或删除 -->
              <el-button 
                size="small" 
                type="warning"
                @click="showReplaceDeviceDialogFunc(scope.row)"
              >
                替换到已有设备
              </el-button>
              <el-button 
                size="small" 
                type="danger"
                @click="deleteEmployee(scope.row)"
              >
                删除
              </el-button>
            </template>
            <template v-else>
              <!-- 正式员工的操作：删除 -->
              <el-button 
                size="small" 
                type="danger"
                @click="deleteEmployee(scope.row)"
              >
                删除
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 新增员工对话框 -->
      <el-dialog v-model="showCreateDialog" title="新增员工" width="500px">
        <el-form :model="newEmployee" :rules="employeeRules" ref="employeeFormRef" label-width="100px">
          <el-form-item label="姓名" prop="name">
            <el-input v-model="newEmployee.name" placeholder="请输入员工姓名" />
          </el-form-item>
          <el-form-item label="员工ID" prop="emp_id">
            <el-input v-model="newEmployee.emp_id" placeholder="请输入员工ID" />
          </el-form-item>
          <el-form-item label="部门" prop="dept">
            <el-input v-model="newEmployee.dept" placeholder="请输入部门" />
          </el-form-item>
          <el-form-item label="角色" prop="user_role">
            <el-select v-model="newEmployee.user_role" placeholder="请选择角色">
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注信息">
            <el-input 
              v-model="newEmployee.remarks" 
              placeholder="请输入备注信息" 
              type="textarea"
              :rows="3"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showCreateDialog = false">取消</el-button>
            <el-button type="primary" @click="createEmployee">创建</el-button>
          </span>
        </template>
      </el-dialog>
      
      <!-- 编辑员工对话框 -->
      <el-dialog v-model="showEditDialogVisible" title="编辑员工信息" width="500px">
        <el-form :model="editEmployee" :rules="employeeRules" ref="editEmployeeFormRef" label-width="100px">
          <el-form-item label="员工ID" prop="emp_id">
            <el-input v-model="editEmployee.emp_id" placeholder="请输入员工ID" />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="editEmployee.name" placeholder="请输入员工姓名" />
          </el-form-item>
          <el-form-item label="部门" prop="dept">
            <el-input v-model="editEmployee.dept" placeholder="请输入部门" />
          </el-form-item>
          <el-form-item label="角色" prop="user_role">
            <el-select v-model="editEmployee.user_role" placeholder="请选择角色">
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态" prop="status">
            <el-select v-model="editEmployee.status" placeholder="请选择状态">
              <el-option label="待绑定" value="pending_binding" />
              <el-option label="待审批" value="pending_approval" />
              <el-option label="已激活" value="active" />
              <el-option label="已停用" value="inactive" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注信息">
            <el-input 
              v-model="editEmployee.remarks" 
              placeholder="请输入备注信息" 
              type="textarea"
              :rows="3"
            />
          </el-form-item>
          <el-form-item label="最后登录时间">
            <el-input v-model="editEmployee.last_login_time" placeholder="最后登录时间" readonly />
          </el-form-item>
          <el-form-item label="登录设备">
            <el-input v-model="editEmployee.login_device" placeholder="登录设备" readonly />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showEditDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="updateEmployee">更新</el-button>
          </span>
        </template>
      </el-dialog>
      
      <!-- 替换设备对话框 -->
      <el-dialog v-model="showReplaceDeviceDialog" title="替换设备MAC" width="500px">
        <div v-if="currentEmployee">
          <p>将临时员工 <strong>{{ currentEmployee.name }}</strong> (ID: {{ currentEmployee.emp_id }}) 的设备转移至：</p>
          <el-form label-width="120px" style="margin-top: 20px;">
            <el-form-item label="目标员工ID：">
              <el-input 
                v-model="targetEmployeeId" 
                placeholder="请输入目标员工ID"
                style="width: 200px;"
              />
              <el-button 
                type="primary" 
                @click="replaceDeviceMac" 
                :disabled="!targetEmployeeId"
                style="margin-left: 10px;"
              >
                确认替换
              </el-button>
            </el-form-item>
          </el-form>
          <p style="margin-top: 15px; color: #f56c6c;">
            <el-icon><Warning /></el-icon>
            注意：此操作会将临时员工的设备MAC转移到目标员工，并删除该临时员工！
          </p>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showReplaceDeviceDialog = false">取消</el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Warning } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { Employee } from '@/types';

// 路由实例
const router = useRouter();

// 用于存储原始员工ID
let originalEmpId = '';

// 员工数据
const employees = ref<Employee[]>([]);
const loading = ref(false);
const showCreateDialog = ref(false);
const showEditDialogVisible = ref(false);
const showDeviceDialog = ref(false);
const showReplaceDeviceDialog = ref(false); // 设备替换对话框
const devices = ref<any[]>([]);
const currentEmployee = ref<Employee | null>(null);
const targetEmployeeId = ref(''); // 目标员工ID
const newEmployee = ref({
  name: '',
  emp_id: '',
  dept: '',
  user_role: 'user' as 'user' | 'admin',
  remarks: ''
});
const editEmployee = ref({
  emp_id: '',
  name: '',
  dept: '',
  user_role: 'user' | 'admin',
  status: 'active' | 'pending_binding' | 'pending_approval' | 'inactive',
  remarks: '',
  last_login_time: '',
  login_device: ''
});
const newDeviceForm = ref({
  device_mac: '',
  device_ip: '',
  device_type: 'Mobile',
  device_info: ''
});
const employeeFormRef = ref();
const editEmployeeFormRef = ref();
const deviceFormRef = ref();

// 验证规则
const employeeRules = {
  name: [
    { required: true, message: '请输入员工姓名', trigger: 'blur' }
  ],
  emp_id: [
    { required: true, message: '请输入员工ID', trigger: 'blur' }
  ],
  dept: [
    { required: true, message: '请输入部门', trigger: 'blur' }
  ]
};

// 获取员工列表
const fetchEmployees = async () => {
  loading.value = true;
  try {
    const response: any = await request.get('/api/employees');
    // 确保返回的数据结构正确
    if (response && response.list) {
      employees.value = response.list;
    } else {
      // 如果API返回的是直接的员工数组
      employees.value = response || [];
    }
  } catch (error) {
    ElMessage.error('获取员工列表失败');
    console.error('Error fetching employees:', error);
  } finally {
    loading.value = false;
  }
};

// 创建新员工
const createEmployee = async () => {
  try {
    await employeeFormRef.value.validate();
    await request.post('/api/employee', newEmployee.value);
    ElMessage.success('员工创建成功');
    showCreateDialog.value = false;
    // 重置表单
    newEmployee.value = {
      name: '',
      emp_id: '',
      dept: '',
      user_role: 'user',
      remarks: ''
    };
    // 刷新员工列表
    fetchEmployees();
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      ElMessage.error('创建员工失败');
    }
  }
};

// 审批员工
const approveEmployee = async (employee: Employee) => {
  try {
    await ElMessageBox.confirm(
      `确定要审批员工 ${employee.name}(${employee.emp_id}) 吗？`,
      '确认审批',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await request.put(`/api/employee/${employee.emp_id}`, { status: 'active' });
    ElMessage.success('员工审批成功');
    fetchEmployees(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('员工审批失败');
    }
  }
};

// 删除员工
const deleteEmployee = async (employee: Employee) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除员工 ${employee.name}(${employee.emp_id}) 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'danger'
      }
    );
    
    // 调用真正的删除API
    await request.delete(`/api/employee/${employee.emp_id}`);
    ElMessage.success('员工删除成功');
    fetchEmployees(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('员工删除失败');
    }
  }
};

// 显示编辑对话框
const showEditDialog = (employee: Employee) => {
  // 复制员工信息到编辑表单
  editEmployee.value = {
    emp_id: employee.emp_id,
    name: employee.name,
    dept: employee.dept || '',
    user_role: employee.user_role as 'user' | 'admin',
    status: employee.status as 'pending_binding' | 'pending_approval' | 'active' | 'inactive',
    remarks: employee.remarks || '',
    last_login_time: employee.last_login_time || '',
    login_device: employee.login_device || ''
  };
  // 保存原始ID用于更新
  originalEmpId = employee.emp_id;
  showEditDialogVisible.value = true;
};

// 更新员工信息
const updateEmployee = async () => {
  try {
    await editEmployeeFormRef.value.validate();
    
    // 如果员工ID被修改，则需要特殊处理
    if (originalEmpId !== editEmployee.value.emp_id) {
      // 首先更新员工信息（不包括ID）
      await request.put(`/api/employee/${originalEmpId}`, {
        emp_id: editEmployee.value.emp_id,  // 新ID作为数据的一部分
        name: editEmployee.value.name,
        dept: editEmployee.value.dept,
        user_role: editEmployee.value.user_role,
        status: editEmployee.value.status,
        remarks: editEmployee.value.remarks
      });
    } else {
      // ID未修改，正常更新
      await request.put(`/api/employee/${originalEmpId}`, {
        name: editEmployee.value.name,
        dept: editEmployee.value.dept,
        user_role: editEmployee.value.user_role,
        status: editEmployee.value.status,
        remarks: editEmployee.value.remarks
      });
    }
    
    ElMessage.success('员工信息更新成功');
    showEditDialogVisible.value = false;
    fetchEmployees(); // 刷新列表
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      ElMessage.error('员工信息更新失败');
    }
  }
};

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'pending_binding': return '待绑定';
    case 'pending_approval': return '待审批';
    case 'active': return '已激活';
    case 'inactive': return '已停用';
    default: return status;
  }
};

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'pending_binding': return 'warning';
    case 'pending_approval': return 'info';
    case 'active': return 'success';
    case 'inactive': return 'danger';
    default: return 'info';
  }
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 组件挂载时获取数据
onMounted(() => {
  fetchEmployees();
});

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '无记录';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  } catch (error) {
    return dateString; // 如果解析失败，返回原始字符串
  }
};

// 检查是否为临时员工
const isTempEmployee = (empId: string) => {
  return empId.startsWith('TEMP_');
};

// 显示设备替换对话框
const showReplaceDeviceDialogFunc = (employee: Employee) => {
  if (!isTempEmployee(employee.emp_id)) {
    ElMessage.warning('只能替换临时员工的设备');
    return;
  }
  currentEmployee.value = employee;
  targetEmployeeId.value = '';
  showReplaceDeviceDialog.value = true;
};

// 替换设备MAC
const replaceDeviceMac = async () => {
  if (!currentEmployee.value || !targetEmployeeId.value) {
    ElMessage.error('请选择临时员工和目标员工');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要将临时员工 ${currentEmployee.value.name}(${currentEmployee.value.emp_id}) 的设备转移到员工ID为 ${targetEmployeeId.value} 的员工，并删除临时员工吗？`,
      '确认替换设备',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 由于request.ts的拦截器会自动处理code=200的情况并返回data部分，
    // 所以这里response将是API返回的data部分
    const response: any = await request.post('/api/replace-device-mac', {
      temp_emp_id: currentEmployee.value.emp_id,
      target_emp_id: targetEmployeeId.value
    });

    // 如果请求成功，拦截器会自动处理并返回data部分
    ElMessage.success(`设备MAC替换成功：${targetEmployeeId.value}的设备已更新，临时员工已删除`);
    showReplaceDeviceDialog.value = false;
    fetchEmployees(); // 刷新列表
  } catch (error: any) {
    // 检查是否是取消操作
    if (error !== 'cancel') {
      // 如果有自定义错误消息，显示它；否则显示通用错误
      const errorMessage = error?.response?.data?.msg || error?.message || '设备替换失败';
      ElMessage.error(errorMessage);
    }
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
.employee-management-container {
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>