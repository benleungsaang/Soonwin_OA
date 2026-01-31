<template>
  <div class="part-management">
    <div class="header-actions">
      <el-button type="primary" @click="showAddPartDialog">娣诲姞閮ㄤ欢</el-button>
      <JsonImportExport
        :import-function="importPartsData"
        :export-function="exportPartsData"
        export-file-name="parts.json"
        import-success-message="閮ㄤ欢鏁版嵁瀵煎叆鎴愬姛"
        export-success-message="閮ㄤ欢鏁版嵁瀵煎嚭鎴愬姛"
      />
    </div>

    <!-- 閮ㄤ欢鍒楄〃 -->
    <el-table
      :data="parts"
      style="width: 100%; margin-top: 20px;"
      v-loading="loading"
      border
      :row-style="{ cursor: 'pointer' }"
      @row-click="handleRowClick"
    >
      <el-table-column prop="image" label="閮ㄤ欢缂╃暐鍥? width="120">
        <template #default="scope">
          <div class="image-placeholder">
            <el-icon><Picture /></el-icon>
            <span>缂╃暐鍥?/span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="part_model" label="閮ㄤ欢鍨嬪彿" width="150" />
      <el-table-column prop="show_price" label="浠锋牸" width="120" />
      <el-table-column label="鎿嶄綔" width="200">
        <template #default="scope">
          <el-button size="small" @click="showEditPartDialog(scope.row)">缂栬緫</el-button>
          <el-button size="small" type="danger" @click="deletePart(scope.row.part_type_id)">鍒犻櫎</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 鍒嗛〉 -->
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

    <!-- 娣诲姞/缂栬緫閮ㄤ欢瀵硅瘽妗?-->
    <el-dialog
      :title="editingPart ? '缂栬緫閮ㄤ欢' : '娣诲姞閮ㄤ欢'"
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
            <el-form-item label="閮ㄤ欢鍨嬪彿" prop="part_model">
              <el-input
                v-model="partForm.part_model"
                :disabled="!!editingPart"
                placeholder="璇疯緭鍏ラ儴浠跺瀷鍙凤紙濡侻OTOR-001銆丼EAL-006锛?
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="鎴愭湰浠锋牸" prop="original_price">
              <el-input-number
                v-model="partForm.original_price"
                :precision="2"
                :min="0"
                :controls=false
                style="width: 100%;"
                :disabled="!isCurrentUserAdmin"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="浠锋牸" prop="show_price">
              <el-input-number
                v-model="partForm.show_price"
                :precision="2"
                :min="0"
                :controls=false
                style="width: 100%;"
                :disabled="!isCurrentUserAdmin"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="缂╃暐鍥捐矾寰? prop="image">
              <el-input v-model="partForm.image" placeholder="璇疯緭鍏ョ缉鐣ュ浘璺緞" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closePartDialog">鍙栨秷</el-button>
          <el-button type="primary" @click="savePart">纭畾</el-button>
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

// 鍝嶅簲寮忔暟鎹?const parts = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 瀵硅瘽妗嗙浉鍏?const showPartDialog = ref(false)
const editingPart = ref<any>(null)
const partFormRef = ref()
const partForm = reactive({
  part_model: '',
  original_price: null as number | null,
  show_price: null as number | null,
  image: ''
})

