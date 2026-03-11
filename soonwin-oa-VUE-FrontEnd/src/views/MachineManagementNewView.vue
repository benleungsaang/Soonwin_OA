<template>
  <div class="machine-management-container">
    <!-- 通用头部 -->
    <CommonHeader title="设备管理" />

    <div class="content-wrapper">
      <!-- 搜索和操作区域 -->
      <div class="search-and-actions">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-input
              v-model="searchQuery"
              placeholder="请输入搜索关键词"
              clearable
              @clear="handleSearchClear"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-col>
          <el-col :span="16" class="text-right">
            <el-dropdown trigger="click" @command="handleOtherFunction">
              <el-button type="info" style="margin-right: 15px;">
                <el-icon><Menu /></el-icon>
                其它功能
                <el-icon class="el-icon--right">
                  <arrow-down />
                </el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <!-- 价格系数管理 -->
                  <el-dropdown-item
                    v-if="isCurrentUserAdmin()"
                    command="coefficient"
                  >
                    <el-icon><Setting /></el-icon>
                    价格系数管理
                  </el-dropdown-item>
                  <!-- 回收站 -->
                  <el-dropdown-item
                    v-if="hasRoutePermission('machine_manage')"
                    command="recycle"
                  >
                    <el-icon><Delete /></el-icon>
                    回收站
                  </el-dropdown-item>
                  <!-- 清空数据 -->
                  <el-dropdown-item
                    v-if="isCurrentUserAdmin()"
                    command="clear"
                    divided
                  >
                    <el-icon><DeleteFilled /></el-icon>
                    清空数据
                  </el-dropdown-item>
                  <!-- 批量导入 -->
                  <el-dropdown-item
                    v-if="hasRoutePermission('upload_manage')"
                    command="import"
                  >
                    <el-icon><Upload /></el-icon>
                    批量导入
                  </el-dropdown-item>
                  <!-- 批量导出 -->
                  <el-dropdown-item
                    v-if="hasRoutePermission('machine_manage')"
                    command="export"
                  >
                    <el-icon><Download /></el-icon>
                    批量导出
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button
              v-if="hasRoutePermission('machine_manage')"
              type="primary"
              @click="openCreateDialog"
            >
              <el-icon><Plus /></el-icon>
              新增设备
            </el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 价格系数管理对话框 -->
      <el-dialog
        v-model="coefficientDialogVisible"
        title="价格系数管理"
        width="500px"
        :before-close="closeCoefficientDialog"
      >
        <el-form label-width="120px">
          <el-form-item label="当前系数">
            <el-input-number
              v-model="currentCoefficient"
              :precision="4"
              :step="0.01"
              :min="0.0001"
              :max="10"
              style="width: 100%"
              :controls="true"
            />
          </el-form-item>
          <el-form-item label="说明">
            <div class="coefficient-description">
              展示价格 = 原始价格 × 系数<br>
              修改系数后，所有设备的展示价格将实时更新
            </div>
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeCoefficientDialog">取消</el-button>
            <el-button type="primary" @click="updateCoefficient">更新系数</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 设备列表 -->
      <el-table
        :data="machines"
        style="width: 100%"
        v-loading="loading"
        row-key="id"
        :row-style="{ cursor: 'pointer' }"
        @row-click="handleRowClick"
      >
        <el-table-column prop="image" label="缩略图" width="120">
          <template #default="{ row }">
            <ErrorFallbackImage
              :src="getThumbnailPath(row.image)"
              :fallback-src="row.image"
              :preview-src-list="[row.image]"
              :alt="row.model"
              fit="cover"
              :preview-teleported="true"
              :hide-on-click-modal="true"
              style="width: 60px; height: 60px; border-radius: 4px;"
              @click.stop
            />
          </template>
        </el-table-column>
        <el-table-column prop="brand" label="品牌" width="120" />
        <el-table-column label="设备型号" width="200">
          <template #default="{ row }">
            <div>{{ row.model }}</div>
            <div style="font-size: 12px; color: #999;">{{ row.original_model }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="show_price" label="参考价格" width="120">
          <template #default="{ row }">
            ¥{{ row.show_price || 0 }}
          </template>
        </el-table-column>
        <!-- <el-table-column v-if="isCurrentUserAdmin()" prop="original_price" label="原始价格" width="120">
          <template #default="{ row }">
            ¥{{ row.original_price || 0 }}
          </template>
        </el-table-column> -->
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="hasRoutePermission('machine_manage')"
              size="small"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="hasRoutePermission('machine_manage')"
              size="small"
              type="danger"
              @click.stop="confirmDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :before-close="handleDialogClose"
    >
      <el-form
        :model="formModel"
        :rules="formRules"
        ref="formRef"
        label-width="120px"
      >
        <el-form-item label="设备型号" prop="model">
          <el-input
            v-model="formModel.model"
            placeholder="请输入设备型号"
          />
        </el-form-item>
        <el-form-item label="原厂型号" prop="original_model">
          <el-input v-model="formModel.original_model" placeholder="请输入原厂型号" />
        </el-form-item>
        <el-form-item label="品牌" prop="brand">
          <el-input v-model="formModel.brand" placeholder="请输入品牌" />
        </el-form-item>
        <el-form-item label="设备重量" prop="machine_weight">
          <el-input v-model="formModel.machine_weight" placeholder="请输入设备重量" />
        </el-form-item>
        <el-form-item label="设备尺寸" prop="dimensions">
          <el-input v-model="formModel.dimensions" placeholder="请输入设备尺寸" />
        </el-form-item>
        <el-form-item label="总功率" prop="general_power">
          <el-input v-model="formModel.general_power" placeholder="请输入总功率" />
        </el-form-item>
        <el-form-item label="供电规格" prop="power_supply">
          <el-input v-model="formModel.power_supply" placeholder="请输入供电规格" />
        </el-form-item>
        <el-form-item label="设备类型" prop="machine_type">
          <el-select v-model="formModel.machine_type" placeholder="请选择设备类型">
            <el-option :value="0" label="主机" />
            <el-option :value="1" label="配件" />
            <el-option :value="2" label="工具" />
            <el-option :value="3" label="耗材" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备缩略图" prop="image">
          <!-- 显示当前缩略图 -->
          <div v-if="formModel.image" class="current-image-preview">
            <ErrorFallbackImage
              :src="getThumbnailPath(formModel.image)"
              :fallback-src="formModel.image"
              :preview-src-list="[formModel.image]"
              :alt="formModel.model || '设备图片'"
              fit="cover"
              :preview-teleported="true"
              :hide-on-click-modal="true"
              style="width: 100px; height: 100px; border-radius: 4px;"
            />
          </div>

          <ImageUploadPreview
            :ref="setUploadPreviewRef"
            :communication-id="null"
            :upload-path="uploadPath"
            @upload-success="onImageUploadSuccess"
            @upload-failure="onImageUploadFailure"
            @upload-clipboard-image="onUploadClipboardImage"
          />

        </el-form-item>
        <el-form-item label="展示价格" prop="show_price">
          <el-input-number
            v-model="formModel.show_price"
            :precision="2"
            :min="0"
            placeholder="请输入展示价格"
            :controls="false"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="价格类型" prop="is_show_price_manual">
          <el-checkbox
            v-model="formModel.is_show_price_manual"
            :true-value="1"
            :false-value="0"
          >
            <span style="color: #409eff;">人工设置价格</span>
            <el-tooltip content="勾选后将使用手动输入的价格，不随原始价格和系数自动计算" placement="top">
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </el-checkbox>
        </el-form-item>
        <el-form-item v-if="isCurrentUserAdmin()" label="原始价格" prop="original_price">
          <el-input-number
            v-model="formModel.original_price"
            :precision="2"
            :min="0"
            placeholder="请输入原始价格"
            style="width: 100%"
            :controls="false"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="formModel.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
          />
        </el-form-item>
        <el-form-item label="自定义属性" prop="custom_attrs">
          <!-- 动态生成的自定义字段表单项 -->
          <div v-for="(item, index) in customAttrsList" :key="index" class="custom-attr-item">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-input
                  v-model="item.key"
                  placeholder="字段名（如：WorkingStations）"
                />
              </el-col>
              <el-col :span="12">
                <el-input
                  v-model="item.value"
                  placeholder="字段值（如：6）"
                />
              </el-col>
              <el-col :span="4">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeCustomAttr(index)"
                  :icon="Delete"
                >
                </el-button>
              </el-col>
            </el-row>
          </div>

          <!-- 新增自定义字段按钮 -->
          <el-button
            type="primary"
            @click="addCustomAttr"
            :icon="Plus"
            size="small"
            style="margin-top: 10px"
          >
            新增自定义字段
          </el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <span v-if="isCurrentUserAdmin()" style="color:#999;font-size: 14px;margin-right: 5px;"> 创建人: {{ formModel.creator }}</span>
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button type="primary" @click="handleSave">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="批量导入设备"
      width="800px"
      :before-close="handleImportDialogClose"
    >
      <el-steps :active="importStep" align-center>
        <el-step title="上传文件" />
        <el-step title="数据预览" />
        <el-step title="导入完成" />
      </el-steps>

      <!-- 步骤1：上传JSON数据 -->
      <div v-if="importStep === 0" class="import-step-content">
        <p>请粘贴JSON格式的设备数据：</p>
        <el-input
          v-model="importJsonData"
          type="textarea"
          :rows="10"
          placeholder='示例格式：[{"Model": "VP-BF-180-06", "OriginalModel": "GDS180-06", ...}]'
        />
        <div class="import-tips">
          <p><strong>数据格式说明：</strong></p>
          <ul>
            <li>支持驼峰命名（如Model, OriginalModel）或下划线命名（如model, original_model）</li>
            <li>非标准字段将自动存储在custom_attrs中</li>
            <li>数据格式应为数组：[{"Model": "设备型号", ...}, {...}]</li>
          </ul>
        </div>
      </div>

      <!-- 步骤2：数据预览 -->
      <div v-if="importStep === 1" class="import-step-content">
        <p>数据预览（前5条）：</p>
        <el-table :data="importPreviewData" max-height="300">
          <el-table-column prop="model" label="设备型号" width="150" />
          <el-table-column prop="original_model" label="原厂型号" width="150" />
          <el-table-column prop="brand" label="品牌" width="120" />
          <el-table-column prop="machine_weight" label="设备重量" width="120" />
          <el-table-column prop="show_price" label="展示价格" width="120" />
        </el-table>
        <p class="preview-info">总共 {{ importPreviewTotal }} 条数据待导入</p>
      </div>

      <!-- 步骤3：导入结果 -->
      <div v-if="importStep === 2" class="import-step-content">
        <el-result
          v-if="importResult.success"
          icon="success"
          title="导入成功"
          :sub-title="`成功导入 ${importResult.imported_count} 条，失败 ${importResult.failed_count} 条`"
        >
          <template #extra>
            <el-button type="primary" @click="handleImportDialogClose">确定</el-button>
          </template>
        </el-result>
        <el-result
          v-else
          icon="error"
          title="导入失败"
          :sub-title="importResult.message || '导入过程中发生错误'"
        >
          <template #extra>
            <el-button type="primary" @click="handleImportDialogClose">确定</el-button>
          </template>
        </el-result>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button v-if="importStep > 0" @click="prevImportStep">上一步</el-button>
          <el-button
            v-if="importStep < 2"
            type="primary"
            @click="nextImportStep"
            :disabled="!canNextStep"
          >
            {{ importStep === 1 ? '开始导入' : '下一步' }}
          </el-button>
          <el-button v-if="importStep === 2" type="primary" @click="handleImportDialogClose">完成</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 回收站对话框 -->
    <el-dialog
      v-model="recycleBinDialogVisible"
      title="设备回收站"
      width="80%"
      :before-close="closeRecycleBinDialog"
    >
      <div class="recycle-bin-content">
        <el-table
          :data="deletedMachines"
          style="width: 100%"
          v-loading="recycleBinLoading"
          @selection-change="handleRecycleBinSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="image" label="缩略图" width="120">
            <template #default="{ row }">
              <ErrorFallbackImage
                :src="getThumbnailPath(row.image)"
                :fallback-src="row.image"
                :preview-src-list="[row.image]"
                :alt="row.model"
                fit="cover"
                :preview-teleported="true"
                :hide-on-click-modal="true"
                style="width: 60px; height: 60px; border-radius: 4px;"
              />
            </template>
          </el-table-column>
          <el-table-column prop="brand" label="品牌" width="120" />
          <el-table-column label="设备型号" width="200">
            <template #default="{ row }">
              <div>{{ row.model }}</div>
              <div style="font-size: 12px; color: #999;">{{ row.original_model }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="show_price" label="展示价格" width="120">
            <template #default="{ row }">
              ¥{{ row.show_price || 0 }}
            </template>
          </el-table-column>
          <el-table-column v-if="isCurrentUserAdmin()" prop="original_price" label="原始价格" width="120">
            <template #default="{ row }">
              ¥{{ row.original_price || 0 }}
            </template>
          </el-table-column>
          <el-table-column prop="delete_time" label="删除时间" width="160" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="hasRoutePermission('machine_manage')"
                size="small"
                type="primary"
                @click="restoreMachine(row.id)"
              >
                恢复
              </el-button>
              <el-button
                v-if="hasRoutePermission('machine_manage')"
                size="small"
                type="danger"
                @click="permanentDeleteMachine(row.id)"
              >
                永久删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 操作按钮 -->
        <div class="recycle-bin-actions" style="margin-top: 15px;">
          <el-button
            v-if="hasRoutePermission('machine_manage')"
            type="danger"
            :disabled="selectedDeletedMachines.length === 0"
            @click="batchPermanentDelete"
          >
            批量删除 ({{ selectedDeletedMachines.length }})
          </el-button>
          <el-button
            v-if="hasRoutePermission('machine_manage')"
            type="warning"
            @click="clearRecycleBin"
          >
            清空回收站
          </el-button>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper" style="margin-top: 15px;">
          <el-pagination
            v-model:current-page="recycleBinCurrentPage"
            v-model:page-size="recycleBinPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :background="true"
            layout="total, sizes, prev, pager, next, jumper"
            :total="recycleBinTotal"
            @size-change="handleRecycleBinSizeChange"
            @current-change="handleRecycleBinCurrentChange"
          />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeRecycleBinDialog">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus';
import { Search, Plus, Upload, Download, Delete, Setting, DeleteFilled, Menu, ArrowDown, QuestionFilled } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';
import ImageUploadPreview from '@/components/ImageUploadPreview.vue';
import ErrorFallbackImage from '@/components/ErrorFallbackImage.vue';
import { hasRoutePermission, getCurrentUserRole } from '@/utils/authUtils';
import request, { importMachinesNewJson, exportMachinesNewJson, getMachinesNew, getMachineNew, createMachineNew, updateMachineNew, deleteMachineNew, getDeletedMachines, restoreMachineFromRecycleBin, uploadMachineThumb, uploadMachineThumbGeneric } from '@/utils/request';

// 定义数据类型
interface Machine {
  id: number;
  model: string;
  original_model: string;
  machine_weight: string;
  dimensions: string;
  general_power: string;
  power_supply: string;
  image: string;
  added_count: number;
  show_price: number | null;
  original_price: number | null;
  machine_type: number;
  remark: string;
  brand: string;
  search_key: string;
  custom_attrs: string;
  is_show_price_manual?: number;  // 新增：价格类型标识字段
  creator?: string; // 新增：创建者字段
}

// 响应式数据
const machines = ref<Machine[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const searchQuery = ref('');

// 回收站相关数据
const recycleBinDialogVisible = ref(false);
const deletedMachines = ref<Machine[]>([]);
const recycleBinLoading = ref(false);
const recycleBinCurrentPage = ref(1);
const recycleBinPageSize = ref(10);
const recycleBinTotal = ref(0);
// 多选相关
const selectedDeletedMachines = ref<number[]>([]);  // 存储已选中的机器ID

// 价格系数管理相关
const coefficientDialogVisible = ref(false);
const currentCoefficient = ref(1.05); // 默认系数

// 图片上传相关
const uploadPreviewRefs = ref<{[key: number]: any}>({}); // 存储图片上传预览组件引用

// 表单相关
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const formModel = ref<Partial<Machine>>({
  id: undefined,
  model: '',
  original_model: '',
  machine_weight: '',
  dimensions: '',
  general_power: '',
  power_supply: '',
  image: './assets/Media/Machine/sample.png',
  added_count: 0,
  show_price: null,
  original_price: null,
  machine_type: 0,
  remark: '',
  brand: '',
  search_key: '',
  custom_attrs: '',
  is_show_price_manual: 0 ,  // 新增：价格类型标识
  creator: '', // 新增：创建者
});
const isEdit = ref(false);

// 表单验证规则
const formRules = ref<FormRules>({
  model: [
    { required: true, message: '请输入设备型号', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  original_model: [
    { required: true, message: '请输入原厂型号', trigger: 'blur' }
  ],
  brand: [
    { required: true, message: '请输入品牌', trigger: 'blur' }
  ]
});

// 导入相关数据
const importDialogVisible = ref(false);
const importStep = ref(0);
const importJsonData = ref('');
const importPreviewData = ref<Partial<Machine>[]>([]);
const importPreviewTotal = ref(0);
const importResult = ref({
  success: false,
  message: '',
  imported_count: 0,
  failed_count: 0
});

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑设备' : '新增设备');

const uploadPath = computed(() => {
  // 如果是编辑模式且有ID，使用更新缩略图的API
  if (isEdit.value && formModel.value.id) {
    return `/api/machines_new/${formModel.value.id}/upload-thumb`;
  }
  // 否则返回一个占位路径，实际上传时会使用专门的API
  return `/api/machines_new/upload-thumb`;
});

const canNextStep = computed(() => {
  if (importStep.value === 0) {
    // 第一步：检查JSON数据是否有效
    try {
      const parsed = JSON.parse(importJsonData.value);
      return Array.isArray(parsed) && parsed.length > 0;
    } catch {
      return false;
    }
  }
  return true;
});

// 获取设备列表
const fetchMachines = async () => {
  loading.value = true;
  try {
    const response = await getMachinesNew({
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchQuery.value
    });

    machines.value = response.machines || [];
    total.value = response.total || 0;
  } catch (error) {
    console.error('获取设备列表失败:', error);
    ElMessage.error('获取设备列表失败');
  } finally {
    loading.value = false;
  }
};

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchMachines();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchMachines();
};

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1;
  fetchMachines();
};

const handleSearchClear = () => {
  searchQuery.value = '';
  currentPage.value = 1;
  fetchMachines();
};

// 操作处理
const openCreateDialog = async () => {
  isEdit.value = false;
  resetForm();
  // 确保表单数据更新后显示对话框
  await nextTick();
  dialogVisible.value = true;
};

const openEditDialog = async (row: Machine) => {
  isEdit.value = true;
  // 创建副本并确保数值字段是正确的类型
  formModel.value = {
    ...row,
    show_price: row.show_price !== null && row.show_price !== undefined ? Number(row.show_price) : null,
    original_price: row.original_price !== null && row.original_price !== undefined ? Number(row.original_price) : null,
    added_count: row.added_count !== null && row.added_count !== undefined ? Number(row.added_count) : 0,
    machine_type: row.machine_type !== null && row.machine_type !== undefined ? Number(row.machine_type) : 0,
    is_show_price_manual: row.is_show_price_manual !== null && row.is_show_price_manual !== undefined ? Number(row.is_show_price_manual) : 0  // 新增：处理价格类型标识
  };

  // 确保custom_attrs是字符串格式
  if (typeof formModel.value.custom_attrs !== 'string') {
    formModel.value.custom_attrs = JSON.stringify(formModel.value.custom_attrs || {});
  }

  // 解析自定义属性
  parseCustomAttrsFromJson(formModel.value.custom_attrs);

  // 等待表单数据更新后，再更新自定义属性列表
  await nextTick();
  dialogVisible.value = true;
};

const resetForm = () => {
  formModel.value = {
    id: undefined,
    model: '',
    original_model: '',
    machine_weight: '',
    dimensions: '',
    general_power: '',
    power_supply: '',
    image: './assets/Media/Machine/sample.png',
    added_count: 0,
    show_price: null,
    original_price: null,
    machine_type: 0,
    remark: '',
    brand: '',
    search_key: '',
    custom_attrs: '{}',
    is_show_price_manual: 0  // 新增：重置价格类型标识
  };
  // 确保数值字段是正确的类型
  formModel.value.added_count = Number(formModel.value.added_count);
  formModel.value.machine_type = Number(formModel.value.machine_type);
  formModel.value.is_show_price_manual = Number(formModel.value.is_show_price_manual);  // 新增：确保价格类型标识是数值类型

  // 重置自定义属性相关数据
  customAttrsList.value = [{ key: '', value: '' }];
};

const handleDialogClose = () => {
  dialogVisible.value = false;
  // 重置表单，包括图片
  resetForm();
  // 重置自定义属性相关数据
  customAttrsList.value = [{ key: '', value: '' }];
};

const handleSave = async () => {
  if (!formRef.value) return;

  try {
    // 先同步自定义属性
    syncCustomAttrsToJson();

    // 验证表单
    await formRef.value.validate();

    // 检查是否有本地图片需要上传（以blob:开头的URL）
    let imageToUpload = null;
    if (formModel.value.image && typeof formModel.value.image === 'string' && formModel.value.image.startsWith('blob:')) {
      imageToUpload = formModel.value.image;
      // 临时使用默认图片路径，等图片上传后再更新
      formModel.value.image = './assets/Media/Machine/sample.png';
    }

    // 确保数值字段是正确的类型
    // 只发送需要更新的字段，避免发送自动生成的字段
    const formData = {
      ...formModel.value,
      show_price: formModel.value.show_price !== null && formModel.value.show_price !== undefined ? Number(formModel.value.show_price) : null,
      original_price: formModel.value.original_price !== null && formModel.value.original_price !== undefined ? Number(formModel.value.original_price) : null,
      added_count: Number(formModel.value.added_count),
      machine_type: Number(formModel.value.machine_type),
      is_show_price_manual: Number(formModel.value.is_show_price_manual)  // 新增：确保价格类型标识是数值类型
    };

    // 移除自动生成的字段，避免发送到后端
    const safeFormData = formData as Record<string, any>;
    delete safeFormData.id;
    delete safeFormData.create_time;
    delete safeFormData.update_time;
    delete safeFormData.search_key;
    delete safeFormData.raw_show_price;
    delete safeFormData.manual_show_price;

    if (isEdit.value) {
      // 更新设备
      const updatedMachine = await updateMachineNew(formModel.value.id as number, formData);
      ElMessage.success('设备更新成功');
      dialogVisible.value = false;

      // 直接更新本地数据
      const index = machines.value.findIndex(machine => machine.id === formModel.value.id);
      if (index !== -1) {
        machines.value[index] = updatedMachine;
      }
    } else {
      // 如果有本地图片需要上传，先上传图片获取原始路径
      if (imageToUpload) {
        try {
          const response = await fetch(imageToUpload);
          const blob = await response.blob();
          const file = new File([blob], `${formData.model || 'machine'}_thumb.jpg`, { type: blob.type });

          const thumbFormData = new FormData();
          thumbFormData.append('file', file);

          // 上传图片并生成缩略图
          const thumbResult: any = await uploadMachineThumbGeneric(thumbFormData);

          // 由于request自动解包，我们需要直接使用结果
          if (thumbResult && thumbResult.original_path) {
            // 使用原始图片路径更新表单数据
            safeFormData.image = thumbResult.original_path;
            console.log('使用上传的原始图片路径:', thumbResult.original_path);
          } else {
            ElMessage.warning('图片上传失败，使用默认图片');
          }
        } catch (thumbError) {
          console.error('上传设备图片失败:', thumbError);
          ElMessage.warning('图片上传失败，使用默认图片');
        }
      }

      // 创建新设备
      const newMachine = await createMachineNew(safeFormData);
      ElMessage.success('设备创建成功');

      dialogVisible.value = false;

      // 直接添加到本地数据
      machines.value.unshift(newMachine);
      total.value++;
    }
  } catch (error) {
    console.error('保存设备失败:', error);
    ElMessage.error('保存设备失败');
  }
};
const confirmDelete = async (row: Machine) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除设备 "${row.model}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await deleteMachineNew(row.id);
    ElMessage.success('设备删除成功');

    // 直接从本地数据中移除已删除的设备，而不是重新获取完整列表
    const index = machines.value.findIndex(machine => machine.id === row.id);
    if (index !== -1) {
      machines.value.splice(index, 1);
      total.value--;
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除设备失败:', error);
      ElMessage.error('删除设备失败');
    }
  }
};

// 辅助函数
const getMachineTypeText = (type: number) => {
  const types = {
    0: '主机',
    1: '配件',
    2: '工具',
    3: '耗材'
  };
  return types[type as keyof typeof types] || '未知';
};

const isCurrentUserAdmin = () => {
  return getCurrentUserRole() === 'admin';
};

// 获取缩略图路径的辅助函数
const getThumbnailPath = (originalPath: string) => {
  // 如果 originalPath 为空或为默认图片，则直接返回
  if (!originalPath || originalPath.endsWith('sample.png')) {
    return originalPath;
  }

  // 检查文件名是否已经包含 _thumb 后缀
  const pathParts = originalPath.split('/');
  const fileName = pathParts[pathParts.length - 1];

  if (fileName.includes('_thumb.')) {
    // 如果已经是缩略图路径，直接返回
    return originalPath;
  } else {
    // 如果不是缩略图路径，生成缩略图路径
    const dirPath = pathParts.slice(0, -1).join('/');
    const fileBase = fileName.split('.')[0];
    const fileExt = fileName.split('.')[1];
    return `${dirPath}/${fileBase}_thumb.${fileExt}`;
  }
};

// 回收站相关函数
const openRecycleBinDialog = async () => {
  recycleBinCurrentPage.value = 1;
  await loadDeletedMachines();
  recycleBinDialogVisible.value = true;
};

const closeRecycleBinDialog = () => {
  recycleBinDialogVisible.value = false;
};

const loadDeletedMachines = async () => {
  recycleBinLoading.value = true;
  try {
    const response = await getDeletedMachines({
      page: recycleBinCurrentPage.value,
      per_page: recycleBinPageSize.value
    });

    deletedMachines.value = response.machines || [];
    recycleBinTotal.value = response.total || 0;
  } catch (error) {
    console.error('获取回收站设备失败:', error);
    ElMessage.error('获取回收站设备失败');
  } finally {
    recycleBinLoading.value = false;
  }
};

const handleRecycleBinSizeChange = (size: number) => {
  recycleBinPageSize.value = size;
  recycleBinCurrentPage.value = 1;
  loadDeletedMachines();
};

const handleRecycleBinCurrentChange = (page: number) => {
  recycleBinCurrentPage.value = page;
  loadDeletedMachines();
};

const restoreMachine = async (id: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要恢复此设备吗？恢复后设备将重新出现在设备列表中。',
      '确认恢复',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await restoreMachineFromRecycleBin(id);
    ElMessage.success('设备恢复成功');

    // 从回收站列表中移除该设备
    const index = deletedMachines.value.findIndex(machine => machine.id === id);
    if (index !== -1) {
      deletedMachines.value.splice(index, 1);
      recycleBinTotal.value--;
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复设备失败:', error);
      ElMessage.error('恢复设备失败');
    }
  }
};

