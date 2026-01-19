<template>
  <div class="order-inspection-container">
    <div class="header">
      <div class="header-content">
        <el-page-header @back="goBack" content="订单验收" />
      </div>
    </div>

    <!-- 订单列表 -->
    <div class="order-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>待验收订单列表</span>
          </div>
        </template>

        <el-table
          :data="orders"
          style="width: 100%"
          @row-click="showOrderDetails"
          v-loading="loading"
        >
          <el-table-column prop="contract_no" label="合同编号" width="150" />
          <el-table-column prop="machine_name" label="名称" width="150" />
          <el-table-column prop="machine_model" label="机型" width="120" />
          <el-table-column prop="order_time" label="下单时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.order_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="ship_time" label="出货时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.ship_time) }}
            </template>
          </el-table-column>
          <el-table-column label="检查完成进度" width="150">
            <template #default="scope">
              <div style="cursor: pointer; display: flex; flex-direction: column; align-items: center;" @click.stop="showOrderDetails(scope.row)">
                <div style="width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                  <div :style="{width: `${getOrderInspectionProgress(scope.row.id)}%`, height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                </div>
                <div class="progress-text" style="margin-top: 2px;">
                  {{ getOrderInspectionFraction(scope.row.id) }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" v-if="isUserAdmin">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
              @click="generateReport(scope.row)"
              >
                <el-icon style="margin-right: 5px;"><List /></el-icon> 查看报告
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          class="pagination"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </el-card>
    </div>

    <!-- 订单验收详情弹窗（整合了订单详情和验收管理） -->
    <el-dialog
      v-model="orderDetailDialogVisible"
      :title="`订单验收详情 - ${selectedOrderDetail?.contract_no || selectedOrder?.contract_no || ''}`"
      width="80%"
      :before-close="handleCloseOrderDetailDialog"
    >
      <div v-if="selectedOrderDetail || selectedOrder">
        <!-- 订单基础信息 -->
        <el-card class="order-info-card">
          <template #header>
            <div class="card-header">
              <span>订单基础数据</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="合同编号">{{ (selectedOrderDetail || selectedOrder).contract_no }}</el-descriptions-item>
            <el-descriptions-item label="订单编号">{{ (selectedOrderDetail || selectedOrder).order_no }}</el-descriptions-item>
            <el-descriptions-item label="包装机单号">{{ (selectedOrderDetail || selectedOrder).machine_no }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ (selectedOrderDetail || selectedOrder).machine_name }}</el-descriptions-item>
            <el-descriptions-item label="机型">{{ (selectedOrderDetail || selectedOrder).machine_model }}</el-descriptions-item>
            <el-descriptions-item label="主机数量">{{ (selectedOrderDetail || selectedOrder).machine_count }}</el-descriptions-item>
            <el-descriptions-item label="下单时间">{{ formatDate((selectedOrderDetail || selectedOrder).order_time) }}</el-descriptions-item>
            <el-descriptions-item label="出货时间">{{ formatDate((selectedOrderDetail || selectedOrder).ship_time) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 检查项区域 -->
        <el-card class="inspection-items-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span style="font-size: 30px;">检查项</span>
              <div>
                <el-button
                  v-if="isUserAdmin"
                  type="danger"
                  style="font-size: 20px; padding: 15px; margin-right: 10px;"
                  @click="clearAllItems"
                >
                  清空检查项
                </el-button>
                <el-button
                  v-if="isUserAdmin"
                  type="success"
                  style="font-size: 20px; padding: 15px;"
                  @click="showAddItemDialog('parent')"
                >
                  添加项目
                </el-button>
              </div>
            </div>
          </template>

          <!-- 检查项列表 -->
          <div v-for="parentItem in groupedItems" :key="parentItem.id" class="inspection-group">
            <div class="parent-item">
              <div class="parent-header">
                <div class="parent-title-container">
                  <span
                    v-if="!parentItem.isEditing"
                    class="parent-title"
                    @click="startEditing(parentItem, 'parent')"
                    style="cursor: pointer;"
                  >
                    {{ parentItem.item_category }}
                  </span>
                  <div class="parent-progress">
                    <div style="margin-left: 10px; width: 100px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                      <div :style="{width: `${parentItem.progress}%`, height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                    </div>
                    <span class="progress-text">{{ getParentItemFraction(parentItem) }}</span>
                  </div>
                </div>
                <!-- 大项的标题后的删除及添加按钮 -->
                <el-icon
                  v-if="isUserAdmin"
                  type="danger"
                  size="small"
                  @click="deleteItem(parentItem)"
                  style="margin-right: 10px;cursor:pointer;font-size: 25px;"
                ><Delete /></el-icon>
                <el-icon
                  v-if="isUserAdmin"
                  type="primary"
                  size="small"
                  @click="addSubItemToParent(parentItem.id, parentItem.item_category)"
                  style="margin-right: 10px;cursor:pointer;font-size: 20px;"
                ><Plus /></el-icon>
              </div>
              <div class="sub-items">
                <div
                  v-for="subItem in parentItem.children"
                  :key="subItem.id"
                  class="sub-item"
                >
                  <div class="sub-item-header">
                    <div class="sub-item-name-container">
                      <span
                        v-if="!subItem.isEditing"
                        class="sub-item-name"
                        @click="startEditing(subItem, 'sub')"
                        style="cursor: pointer;"
                      >
                        {{ subItem.item_name }}
                      </span>
                    </div>
                    <div class="sub-item-actions">
                      <el-radio-group
                        v-model="subItem.inspection_result"
                        @change="updateInspectionItem(subItem)"
                      >
                        <el-radio value="pending">未检查</el-radio>
                        <el-radio value="normal">正常</el-radio>
                        <el-radio value="defect">不正常</el-radio>
                        <el-radio value="not_applicable">没此项</el-radio>
                      </el-radio-group>
                      <!-- 小项的标题后的删除及添加按钮 -->
                      <el-icon
                        v-if="isUserAdmin"
                        type="danger"
                        size="small"
                        @click="deleteItem(subItem)"
                        style="margin-left:25px;font-size: 20px;cursor:pointer;"
                      ><Delete /></el-icon>
                    </div>
                  </div>
                  <div class="sub-item-content">
                    <div v-if="subItem.inspection_result === 'normal'" class="upload-section">
                      <!-- 展示多张图片 -->
                      <div class="photo-grid">
                        <div
                          v-for="(photo, index) in getPhotoPaths(subItem.photo_path)"
                          :key="index"
                          class="photo-preview"
                          @click="showImagePreview(getPhotoUrl(photo))"
                        >
                          <img :src="getPhotoUrl(photo)" :alt="`正常照片${index + 1}`" style="max-width: 100px; max-height: 100px; cursor: pointer;">
                          <el-icon
                            class="delete-photo-icon"
                            @click.stop="removePhoto(subItem, photo)"
                            style="position: absolute; top: -8px; right: -8px; background: red; border-radius: 50%; color: white; cursor: pointer;"
                          >
                            <Close />
                          </el-icon>
                        </div>
                      </div>
                      <el-upload
                        class="upload-demo"
                        :auto-upload="true"
                        :show-file-list="false"
                        list-type="picture"
                        :http-request="(options) => handlePhotoUpload(options, subItem, 'normal')"
                      >
                      <el-icon style="cursor: pointer;border: 1px ;margin-left: 2cqw;font-size: 25px;background-color: #ddd;padding: 8px;border-radius: 5px;">
                        <Plus />
                      </el-icon>

                      </el-upload>
                  </div>
                <div v-if="subItem.inspection_result === 'defect'" class="defect-section">
                  <!-- 展示多张图片 -->
                  <div class="photo-grid">
                    <div
                      v-for="(photo, index) in getPhotoPaths(subItem.photo_path)"
                      :key="index"
                      class="photo-preview"
                      @click="showImagePreview(getPhotoUrl(photo))"
                    >
                      <img :src="getPhotoUrl(photo)" :alt="`缺陷照片${index + 1}`" style="max-width: 100px; max-height: 100px; cursor: pointer;">
                      <el-icon
                        class="delete-photo-icon"
                        @click.stop="removePhoto(subItem, photo)"
                        style="position: absolute; top: -8px; right: -8px; background: red; border-radius: 50%; color: white; cursor: pointer;"
                      >
                        <Close />
                      </el-icon>
                    </div>
                  </div>

                  <el-input
                    v-model="subItem.description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入缺陷描述"
                    @blur="updateInspectionItem(subItem)"
                  />

                  <el-upload
                    class="upload-demo"
                    :auto-upload="true"
                    :show-file-list="false"
                    list-type="picture"
                    style="display: inline-flex; margin-left: 15px;"
                    :http-request="(options) => handlePhotoUpload(options, subItem, 'defect')"
                  >
                    <el-icon style=" cursor: pointer;border: 1px ;font-size: 25px;background-color: #ddd;padding: 8px;border-radius: 5px;">
                      <Plus />
                    </el-icon>

                  </el-upload>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- 添加的独立检查项（没有父项的） -->
          <div v-for="item in standaloneItems" :key="item.id" class="standalone-item">
            <div class="sub-item-header">
              <div class="sub-item-name-container">
                <span
                  v-if="!item.isEditing"
                  class="sub-item-name"
                  @click="startEditing(item, 'sub')"
                  style="cursor: pointer;"
                >
                  {{ item.item_name }}
                </span>
                <el-input
                  v-else
                  v-model="item.editingValue"
                  @blur="finishEditing(item, 'sub')"
                  @keyup.enter="finishEditing(item, 'sub')"
                />
              </div>
              <div class="sub-item-actions">
                <el-radio-group
                  v-model="item.inspection_result"
                  @change="updateInspectionItem(item)"
                >
                  <el-radio value="pending">未检查</el-radio>
                  <el-radio value="normal">正常</el-radio>
                  <el-radio value="defect">不正常</el-radio>
                  <el-radio value="not_applicable">没此项</el-radio>
                </el-radio-group>
                <!-- <el-button
                  v-if="isUserAdmin"
                  type="danger"
                  size="small"
                  icon="Delete"
                  @click="deleteItem(item)"
                  circle
                  style="margin-left: 10px;"
                /> -->
              </div>
            </div>

            <div class="sub-item-content" v-if="item.inspection_result !== 'not_applicable' && item.inspection_result !== 'pending'">
              <div v-if="item.inspection_result === 'normal'" class="upload-section">
                <el-upload
                  class="upload-demo"
                  :auto-upload="true"
                  :show-file-list="false"
                  list-type="picture"
                  :http-request="(options) => handlePhotoUpload(options, item, 'normal')"
                >
                  <!-- <el-button type="primary" style="font-size: 15px;padding:5px;margin-bottom: 10px;">上传照片</el-button> -->
                </el-upload>
                <!-- 展示多张图片 -->
                <div class="photo-grid">
                  <div
                    v-for="(photo, index) in getPhotoPaths(item.photo_path)"
                    :key="index"
                    class="photo-preview"
                    @click="showImagePreview(getPhotoUrl(photo))"
                  >
                    <img :src="getPhotoUrl(photo)" :alt="`正常照片${index + 1}`" style="max-width: 100px; max-height: 100px; cursor: pointer;">
                    <el-icon
                      class="delete-photo-icon"
                      @click.stop="removePhoto(item, photo)"
                      style="position: absolute; top: -8px; right: -8px; background: red; border-radius: 50%; color: white; cursor: pointer;"
                    >
                      <Close />
                    </el-icon>
                  </div>
                </div>
              </div>

              <div v-if="item.inspection_result === 'defect'" class="defect-section">
                <!-- <el-upload
                  class="upload-demo"
                  :auto-upload="true"
                  :show-file-list="false"
                  list-type="picture"
                  :http-request="(options) => handlePhotoUpload(options, item, 'defect')"
                >
                  <el-button style="font-size: 15px; margin-bottom: 10px;" type="danger">上传缺陷照片</el-button>
                </el-upload> -->
                <!-- 展示多张图片 -->
                <div class="photo-grid">
                  <div
                    v-for="(photo, index) in getPhotoPaths(item.photo_path)"
                    :key="index"
                    class="photo-preview"
                    @click="showImagePreview(getPhotoUrl(photo))"
                  >
                    <img :src="getPhotoUrl(photo)" :alt="`缺陷照片${index + 1}`" style="max-width: 100px; max-height: 100px; cursor: pointer;">
                    <el-icon
                      class="delete-photo-icon"
                      @click.stop="removePhoto(item, photo)"
                      style="position: absolute; top: -8px; right: -8px; background: red; border-radius: 50%; color: white; cursor: pointer;"
                    >
                      <Close />
                    </el-icon>
                  </div>
                </div>
                <el-input
                  v-model="item.description"
                  type="textarea"
                  :rows="3"
                  style="margin-top:10px;"
                  placeholder="请输入缺陷描述"
                  @blur="updateInspectionItem(item)"
                />
              </div>
            </div>
          </div>

          <!-- 在所有大项最后添加+按钮 -->
          <div class="add-new-parent-section" v-if="isUserAdmin">
            <el-icon
              size="default"
              @click="addNewParentItem"
              style="cursor:pointer;
              width: 98%;
              border-radius: 5px;
              border:1px solid #d3dce6;
              padding:10px; margin-top: 5px;font-size: 25px;  background-color:#ffffff;"
            >
              <Plus />
            </el-icon>
          </div>
        </el-card>
        <!-- 底部操作区域 -->
        <div class="bottom-actions">
          <div class="progress-summary">
            <p>检查项进度：{{ realTimeProgress.completed_items }} / {{ realTimeProgress.total_items }}</p>
          </div>
          <div class="action-buttons">
            <el-button
              type="success"
              @click="generateReport"
            >
              <el-icon style="margin-right: 5px;"><List /></el-icon>生成报告
            </el-button>
            <el-button @click="cacheData">缓存</el-button>
            <el-button @click="closeDialog">关闭</el-button>
            <el-button
              type="primary"
              @click="saveAndClose"
            >
              保存
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 添加检查项对话框 -->
    <el-dialog
      v-model="addItemDialogVisible"
      title="添加检查项"
      width="500px"
      :before-close="closeAddItemDialog"
    >
      <el-form :model="newItemForm" :rules="itemRules" ref="itemFormRef" label-width="100px">
        <el-form-item label="类型" prop="itemType">
                      <el-radio-group v-model="newItemForm.itemType">
                        <el-radio value="parent">大项</el-radio>
                        <el-radio value="sub">细项</el-radio>
                      </el-radio-group>        </el-form-item>

        <el-form-item
          label="大项"
          prop="parentItem"
          v-if="newItemForm.itemType === 'sub'"
        >
          <el-select
            v-model="newItemForm.parentItem"
            placeholder="请选择大项"
            style="width: 100%"
          >
            <el-option
              v-for="item in parentItems"
              :key="item.id"
              :label="item.item_category"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          label="名称"
          prop="itemName"
        >
          <el-input
            v-model="newItemForm.itemName"
            :placeholder="newItemForm.itemType === 'parent' ? '请输入大项名称，如：配件、外观等' : '请输入细项名称，如：部件1、角度1等'"
            required
            />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeAddItemDialog">取消</el-button>
          <el-button type="primary" @click="confirmAddItem">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改检查项标题对话框 -->
    <el-dialog
      v-model="editItemTitleDialogVisible"
      :title="titleEditingType === 'parent' ? '修改大项标题' : '修改细项标题'"
      width="500px"
      :before-close="closeEditItemTitleDialog"
    >
      <el-input
        v-model="titleEditingValue"
        :placeholder="titleEditingType === 'parent' ? '请输入大项标题' : '请输入细项标题'"
        maxlength="200"
        show-word-limit
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeEditItemTitleDialog">取消</el-button>
          <el-button type="primary" @click="confirmEditItemTitle">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="imagePreviewVisible"
      :show-close="true"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
      width="auto"
      top="5vh"
      class="image-preview-dialog"
    >
      <div style="text-align: center;">
        <img :src="previewImageUrl" style="max-width: 90vw; max-height: 80vh; object-fit: contain;" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { Delete, Plus, Close, List } from '@element-plus/icons-vue';
import { uploadFile, moveFile, deleteFile, sanitizeFilename } from '@/utils/upload';

// 响应式数据
const orders = ref<any[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const detailDialogVisible = ref(false);
const orderDetailDialogVisible = ref(false);
const addItemDialogVisible = ref(false);
const addSubItemDialogVisible = ref(false);
const editItemTitleDialogVisible = ref(false); // 新增：修改标题对话框
const selectedOrder = ref<any>({});
const selectedOrderDetail = ref<any>(null);
const selectedInspection = ref<any>(null);
const items = ref<any[]>([]);
const token = ref(localStorage.getItem('oa_token') || '');
const isEditingMode = ref(false);
const hasUnsavedChangesFlag = ref(false); // 跟踪是否有未保存的更改

// 标题编辑相关变量
const titleEditingItem = ref<any>(null); // 当前正在编辑的项目
const titleEditingValue = ref(''); // 编辑框的值
const titleEditingType = ref<'parent' | 'sub'>('sub'); // 编辑类型

// 新检查项表单
const newItemForm = ref({
  itemType: 'sub', // 'parent' 或 'sub'
  parentItem: null as number | null,
  itemName: '',
  itemCategory: '' // 用于父项的类别
});

const itemRules = {
  itemType: [
    { required: true, message: '请选择类型', trigger: 'change' }
  ],
  itemName: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ]
};

// 图片预览相关变量
const imagePreviewVisible = ref(false);
const previewImageUrl = ref('');



// 计算属性
const groupedItems = computed(() => {
  return items.value
    .filter((item: any) => item.item_type === 'parent' && !item._toBeDeleted)
    .map((parent: any) => {
      const children = items.value.filter((child: any) => child.parent_id === parent.id && !child._toBeDeleted);
      return {
        ...parent,
        children: children,
        completed_children: children.filter((child: any) => {
          if (child.inspection_result === 'normal' && child.photo_path) {
            // 正常状态需要有照片
            return true;
          } else if (child.inspection_result === 'not_applicable') {
            // 无此项直接算完成
            return true;
          } else if (child.inspection_result === 'defect' && child.photo_path && child.description) {
            // 不正常状态需要有照片和描述
            return true;
          }
          return false;
        }).length,
        total_children: children.length,
        progress: children.length > 0
          ? Math.round((children.filter((child: any) => {
              if (child.inspection_result === 'normal' && child.photo_path) {
                // 正常状态需要有照片
                return true;
              } else if (child.inspection_result === 'not_applicable') {
                // 无此项直接算完成
                return true;
              } else if (child.inspection_result === 'defect' && child.photo_path && child.description) {
                // 不正常状态需要有照片和描述
                return true;
              }
              return false;
            }).length / children.length) * 100)
          : 0
      };
    });
});

const standaloneItems = computed(() => {
  return items.value.filter((item: any) => item.item_type === 'sub' && item.parent_id === null && !item._toBeDeleted);
});

const parentItems = computed(() => {
  return items.value.filter((item: any) => item.item_type === 'parent' && !item._toBeDeleted);
});

// 提交按钮是否可点击的条件
const canSubmit = computed(() => {
  if (!selectedInspection.value) return false;

  // 所有细项都必须完成（正常项有照片，缺陷项有照片加描述，无此项直接完成）
  // 但允许有pending状态的检查项（提交时会提示）
  const allSubItems = items.value.filter((item: any) => item.item_type === 'sub' && !item._toBeDeleted);

  if (allSubItems.length === 0) {
    return false; // 如果没有检查项，不能提交
  }

  for (const item of allSubItems) {
    if (item.inspection_result === 'normal' && !item.photo_path) {
      return false;
    }
    if (item.inspection_result === 'defect' && (!item.photo_path || !item.description)) {
      return false;
    }
  }

  return true; // 所有检查项都符合要求
});

// 获取用户角色
const userRole = ref('');
const isUserAdmin = computed(() => userRole.value === 'admin');
const isUserGeneral = computed(() => userRole.value !== 'admin');

// 实时计算验收进度
const realTimeProgress = computed(() => {
  // 统计所有细项（sub items）
  const allSubItems = items.value.filter((item: any) => item.item_type === 'sub' && !item._toBeDeleted);
  const totalItems = allSubItems.length;

  // 统计已完成的细项
  const completedItems = allSubItems.filter((item: any) => {
    if (item.inspection_result === 'normal' && item.photo_path) {
      // 正常状态需要有照片
      return true;
    } else if (item.inspection_result === 'not_applicable') {
      // 无此项直接算完成
      return true;
    } else if (item.inspection_result === 'defect' && item.photo_path && item.description) {
      // 不正常状态需要有照片和描述
      return true;
    }
    return false;
  }).length;

  // 计算进度百分比
  const progress = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

  return {
    total_items: totalItems,
    completed_items: completedItems,
    progress: progress
  };
});

// 上传配置
const uploadUrl = computed(() => {
  // 开发环境下使用代理，生产环境下使用完整URL
  if (import.meta.env.MODE === 'development') {
    return '/api/upload';
  }
  return `${window.location.protocol}//${window.location.hostname}:5000/api/upload`;
});

const uploadHeaders = computed(() => {
  return {
    'Authorization': `Bearer ${token.value}`
  };
});

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
};

// 显示订单详情
const showOrderDetails = async (row: any) => {
  selectedOrderDetail.value = { ...row };
  orderDetailDialogVisible.value = true;

  // 获取或创建验收数据
  await refreshInspectionData();
};

// 关闭订单详情对话框
const handleCloseOrderDetailDialog = () => {
  orderDetailDialogVisible.value = false;
  selectedOrderDetail.value = null;
  selectedInspection.value = null;
  items.value = [];
};

// 显示添加检查项对话框
const showAddItemDialog = (type: 'parent' | 'sub') => {
  newItemForm.value = {
    itemType: type,
    parentItem: null,
    itemName: '',
    itemCategory: type === 'parent' ? '' : (parentItems.value.length > 0 ? parentItems.value[0].item_category : '')
  };
  addItemDialogVisible.value = true;
};


// 关闭添加检查项对话框
const closeAddItemDialog = () => {
  addItemDialogVisible.value = false;
};

// 确认添加检查项
const confirmAddItem = () => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    ElMessage.error('请先选择一个订单');
    return;
  }

  // 验证名称输入框不能为空
  if (!newItemForm.value.itemName || newItemForm.value.itemName.trim() === '') {
    ElMessage.error('项目名称不能为空');
    return;
  }

  // 如果是子项，验证是否选择了父项（如果存在父项）
  if (newItemForm.value.itemType === 'sub' && parentItems.value.length > 0 && !newItemForm.value.parentItem) {
    ElMessage.error('请选择父项');
    return;
  }

  // 如果是编辑模式，更新现有项目
  if (isEditingMode.value) {
    // 查找当前正在编辑的项目（通过对话框状态判断）
    // 如果需要编辑现有项目，应该通过专门的函数处理
    console.log('编辑模式下，更新现有项目');
  }

  const newLocalItem = createNewItem(
    newItemForm.value.itemType as 'parent' | 'sub',
    newItemForm.value.itemName,
    newItemForm.value.itemType === 'parent' ? newItemForm.value.itemName : newItemForm.value.itemCategory,
    newItemForm.value.itemType === 'sub' ? newItemForm.value.parentItem : null
  );

  if (!newLocalItem) return;

  // 关闭对话框
  closeAddItemDialog();
  ElMessage.success('检查项已添加到本地');
};

// 获取验收数据
const refreshInspectionData = async () => {
  const orderId = selectedOrderDetail.value ? selectedOrderDetail.value.id : selectedOrder.value.id;

  try {
    // 检查是否已有验收记录
    let inspectionId = (selectedOrderDetail.value || selectedOrder.value).inspection_id;
    if (!inspectionId) {
      const inspectionRes: any = await request.get('/api/inspections', {
        params: {
          order_no: (selectedOrderDetail.value || selectedOrder.value).order_no
        }
      });
      if (inspectionRes.list && inspectionRes.list.length > 0) {
        inspectionId = inspectionRes.list[0].id;
        // 更新订单列表中的ID
        if (selectedOrderDetail.value) selectedOrderDetail.value.inspection_id = inspectionId;
        if (selectedOrder.value) selectedOrder.value.inspection_id = inspectionId;
      }
    }

    if (inspectionId) {
      const response: any = await request.get(`/api/inspections/${inspectionId}`);
      selectedInspection.value = response;
      // 初始化items并保存原始状态，保留本地新建的项目和删除标记
      // 注意：后端返回的数据中，items包含父项和嵌套的子项，需要扁平化处理
      const serverItems = [];

      // 遍历后端返回的items，包括parent和其children
      (response.items || []).forEach((item: any) => {
        // 添加父项
        serverItems.push({
          ...item,
          original_inspection_result: item.inspection_result,
          original_description: item.description,
          original_photo_path: item.photo_path,
          is_local_new: false // 标记为非本地新建
        });

        // 添加子项（如果存在）
        if (item.children && Array.isArray(item.children)) {
          item.children.forEach((child: any) => {
            serverItems.push({
              ...child,
              original_inspection_result: child.inspection_result,
              original_description: child.description,
              original_photo_path: child.photo_path,
              is_local_new: false // 标记为非本地新建
            });
          });
        }
      });

      // 保留本地状态：删除标记、本地新建项目等
      const preservedItems = [];

      // 处理现有的服务器项目，保留本地状态
      for (const serverItem of serverItems) {
        const existingItem = items.value.find((item: any) => item.id === serverItem.id);
        if (existingItem) {
          // 保留本地的删除标记和其他状态
          preservedItems.push({
            ...serverItem,
            _toBeDeleted: existingItem._toBeDeleted, // 保留删除标记
            _photo_needs_move: existingItem._photo_needs_move, // 保留照片移动标记
            _modified: existingItem._modified, // 保留修改标记
            photo_path: existingItem._toBeDeleted ? existingItem.photo_path : serverItem.photo_path // 如果要删除，保留原路径
          });
        } else {
          preservedItems.push(serverItem);
        }
      }

      // 保留本地新建的项目
      const localNewItems = items.value.filter((item: any) => item.is_local_new);

      // 保留仍标记为删除但不在服务器数据中的项目（可能已被服务器删除）
      const locallyDeletedItems = items.value.filter((item: any) =>
        item._toBeDeleted === true && !serverItems.find((serverItem: any) => serverItem.id === item.id)
      );

      // 合并所有项目
      items.value = [...preservedItems, ...localNewItems, ...locallyDeletedItems];
    }
  } catch (error) {
    console.error('获取验收详情失败:', error);
    ElMessage.error('获取验收详情失败');
  }
};
// 开始编辑标题 - 弹出对话框
const startEditing = (item: any, type: 'parent' | 'sub') => {
  if (!isUserAdmin.value) return;

  // 设置编辑项目和类型
  titleEditingItem.value = item;
  titleEditingValue.value = type === 'parent' ? item.item_category : item.item_name;
  titleEditingType.value = type;

  // 显示对话框
  editItemTitleDialogVisible.value = true;
};

// 关闭编辑标题对话框
const closeEditItemTitleDialog = () => {
  editItemTitleDialogVisible.value = false;
  titleEditingItem.value = null;
  titleEditingValue.value = '';
  titleEditingType.value = 'sub';
};

// 确认编辑标题
const confirmEditItemTitle = async () => {
  if (!titleEditingItem.value) {
    ElMessage.error('没有选中要编辑的项目');
    return;
  }

  const updatedValue = titleEditingValue.value.trim();
  if (!updatedValue) {
    ElMessage.error('标题不能为空');
    return;
  }

  const originalValue = titleEditingType.value === 'parent'
    ? titleEditingItem.value.item_category
    : titleEditingItem.value.item_name;

  if (updatedValue === originalValue) {
    // 如果值没有改变，直接关闭对话框
    closeEditItemTitleDialog();
    return;
  }

  // 从原始items数组中找到相同的项目进行修改
  const originalItem = items.value.find((item: any) => item.id === titleEditingItem.value.id);
  if (originalItem) {
    // 本地更新原始项目数据
    if (titleEditingType.value === 'parent') {
      originalItem.item_category = updatedValue;
      // 如果是大项，同时更新名称字段
      originalItem.item_name = updatedValue;
    } else {
      originalItem.item_name = updatedValue;
    }

    // 标记项目为已修改，以便在缓存时发送到服务器
    originalItem._modified = true;
  }

  ElMessage.success('标题已更新到本地，点击"缓存"或"保存"按钮后会同步到服务器');
  closeEditItemTitleDialog();
};

// 完成编辑（保留原函数，用于其他编辑场景）
const finishEditing = async (item: any, type: 'parent' | 'sub') => {
  if (!item.isEditing) return;

  const updatedValue = item.editingValue.trim();
  if (updatedValue && updatedValue !== (type === 'parent' ? item.item_category : item.item_name)) {
    if (type === 'parent') {
      item.item_category = updatedValue;
      // 如果是大项，同时更新名称字段
      item.item_name = updatedValue;
    } else {
      item.item_name = updatedValue;
    }

    // 标记项目为已修改，但不立即发送到服务器
    item._modified = true;
    
    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;
    
    ElMessage.success('项目已更新到本地');
  }

  item.isEditing = false;
  item.editingValue = '';
};

// 清空所有检查项
const clearAllItems = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空当前订单的全部检查项数据吗？此操作将删除所有大小项数据及对应图片等。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 调用后端API清空检查项
    if (selectedInspection.value) {
      const response: any = await request.post(`/api/inspections/${selectedInspection.value.id}/clear`);

      if (response && response.total_deleted !== undefined) {
        // 清空本地数据
        items.value = [];
        // 更新进度信息
        if (selectedInspection.value) {
          selectedInspection.value.total_items = 0;
          selectedInspection.value.completed_items = 0;
          selectedInspection.value.inspection_progress = 0;
        }

        // 标记有未保存的更改
        hasUnsavedChangesFlag.value = true;

        ElMessage.success(`成功清空检查项数据，共删除 ${response.total_deleted} 个项目`);
      } else {
        ElMessage.error('清空检查项失败');
      }
    } else {
      ElMessage.error('当前没有验收记录');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空检查项失败:', error);
      ElMessage.error('清空检查项失败');
    }
  }
};