// 琛ㄥ崟楠岃瘉瑙勫垯
const partRules = {
  part_model: [
    { required: true, message: '璇疯緭鍏ラ儴浠跺瀷鍙?, trigger: 'blur' },
    { min: 1, max: 100, message: '闀垮害鍦?1 鍒?100 涓瓧绗?, trigger: 'blur' }
  ]
}

const props = defineProps({
  // 鏄惁涓虹鐞嗗憳
  isCurrentUserAdmin: {
    type: Boolean,
    required: true, // 蹇呭～锛岀‘淇濈埗缁勪欢浼犻€?    default: false  // 榛樿鍊硷紙闃叉鏈紶閫掓椂鍑洪敊锛?  },
  // 鏄惁鐧诲綍锛堟湁token锛?  hasToken: {
    type: Boolean,
    required: true,
    default: false
  }
});

// 鑾峰彇閮ㄤ欢鍒楄〃
const fetchParts = async () => {
  loading.value = true
  try {
    const response: any = await getParts({
      page: currentPage.value,
      per_page: pageSize.value
    })
    // 娣诲姞瀹夊叏妫€鏌ワ紝纭繚response瀛樺湪涓斾负瀵硅薄
    if (response && typeof response === 'object') {
      parts.value = response.parts || []
      total.value = response.total || 0
    } else {
      console.error('API鍝嶅簲鏍煎紡閿欒:', response)
      ElMessage.error('API鍝嶅簲鏍煎紡閿欒')
      parts.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('鑾峰彇閮ㄤ欢鍒楄〃澶辫触:', error)
    ElMessage.error('鑾峰彇閮ㄤ欢鍒楄〃澶辫触')
    parts.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 鏄剧ず娣诲姞閮ㄤ欢瀵硅瘽妗?const showAddPartDialog = () => {
  editingPart.value = null
  Object.keys(partForm).forEach(key => {
    (partForm as any)[key] = key === 'original_price' || key === 'show_price' ? null : ''
  })
  showPartDialog.value = true
}

// 鏄剧ず缂栬緫閮ㄤ欢瀵硅瘽妗?const showEditPartDialog = (part: any) => {
  editingPart.value = { ...part }
  Object.keys(partForm).forEach(key => {
    if (key === 'original_price' || key === 'show_price') {
      // 纭繚鏁板€煎瓧娈垫槸鏁板瓧绫诲瀷
      const value = part[key];
      (partForm as any)[key] = value === null || value === undefined ? null : Number(value);
    } else {
      (partForm as any)[key] = part[key]
    }
  })
  showPartDialog.value = true
}

// 淇濆瓨閮ㄤ欢
const savePart = async () => {
  if (!partFormRef.value) return

  try {
    await partFormRef.value.validate()

    // 纭繚鏁板€煎瓧娈电被鍨嬫纭?    const partData = {
      ...partForm,
      original_price: partForm.original_price !== null && partForm.original_price !== undefined ? Number(partForm.original_price) : null,
      show_price: partForm.show_price !== null && partForm.show_price !== undefined ? Number(partForm.show_price) : null
    }

    if (editingPart.value) {
      // 鏇存柊閮ㄤ欢
      await updatePart(editingPart.value.part_type_id, partData)
      ElMessage.success('閮ㄤ欢鏇存柊鎴愬姛')
    } else {
      // 鍒涘缓閮ㄤ欢
      await createPart(partData)
      ElMessage.success('閮ㄤ欢鍒涘缓鎴愬姛')
    }

    showPartDialog.value = false
    fetchParts()
  } catch (error) {
    console.error('淇濆瓨閮ㄤ欢澶辫触:', error)
    if (error !== true) { // Element Plus楠岃瘉澶辫触鏃朵細杩斿洖true
      ElMessage.error('淇濆瓨閮ㄤ欢澶辫触')
    }
  }
}

// 鍏抽棴瀵硅瘽妗?const closePartDialog = () => {
  showPartDialog.value = false
  editingPart.value = null
}

// 鍒犻櫎閮ㄤ欢
const deletePart = async (partTypeId: number) => {
  try {
    await ElMessageBox.confirm(
      `纭畾瑕佸垹闄D涓?${partTypeId} 鐨勯儴浠跺悧锛焋,
      '纭鍒犻櫎',
      {
        confirmButtonText: '纭畾',
        cancelButtonText: '鍙栨秷',
        type: 'warning'
      }
    )

    await deletePartAPI(partTypeId)
    ElMessage.success('閮ㄤ欢鍒犻櫎鎴愬姛')
    fetchParts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('鍒犻櫎閮ㄤ欢澶辫触:', error)
      ElMessage.error('鍒犻櫎閮ㄤ欢澶辫触')
    }
  }
}

// 澶勭悊鍒嗛〉
const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchParts()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchParts()
}

// 瀵煎叆閮ㄤ欢鏁版嵁
const importPartsData = async (jsonData: any) => {
  try {
    // 纭繚jsonData鏄暟缁勬牸寮?    let dataToImport = jsonData;
    if (!Array.isArray(jsonData)) {
      if (typeof jsonData === 'object' && jsonData !== null) {
        // 濡傛灉鏄崟涓璞★紝杞崲涓烘暟缁?        dataToImport = [jsonData];
      } else {
        throw new Error('JSON鏁版嵁鏍煎紡涓嶆纭紝搴斾负瀵硅薄鎴栧璞℃暟缁?);
      }
    }

    // 閬垫椿澶勭悊鏁版嵁瀵煎叆 - 杩欓噷闇€瑕佽皟鐢ㄥ悗绔殑瀵煎叆API
    // 鐢变簬鍚庣娌℃湁涓撻棬鐨勯儴浠跺鍏PI锛屾垜浠€愪釜鍒涘缓
    let successCount = 0;
    for (const part of dataToImport) {
      try {
        await createPart(part);
        successCount++;
      } catch (error) {
        console.error(`瀵煎叆閮ㄤ欢 ${part.part_model} 澶辫触:`, error);
      }
    }

    const message = `鎴愬姛瀵煎叆 ${successCount} 涓儴浠禶;
    ElMessage.success(message);

    // 鍒锋柊鍒楄〃
    fetchParts();
    return { success: true, message, importedCount: successCount };
  } catch (error) {
    console.error('瀵煎叆閮ㄤ欢鏁版嵁澶辫触:', error);
    ElMessage.error('瀵煎叆閮ㄤ欢鏁版嵁澶辫触');
    throw error;
  }
};

// 瀵煎嚭閮ㄤ欢鏁版嵁
const exportPartsData = async () => {
  try {
    // 浣跨敤鏂扮殑鐩存帴JSON瀵煎嚭API
    const response: any = await exportPartsJson();

    return response.data || [];
  } catch (error) {
    console.error('瀵煎嚭閮ㄤ欢鏁版嵁澶辫触:', error);
    ElMessage.error('瀵煎嚭閮ㄤ欢鏁版嵁澶辫触');
    throw error;
  }
};

// 澶勭悊琛岀偣鍑讳簨浠?const handleRowClick = (row: any) => {
  // 鐐瑰嚮琛屾椂鏄剧ず缂栬緫瀵硅瘽妗?  showEditPartDialog(row);
}

// 鍒濆鍖栨暟鎹?onMounted(() => {
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