const permanentDeleteMachine = async (id: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要永久删除此设备吗？此操作不可恢复！',
      '确认永久删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await request.delete(`/api/machines_new/recycle-bin/${id}/permanent-delete`);
    ElMessage.success('设备已永久删除');

    // 从回收站列表中移除该设备
    const index = deletedMachines.value.findIndex(machine => machine.id === id);
    if (index !== -1) {
      deletedMachines.value.splice(index, 1);
      recycleBinTotal.value--;
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('永久删除设备失败:', error);
      ElMessage.error('永久删除设备失败');
    }
  }
};

// 处理回收站表格多选
const handleRecycleBinSelectionChange = (selection: any[]) => {
  selectedDeletedMachines.value = selection.map(item => item.id);
};

// 批量永久删除单个设备
// const permanentDeleteMachine = async (id: number) => {
//   try {
//     await request.delete(`/api/machines_new/${id}/permanent_delete`);
//   } catch (error) {
//     console.error(`删除设备 ${id} 失败:`, error);
//     throw error; // 重新抛出错误以被调用方捕获
//   }
// };

// 批量永久删除设备
const batchPermanentDeleteMachines = async (ids: number[]) => {
  try {
    // 使用Promise.all来并行删除多个设备
    const promises = ids.map(id => request.delete(`/api/machines_new/${id}/permanent_delete`));
    await Promise.all(promises);
  } catch (error) {
    console.error('批量永久删除设备失败:', error);
    throw error; // 重新抛出错误
  }
};