// 删除检查项
const deleteItem = async (item: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除检查项 "${item.item_type === 'parent' ? item.item_category : item.item_name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 在items.value中找到原始项目对象
    const originalItem = items.value.find((i: any) => i.id === item.id);
    if (!originalItem) {
      console.error(`找不到ID为 ${item.id} 的原始项目`);
      return;
    }

    // 如果是父项，需要同时标记其所有子项为待删除
    if (item.item_type === 'parent') {
      const childItems = items.value.filter((i: any) => i.parent_id === item.id);
      for (const childItem of childItems) {
        childItem._toBeDeleted = true; // 标记子项为待删除
      }
    }

    // 不再直接删除照片文件，而是在保存时由后端统一处理
    // 标记照片也需要删除，由后端处理
    originalItem._photo_needs_delete = true;

    // 标记原始项目为待删除，而不是立即从数组中移除
    originalItem._toBeDeleted = true; // 添加标记表示待删除

    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;

    ElMessage.success('检查项已标记为删除，将在保存时提交到服务器');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除检查项失败:', error);
      ElMessage.error('删除检查项失败');
    }
  }
};// 缓存数据
const cacheData = async () => {
  try {
    // 验证检查结果是否符合要求
    const validationErrors: string[] = [];

    for (const item of items.value) {
      if (item.item_type === 'sub' && !item._toBeDeleted) { // 只对未被删除的细项进行验证
        if (item.inspection_result === 'normal' && !item.photo_path) {
          validationErrors.push(`细项 "${item.item_name}" 选择正常，但未上传照片`);
        } else if (item.inspection_result === 'defect' && (!item.photo_path || !item.description)) {
          if (!item.photo_path && !item.description) {
            validationErrors.push(`细项 "${item.item_name}" 选择不正常，但未上传照片且未填写描述`);
          } else if (!item.photo_path) {
            validationErrors.push(`细项 "${item.item_name}" 选择不正常，但未上传照片`);
          } else {
            validationErrors.push(`细项 "${item.item_name}" 选择不正常，但未填写描述`);
          }
        }
      }
    }

    if (validationErrors.length > 0) {
      ElMessage.error(`验证失败：\n${validationErrors.join('\n')}`);
      return false;
    }

    if (!selectedInspection.value) {
      // 如果没有验收记录，先创建验收记录
      const orderId = selectedOrderDetail.value ? selectedOrderDetail.value.id : selectedOrder.value.id;
      const newInspection: any = await request.post('/api/inspections', {
        order_id: orderId,
        remarks: '订单验收记录'
      });
      const inspectionId = newInspection.id;
      selectedInspection.value = newInspection;

      // 更新订单列表中的ID
      if (selectedOrderDetail.value) selectedOrderDetail.value.inspection_id = inspectionId;
      if (selectedOrder.value) selectedOrder.value.inspection_id = inspectionId;
    }

    // 在构建发送数据之前，准备图片移动标记
    // 不再调用handlePhotoFiles，因为图片移动将由后端处理
    // 但我们需要确保需要移动的标记被发送到后端
    const itemsToProcess = items.value
      .filter((item: any) => !(item.is_local_new && item._toBeDeleted))  // 过滤掉本地新建且被删除的项目
      .map((item: any) => {
        // 确保即使未定义也要包含 _toBeDeleted 属性
        const itemToSend: any = {
          id: item.id,
          parent_id: item.parent_id,
          item_category: item.item_category,
          item_name: item.item_name,
          item_type: item.item_type,
          inspection_result: item.inspection_result,
          photo_path: item.photo_path,  // 发送原始路径
          description: item.description,
          sort_order: item.sort_order,
          is_local_new: item.is_local_new,
          // 添加图片移动标记，让后端知道需要移动图片
          _photo_needs_move: item._photo_needs_move || false,
          // 添加需要删除的照片路径
          photos_to_delete: item.photos_to_delete || []
        };

        // 显式添加 _toBeDeleted 属性，确保它被发送到服务器
        itemToSend._toBeDeleted = item._toBeDeleted || false;

        return itemToSend;
      });

    // 使用批量API处理所有项目
    const batchResult: any = await request.post(`/api/inspections/${selectedInspection.value.id}/items/batch`, {
      items: itemsToProcess
    });

    // 更新本地数据，将服务器返回的ID和状态同步
    if (batchResult.created_items) {
      batchResult.created_items.forEach((serverItem: any) => {
        // 根据服务器返回的原始信息更新本地项目
        // 查找对应的本地项目
        const localItemIndex = items.value.findIndex((item: any) =>
          item.is_local_new &&
          item.item_name === serverItem.item_name &&
          item.item_category === serverItem.item_category &&
          item.item_type === serverItem.item_type
        );

        if (localItemIndex !== -1) {
          const localItem = items.value[localItemIndex];
          const oldId = localItem.id; // 保存旧ID用于更新子项的parent_id

          localItem.id = serverItem.id;
          localItem.is_local_new = false;
          localItem.original_inspection_result = localItem.inspection_result;
          localItem.original_description = localItem.description;
          localItem.original_photo_path = localItem.photo_path;

          // 如果这是一个父项目，更新所有引用它的子项的parent_id
          if (localItem.item_type === 'parent') {
            items.value.forEach(item => {
              if (item.parent_id === oldId) {
                item.parent_id = serverItem.id; // 更新子项的parent_id为新的服务器ID
              }
            });
          }
        }
      });
    }

    // 从本地items中移除已删除的项目
    if (batchResult.deleted_items && batchResult.deleted_items.length > 0) {
      for (const deletedItem of batchResult.deleted_items) {
        const itemIndex = items.value.findIndex((item: any) => item.id === deletedItem.id);
        if (itemIndex !== -1) {
          items.value.splice(itemIndex, 1);
        }
      }
    }

    // 更新验收记录的进度信息（使用批量API返回的进度）
    if (selectedInspection.value && batchResult.progress !== undefined) {
      selectedInspection.value.inspection_progress = batchResult.progress;
      selectedInspection.value.completed_items = batchResult.completed_items;
      selectedInspection.value.total_items = batchResult.total_items;

      // 更新订单列表中的进度信息
      if (selectedOrderDetail.value) {
        selectedOrderDetail.value.inspection_progress = batchResult.progress;
        selectedOrderDetail.value.completed_items = batchResult.completed_items;
        selectedOrderDetail.value.total_items = batchResult.total_items;
      }
      if (selectedOrder.value) {
        selectedOrder.value.inspection_progress = batchResult.progress;
        selectedOrder.value.completed_items = batchResult.completed_items;
        selectedOrder.value.total_items = batchResult.total_items;
      }
    }

    // 注意：由于批量API已经重新计算并保存了进度信息，无需再单独PUT请求更新
    // 以避免覆盖数据库中正确的进度值

    // 缓存成功后，重新获取数据以确保页面显示最新状态
    await refreshInspectionData();

    // 同时更新订单列表中的进度信息，确保列表视图也能显示最新进度
    if (selectedOrderDetail.value || selectedOrder.value) {
      const currentOrder = selectedOrderDetail.value || selectedOrder.value;
      const orderInList = orders.value.find((order: any) => order.id === currentOrder.id);
      if (orderInList && selectedInspection.value) {
        orderInList.inspection_progress = batchResult.progress || 0;
        orderInList.completed_items = batchResult.completed_items || 0;
        orderInList.total_items = batchResult.total_items || 0;
      }
    }

    hasUnsavedChangesFlag.value = false; // 缓存成功后重置未保存更改标志
    ElMessage.success('数据已缓存');
    return true;
  } catch (error) {
    console.error('缓存数据失败:', error);
    ElMessage.error('缓存数据失败');
    return false;
  }
};

