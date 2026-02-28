<template>
  <div class="employee-management-container">
    <CommonHeader title="员工管理" />

    <el-card shadow="hover" class="management-card">
      <template #header>
        <div class="card-header">
          <span>员工管理</span>
          <div>
            <el-button
              v-if="isAdmin"
              type="info"
              @click="showDeviceChangeApprovalDialogFunc"
              :icon="Position"
              style="margin-right: 10px;"
            >
              设备更换审批
            </el-button>

            <el-button
              type="success"
              @click="showRoleManager"
              :icon="Setting"
              style="margin-right: 10px;"
            >
              角色管理
            </el-button>
            <el-button
              v-if="hasEmployeeManagePermission"
              class="button"
              type="primary"
              @click="showCreateDialog = true">
              新增员工
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="employees"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ 'text-align': 'center' }"
        :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
      >
        <el-table-column prop="emp_id" label="员工ID" width="120" align="center" header-align="center" />
        <el-table-column prop="name" label="姓名" width="120" align="center" header-align="center" />
        <el-table-column prop="user_role" label="角色" width="100" align="center" header-align="center">
          <template #default="scope">
            <el-tag :type="getRoleType(scope.row.user_role)">
              {{ getRoleText(scope.row.user_role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录时间" width="180" align="center" header-align="center">
          <template #default="scope">
            {{ scope.row.last_login_time ? formatDateTime(scope.row.last_login_time) : '无记录' }}
          </template>
        </el-table-column>
        <el-table-column label="设备" width="180" align="center" header-align="center">
          <template #default="scope">
            <el-tooltip :content="scope.row.login_device" placement="top" :disabled="!scope.row.login_device || scope.row.login_device.length <= 20">
              <span class="device-text">{{ scope.row.login_device && scope.row.login_device.length > 20 ? scope.row.login_device.substring(0, 20) + '...' : scope.row.login_device || '无设备' }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center" header-align="center">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="showDetails(scope.row)"
              :icon="View"
              circle
            />
            <el-button
              size="small"
              type="info"
              @click="showEditDialog(scope.row)"
              :icon="Edit"
              circle
            />
            <template v-if="isTempEmployee(scope.row.emp_id)">
              <!-- 临时员工的操作：替换设备或删除 -->
              <el-button
                size="small"
                type="warning"
                @click="showReplaceDeviceDialogFunc(scope.row)"
                :icon="Position"
                circle
              />
              <el-button
                size="small"
                type="danger"
                @click="deleteEmployee(scope.row)"
                :icon="Delete"
                circle
              />
            </template>
            <template v-else>
              <!-- 正式员工的操作：删除 -->
              <el-button
                size="small"
                type="danger"
                @click="deleteEmployee(scope.row)"
                :icon="Delete"
                circle
              />
              <el-button
                size="small"
                type="primary"
                v-if="scope.row.status === 'pending_approval'"
                @click="activateEmployee(scope.row)"
                :icon="CircleCheck"
                circle
              />
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 详情弹窗 -->
      <el-dialog
        v-model="detailDialogVisible"
        title="员工详情"
        width="600px"
        :before-close="closeDetailDialog"
      >
        <el-descriptions v-if="selectedEmployee" :column="1" border>
          <el-descriptions-item label="员工ID">{{ selectedEmployee.emp_id }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ selectedEmployee.name }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ selectedEmployee.dept || '无部门' }}</el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag :type="getRoleType(selectedEmployee.user_role)">
              {{ getRoleText(selectedEmployee.user_role) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedEmployee.status)">
              {{ getStatusText(selectedEmployee.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag v-if="isTempEmployee(selectedEmployee.emp_id)" type="warning">临时</el-tag>
            <el-tag v-else type="success">正式</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最后登录时间">{{ selectedEmployee.last_login_time ? formatDateTime(selectedEmployee.last_login_time) : '无记录' }}</el-descriptions-item>
          <el-descriptions-item label="登录设备">
            <el-tooltip :content="selectedEmployee.login_device" placement="top" :disabled="!selectedEmployee.login_device || selectedEmployee.login_device.length <= 50">
              <span>{{ selectedEmployee.login_device && selectedEmployee.login_device.length > 50 ? selectedEmployee.login_device.substring(0, 50) + '...' : selectedEmployee.login_device || '无设备' }}</span>
            </el-tooltip>
          </el-descriptions-item>
          <el-descriptions-item label="TOTP密钥">
            <el-tooltip :content="selectedEmployee.totp_secret" placement="top" :disabled="!selectedEmployee.totp_secret || selectedEmployee.totp_secret.length <= 50">
              <span>{{ selectedEmployee.totp_secret && selectedEmployee.totp_secret.length > 50 ? selectedEmployee.totp_secret.substring(0, 50) + '...' : selectedEmployee.totp_secret || '无TOTP密钥' }}</span>
            </el-tooltip>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ selectedEmployee.create_time ? formatDateTime(selectedEmployee.create_time) : '无记录' }}</el-descriptions-item>
          <el-descriptions-item label="备注信息">{{ selectedEmployee.remarks || '无备注' }}</el-descriptions-item>
        </el-descriptions>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeDetailDialog">关闭</el-button>
          </span>
        </template>
      </el-dialog>

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
              <el-option
                v-for="role in roles"
                :key="role.role_name"
                :label="role.description || role.role_name"
                :value="role.role_name"
              />
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
              <el-option
                v-for="role in rolesForEdit"
                :key="role.role_name"
                :label="role.description || role.role_name"
                :value="role.role_name"
              />
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
      <el-dialog v-model="showReplaceDeviceDialog" title="替换设备ID" width="500px">
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
                @click="replaceDeviceId"
                :disabled="!targetEmployeeId"
                style="margin-left: 10px;"
              >
                确认替换
              </el-button>
            </el-form-item>
          </el-form>
          <p style="margin-top: 15px; color: #f56c6c;">
            <el-icon><Warning /></el-icon>
            注意：此操作会将临时员工的设备ID转移到目标员工，并删除该临时员工！
          </p>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showReplaceDeviceDialog = false">取消</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 设备更换申请审批对话框 -->
      <el-dialog v-model="showDeviceChangeApprovalDialog" title="设备更换申请审批" width="700px">
        <div v-if="deviceChangeRequests.length === 0 && !loadingDeviceChangeRequests" class="no-data">
          <el-empty description="暂无设备更换申请" :image-size="100" />
          <p style="text-align: center; margin-top: 10px; color: #909399;">
            员工需要在打卡页面申请更换设备后，才会显示在此处进行审批
          </p>
        </div>
        <el-table
          v-else
          :data="deviceChangeRequests"
          v-loading="loadingDeviceChangeRequests"
          style="width: 100%"
          stripe
          border
          :header-cell-style="{ 'text-align': 'center' }"
          :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
        >
          <el-table-column prop="emp_id" label="员工ID" width="120" align="center" header-align="center" />
          <el-table-column prop="name" label="员工姓名" width="120" align="center" header-align="center" />
          <el-table-column prop="punch_type" label="申请类型" width="150" align="center" header-align="center">
            <template #default="scope">
              <el-tag type="warning">{{ scope.row.punch_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="punch_time" label="申请时间" width="160" align="center" header-align="center" />
          <el-table-column prop="device_id" label="新设备ID" width="200" align="center" header-align="center">
            <template #default="scope">
              <el-tooltip :content="scope.row.device_id" placement="top" :disabled="!scope.row.device_id || scope.row.device_id.length <= 20">
                <span class="device-text">{{ scope.row.device_id && scope.row.device_id.length > 20 ? scope.row.device_id.substring(0, 20) + '...' : scope.row.device_id || '无设备ID' }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" align="center" header-align="center">
            <template #default="scope">
              <el-button
                size="small"
                type="success"
                @click="approveDeviceChange(scope.row.id)"
                :icon="CircleCheck"
                circle
              />
              <el-button
                size="small"
                type="danger"
                @click="rejectDeviceChange(scope.row.id)"
                :icon="Delete"
                circle
              />
            </template>
          </el-table-column>
        </el-table>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showDeviceChangeApprovalDialog = false">关闭</el-button>
          </span>
        </template>
      </el-dialog>



      <!-- 角色管理对话框 -->
      <el-dialog
        v-model="showRoleDialog"
        title="角色管理（查看与删除角色）"
        width="800px"
        :before-close="closeRoleDialog"
      >
        <div class="role-management">
          <div class="role-header">
            <el-button type="primary" @click="showCreateRoleWithPermissions()">
              <el-icon><Edit /></el-icon>
              添加角色
            </el-button>
          </div>

          <el-table
            :data="roles"
            v-loading="loadingRoles"
            style="width: 100%; margin-top: 20px;"
            stripe
            border
            :header-cell-style="{ 'text-align': 'center' }"
            :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
          >
            <!-- <el-table-column prop="role_name" label="角色英文" width="150" align="center" header-align="center">
              <template #default="scope">
                {{ scope.row.role_name }}
              </template>
            </el-table-column> -->
            <el-table-column prop="description" label="角色" width="200" align="center" header-align="center">
              <template #default="scope">
                <el-tag
                  :type="scope.row.role_name === 'admin' ? 'success' :  'warning' "
                >
                  {{ scope.row.description }}（{{scope.row.role_name}}）
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="permissions_count" label="权限数量" width="120" align="center" header-align="center" />
            <el-table-column label="操作" width="200" align="center" header-align="center">
              <template #default="scope">
                <el-button
                  size="small"
                  type="primary"
                  @click="showEditRoleDialog(scope.row)"
                  :icon="Edit"
                  circle
                />
                <el-button
                  size="small"
                  type="danger"
                  @click="deleteRole(scope.row)"
                  :icon="Delete"
                  circle
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeRoleDialog">关闭</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 添加角色对话框 -->
      <el-dialog v-model="showCreateRoleDialog" title="添加角色" width="500px">
        <el-form :model="newRole" ref="roleFormRef" label-width="100px">
          <el-form-item label="角色中文" prop="description" :rules="[{ required: true, message: '请输入角色中文名称', trigger: 'blur' }]">
            <el-input v-model="newRole.role_name" placeholder="请输入角色名称，如：业务专员、运营专员、跟单专员、美工专员等" />
          </el-form-item>
          <el-form-item label="角色英文" prop="role_name" :rules="[{ required: true, message: '请输入角色英文名称', trigger: 'blur' }]">
            <el-input v-model="newRole.role_name" placeholder="请输入角色名称，如：sales、ops、order、design等" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showCreateRoleDialog = false">取消</el-button>
            <el-button type="primary" @click="createRole">创建</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 统一角色管理对话框 -->
      <el-dialog
        v-model="showRoleManagementDialog"
        :title="isEditingRole ? '编辑角色' : '创建角色'"
        width="900px"
        :before-close="() => { showRoleManagementDialog = false; }"
      >
        <el-form :model="currentRole" label-width="100px">
          <el-form-item label="角色名字" required>
            <el-input
              v-model="currentRole.description"
              placeholder="请输入角色名字，如：运营专员、跟单专员、美工专员..."
              :rows="2"
            />
          </el-form-item>
          <el-form-item label="角色英文" required>
            <el-input
              v-model="currentRole.role_name"
              :placeholder="isEditingRole ? '角色名称不可修改' : '请输入角色英文，如：ops、order、design...'"
            />
          </el-form-item>
        </el-form>

        <!-- 权限选择区域 -->
        <div class="permissions-section" style="margin-top: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h4>权限配置</h4>
            <el-button size="small" @click="selectAllPermissions">【{{ allBtnText }}】所有权限</el-button>
          </div>
          <el-table
            :data="allPermissions"
            v-loading="loadingAllPermissions"
            style="width: 100%; margin-top: 10px;"
            border
            :header-cell-style="{ 'text-align': 'center' }"
            :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
            max-height="500px"
            scrollbar-always-on
          >
            <el-table-column prop="route_label" label="路由名称" width="200" align="center" header-align="center" />
            <el-table-column label="拥有权限" width="120" align="center" header-align="center">
              <template #default="scope">
                <el-checkbox v-model="scope.row.is_active" @change="handlePermissionChange(scope.row)" />
              </template>
            </el-table-column>
          </el-table>
        </div>

        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showRoleManagementDialog = false">取消</el-button>
            <el-button
              type="primary"
              @click="isEditingRole ? updateRole() : createRole()"
            >
              {{ isEditingRole ? '更新' : '创建' }}
            </el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Warning, View, Edit, Delete, Position, CircleCheck, Setting } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { Employee } from '@/types';
import CommonHeader from '@/components/CommonHeader.vue';
import { getCurrentUserRole, hasModulePermission, ModuleNames } from '@/utils/authUtils';

// 路由实例
const router = useRouter();

// 用于存储原始员工ID
let originalEmpId = '';

// 检查当前用户是否为管理员
const isAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'admin';
});

// ========== 权限判断计算属性 ==========
const hasEmployeeManagePermission = computed(() => {
  return hasModulePermission(ModuleNames.EMPLOYEE_MANAGE, 'edit');
});

// 员工数据
const employees = ref<Employee[]>([]);
const loading = ref(false);
const showCreateDialog = ref(false);
const showEditDialogVisible = ref(false);
const showDeviceDialog = ref(false);
const showReplaceDeviceDialog = ref(false); // 设备替换对话框
const showDeviceChangeApprovalDialog = ref(false); // 设备更换申请审批对话框
const detailDialogVisible = ref(false); // 详情对话框
const devices = ref<any[]>([]);
const currentEmployee = ref<Employee | null>(null);
const targetEmployeeId = ref(''); // 目标员工ID
const selectedEmployee = ref<Employee | null>(null); // 选中的员工（用于详情）
const deviceChangeRequests = ref<any[]>([]); // 设备更换申请列表
const loadingDeviceChangeRequests = ref(false); // 加载设备更换申请的加载状态



// 角色管理相关数据
const showRoleDialog = ref(false);
const roles = ref<any[]>([]);
const loadingRoles = ref(false);

// 编辑员工时的角色列表（独立于角色管理的角色列表）
const rolesForEdit = ref<any[]>([]);

// 角色映射，用于显示角色描述
const roleMap = ref<{[key: string]: string}>({});

const roleFormRef = ref();
const showCreateRoleDialog = ref(false);

// 统一角色管理对话框相关数据
const showRoleManagementDialog = ref(false);
const isEditingRole = ref(false); // 标记是创建还是编辑模式
const currentRole = ref({
  role_name: '',
  description: ''
});
const allPermissions = ref<any[]>([]); // 所有权限列表
const selectedPermissions = ref<any[]>([]); // 与allPermissions同步的权限
const loadingAllPermissions = ref(false);
const allBtnText = ref('全选'); // 全选角色权限按钮

const newEmployee = ref({
  name: '',
  emp_id: '',
  dept: '',
  user_role: 'user' as 'user' | 'admin' | 'sales',
  remarks: ''
});

// 添加newRole响应式变量
const newRole = ref({
  role_name: '',
  description: ''
});
const editEmployee = ref({
  emp_id: '',
  name: '',
  dept: '',
  user_role: 'user' as 'user' | 'admin' | 'sales',
  status: 'active' as 'active' | 'pending_binding' | 'pending_approval' | 'inactive',
  remarks: '',
  last_login_time: '',
  login_device: ''
});
const newDeviceForm = ref({
          device_id: '',  device_ip: '',
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
      user_role: 'user' as 'user' | 'admin' | 'sales',
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

// 激活员工账号
const activateEmployee = async (employee: Employee) => {
  try {
    await ElMessageBox.confirm(
      `确定要激活员工 ${employee.name}(${employee.emp_id}) 的账号吗？激活后员工可申请绑定TOTP验证器`,
      '确认激活账号',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 激活员工账号，状态从"待审批"变为"待绑定"
    await request.put(`/api/employee/${employee.emp_id}`, { status: 'pending_binding' });
    ElMessage.success('员工账号激活成功');
    fetchEmployees(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('员工账号激活失败');
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
        type: 'error'
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
    user_role: employee.user_role as 'user' | 'admin' | 'sales',
    status: employee.status as 'pending_binding' | 'pending_approval' | 'active' | 'inactive',
    remarks: employee.remarks || '',
    last_login_time: employee.last_login_time || '',
    login_device: employee.login_device || ''
  };
  // 深度复制当前角色列表，避免角色管理操作影响编辑对话框
  rolesForEdit.value = JSON.parse(JSON.stringify(roles.value));
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
onMounted(async () => {
  // 先获取员工列表
  await fetchEmployees();
  // 获取角色列表
  await fetchRoles();
  // 初始化编辑员工时的角色列表
  rolesForEdit.value = JSON.parse(JSON.stringify(roles.value));
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

// 替换设备ID
const replaceDeviceId = async () => {
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
    // 注意：API端点名为replace-device-mac，但实际操作的是device_id字段
    const response: any = await request.post('/api/replace-device-mac', {
      temp_emp_id: currentEmployee.value.emp_id,
      target_emp_id: targetEmployeeId.value
    });

    // 如果请求成功，拦截器会自动处理并返回data部分
    ElMessage.success(`设备ID替换成功：${targetEmployeeId.value}的设备已更新，临时员工已删除`);
    showReplaceDeviceDialog.value = false;
    fetchEmployees(); // 刷新列表
  } catch (error: any) {
    // 检查是否是取消操作
    if (error !== 'cancel') {
      // 错误已经通过拦截器处理，这里不再需要特殊处理
      // 拦截器会自动显示格式化的错误消息
    }
  }
};

// 获取角色文本
const getRoleText = (role: string) => {
  // 使用角色映射中的描述
  return roleMap.value[role] || role;
};

// 获取角色类型
const getRoleType = (role: string) => {
  switch (role) {
    case 'admin': return 'danger';
    case 'sales': return 'warning';
    case 'user': return 'success';
    default: return 'info';
  }
};

// 定义模块名称常量
// const MODULE_CONSTANTS = {
//   employee_manage: '员工管理',
//   device_manage: '设备管理',
//   log_manage: '日志管理',
//   report_stat: '报表统计',
//   order_manage: '订单管理',
//   expense_manage: '费用管理',
//   inquiry_manage: '询盘管理',
//   machine_manage: '机器管理',
//   machine_list: '机器列表',
//   photo_manage: '照片管理',
//   video_manage: '视频管理',
//   display_file_manage: '展示文件管理',
//   order_progress_manage: '订单进度管理',
//   order_status_manage: '订单状态管理',
//   punch_manage: '打卡管理',
//   auth_manage: '认证管理',
//   upload_manage: '上传管理',
//   user_manage: '用户管理',
//   permission_manage: '权限管理'
// };

// // 获取模块名称显示文本
// const getModuleNameText = (moduleName: string) => {
//   return MODULE_CONSTANTS[moduleName as keyof typeof MODULE_CONSTANTS] || moduleName;
// };

// 显示详情
const showDetails = (employee: Employee) => {
  selectedEmployee.value = employee;
  detailDialogVisible.value = true;
};

// 关闭详情弹窗
const closeDetailDialog = () => {
  detailDialogVisible.value = false;
  selectedEmployee.value = null;
};

// 获取设备更换申请列表
const fetchDeviceChangeRequests = async () => {
  loadingDeviceChangeRequests.value = true;
  try {
    // 获取所有打卡记录，然后筛选出设备更换申请
    const response: any = await request.get('/api/punch-records', {
      params: {
        punch_type: '设备更换申请',
        page: 1,
        size: 100  // 获取所有申请
      }
    });

    if (response && response.list) {
      deviceChangeRequests.value = response.list;
    } else {
      deviceChangeRequests.value = [];
    }
  } catch (error) {
    ElMessage.error('获取设备更换申请列表失败');
    console.error('Error fetching device change requests:', error);
    deviceChangeRequests.value = [];
  } finally {
    loadingDeviceChangeRequests.value = false;
  }
};

// 显示设备更换申请审批对话框
const showDeviceChangeApprovalDialogFunc = async () => {
  await fetchDeviceChangeRequests();
  showDeviceChangeApprovalDialog.value = true;
};

// 批准设备更换申请
const approveDeviceChange = async (requestId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要批准此设备更换申请吗？',
      '确认批准',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await request.post('/api/approve-device-change', {
      request_id: requestId
    });

    ElMessage.success('设备更换申请已批准');
    await fetchDeviceChangeRequests(); // 刷新列表
    fetchEmployees(); // 也刷新员工列表以确保最新状态
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批准设备更换申请失败');
    }
  }
};

// 拒绝设备更换申请
const rejectDeviceChange = async (requestId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要拒绝此设备更换申请吗？',
      '确认拒绝',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await request.post('/api/reject-device-change', {
      request_id: requestId
    });

    ElMessage.success('设备更换申请已拒绝');
    await fetchDeviceChangeRequests(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('拒绝设备更换申请失败');
    }
  }
};



// 显示角色管理对话框
const showRoleManager = async () => {
  // 只有在角色列表为空时才获取数据
  if (!roles.value || roles.value.length === 0) {
    await fetchRoles();
  }
  showRoleDialog.value = true;
};

// 获取角色列表
const fetchRoles = async () => {
  loadingRoles.value = true;
  try {
    // 获取所有角色信息，只返回不重复的role_name和对应的role_description
    const response: any = await request.get('/api/user/permission/roles');
    // 由于request.ts会自动解包data，response直接就是数据数组
    if (response && Array.isArray(response)) {
      // 创建角色列表
      roles.value = response.map((role: any) => ({
        role_name: role.role_name,
        description: role.role_description,
        permissions_count: role.permissions_count || 0  // 从响应中获取权限计数
      }));

      // 更新角色映射
      const newRoleMap: {[key: string]: string} = {};
      response.forEach((role: any) => {
        newRoleMap[role.role_name] = role.role_description || role.role_name;
      });
      roleMap.value = newRoleMap;
    }
  } catch (error) {
    console.error('获取角色列表失败:', error);
    // 如果API调用失败，使用默认值
    roles.value = [
      { role_name: 'admin', description: '系统管理员', permissions_count: '全部' },
      { role_name: 'sales', description: '业务员', permissions_count: 0 },
      { role_name: 'user', description: '普通用户', permissions_count: 0 }
    ];

    // 更新角色映射为默认值
    roleMap.value = {
      'admin': '管理员',
      'sales': '业务员',
      'user': '普通用户'
    };
  } finally {
    loadingRoles.value = false;
  }
};


// 获取角色权限数量
const getRolePermissionsCount = async (roleName: string) => {
  try {
    const response: any = await request.get('/api/user/permission/role-permissions', { params: { role_name: roleName } });
    // 由于request.ts会自动解包data，response直接就是权限数组
    if (response && Array.isArray(response)) {
      return response.length;
    }
    return 0;
  } catch (error) {
    console.error(`获取角色 ${roleName} 权限数量失败:`, error);
    return 0;
  }
};

// 显示统一角色管理对话框（创建新角色）
const showCreateRoleWithPermissions = async () => {
  isEditingRole.value = false;
  currentRole.value = {
    role_name: '',
    description: ''
  };

  // 加载所有权限（用于新角色）
  await loadAllPermissionsForRole();

  showRoleManagementDialog.value = true;
};

// 创建角色
const createRole = async () => {
        // 如果是编辑模式，只更新描述和权限
        if (isEditingRole.value) {
            if (!currentRole.value.role_name || currentRole.value.role_name.length < 2) {
                ElMessage.error('角色英文名称长度至少为2个字符');
                return;
            }

            // 更新角色描述
            await request.post('/api/user/permission/update-role-description', {
                role_name: currentRole.value.role_name,
                role_description: currentRole.value.description || `${currentRole.value.role_name}角色`
            });
        } else {
            // 验证角色名称
            if (!currentRole.value.role_name || currentRole.value.role_name.length < 2) {
                ElMessage.error('角色英文名称长度至少为2个字符');
                return;
            }

            // 创建新角色（通过更新角色描述来创建）
            await request.post('/api/user/permission/update-role-description', {
                role_name: currentRole.value.role_name,
                role_description: currentRole.value.description || `${currentRole.value.role_name}角色`
            });
        }

        // 更新角色权限
        const selectedRouteNames = allPermissions.value
            .filter(perm => perm.is_active)  // 只选择已激活的权限
            .map(perm => perm.route_name);
        await request.post('/api/user/permission/update-role-permissions', {
            role_name: currentRole.value.role_name,
            permissions: selectedRouteNames
        });

        showRoleManagementDialog.value = false;
        fetchRoles();
};



// 显示编辑角色对话框

const showEditRoleDialog = async (role: any) => {

  // if (role.role_name === 'admin' || role.role_name === 'sales' || role.role_name === 'user') {

  //   ElMessage.warning('系统内置角色不能编辑');

  //   return;

  // }



  isEditingRole.value = true;

  currentRole.value = { ...role };



  // 加载所有权限并设置当前角色的权限

  await loadAllPermissionsForRole(role.role_name);



  showRoleManagementDialog.value = true;

};
// 编辑角色（重定向到权限管理界面并预设角色）
const editRole = async (roleName: string) => {
  // 关闭角色管理对话框
  showRoleDialog.value = false;
  // 短暂延迟以确保对话框关闭，然后显示权限管理对话框并预设角色
  setTimeout(() => {

  }, 100);
};

// 加载所有权限并设置当前角色的权限
const loadAllPermissionsForRole = async (roleName?: string) => {
  loadingAllPermissions.value = true;
  try {
    let permissionsData = [];

    // 获取所有可用的路由权限
    const allRoutesResponse: any = await request.get('/api/user/permission/all-routes');
    const allRoutes = allRoutesResponse || [];

    if (roleName) {
      // 获取指定角色的权限
      const response: any = await request.get('/api/user/permission/role-permissions', {
        params: { role_name: roleName }
      });

      if (response && Array.isArray(response)) {
        // 格式化权限数据，标记角色已有的权限
        permissionsData = allRoutes.map((route: any) => {
          const hasPermission = response.includes(route.route_name);
          return {
            route_name: route.route_name,
            route_label: route.route_label,
            is_active: hasPermission
          };
        });
      }
    } else {
      // 如果没有指定角色，初始化所有权限为未选择状态
      permissionsData = allRoutes.map((route: any) => ({
        route_name: route.route_name,
        route_label: route.route_label,
        is_active: false  // 默认未选择
      }));
    }

    // 设置所有权限和选中权限
    allPermissions.value = [...permissionsData];
    selectedPermissions.value = [...permissionsData]; // 包含所有权限
    updateAllBtnText(); // 更新按钮文本

  } catch (error) {
    console.error('加载权限失败:', error);
    // 使用默认权限列表
    allPermissions.value = [
      { route_name: 'employee_manage', route_label: '员工管理', is_active: false },
      { route_name: 'device_manage', route_label: '设备管理', is_active: false },
      { route_name: 'permission_manage', route_label: '权限管理', is_active: false },
      { route_name: 'log_manage', route_label: '日志管理', is_active: false },
      { route_name: 'report_stat', route_label: '报表统计', is_active: false },
      { route_name: 'expense_manage', route_label: '费用管理', is_active: false },
      { route_name: 'inquiry_manage', route_label: '询盘管理', is_active: false },
      { route_name: 'machine_manage', route_label: '机器管理', is_active: false },
      { route_name: 'machine_list', route_label: '机器列表', is_active: false },
      { route_name: 'order_manage', route_label: '订单管理', is_active: false },
      { route_name: 'order_status_manage', route_label: '订单状态管理', is_active: false },
      { route_name: 'photo_manage', route_label: '照片管理', is_active: false },
      { route_name: 'video_manage', route_label: '视频管理', is_active: false },
      { route_name: 'punch_manage', route_label: '打卡管理', is_active: false },
      { route_name: 'display_file_manage', route_label: '展示文件管理', is_active: false },
      { route_name: 'order_progress_manage', route_label: '订单进度管理', is_active: false },
      { route_name: 'user_manage', route_label: '用户管理', is_active: false },
      { route_name: 'permission_manage', route_label: '权限管理', is_active: false }
    ];

    selectedPermissions.value = [...allPermissions.value];
  } finally {
    loadingAllPermissions.value = false;
  }
};

// 获取模块的显示名称
const getModuleLabel = (moduleName: string) => {
  const moduleLabels: { [key: string]: string } = {
    'employee_manage': '员工管理',
    'device_manage': '设备管理',
    'log_manage': '日志管理',
    'report_stat': '报表统计',
    'expense_manage': '费用管理',
    'inquiry_manage': '询盘管理',
    'machine_manage': '机器管理',
    'machine_list': '机器列表',
    'order_manage': '订单管理',
    'order_status_manage': '订单状态管理',
    'photo_manage': '照片管理',
    'video_manage': '视频管理',
    'punch_manage': '打卡管理',
    'display_file_manage': '展示文件管理',
    'order_progress_manage': '订单进度管理',
    'user_manage': '用户管理',
    'permission_manage': '权限管理',
  };

  return moduleLabels[moduleName] || moduleName;
};

// 为单个模块设置所有权限
    const setModuleAllPermissions = (module: any, checked: boolean) => {
        // 对于路由权限，只需设置is_active属性
        module.is_active = checked;
        updateAllBtnText(); // 更新按钮文本
    };

    // 处理权限状态变化
    const handlePermissionChange = (permission: any) => {
        // 由于allPermissions现在用于UI显示，只需确保UI更新即可
        // selectedPermissions用于收集所有权限，但仅在更新时筛选激活的权限
        updateAllBtnText(); // 更新按钮文本
    };

    const selectAllPermissions = () => {
        // 获取按钮当前状态（全选还是取消全选）
        const allSelected = allPermissions.value.length > 0 &&
                          allPermissions.value.every(perm => perm.is_active);

        if (!allSelected) {
            // 全选 - 更新allPermissions中所有权限的is_active为true
            allPermissions.value.forEach(permission => {
                permission.is_active = true;
            });
            // 同步更新selectedPermissions
            selectedPermissions.value.forEach(permission => {
                permission.is_active = true;
            });
        } else {
            // 取消全选 - 更新allPermissions中所有权限的is_active为false
            allPermissions.value.forEach(permission => {
                permission.is_active = false;
            });
            // 同步更新selectedPermissions
            selectedPermissions.value.forEach(permission => {
                permission.is_active = false;
            });
        }
        updateAllBtnText(); // 更新按钮文本
    };

    const updateAllBtnText = () => {
        const allSelected = allPermissions.value.length > 0 &&
                          allPermissions.value.every(perm => perm.is_active);
        allBtnText.value = allSelected ? '取消全选' : '全选';
    };
// 更新角色权限
    const updateRole = async () => {
      try {
        if (!currentRole.value.role_name || currentRole.value.role_name.length < 2) {
          ElMessage.error('角色名至少需要2个字符');
          return;
        }

        // 更新角色描述
        await request.post('/api/user/permission/update-role-description', {
          role_name: currentRole.value.role_name,
          role_description: currentRole.value.description || `${currentRole.value.role_name}角色`
        });

        // 更新角色权限
        const selectedRouteNames = allPermissions.value
            .filter(perm => perm.is_active)  // 只选择已激活的权限
            .map(perm => perm.route_name);
        await request.post('/api/user/permission/update-role-permissions', {
          role_name: currentRole.value.role_name,
          permissions: selectedRouteNames
        });
    ElMessage.success('角色更新成功');
    showRoleManagementDialog.value = false;

    // 重新加载角色列表
    await fetchRoles();
    // 更新编辑员工时使用的角色列表
    rolesForEdit.value = JSON.parse(JSON.stringify(roles.value));
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      ElMessage.error('更新角色失败');
    }
  }
};

// 删除角色
const deleteRole = async (role: any) => {

  try {
    await ElMessageBox.confirm(
      `确定要删除角色 ${role.role_name} 吗？此操作将同时删除该角色的所有权限配置！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    // 调用后端删除角色API
    await request.post('/api/user/permission/delete-role', {
      role_name: role.role_name
    });

    await fetchRoles();
    // 更新编辑员工时使用的角色列表
    rolesForEdit.value = JSON.parse(JSON.stringify(roles.value));
    ElMessage.success('角色删除成功');
  } catch (error: any) {
    if (error?.message?.includes('用户')) {
      ElMessage.error(error.message || '删除失败：角色下有用户');
    } else if (error?.message !== '取消' && error !== 'cancel') {
      ElMessage.error(error.message || '删除角色失败');
    }
    console.log('取消删除或删除失败:', error);
  }
};

// 关闭角色管理对话框
const closeRoleDialog = () => {
  showRoleDialog.value = false;
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

.device-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.no-data {
  text-align: center;
  padding: 40px 0;
}


</style>