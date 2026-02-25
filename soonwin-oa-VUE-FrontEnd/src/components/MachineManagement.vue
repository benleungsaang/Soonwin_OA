<template>
  <div class="machine-management">
    <div class="header-actions">
      <el-button type="primary" @click="showAddMachineDialog">添加机器</el-button>
      <JsonImportExport
        :import-function="importMachinesData"
        :export-function="exportMachinesData"
        export-file-name="machines.json"
        import-success-message="机器数据导入成功"
        export-success-message="机器数据导出成功"
      />
    </div>
    <el-table :data="machines" style="width: 100%" border
    :row-style="{ cursor: 'pointer' }"
    @row-click="handleRowClick"
    >
      <el-table-column prop="thumbnail" label="设备缩略图" width="120">
        <template #default="{ row }">
          <div class="image-placeholder">
            <el-icon><Picture /></el-icon>
            <span>缩略图</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="model" label="设备型号" width="200" />
      <el-table-column prop="packing_speed" label="包装速度" width="150" />
      <el-table-column prop="show_price" label="价格" width="120" />
          <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="showEditMachineDialog(row)">编辑</el-button>
                <el-button v-if="props.isAdmin" size="small" type="danger" @click="deleteMachine(row.model)">删除</el-button>
              </template>
          </el-table-column>    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :background="true"
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      style="margin-top: 20px; justify-content: center; display: flex;"
    />

    <!-- 添加/编辑机器对话框 -->
    <el-dialog
      :title="editingMachine ? '编辑机器' : '添加机器'"
      v-model="showMachineDialog"
      width="60%"
      :before-close="closeMachineDialog"
    >
      <el-form
        :model="machineForm"
        :rules="machineRules"
        ref="machineFormRef"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备型号" prop="model">
              <el-input
                v-model="machineForm.model"
                :disabled="!!editingMachine"
                placeholder="请输入设备型号"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原厂型号" prop="original_model">
              <el-input v-model="machineForm.original_model" placeholder="请输入原厂型号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="成本价格" prop="original_price">
              <el-input-number
                v-model="machineForm.original_price"
                :precision="2"
                :min="0"
                :controls=false
                style="width: 100%;"
                :disabled="!props.isAdmin"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="价格" prop="show_price">
              <el-input-number
                v-model="machineForm.show_price"
                :precision="2"
                :min="0"
                :controls=false
                style="width: 100%;"
                :disabled="!props.isAdmin"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="包装速度" prop="packing_speed">
              <el-input v-model="machineForm.packing_speed" placeholder="请输入包装速度" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总功率" prop="general_power">
              <el-input v-model="machineForm.general_power" placeholder="请输入总功率" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供电规格" prop="power_supply">
              <el-input v-model="machineForm.power_supply" placeholder="请输入供电规格" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="气源要求" prop="air_source">
              <el-input v-model="machineForm.air_source" placeholder="请输入气源要求" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备重量" prop="machine_weight">
              <el-input v-model="machineForm.machine_weight" placeholder="请输入设备重量" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备尺寸" prop="dimensions">
              <el-input v-model="machineForm.dimensions" placeholder="请输入设备尺寸" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="包装材料" prop="package_material">
              <el-input v-model="machineForm.package_material" placeholder="请输入包装材料" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="缩略图路径" prop="image">
              <el-input v-model="machineForm.image" placeholder="请输入缩略图路径" />
            </el-form-item>
          </el-col>
          <el-col
            v-for="(attr, index) in customAttributes"
            :key="index" :span="12">
              <el-form-item :label="attrConfig[attr.key]?.label || attr.key">
              <el-input
                v-model="attr.value"
                :placeholder="attrConfig[attr.key]?.placeholder || `请输入${attr.key}`"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="被添加次数" prop="added_count">
              <span>{{ machineForm.added_count }} 次</span>
            </el-form-item>
          </el-col>
          <!-- <el-col :span="24">
            <el-button @click="addCustomAttribute" style="margin-top: 10px;">
              <el-icon><Plus /></el-icon>
              添加自定义属性
            </el-button>
          </el-col> -->
          <!-- <el-col :span="24">
            <el-form-item label="自定义属性">
              <div class="custom-attributes-section">
                <div
                  v-for="(attr, index) in customAttributes"
                  :key="index"
                  class="custom-attribute-item"
                >
                  <el-input
                    v-model="attr.key"
                    placeholder="属性名"
                    style="width: 200px; margin-right: 10px;"
                  />
                  <el-input
                    v-model="attr.value"
                    placeholder="属性值"
                    style="width: 200px; margin-right: 10px;"
                  />
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeCustomAttribute(index)"
                  >
                    删除
                  </el-button>
                </div>
                <el-button @click="addCustomAttribute" style="margin-top: 10px;">
                  <el-icon><Plus /></el-icon>
                  添加自定义属性
                </el-button>
              </div>
            </el-form-item>
          </el-col> -->
        </el-row>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeMachineDialog">取消</el-button>
          <el-button type="primary" @click="saveMachine">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture } from '@element-plus/icons-vue'