// 处理照片文件：仅标记需要移动的文件，实际移动由后端批量API处理
const handlePhotoFiles = async () => {
  // 前端不再处理文件移动，而是将需要移动的标记发送到后端
  // 后端的批量API将在服务器内部处理文件移动
  console.log('图片移动将由后端批量API处理');
};

// 保存并关闭
const saveAndClose = async () => {
  try {
    // 检查是否有未保存的更改，如果没有则直接关闭
    if (!hasUnsavedChangesFlag.value) {
      orderDetailDialogVisible.value = false;
      ElMessage.info('没有未保存的更改');
      return;
    }

    // 首先执行验证和保存
    const result = await cacheData();
    // 只有在保存成功后才关闭对话框
    if (result === true) {
      orderDetailDialogVisible.value = false;
    }
  } catch (error) {
    console.error('保存数据失败:', error);
    ElMessage.error('保存数据失败');
  }
};

// 打开编辑检查项对话框
const openEditItemDialog = (item: any) => {
  // 设置编辑表单的值
  newItemForm.value = {
    itemType: item.item_type,
    parentItem: item.parent_id, // 对于子项，设置父项ID
    itemName: item.item_type === 'parent' ? item.item_category : item.item_name, // 对于父项，使用item_category，对于子项，使用item_name
    itemCategory: item.item_category
  };

  // 如果是子项，需要查找父项类别
  if (item.item_type === 'sub' && item.parent_id) {
    const parentItem = items.value.find((i: any) => i.id === item.parent_id);
    if (parentItem) {
      newItemForm.value.itemCategory = parentItem.item_category;
    }
  }

  // 打开对话框
  addItemDialogVisible.value = true;
};

