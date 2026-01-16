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
          @row-click="handleRowClick"
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
              <el-progress 
                :percentage="getOrderInspectionProgress(scope.row.id)" 
                :status="getOrderInspectionStatus(scope.row.id)"
                :show-text="false"
                height="20px"
              />
              <div class="progress-text">
                {{ getOrderInspectionProgress(scope.row.id) }}%
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" v-if="isUserAdmin">
            <template #default="scope">
              <el-button 
                type="primary" 
                size="small"
                @click.stop="viewInspectionReport(scope.row)"
              >
                查看进度
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

    <!-- 验收详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`订单验收详情 - ${selectedOrder.contract_no}`"
      width="80%"
      :before-close="handleCloseDetailDialog"
    >
      <div v-if="selectedInspection">
        <!-- 订单基础信息 -->
        <el-card class="order-info-card">
          <template #header>
            <div class="card-header">
              <span>订单基础数据</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="合同编号">{{ selectedOrder.contract_no }}</el-descriptions-item>
            <el-descriptions-item label="订单编号">{{ selectedOrder.order_no }}</el-descriptions-item>
            <el-descriptions-item label="包装机单号">{{ selectedOrder.machine_no }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ selectedOrder.machine_name }}</el-descriptions-item>
            <el-descriptions-item label="机型">{{ selectedOrder.machine_model }}</el-descriptions-item>
            <el-descriptions-item label="数量">{{ selectedOrder.machine_count }}</el-descriptions-item>
            <el-descriptions-item label="下单时间">{{ formatDate(selectedOrder.order_time) }}</el-descriptions-item>
            <el-descriptions-item label="出货时间">{{ formatDate(selectedOrder.ship_time) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 检查项区域 -->
        <el-card class="inspection-items-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>检查项</span>
              <el-button 
                v-if="isUserAdmin" 
                type="primary" 
                size="small"
                @click="showAddItemDialog"
              >
                添加检查项
              </el-button>
            </div>
          </template>
          
          <!-- 检查项列表 -->
          <div v-for="parentItem in groupedItems" :key="parentItem.id" class="inspection-group">
            <div class="parent-item">
              <div class="parent-header">
                <span class="parent-title">{{ parentItem.item_category }}</span>
                <div class="parent-progress">
                  <el-progress 
                    :percentage="parentItem.progress" 
                    :status="parentItem.progress === 100 ? 'success' : 'warning'"
                    :show-text="false"
                    height="10px"
                  />
                  <span class="progress-text">{{ parentItem.progress }}%</span>
                </div>
              </div>
              
              <div class="sub-items">
                <div 
                  v-for="subItem in parentItem.children" 
                  :key="subItem.id" 
                  class="sub-item"
                >
                  <div class="sub-item-header">
                    <span class="sub-item-name">{{ subItem.item_name }}</span>
                    <div class="sub-item-actions">
                      <el-radio-group 
                        v-model="subItem.inspection_result" 
                        @change="updateInspectionItem(subItem)"
                        :disabled="!isUserGeneral"
                      >
                        <el-radio label="normal">正常</el-radio>
                        <el-radio label="defect">缺陷</el-radio>
                        <el-radio label="not_applicable">无此项</el-radio>
                      </el-radio-group>
                    </div>
                  </div>
                  
                  <div class="sub-item-content" v-if="subItem.inspection_result !== 'not_applicable'">
                    <div v-if="subItem.inspection_result === 'normal'" class="upload-section normal-upload">
                      <el-upload
                        class="upload-demo"
                        :action="uploadUrl"
                        :headers="uploadHeaders"
                        :on-success="(response, file) => handlePhotoUploadSuccess(response, subItem, 'normal')"
                        :on-error="handlePhotoUploadError"
                        :show-file-list="false"
                        list-type="picture"
                      >
                        <el-button size="small" type="primary">上传照片</el-button>
                        <div v-if="subItem.photo_path" class="photo-preview">
                          <img :src="subItem.photo_path" alt="正常照片" style="max-width: 100px; max-height: 100px;">
                        </div>
                      </el-upload>
                    </div>
                    
                    <div v-if="subItem.inspection_result === 'defect'" class="defect-section">
                      <el-upload
                        class="upload-demo"
                        :action="uploadUrl"
                        :headers="uploadHeaders"
                        :on-success="(response, file) => handlePhotoUploadSuccess(response, subItem, 'defect')"
                        :on-error="handlePhotoUploadError"
                        :show-file-list="false"
                        list-type="picture"
                      >
                        <el-button size="small" type="danger">上传缺陷照片</el-button>
                        <div v-if="subItem.photo_path" class="photo-preview">
                          <img :src="subItem.photo_path" alt="缺陷照片" style="max-width: 100px; max-height: 100px;">
                        </div>
                      </el-upload>
                      <el-input
                        v-model="subItem.description"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入缺陷描述"
                        @blur="updateInspectionItem(subItem)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 添加的独立检查项（没有父项的） -->
          <div v-for="item in standaloneItems" :key="item.id" class="standalone-item">
            <div class="sub-item-header">
              <span class="sub-item-name">{{ item.item_name }}</span>
              <div class="sub-item-actions">
                <el-radio-group 
                  v-model="item.inspection_result" 
                  @change="updateInspectionItem(item)"
                  :disabled="!isUserGeneral"
                >
                  <el-radio label="normal">正常</el-radio>
                  <el-radio label="defect">缺陷</el-radio>
                  <el-radio label="not_applicable">无此项</el-radio>
                </el-radio-group>
              </div>
            </div>
            
            <div class="sub-item-content" v-if="item.inspection_result !== 'not_applicable'">
              <div v-if="item.inspection_result === 'normal'" class="upload-section normal-upload">
                <el-upload
                  class="upload-demo"
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :on-success="(response, file) => handlePhotoUploadSuccess(response, item, 'normal')"
                  :on-error="handlePhotoUploadError"
                  :show-file-list="false"
                  list-type="picture"
                >
                  <el-button size="small" type="primary">上传照片</el-button>
                  <div v-if="item.photo_path" class="photo-preview">
                    <img :src="item.photo_path" alt="正常照片" style="max-width: 100px; max-height: 100px;">
                  </div>
                </el-upload>
              </div>
              
              <div v-if="item.inspection_result === 'defect'" class="defect-section">
                <el-upload
                  class="upload-demo"
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :on-success="(response, file) => handlePhotoUploadSuccess(response, item, 'defect')"
                  :on-error="handlePhotoUploadError"
                  :show-file-list="false"
                  list-type="picture"
                >
                  <el-button size="small" type="danger">上传缺陷照片</el-button>
                  <div v-if="item.photo_path" class="photo-preview">
                    <img :src="item.photo_path" alt="缺陷照片" style="max-width: 100px; max-height: 100px;">
                  </div>
                </el-upload>
                <el-input
                  v-model="item.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入缺陷描述"
                  @blur="updateInspectionItem(item)"
                />
              </div>
            </div>
          </div>
        </el-card>

        <!-- 底部操作区域 -->
        <div class="bottom-actions">
          <div class="progress-summary">
            <p>检查项进度：{{ selectedInspection.completed_items }} / {{ selectedInspection.total_items }}</p>
          </div>
          <div class="action-buttons">
            <el-button @click="resetForm">重置</el-button>
            <el-button 
              type="primary" 
              @click="submitInspection"
              :disabled="!canSubmit"
            >
              提交
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
            <el-radio label="parent">大项</el-radio>
            <el-radio label="sub">细项</el-radio>
          </el-radio-group>
        </el-form-item>
        
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';

// 响应式数据
const orders = ref<any[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const detailDialogVisible = ref(false);
const addItemDialogVisible = ref(false);
const selectedOrder = ref<any>({});
const selectedInspection = ref<any>(null);
const items = ref<any[]>([]);
const token = ref(localStorage.getItem('oa_token') || '');

// 新检查项表单
const newItemForm = ref({
  itemType: 'sub', // 'parent' 或 'sub'
  parentItem: null as number | null,
  itemName: ''
});

const itemRules = {
  itemType: [
    { required: true, message: '请选择类型', trigger: 'change' }
  ],
  itemName: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ]
};

// 计算属性
const groupedItems = computed(() => {
  return items.value
    .filter((item: any) => item.item_type === 'parent')
    .map((parent: any) => {
      const children = items.value.filter((child: any) => child.parent_id === parent.id);
      return {
        ...parent,
        children: children,
        completed_children: children.filter((child: any) => 
          child.inspection_result === 'normal' || child.inspection_result === 'not_applicable'
        ).length,
        total_children: children.length,
        progress: children.length > 0 
          ? Math.round((children.filter((child: any) => 
              child.inspection_result === 'normal' || child.inspection_result === 'not_applicable'
            ).length / children.length) * 100)
          : 0
      };
    });
});

const standaloneItems = computed(() => {
  return items.value.filter((item: any) => item.item_type === 'sub' && item.parent_id === null);
});

const parentItems = computed(() => {
  return items.value.filter((item: any) => item.item_type === 'parent');
});

// 获取用户角色
const userRole = ref('');
const isUserAdmin = computed(() => userRole.value === 'admin');
const isUserGeneral = computed(() => userRole.value !== 'admin');

// 提交按钮是否可点击的条件
const canSubmit = computed(() => {
  if (!selectedInspection.value) return false;
  
  // 所有细项都必须完成（正常项有照片，缺陷项有照片加描述，无此项直接完成）
  const allSubItems = items.value.filter((item: any) => item.item_type === 'sub');
  
  if (allSubItems.length === 0) {
    return false; // 如果没有检查项，不能提交
  }
  
  for (const item of allSubItems) {
    if (item.inspection_result === 'pending') {
      return false;
    }
    if (item.inspection_result === 'normal' && !item.photo_path) {
      return false;
    }
    if (item.inspection_result === 'defect' && (!item.photo_path || !item.description)) {
      return false;
    }
  }
  
  return true; // 所有检查项都符合要求
});

// 上传配置
const uploadUrl = computed(() => {
  // 开发环境下使用代理，生产环境下使用完整URL
  if (import.meta.env.MODE === 'development') {
    return '/api/upload'; // 假设后端有上传接口
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

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const response: any = await request.get('/api/orders', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    });
    
    orders.value = response.list || [];
    total.value = response.total || 0;
    
    // 获取每个订单的验收进度
    for (const order of orders.value) {
      try {
        // 先检查订单号是否存在，避免空参数调用API
        if (order.order_no && order.order_no.trim() !== '') {
          const inspectionRes: any = await request.get('/api/inspections', {
            params: {
              order_no: order.order_no
            }
          });
        
          if (inspectionRes.list && inspectionRes.list.length > 0) {
            const inspection = inspectionRes.list[0];
            order.inspection_progress = inspection.inspection_progress || 0;
            order.inspection_id = inspection.id;
          } else {
            // 如果没有验收记录，不自动创建，只设置默认值
            order.inspection_progress = 0;
            order.inspection_id = null;
          }
        } else {
          // 如果订单号为空，也不自动创建验收记录
          order.inspection_progress = 0;
          order.inspection_id = null;
        }
      } catch (error) {
        console.error(`获取订单 ${order.order_no} 验收进度失败:`, error);
        // 设置默认值
        order.inspection_progress = 0;
        order.inspection_id = null;
      }
    }
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

// 表格行点击事件
const handleRowClick = async (row: any) => {
  selectedOrder.value = row;
  
  // 检查是否已有验收记录，如果没有则创建
  let inspectionId = row.inspection_id;
  if (!inspectionId) {
    try {
      // 创建验收记录
      const newInspection: any = await request.post('/api/inspections', {
        order_id: row.id,
        remarks: '订单验收记录'
      });
      inspectionId = newInspection.id;
      // 更新订单列表中的ID，以便下次点击不需要重复创建
      const orderIndex = orders.value.findIndex((order: any) => order.id === row.id);
      if (orderIndex !== -1) {
        orders.value[orderIndex].inspection_id = inspectionId;
      }
    } catch (error: any) {
      if (error && error.data && error.data.msg && error.data.msg.includes('该订单已创建验收记录')) {
        // 如果是因为并发创建导致的冲突，获取现有记录
        const inspectionRes: any = await request.get('/api/inspections', {
          params: {
            order_no: row.order_no
          }
        });
        if (inspectionRes.list && inspectionRes.list.length > 0) {
          inspectionId = inspectionRes.list[0].id;
          // 更新订单列表中的ID
          const orderIndex = orders.value.findIndex((order: any) => order.id === row.id);
          if (orderIndex !== -1) {
            orders.value[orderIndex].inspection_id = inspectionId;
          }
        }
      } else {
        console.error('创建验收记录失败:', error);
        ElMessage.error('创建验收记录失败');
        return;
      }
    }
  }
  
  // 获取验收详情
  try {
    const response: any = await request.get(`/api/inspections/${inspectionId}`);
    selectedInspection.value = response;
    items.value = response.items || [];
    detailDialogVisible.value = true;
  } catch (error) {
    console.error('获取验收详情失败:', error);
    ElMessage.error('获取验收详情失败');
  }
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

// 显示添加检查项对话框
const showAddItemDialog = () => {
  newItemForm.value = {
    itemType: 'sub',
    parentItem: null,
    itemName: ''
  };
  addItemDialogVisible.value = true;
};

// 关闭添加检查项对话框
const closeAddItemDialog = () => {
  addItemDialogVisible.value = false;
};

// 确认添加检查项
const confirmAddItem = async () => {
  if (!selectedInspection.value) {
    ElMessage.error('请先选择一个订单');
    return;
  }
  
  try {
    const payload: any = {
      inspection_id: selectedInspection.value.id,
      item_type: newItemForm.value.itemType,
      item_name: newItemForm.value.itemName
    };
    
    if (newItemForm.value.itemType === 'sub' && newItemForm.value.parentItem) {
      payload.parent_id = newItemForm.value.parentItem;
      // 获取父项的类别名称
      const parentItem = parentItems.value.find((p: any) => p.id === newItemForm.value.parentItem);
      payload.item_category = parentItem ? parentItem.item_category : '';
    } else if (newItemForm.value.itemType === 'parent') {
      payload.item_category = newItemForm.value.itemName;
    }
    
    const result: any = await request.post(`/api/inspections/${selectedInspection.value.id}/items`, payload);
    ElMessage.success('检查项添加成功');
    
    // 重新获取详情
    await handleRowClick(selectedOrder.value);
    closeAddItemDialog();
  } catch (error) {
    console.error('添加检查项失败:', error);
    ElMessage.error('添加检查项失败');
  }
};

// 更新检查项
const updateInspectionItem = async (item: any) => {
  try {
    const payload: any = {
      item_category: item.item_category,
      item_name: item.item_name,
      inspection_result: item.inspection_result,
      photo_path: item.photo_path,
      description: item.description,
      sort_order: item.sort_order
    };
    
    const result: any = await request.put(`/api/inspections/${item.inspection_id}/items/${item.id}`, payload);
    ElMessage.success('检查项更新成功');
    
    // 更新本地数据
    const itemIndex = items.value.findIndex((i: any) => i.id === item.id);
    if (itemIndex !== -1) {
      items.value[itemIndex] = { ...item };
    }
  } catch (error) {
    console.error('更新检查项失败:', error);
    ElMessage.error('更新检查项失败');
  }
};

// 上传照片成功回调
const handlePhotoUploadSuccess = (response: any, item: any, type: string) => {
  // 根据后端实际返回的数据结构调整
  if (response && typeof response === 'object') {
    // 如果响应数据在data字段中
    if (response.data && response.data.path) {
      item.photo_path = response.data.path;
    } else if (response.data && response.data.url) {
      item.photo_path = response.data.url;
    } else if (response.path) {
      item.photo_path = response.path;
    } else if (response.url) {
      item.photo_path = response.url;
    } else {
      // 如果响应是直接的路径字符串
      item.photo_path = response;
    }
  } else {
    // 如果响应是直接的路径字符串
    item.photo_path = response;
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
  if (!canSubmit.value) {
    ElMessage.warning('请完成所有检查项后再提交');
    return;
  }
  
  try {
    // 检查是否所有必填项都已完成
    const allSubItems = items.value.filter((item: any) => item.item_type === 'sub');
    for (const item of allSubItems) {
      if (item.inspection_result === 'pending') {
        ElMessage.warning(`检查项 "${item.item_name}" 还未检查`);
        return;
      }
      if (item.inspection_result === 'normal' && !item.photo_path) {
        ElMessage.warning(`检查项 "${item.item_name}" 需要上传照片`);
        return;
      }
      if (item.inspection_result === 'defect' && (!item.photo_path || !item.description)) {
        if (!item.photo_path) {
          ElMessage.warning(`检查项 "${item.item_name}" 需要上传缺陷照片`);
        } else {
          ElMessage.warning(`检查项 "${item.item_name}" 需要填写缺陷描述`);
        }
        return;
      }
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
      detailDialogVisible.value = false;
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
}

.parent-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
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
}

.progress-text {
  margin-left: 10px;
  font-size: 12px;
  color: #606266;
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
}

.upload-section {
  margin-bottom: 10px;
}

.defect-section {
  margin-top: 10px;
}

.photo-preview {
  margin-top: 10px;
}

.photo-preview img {
  border-radius: 4px;
  border: 1px solid #dcdfe6;
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
</style>