<template>
  <div class="part-management">
    <div class="header-actions">
      <el-button type="primary" @click="showAddPartDialog">添加部件</el-button>
      <JsonImportExport
        :import-function="importPartsData"
        :export-function="exportPartsData"
        export-file-name="parts.json"
        import-success-message="部件数据导入成功"
        export-success-message="部件数据导出成功"
      />
    </div>

    <!-- 部件列表 -->
    <el-table
      :data="parts"
      style="width: 100%; margin-top: 20px;"
      v-loading="loading"
      border
    >
      <el-table-column prop="image" label="部件缩略图" width="120">
        <template #default="scope">
          <div class="image-placeholder">
            <el-icon><Picture /></el-icon>
            <span>缩略图</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="part_model" label="部件型号" width="150" />
      <el-table-column prop="show_price" label="展示价格" width="120" />
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="showEditPartDialog(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deletePart(scope.row.part_type_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

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

    <!-- 添加/编辑部件对话框 -->
    <el-dialog
      :title="editingPart ? '编辑部件' : '添加部件'"
      v-model="showPartDialog"
      width="50%"
      :before-close="closePartDialog"
    >
      <el-form
        :model="partForm"
        :rules="partRules"
        ref="partFormRef"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="部件型号" prop="part_model">
              <el-input
                v-model="partForm.part_model"
                :disabled="!!editingPart"
                placeholder="请输入部件型号（如MOTOR-001、SEAL-006）"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原始价格" prop="original_price">
              <el-input-number
                v-model="partForm.original_price"
                :precision="2"
                :min="0"
                controls-position="right"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="展示价格" prop="show_price">
              <el-input-number
                v-model="partForm.show_price"
                :precision="2"
                :min="0"
                controls-position="right"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="缩略图路径" prop="image">
              <el-input v-model="partForm.image" placeholder="请输入缩略图路径" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closePartDialog">取消</el-button>
          <el-button type="primary" @click="savePart">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { getParts, createPart, updatePart, deletePart as deletePartAPI, importPartsJson, exportPartsJson } from '@/utils/request'
import JsonImportExport from '@/components/JsonImportExport.vue'

// 响应式数据
const parts = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 对话框相关
const showPartDialog = ref(false)
const editingPart = ref<any>(null)
const partFormRef = ref()
const partForm = reactive({
  part_model: '',
  original_price: null as number | null,
  show_price: null as number | null,
  image: ''
})

// 表单验证规则
const partRules = {
  part_model: [
    { required: true, message: '请输入部件型号', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 获取部件列表
const fetchParts = async () => {
  loading.value = true
  try {
    const response: any = await getParts({
      page: currentPage.value,
      per_page: pageSize.value
    })
    // 添加安全检查，确保response存在且为对象
    if (response && typeof response === 'object') {
      parts.value = response.parts || []
      total.value = response.total || 0
    } else {
      console.error('API响应格式错误:', response)
      ElMessage.error('API响应格式错误')
      parts.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取部件列表失败:', error)
    ElMessage.error('获取部件列表失败')
    parts.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 显示添加部件对话框
const showAddPartDialog = () => {
  editingPart.value = null
  Object.keys(partForm).forEach(key => {
    (partForm as any)[key] = key === 'original_price' || key === 'show_price' ? null : ''
  })
  showPartDialog.value = true
}

// 显示编辑部件对话框
const showEditPartDialog = (part: any) => {
  editingPart.value = { ...part }
  Object.keys(partForm).forEach(key => {
    if (key === 'original_price' || key === 'show_price') {
      // 确保数值字段是数字类型
      const value = part[key];
      (partForm as any)[key] = value === null || value === undefined ? null : Number(value);
    } else {
      (partForm as any)[key] = part[key]
    }
  })
  showPartDialog.value = true
}

// 保存部件
const savePart = async () => {
  if (!partFormRef.value) return

  try {
    await partFormRef.value.validate()

    // 确保数值字段类型正确
    const partData = {
      ...partForm,
      original_price: partForm.original_price !== null && partForm.original_price !== undefined ? Number(partForm.original_price) : null,
      show_price: partForm.show_price !== null && partForm.show_price !== undefined ? Number(partForm.show_price) : null
    }

    if (editingPart.value) {
      // 更新部件
      await updatePart(editingPart.value.part_type_id, partData)
      ElMessage.success('部件更新成功')
    } else {
      // 创建部件
      await createPart(partData)
      ElMessage.success('部件创建成功')
    }

    showPartDialog.value = false
    fetchParts()
  } catch (error) {
    console.error('保存部件失败:', error)
    if (error !== true) { // Element Plus验证失败时会返回true
      ElMessage.error('保存部件失败')
    }
  }
}

// 关闭对话框
const closePartDialog = () => {
  showPartDialog.value = false
  editingPart.value = null
}

// 删除部件
const deletePart = async (partTypeId: number) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除ID为 ${partTypeId} 的部件吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deletePartAPI(partTypeId)
    ElMessage.success('部件删除成功')
    fetchParts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除部件失败:', error)
      ElMessage.error('删除部件失败')
    }
  }
}

// 处理分页
const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchParts()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchParts()
}

// 导入部件数据
const importPartsData = async (jsonData: any) => {
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

    // 遵活处理数据导入 - 这里需要调用后端的导入API
    // 由于后端没有专门的部件导入API，我们逐个创建
    let successCount = 0;
    for (const part of dataToImport) {
      try {
        await createPart(part);
        successCount++;
      } catch (error) {
        console.error(`导入部件 ${part.part_model} 失败:`, error);
      }
    }

    const message = `成功导入 ${successCount} 个部件`;
    ElMessage.success(message);
    
    // 刷新列表
    fetchParts();
    return { success: true, message, importedCount: successCount };
  } catch (error) {
    console.error('导入部件数据失败:', error);
    ElMessage.error('导入部件数据失败');
    throw error;
  }
};

// 导出部件数据
const exportPartsData = async () => {
  try {
    // 使用新的直接JSON导出API
    const response: any = await exportPartsJson();
    
    return response.data || [];
  } catch (error) {
    console.error('导出部件数据失败:', error);
    ElMessage.error('导出部件数据失败');
    throw error;
  }
};

// 初始化数据
onMounted(() => {
  fetchParts()
})
</script>

<style scoped>
.part-management {
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
</style>