// 创建新的检查项的辅助函数
const createNewItem = (itemType: 'parent' | 'sub', itemName: string, itemCategory: string, parentId: number | null, options: any = {}) => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    ElMessage.error('请先选择一个订单');
    return null;
  }

  const newLocalItem: any = {
    id: Date.now(), // 使用时间戳作为临时ID
    inspection_id: selectedInspection.value?.id || null,
    parent_id: parentId,
    item_category: itemCategory,
    item_name: itemName,
    item_type: itemType,
    inspection_result: 'pending',
    photo_path: null,
    description: null,
    sort_order: 0,
    create_time: new Date().toISOString(),
    update_time: new Date().toISOString(),
    // 用于标识这是本地新建的项目
    is_local_new: true,
    ...options // 合并其他选项
  };

  // 添加到本地items数组
  items.value.push(newLocalItem);

  // 标记有未保存的更改
  hasUnsavedChangesFlag.value = true;

  return newLocalItem;
};

// 添加新的大项
const addNewParentItem = async () => {
  try {
    const result = await ElMessageBox.prompt('请输入大项名称', '添加大项', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '大项名称不能为空',
      inputPlaceholder: '请输入大项名称，如：配件、外观等'
    });

    const itemName = result.value.trim();
    if (!itemName) {
      ElMessage.warning('大项名称不能为空');
      return;
    }

    const newLocalItem = createNewItem('parent', itemName, itemName, null, null);

    if (!newLocalItem) return;

    ElMessage.success('大项已添加');
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel' && error.type !== 'cancel') {
      console.error('添加大项失败:', error);
    }
  }
};


