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
          <el-descriptions-item label="创建时间">{{ selectedEmployee.create_time ? formatDateTime(selectedEmployee.create_time) : '无记录' }}</el-descriptions-item>
          <el-descriptions-item label="备注信息">{{ selectedEmployee.remarks || '无备注' }}</el-descriptions-item>
          <el-descriptions-item label="TOTP密钥">
            <el-tooltip :content="selectedEmployee.totp_secret || '未设置TOTP密钥'" placement="top">
              <span>{{ selectedEmployee.totp_secret ? selectedEmployee.totp_secret : '未设置TOTP密钥' }}</span>
            </el-tooltip>
          </el-descriptions-item>
        </el-descriptions>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeDetailDialog">关闭</el-button>
          </span>
        </template>
      </el-dialog>