// 批量永久删除
const batchPermanentDelete = async () => {
  if (selectedDeletedMachines.value.length === 0) {
    ElMessage.warning('请先选择要删除的设备');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要永久删除选中的 ${selectedDeletedMachines.value.length} 台设备吗？此操作不可恢复！`,
      '确认批量永久删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await batchPermanentDeleteMachines(selectedDeletedMachines.value);
    ElMessage.success(`成功永久删除了 ${selectedDeletedMachines.value.length} 台设备`);

    // 重新加载回收站数据
    await loadDeletedMachines();
    selectedDeletedMachines.value = []; // 清空选中项
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量永久删除设备失败:', error);
      ElMessage.error('批量永久删除设备失败');
    }
  }
};

// 清空回收站
const clearRecycleBin = async () => {
  if (recycleBinTotal.value === 0) {
    ElMessage.info('回收站已经是空的');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要清空回收站吗？将永久删除所有 ${recycleBinTotal.value} 台设备，此操作不可恢复！`,
      '确认清空回收站',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await request.delete('/api/machines_new/recycle-bin/clear');
    ElMessage.success('回收站已清空');

    // 重新加载回收站数据
    await loadDeletedMachines();
    selectedDeletedMachines.value = []; // 清空选中项
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空回收站失败:', error);
      ElMessage.error('清空回收站失败');
    }
  }
};