// 直接添加细项到指定父项
const addSubItemToParent = async (parentId: number | null, parentCategory?: string) => {
  try {
    const result = await ElMessageBox.prompt('请输入细项名称', '添加细项', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '细项名称不能为空',
      inputPlaceholder: '请输入细项名称，如：部件1、角度1等'
    });

    const itemName = result.value.trim();
    if (!itemName) {
      ElMessage.warning('细项名称不能为空');
      return;
    }

    const newLocalItem: any = {
      id: Date.now(), // 使用时间戳作为唯一ID
      inspection_id: selectedInspection.value?.id || null,
      parent_id: parentId,
      item_category: parentCategory || '未分类',
      item_name: itemName, // 使用用户输入的名称
      item_type: 'sub',
      inspection_result: 'pending',
      photo_path: null,
      description: null,
      sort_order: 0,
      create_time: new Date().toISOString(),
      update_time: new Date().toISOString(),
      is_local_new: true
    };

    // 添加到本地items数组
    items.value.push(newLocalItem);

    // 标记有未保存的更改
    hasUnsavedChangesFlag.value = true;
    
    ElMessage.success('已添加新检查细项');
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel' && error.type !== 'cancel') {
      console.error('添加细项失败:', error);
    }
  }
};
// 设置父项输入框ref
const parentInputRefs = ref({});
const setParentInputRef = (el: any, id: any) => {
  if (el) {
    parentInputRefs.value[id] = el;
  }
};

