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
        <el-table-column label="操作" width="280">
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
            <el-button 
              size="small" 
              type="danger"
              @click="deleteEmployee(scope.row)"
            >
              删除
            </el-button>
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
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showEditDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="updateEmployee">更新</el-button>
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
const newEmployee = ref({
  name: '',
  emp_id: '',
  dept: '',
  user_role: 'user' as 'user' | 'admin'
});
const editEmployee = ref({
  emp_id: '',
  name: '',
  dept: '',
  user_role: 'user' as 'user' | 'admin',
  status: 'active' as 'pending_binding' | 'pending_approval' | 'active' | 'inactive'
});
const employeeFormRef = ref();
const editEmployeeFormRef = ref();

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
    const data = await request.get('/api/employees');
    employees.value = data;
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
      user_role: 'user'
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
    status: employee.status as 'pending_binding' | 'pending_approval' | 'active' | 'inactive'
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
        status: editEmployee.value.status
      });
    } else {
      // ID未修改，正常更新
      await request.put(`/api/employee/${originalEmpId}`, {
        name: editEmployee.value.name,
        dept: editEmployee.value.dept,
        user_role: editEmployee.value.user_role,
        status: editEmployee.value.status
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