// 价格系数管理相关方法
const openCoefficientDialog = async () => {
  try {
    // 获取当前系数
    const response = await request.get('/api/config/show_price_coefficient');
    // 由于后端现在返回 {success: true, data: {coefficient: "1.05"}} 格式
    // request.ts会自动解包为 {coefficient: "1.05"}，即data部分
    if (response && typeof response === 'object' && 'coefficient' in response) {
      currentCoefficient.value = parseFloat(response.coefficient);
    } else {
      ElMessage.error('获取当前系数失败，响应格式不正确');
    }
  } catch (error) {
    console.error('获取系数失败:', error);
    ElMessage.error('获取当前系数失败');
  }
  coefficientDialogVisible.value = true;
};

const closeCoefficientDialog = () => {
  coefficientDialogVisible.value = false;
};

const updateCoefficient = async () => {
  try {
    const response = await request.post('/api/config/show_price_coefficient', {
      coefficient: currentCoefficient.value
    });

    // request.ts会自动解包响应，成功时返回data字段的内容
    ElMessage.success('系数更新成功');
    coefficientDialogVisible.value = false;
    // 重新加载设备列表以显示新的价格
    await fetchMachines();
  } catch (error) {
    console.error('更新系数失败:', error);
    ElMessage.error('系数更新失败');
  }
};