// 设置子项输入框ref
const subItemInputRefs = ref({});
const setSubItemInputRef = (el: any, id: any) => {
  if (el) {
    subItemInputRefs.value[id] = el;
  }
};

// 检查是否有变更
const hasUnsavedChanges = () => {
  return items.value.some(item =>
    item.inspection_result !== item.original_inspection_result ||
    item.description !== item.original_description ||
    item.photo_path !== item.original_photo_path
  );
};
// 关闭对话框
const closeDialog = async () => {
  // 检查是否有未保存的更改
  if (hasUnsavedChanges()) {
    try {
      const result = await ElMessageBox.confirm(
        '当前有未保存的更改，是否保存？',
        '提示',
        {
          confirmButtonText: '保存',
          cancelButtonText: '不保存',
          type: 'warning'
        }
      );

      if (result === 'confirm') {
        await cacheData();
      }
    } catch (error) {
      // 用户点击了取消，不关闭对话框
      return;
    }
  }

  orderDetailDialogVisible.value = false;
};

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    // 使用新的专门用于验收的API
    const response: any = await request.get('/api/inspection-orders', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    });

    orders.value = response.list || [];
    total.value = response.total || 0;
  } catch (error) {
    console.error('获取订单列表失败:', error);
    ElMessage.error('获取订单列表失败');
  } finally {
    loading.value = false;
  }
};

// 获取订单验收进度
const getOrderInspectionProgress = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  return order ? (order.inspection_progress || 0) : 0;
};

const getOrderInspectionStatus = (orderId: number) => {
  const progress = getOrderInspectionProgress(orderId);
  if (progress === 100) return 'success';
  if (progress > 0) return 'warning';
  return '';
};