import { getCurrentUserRole } from '@/utils/authUtils';
import { getMachines, createMachine, updateMachine, deleteMachine as deleteMachineAPI, importMachines, importMachinesJson, exportMachinesJson } from '@/utils/request'
import JsonImportExport from '@/components/JsonImportExport.vue'

// 响应式数据
const machines = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 对话框相关
const showMachineDialog = ref(false)
const editingMachine = ref<any>(null)
const machineFormRef = ref()
const machineForm = reactive({
  model: '',
  original_model: '',
  packing_speed: '',
  general_power: '',
  power_supply: '',
  air_source: '',
  machine_weight: '',
  dimensions: '',
  package_material: '',
  image: '',
  added_count: 0,
  original_price: null as number | null,
  show_price: null as number | null,
  custom_attrs: ''
})

const props = defineProps({
  // 是否为管理员
  isAdmin: {
    type: Boolean,
    required: true, // 必填，确保父组件传递
    default: false  // 默认值（防止未传递时出错）
  },
  // 是否登录（有token）
  hasToken: {
    type: Boolean,
    required: true,
    default: false
  }
});

// 自定义属性相关
const customAttributes = ref<{ key: string; value: string }[]>([])

// 表单验证规则
const machineRules = {
  model: [
    { required: true, message: '请输入设备型号', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 获取机器列表
const fetchMachines = async () => {
  loading.value = true
  try {
    const response: any = await getMachines({
      page: currentPage.value,
      per_page: pageSize.value
    })
    // 添加安全检查，确保response存在且为对象
    if (response && typeof response === 'object') {
      machines.value = response.machines || []
      total.value = response.total || 0
    } else {
      console.error('API响应格式错误:', response)
      ElMessage.error('API响应格式错误')
      machines.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取机器列表失败:', error)
    ElMessage.error('获取机器列表失败')
    machines.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 定义行点击处理函数
const handleRowClick = (row) => {
  // 调用编辑弹窗方法，和编辑按钮逻辑一致
  showEditMachineDialog(row);
};

// 显示添加机器对话框
const showAddMachineDialog = () => {
  editingMachine.value = null
  Object.keys(machineForm).forEach(key => {
    if (key === 'added_count') {
      (machineForm as any)[key] = 0
    } else if (key === 'original_price' || key === 'show_price') {
      (machineForm as any)[key] = null
    } else {
      (machineForm as any)[key] = ''
    }
  })
  customAttributes.value = []
  showMachineDialog.value = true
}

// 显示编辑机器对话框
const showEditMachineDialog = (machine: any) => {
  editingMachine.value = { ...machine }
  Object.keys(machineForm).forEach(key => {
    if (key === 'custom_attrs') {
      // 不处理custom_attrs字段，而是单独处理
    } else if (key === 'added_count' || key === 'original_price' || key === 'show_price') {
      // 确保数值字段是数字类型
      const value = machine[key];
      (machineForm as any)[key] = value === null || value === undefined ? null : Number(value);
    } else {
      (machineForm as any)[key] = machine[key]
    }
  })

  // 处理自定义属性
  customAttributes.value = []
  if (machine.custom_attrs) {
    try {
      const customAttrsObj = typeof machine.custom_attrs === 'string'
        ? JSON.parse(machine.custom_attrs)
        : machine.custom_attrs

      if (typeof customAttrsObj === 'object' && customAttrsObj !== null) {
        customAttributes.value = Object.entries(customAttrsObj).map(([key, value]) => ({
          key,
          value: String(value)
        }))
      }
    } catch (e) {
      console.error('解析自定义属性失败:', e)
      // 如果解析失败，尝试直接使用对象
      if (typeof machine.custom_attrs === 'object' && machine.custom_attrs !== null) {
        customAttributes.value = Object.entries(machine.custom_attrs).map(([key, value]) => ({
          key,
          value: String(value)
        }))
      }
    }
  }

  showMachineDialog.value = true
}

// 保存机器
const saveMachine = async () => {
  if (!machineFormRef.value) return

  try {
    await machineFormRef.value.validate()

    // 构建自定义属性对象
    const customAttrsObj: Record<string, string> = {}
    customAttributes.value.forEach(attr => {
      if (attr.key.trim()) {
        customAttrsObj[attr.key.trim()] = attr.value.trim()
      }
    })

    // 将自定义属性转换为JSON字符串
    const customAttrsString = Object.keys(customAttrsObj).length > 0
      ? JSON.stringify(customAttrsObj)
      : ''

    // 创建要保存的数据对象，确保数值字段类型正确
    const machineData = {
      ...machineForm,
      added_count: machineForm.added_count !== null && machineForm.added_count !== undefined ? Number(machineForm.added_count) : null,
      original_price: machineForm.original_price !== null && machineForm.original_price !== undefined ? Number(machineForm.original_price) : null,
      show_price: machineForm.show_price !== null && machineForm.show_price !== undefined ? Number(machineForm.show_price) : null,
      custom_attrs: customAttrsString
    }

    if (editingMachine.value) {
      // 更新机器
      await updateMachine(editingMachine.value.model, machineData)
      ElMessage.success('机器更新成功')
    } else {
      // 创建机器
      await createMachine(machineData)
      ElMessage.success('机器创建成功')
    }

    showMachineDialog.value = false
    fetchMachines()
  } catch (error) {
    console.error('保存机器失败:', error)
    if (error !== true) { // Element Plus验证失败时会返回true
      ElMessage.error('保存机器失败')
    }
  }
}

// 添加自定义属性
const addCustomAttribute = () => {
  customAttributes.value.push({ key: '', value: '' })
}

// 删除自定义属性
const removeCustomAttribute = (index: number) => {
  customAttributes.value.splice(index, 1)
}

// 关闭对话框
const closeMachineDialog = () => {
  showMachineDialog.value = false
  editingMachine.value = null
  // 清空自定义属性
  customAttributes.value = []
}

// 删除机器
const deleteMachine = async (model: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除型号为 ${model} 的机器吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteMachineAPI(model)
    ElMessage.success('机器删除成功')
    fetchMachines()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除机器失败:', error)
      ElMessage.error('删除机器失败')
    }
  }
}

// 处理分页
const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchMachines()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchMachines()
}

// 导入机器数据
const importMachinesData = async (jsonData: any) => {
  try {
    // 确保jsonData是数组格式
    let dataToImport = jsonData;
    if (!Array.isArray(jsonData)) {
      if (typeof jsonData === 'object' && jsonData !== null) {
        // 如果是单个对象，转换为数组
        dataToImport = [jsonData];
      } else {
        throw new Error('JSON数据格式不正确，应为对象或对象数组');
      }
    }

    // 直接发送JSON数据到新的API端点
    const response: any = await importMachinesJson(dataToImport);
    ElMessage.success(response.message || '机器数据导入成功');

    // 刷新列表
    fetchMachines();
    return response;
  } catch (error) {
    console.error('导入机器数据失败:', error);
    ElMessage.error('导入机器数据失败');
    throw error;
  }
};

// 导出机器数据
const exportMachinesData = async () => {
  try {
    // 使用新的直接JSON导出API
    const response: any = await exportMachinesJson();

    return response.data || [];
  } catch (error) {
    console.error('导出机器数据失败:', error);
    ElMessage.error('导出机器数据失败');
    throw error;
  }
};

// 设备差异化参数配置（剔除全量重复字段）
const attrConfig = {
  working_stations: {
    label: '工位数',
    placeholder: '请输入工作工位数量（如6/8/10）'
  },
  packing_speed: {
    label: '包装速度',
    placeholder: '请输入包装速度（如≤60pouches/min）'
  },
  bagsize_length: {
    label: '包装袋长度',
    placeholder: '请输入包装袋长度（如L≤360mm）'
  },
  bagsize_width: {
    label: '包装袋宽度',
    placeholder: '请输入包装袋宽度（如W70-180mm）'
  },
  machine_weight: {
    label: '设备重量',
    placeholder: '请输入设备重量（如400kg）'
  },
  dimensions: {
    label: '设备外形尺寸',
    placeholder: '请输入设备外形尺寸（如1500x900x1150mm）'
  },
  general_power: {
    label: '总功率',
    placeholder: '请输入设备总功率（如3.4kW）'
  },
  premade_bag_type: {
    label: '预制袋类型',
    placeholder: '请输入预制袋类型（如Flatpouch,Stand-up Pouch等）'
  },
  package_material: {
    label: '包装材料',
    placeholder: '请输入包装材料（如Single layer PE, PE laminated film等）'
  },
  bagging_stations: {
    label: '装袋工位数量',
    placeholder: '请输入装袋工位数量（如10）'
  },
  vacuumized_stations: {
    label: '抽真空工位数量',
    placeholder: '请输入抽真空工位数量（如12）'
  },
  open_pouch_speed: {
    label: '开袋速度',
    placeholder: '请输入开袋速度（如Max.60pouches/min）'
  },
  sealed_pouch_speed: {
    label: '封袋速度',
    placeholder: '请输入封袋速度（如Max.45pouches/min）'
  },
  pouch_length: {
    label: '袋长',
    placeholder: '请输入袋长（如150-300mm）'
  },
  pouch_width: {
    label: '袋宽',
    placeholder: '请输入袋宽（如70-150mm）'
  },
  pouch_height: {
    label: '袋高',
    placeholder: '请输入袋高（如40-90mm）'
  },
  packing_film_width: {
    label: '包装膜宽度',
    placeholder: '请输入包装膜宽度（如100-320mm）'
  },
  end_sealing: {
    label: '刀封类型',
    placeholder: '请输入刀封类型（如Box-motion Rotray-motion）'
  },
  packaging_material: {
    label: '包装物料类型',
    placeholder: '请输入包装物料类型（如Liquid,high viscosity fluid）'
  },
  filling_capacity: {
    label: '填充容量',
    placeholder: '请输入填充容量（如500-5000g）'
  },
  productsizerange: {
    label: '产品尺寸范围',
    placeholder: '请输入产品尺寸范围（如H5-60mm）'
  },
  sealing_wheels_structure: {
    label: '密封轮结构',
    placeholder: '请输入密封轮结构（如Small/Big）'
  },
  centerdistance: {
    label: '中心距',
    placeholder: '请输入中心距（如150mm）'
  },
  centerdiameter: {
    label: '中心直径',
    placeholder: '请输入中心直径（如120mm）'
  }
};


// 初始化数据
onMounted(() => {
  fetchMachines()
})
</script>

<style scoped>
.machine-management {
  padding: 20px 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

:deep(.el-table) {
  border-radius: 4px;
}

:deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
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

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 60px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
}

.image-placeholder .el-icon {
  font-size: 20px;
  color: #8c939d;
  margin-bottom: 4px;
}

.image-placeholder span {
  font-size: 12px;
  color: #8c939d;
}

.custom-attributes-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  min-height: 50px;
}

.custom-attribute-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

tr.el-table__row:hover {
  cursor: pointer;
  background-color: #f5f7fa;
}
</style>