// 处理其他功能菜单命令
const handleOtherFunction = async (command: string) => {
  switch (command) {
    case 'coefficient':
      openCoefficientDialog();
      break;
    case 'recycle':
      openRecycleBinDialog();
      break;
    case 'clear':
      confirmClearAllData();
      break;
    case 'import':
      openImportDialog();
      break;
    case 'export':
      handleExport();
      break;
    default:
      console.warn('未知的菜单命令:', command);
  }
};

// 清空数据相关方法
const confirmClearAllData = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有设备数据吗？此操作不可恢复！',
      '确认清空数据',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await clearAllData();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空数据失败:', error);
      ElMessage.error('清空数据失败');
    }
  }
};

const clearAllData = async () => {
  try {
    const response = await request.delete('/api/machines_new/clear-all');
    ElMessage.success('数据已清空');
    // 重新加载设备列表
    await fetchMachines();
  } catch (error) {
    console.error('清空数据失败:', error);
    ElMessage.error('清空数据失败');
  }
};

// 自定义属性相关数据
const customAttrsList = ref<{key: string, value: string}[]>([]);

// 解析JSON为自定义属性列表（仅在打开编辑对话框时调用）
const parseCustomAttrsFromJson = (jsonStr: string) => {
  if (!jsonStr) jsonStr = '{}';
  try {
    // 解析JSON为对象
    const jsonObj = JSON.parse(jsonStr);
    // 转换为[{key: '', value: ''}]格式，保持原有顺序
    const list: {key: string, value: string}[] = [];
    for (const [k, v] of Object.entries(jsonObj)) {
      list.push({
        key: k,
        value: String(v)
      });
    }
    // 若无数据，默认加一个空项
    customAttrsList.value = list.length > 0 ? list : [{ key: '', value: '' }];
  } catch (e) {
    // 解析失败，给出提示
    console.error('JSON解析错误：', e);
    customAttrsList.value = [{ key: '', value: '' }];
  }
};