// 获取订单验收进度的分数格式 (如: "1/3")
const getOrderInspectionFraction = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  if (!order) return '0/0';

  const completedItems = order.completed_items || 0;
  const totalItems = order.total_items || 0;

  return `${completedItems}/${totalItems}`;
};

// 获取父项进度的分数格式 (如: "1/3")
const getParentItemFraction = (parentItem: any) => {
  if (!parentItem.total_children) return '0/0';

  return `${parentItem.completed_children}/${parentItem.total_children}`;
};

// 开始验收
const startInspection = async (row: any) => {
  selectedOrder.value = row;
  selectedOrderDetail.value = null; // 清除之前选择的详情

  // 获取或创建验收数据
  orderDetailDialogVisible.value = true;
  await refreshInspectionData();
};

// 查看验收报告
const viewInspectionReport = async (order: any) => {
  try {
    // 获取或创建验收记录
    let inspectionId = order.inspection_id;
    if (!inspectionId) {
      const newInspection: any = await request.post('/api/inspections', {
        order_id: order.id,
        remarks: '订单验收记录'
      });
      inspectionId = newInspection.id;
      order.inspection_id = inspectionId;
    }

    // 跳转到验收报告页面（在新窗口打开）
    window.open(`/api/inspections/${inspectionId}/report`, '_blank');
  } catch (error) {
    console.error('查看验收报告失败:', error);
    ElMessage.error('查看验收报告失败');
  }
};

// 关闭详情对话框
const handleCloseDetailDialog = () => {
  detailDialogVisible.value = false;
  selectedInspection.value = null;
  items.value = [];
};



// 更新检查项
const updateInspectionItem = async (item: any) => {
  // 根据新的检查结果，处理描述内容
  if (item.inspection_result === 'normal') {
    // 如果切换到"正常"状态，清除描述内容
    item.description = null;
  } else if (item.inspection_result === 'not_applicable') {
    // 如果切换到"没此项"状态，也清除描述内容
    item.description = null;
  }
  // 如果切换到"不正常"或"未检查"状态，保持现有的描述内容或允许用户输入

  // 在本地更新项目，不立即验证，验证将在保存时进行
  item._modified = true;
  hasUnsavedChangesFlag.value = true; // 标记有未保存的更改
  ElMessage.success('检查项已更新到本地');
};
// 获取图片路径数组
const getPhotoPaths = (photoPath: string | null) => {
  if (!photoPath) return [];
  return photoPath.split(',').map(path => path.trim()).filter(path => path);
};

// 删除单张图片
const removePhoto = async (item: any, photoToRemove: string) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这张照片吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 从路径字符串中移除指定图片路径
    const currentPaths = getPhotoPaths(item.photo_path);
    const updatedPaths = currentPaths.filter(path => path !== photoToRemove);

    // 更新项目照片路径
    item.photo_path = updatedPaths.join(',');

    // 只有当图片不是新上传的图片时，才标记为需要删除
    // 新上传的图片如果被删除，不需要向服务器发送删除请求
    const isNewUploadedPhoto = item.new_uploaded_photos && item.new_uploaded_photos.includes(photoToRemove);

    if (!isNewUploadedPhoto) {
      // 标记图片需要删除，由后端在保存时统一处理
      if (!item.photos_to_delete) {
        item.photos_to_delete = [];
      }
      item.photos_to_delete.push(photoToRemove);
    } else {
      // 如果是新上传的图片，从new_uploaded_photos数组中移除
      if (item.new_uploaded_photos) {
        item.new_uploaded_photos = item.new_uploaded_photos.filter(path => path !== photoToRemove);
      }
    }

    // 更新检查项
    updateInspectionItem(item);

    ElMessage.success('照片已标记为删除，将在保存时提交到服务器');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除照片失败:', error);
      ElMessage.error('删除照片失败');
    }
  }
};// 上传照片成功回调
const handlePhotoUploadSuccess = (response: any, item: any, type: string) => {
  // 根据后端实际返回的数据结构调整
  if (response && typeof response === 'object') {
    // 如果响应数据在data字段中
    if (response.data && response.data.path) {
      item.photo_path = response.data.path; // 临时路径
      item._photo_needs_move = true; // 标记需要移动文件
    } else if (response.data && response.data.url) {
      item.photo_path = response.data.url;
      item._photo_needs_move = true;
    } else if (response.path) {
      item.photo_path = response.path;
      item._photo_needs_move = true;
    } else if (response.url) {
      item.photo_path = response.url;
      item._photo_needs_move = true;
    } else {
      // 如果响应是直接的路径字符串
      item.photo_path = response;
      item._photo_needs_move = true;
    }
  } else {
    // 如果响应是直接的路径字符串
    item.photo_path = response;
    item._photo_needs_move = true;
  }

  ElMessage.success(`${type === 'normal' ? '正常' : '缺陷'}照片上传成功`);

  // 更新检查项
  updateInspectionItem(item);
};
// 上传照片失败回调
const handlePhotoUploadError = (error: any) => {
  console.error('照片上传失败:', error);
  ElMessage.error('照片上传失败');
};

// 手动上传照片处理
const handlePhotoUpload = async (options: any, item: any, type: string) => {
  const { file, onProgress, onError, onSuccess } = options;

  try {
    // 使用新的上传模块上传文件到临时位置
    const result: any = await uploadFile(file);

    // 调用成功回调
    onSuccess(result);

    // 更新项目照片路径 - 支持多张图片
    if (result && result.path) {
      if (item.photo_path) {
        // 如果已有照片路径，添加新路径（逗号分隔）
        item.photo_path = `${item.photo_path},${result.path}`;
      } else {
        // 如果没有照片路径，直接设置
        item.photo_path = result.path;
      }

      // 记录新上传的图片路径，用于后续删除时判断是否需要真正删除
      if (!item.new_uploaded_photos) {
        item.new_uploaded_photos = [];
      }
      item.new_uploaded_photos.push(result.path);

      item._photo_needs_move = true; // 标记需要移动文件
      ElMessage.success(`${type === 'normal' ? '正常' : '缺陷'}照片上传成功`);

      // 更新检查项
      updateInspectionItem(item);
    }
  } catch (error: any) {
    console.error('照片上传失败:', error);
    onError(error);
    ElMessage.error(`${type === 'normal' ? '正常' : '缺陷'}照片上传失败`);
  }
};

// 获取照片URL（处理相对路径）
const getPhotoUrl = (path: string) => {
  if (!path) return '';

  // 标准化路径分隔符
  const normalizedPath = path.replace(/\\/g, '/');

  // 如果路径已经是完整URL，则直接返回
  if (normalizedPath.startsWith('http://') || normalizedPath.startsWith('https://')) {
    return normalizedPath;
  }

  // 否则添加基础URL
  if (import.meta.env.MODE === 'development') {
    // 开发环境下，假设文件服务在后端服务器上
    return `http://192.168.30.70:5000/${normalizedPath}`;
  } else {
    return `${window.location.protocol}//${window.location.hostname}:5000/${normalizedPath}`;
  }
};

// 显示图片预览
const showImagePreview = (imageUrl: string) => {
  previewImageUrl.value = imageUrl;
  imagePreviewVisible.value = true;
};