// 新增自定义字段
const addCustomAttr = () => {
  customAttrsList.value.push({ key: '', value: '' });
};

// 删除自定义字段
const removeCustomAttr = (index: number) => {
  customAttrsList.value.splice(index, 1);
};

// 同步动态列表回JSON字符串（仅在保存时调用）
const syncCustomAttrsToJson = () => {
  // 过滤空键的项
  const validList = customAttrsList.value.filter(item => item.key.trim());
  // 使用Map来保持顺序
  const map = new Map();
  validList.forEach(item => {
    map.set(item.key.trim(), item.value.trim());
  });
  // 转为格式化的JSON字符串
  formModel.value.custom_attrs = JSON.stringify(Object.fromEntries(map), null, 2);
};

// 导入导出相关方法
const openImportDialog = () => {
  importStep.value = 0;
  importJsonData.value = '';
  importPreviewData.value = [];
  importPreviewTotal.value = 0;
  importResult.value = {
    success: false,
    message: '',
    imported_count: 0,
    failed_count: 0
  };
  importDialogVisible.value = true;
};

const handleImportDialogClose = () => {
  importDialogVisible.value = false;
};

const prevImportStep = () => {
  if (importStep.value > 0) {
    importStep.value--;
  }
};

const nextImportStep = async () => {
  if (importStep.value === 0) {
    // 第一步：解析并预览数据
    try {
      const parsedData = JSON.parse(importJsonData.value);
      if (!Array.isArray(parsedData)) {
        throw new Error('数据格式错误，应为数组格式');
      }

      // 限制预览数量为前5条
      importPreviewData.value = parsedData.slice(0, 5).map(item => ({
        model: item.Model || item.model || '',
        original_model: item.OriginalModel || item.original_model || '',
        brand: item.brand || item.Brand || '',
        machine_weight: item.MachineWeight || item.machine_weight || '',
        show_price: item.ShowPrice || item.show_price || 0
      }));

      importPreviewTotal.value = parsedData.length;
      importStep.value = 1;
    } catch (error) {
      ElMessage.error(`JSON格式错误: ${error.message}`);
    }
  } else if (importStep.value === 1) {
    // 第二步：开始导入
    try {
      const data = JSON.parse(importJsonData.value);
      const response = await importMachinesNewJson(data);

      // 由于request.ts的拦截器已经解包了数据，response直接包含了解析后的data内容
      importResult.value = {
        success: true, // 前面的await没有抛出异常，说明请求成功
        message: `成功导入 ${response.imported_count || 0} 条，失败 ${response.failed_count || 0} 条`,
        imported_count: response.imported_count || 0,
        failed_count: response.failed_count || 0
      };

      importStep.value = 2;

      // 导入完成后，无论成功或失败都刷新数据，确保显示最新状态
      fetchMachines();
    } catch (error: any) {
      console.error('导入设备失败:', error);
      importResult.value = {
        success: false,
        message: error.message || error || '导入失败',
        imported_count: 0,
        failed_count: 0
      };
      importStep.value = 2;
    }
  }
};

const handleRowClick = (row: Machine) => {
  // 检查用户是否有编辑权限
  if (!hasRoutePermission('machine_manage')) {
    ElMessage.warning('您没有编辑设备的权限');
    return;
  }

  openEditDialog(row);
};

const handleExport = async () => {
  try {
    const response = await exportMachinesNewJson();
    if (response && response.data) {
      // 将数据转换为JSON字符串并下载
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `machines_new_export_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      ElMessage.success('导出成功');
    } else {
      ElMessage.error('导出失败，未获取到数据');
    }
  } catch (error) {
    console.error('导出设备失败:', error);
    ElMessage.error('导出失败');
  }
};

// 设置上传预览组件引用
const setUploadPreviewRef = (el: any) => {
  // 由于这是设备管理中的上传，使用一个固定的key，这里使用'new'表示新增设备
  if (el) {
    uploadPreviewRefs.value['new'] = el;
  } else {
    delete uploadPreviewRefs.value['new'];
  }
};

// 处理图片上传成功
const onImageUploadSuccess = async (files: File[], mediaFiles: any[] = []) => {
  if (files && files.length > 0) {
    // 如果是编辑模式且有设备ID，直接上传到后端
    if (isEdit.value && formModel.value.id) {
      try {
        const formData = new FormData();
        // 添加第一个文件（缩略图）
        formData.append('file', files[0]);

        // 使用专门的缩略图上传API
        const result: any = await uploadMachineThumb(formModel.value.id as number, formData);

        // 由于request自动解包，我们需要直接使用结果
        // 后端现在返回格式为 { machine: {...}, new_thumb_path: "...", original_path: "..." }
        if (result && result.original_path) {
          // 更新设备的图片路径为原始路径（后端已保存原始路径到数据库）
          formModel.value.image = result.original_path;
          ElMessage.success('设备图片上传成功');

          // 更新列表中对应设备的图片路径
          const index = machines.value.findIndex(m => m.id === formModel.value.id);
          if (index !== -1) {
            machines.value[index].image = result.original_path;
          }
        } else {
          // 如果解包后的数据不符合预期，可能说明后端返回了错误格式
          ElMessage.error('图片上传失败，响应格式异常');
        }
      } catch (error) {
        console.error('上传图片失败:', error);
        ElMessage.error('上传图片失败');
      }
    } else {
      // 如果是新增模式，暂时保存为本地预览URL，等保存设备时再上传
      const file = files[0];
      const fileUrl = URL.createObjectURL(file);
      formModel.value.image = fileUrl;
      ElMessage.success('图片已选择，保存设备时将上传');
    }
  }
};

// 处理图片上传失败
const onImageUploadFailure = (error: any) => {
  console.error('图片上传失败：', error);
  ElMessage.error('图片上传失败');
};

// 处理剪贴板图片上传
const onUploadClipboardImage = async (response: any, file: File, commId: number) => {
  try {
    // 检查文件类型 - 支持图片
    if (!file.type.startsWith('image/')) {
      ElMessage.error('请选择图片文件');
      return;
    }

    // 验证文件类型
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];

    if (!allowedImageExts.includes(ext)) {
      ElMessage.error(`不支持的图片格式：${ext}，支持的格式：${allowedImageExts.join(', ')}`);
      return;
    }

    // 显示成功消息
    ElMessage.success(`已添加图片: ${file.name}`);
  } catch (error) {
    console.error('添加剪贴板图片失败:', error);
    ElMessage.error('添加剪贴板图片失败');
  }
};

// 组件挂载时获取数据
onMounted(() => {
  fetchMachines();
});
</script>

<style scoped>
.machine-management-container {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.content-wrapper {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.search-and-actions {
  margin-bottom: 20px;
}

.text-right {
  text-align: right;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.import-step-content {
  margin-top: 20px;
}

.import-tips {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.import-tips ul {
  margin: 5px 0;
  padding-left: 20px;
}

.import-tips li {
  margin: 3px 0;
}

.preview-info {
  margin-top: 10px;
  font-weight: bold;
  color: #606266;
}

.custom-attr-error {
  color: #f56c6c;
  font-size: 12px;
  margin-bottom: 8px;
}

.custom-attr-item {
  margin-bottom: 8px;
}

/* 回收站对话框样式 */
.recycle-bin-content {
  max-height: 70vh;
  overflow-y: auto;
}

.current-image-preview {
  margin-top: 10px;
}

.coefficient-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}
</style>