// 重置表单
const resetForm = () => {
  ElMessageBox.confirm('确定要重置当前表单吗？所有检查项将被设为待检查状态', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // 重置所有检查项为待检查状态
      for (const item of items.value) {
        if (item.item_type === 'sub') {
          item.inspection_result = 'pending';
          item.photo_path = null;
          item.description = '';

          await request.put(`/api/inspections/${item.inspection_id}/items/${item.id}`, {
            inspection_result: 'pending',
            photo_path: null,
            description: ''
          });
        }
      }
      ElMessage.success('表单重置成功');

      // 重新获取详情
      await handleRowClick(selectedOrder.value);
    } catch (error) {
      console.error('重置表单失败:', error);
      ElMessage.error('重置表单失败');
    }
  }).catch(() => {
    // 用户取消操作
  });
};

// 提交验收
const submitInspection = async () => {
  try {
    // 检查是否所有必填项都已完成
    const allSubItems = items.value.filter((item: any) => item.item_type === 'sub');
    const validationErrors: string[] = [];

    for (const item of allSubItems) {
      if (item.inspection_result === 'pending') {
        validationErrors.push(`检查项 "${item.item_name}" 还未检查`);
      } else if (item.inspection_result === 'normal' && !item.photo_path) {
        validationErrors.push(`检查项 "${item.item_name}" 选择正常，但未上传照片`);
      } else if (item.inspection_result === 'defect' && (!item.photo_path || !item.description)) {
        if (!item.photo_path && !item.description) {
          validationErrors.push(`检查项 "${item.item_name}" 选择不正常，但未上传照片且未填写描述`);
        } else if (!item.photo_path) {
          validationErrors.push(`检查项 "${item.item_name}" 选择不正常，但未上传照片`);
        } else {
          validationErrors.push(`检查项 "${item.item_name}" 选择不正常，但未填写描述`);
        }
      }
    }

    if (validationErrors.length > 0) {
      ElMessage.error(`验证失败：\n${validationErrors.join('\n')}`);
      return;
    }

    // 如果所有检查项都完成，更新验收状态
    if (selectedInspection.value) {
      await request.put(`/api/inspections/${selectedInspection.value.id}`, {
        remarks: selectedInspection.value.remarks || '验收完成'
      });

      // 再次获取验收详情以更新进度
      const response: any = await request.get(`/api/inspections/${selectedInspection.value.id}`);
      selectedInspection.value = response;

      ElMessage.success('验收提交成功');
      orderDetailDialogVisible.value = false;
    }
  } catch (error: any) {
    console.error('提交验收失败:', error);
    if (error.message) {
      ElMessage.error(`提交验收失败: ${error.message}`);
    } else {
      ElMessage.error('提交验收失败');
    }
  }
};

// 分页相关方法
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchOrders();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchOrders();
};

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    // 这里需要一个获取用户信息的API，如果不存在则需要创建
    // 临时从token中解析用户信息
    const tokenStr = localStorage.getItem('oa_token');
    if (tokenStr) {
      // 简单解析JWT token获取用户角色
      const tokenParts = tokenStr.split('.');
      if (tokenParts.length === 3) {
        try {
          const payload = JSON.parse(atob(tokenParts[1]));
          userRole.value = payload.user_role || 'user';
        } catch (e) {
          console.error('解析token失败:', e);
          userRole.value = 'user';
        }
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
    userRole.value = 'user';
  }
};

// 组件挂载时获取数据
onMounted(async () => {
  await fetchUserInfo();
  fetchOrders();
});

// 生成报告
const generateReport = async () => {
  if (!selectedInspection.value || !selectedInspection.value.id) {
    ElMessage.warning('请先保存验收记录');
    return;
  }

  // 检查是否有未保存的更改，如果有则先缓存
  if (hasUnsavedChangesFlag.value) {
    // 在生成报告前先调用缓存以确保更新最新时间
    try {
      await cacheData();
      // 短暂延迟以确保后端处理完成
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('缓存数据失败:', error);
      ElMessage.error('生成报告前缓存数据失败，仍将尝试生成报告');
    }
  } else {
    ElMessage.info('数据已是最新，无需重复保存');
  }

  // 在新窗口中打开报告页面
  window.open(`/inspection-report/${selectedInspection.value.id}`, '_blank');
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 路由
const router = useRouter();
</script>

<style scoped>
.order-inspection-container {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-list-section {
  margin-bottom: 20px;
}

/* 为表格行添加鼠标指针样式 */
:deep(.el-table .el-table__row) {
  cursor: pointer;
}

:deep(.el-table .el-table__row:hover > td) {
  background-color: #f5f7fa;
}

/* 可编辑标题样式 */
.parent-title-container, .sub-item-name-container {
  display: inline-flex;
  align-items: center;
  flex: 1;
}

.parent-title, .sub-item-name {
  cursor: pointer;
}

.parent-title:hover, .sub-item-name:hover {
  background-color: #777777;
  color: white;
  /* padding: 2px 4px;
  border-radius: 3px; */
}

.add-sub-item {
  padding: 10px 0 0 20px;
}

.parent-title-container, .sub-item-name-container {
  display: flex;
  align-items: center;
}

.parent-title-container .el-input, .sub-item-name-container .el-input {
  width: 200px;
  margin-right: 10px;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.order-info-card {
  margin-bottom: 20px;
}

.inspection-items-card {
  margin-bottom: 20px;
}

.inspection-group {
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  background-color: rgb(235, 235, 235);
}

.parent-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  background-color: white;
}

.parent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.parent-title {
  font-weight: bold;
  font-size: 16px;
}

.parent-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  background-color: white;
}

.parent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.parent-title {
  font-weight: bold;
  font-size: 16px;
}

.parent-progress {
  display: flex;
  align-items: center;
  min-width: 250px; /* 确保进度条有足够的显示空间 */
}

.progress-text {
  margin-left: 10px;
  font-size: 12px;
  color: #606266;
}

/* 专门针对进度条的样式，使用更高的优先级 */
:deep(.el-progress-bar__outer) {
  height: 20px !important;
  border-radius: 10px !important;
  background-color: #ebeef5 !important;
}

:deep(.el-progress-bar__inner) {
  height: 20px !important;
  border-radius: 10px !important;
  line-height: 20px !important;
}

/* 确保整个进度条容器的样式 */
:deep(.el-progress) {
  display: flex !important;
  align-items: center !important;
  min-width: 200px;
}

/* 针对特定组件的样式 */
.parent-progress :deep(.el-progress) {
  width: 200px !important;
  min-width: 200px !important;
}

.sub-items {
  padding-left: 20px;
}

.sub-item {
  margin-bottom: 15px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fafafa;
}

.sub-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.sub-item-name {
  font-weight: 500;
}

.sub-item-actions {
  display: flex;
  align-items: center;
}

.sub-item-content {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #dcdfe6;
  display: flex;
  gap: 20px;
  flex-wrap: nowrap;
  white-space: nowrap;
  align-items: center;
}
.sub-item-content > div {
  flex-shrink: 0;
}

.upload-section {
  margin-bottom: 10px;
  display: inline-flex;
  align-items: center;
}

.photo-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.photo-preview {
  position: relative;
  display: inline-block;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: visible; /* 改为visible以显示超出部分的删除图标 */
}

.delete-photo-icon {
  position: absolute;
  top: -6px;
  right: -6px;
  background: red;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  z-index: 10; /* 增加z-index确保在顶层 */
}

.photo-preview img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  z-index: 1;
  position: relative;
}

.defect-section {
  margin-top: 10px;
}

.photo-preview {
  margin-top: 10px;
}



.bottom-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.standalone-item {
  margin-bottom: 15px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.progress-cell {
  cursor: pointer;
}

/* 图片预览对话框样式 */
.image-preview-dialog .el-dialog {
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview-dialog .el-dialog__body {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>