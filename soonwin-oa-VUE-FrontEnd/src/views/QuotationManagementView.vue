<template>
  <div class="quotation-management-container">
    <!-- 通用头部 -->
    <CommonHeader title="临时报价" />

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
            <el-button type="primary" @click="showCartModal = true">
              <el-icon><ShoppingCart /></el-icon>
              购物车
              <el-badge :value="cartStore.cartData.machineList.length" :max="99" v-if="cartStore.cartData.machineList.length > 0" style="margin-left: 5px;" />
            </el-button>
          </el-col>
        </el-row>
      </div>

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
            <el-image
              :src="row.image"
              :preview-src-list="[row.image]"
              fit="cover"
              style="width: 60px; height: 60px; border-radius: 4px;"
              :preview-teleported="true"
              hide-on-click-modal
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
        <el-table-column v-if="isCurrentUserAdmin()" prop="original_price" label="原始价格" width="120">
          <template #default="{ row }">
            ¥{{ row.original_price || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="show_price" label="参考价格" width="120">
          <template #default="{ row }">
            ¥{{ row.show_price || 0 }}
          </template>
        </el-table-column>
        <!-- <el-table-column prop="added_count" label="使用次数" width="100" /> -->
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              @click.stop="addToCart(row)"
            >
              <el-icon><ShoppingCart /></el-icon>
              加入购物车
            </el-button>
            <el-button
              size="small"
              @click.stop="viewQuotation(row)"
            >
              <el-icon><View /></el-icon>
              查看报价
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

    <!-- 报价详情对话框 -->
    <el-dialog
      v-model="quotationDialogVisible"
      title="报价详情"
      width="800px"
      :before-close="handleQuotationDialogClose"
    >
      <div v-if="selectedMachine" class="quotation-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="缩略图" :span="2">
            <el-image
              :src="selectedMachine.image"
              :preview-src-list="[selectedMachine.image]"
              fit="scale-down"
              style="width: 120px; height: 120px; border-radius: 4px; object-fit: contain;"
              :preview-teleported="true"
              hide-on-click-modal
            />
          </el-descriptions-item>
          <el-descriptions-item label="设备型号">
            <span>{{ selectedMachine.model }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="原厂型号">
            <span>{{ selectedMachine.original_model }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="品牌">
            <span>{{ selectedMachine.brand }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="设备重量">
            <span>{{ selectedMachine.machine_weight || 'N/A' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="设备尺寸">
            <span>{{ selectedMachine.dimensions || 'N/A' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="总功率">
            <span>{{ selectedMachine.general_power || 'N/A' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="供电规格">
            <span>{{ selectedMachine.power_supply || 'N/A' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="设备类型">
            <span>{{ getMachineTypeText(selectedMachine.machine_type) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="使用次数">
            <span>{{ selectedMachine.added_count || 0 }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">
            <span>{{ selectedMachine.remark || '无' }}</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="isCurrentUserAdmin()" label="原始价格">
            <span class="price">¥{{ selectedMachine.original_price || 0 }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="参考价格">
            <span class="price">¥{{ selectedMachine.show_price || 0 }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 自定义属性 -->
        <div class="attributes-info" v-if="customAttrsList.length > 0">
          <h4 style="margin-top: 20px;">自定义属性</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item
              v-for="(item, index) in customAttrsList"
              :key="index"
              :label="item.key"
            >
              <span>{{ item.value }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>

    <!-- 购物车模态框 -->
    <el-dialog
      v-model="showCartModal"
      title="报价购物车"
      width="80%"
      :before-close="() => { showCartModal = false; }"
    >
      <div class="cart-modal-content">
        <!-- 设备列表 -->
        <div class="cart-section">
          <h3>设备列表</h3>
          <el-table
            :data="cartStore.cartData.machineList"
            border
            style="width: 100%"
            v-if="cartStore.cartData.machineList.length > 0"
          >
                        <el-table-column label="缩略图" width="120">
                          <template #default="scope">
                            <el-image
                              :src="getImageUrl(scope.row.thumbUrl)"
                              style="width: 80px; height: 60px; object-fit: cover; border-radius: 4px;"
                              :preview-src-list="[getImageUrl(scope.row.thumbUrl)]"
                              :preview-teleported="true"
                            ></el-image>
                          </template>
                        </el-table-column>            <el-table-column label="设备型号" width="150">
              <template #default="scope">
                {{ scope.row.machineName || '未知设备' }}
                <div style="font-size: 12px; color: #999;">{{  scope.row.originalModel }}</div>
              </template>
            </el-table-column>
            <!-- <el-table-column label="原厂型号" width="150">
              <template #default="scope">
                {{ scope.row.originalModel || '' }}
              </template>
            </el-table-column> -->
            <!-- <el-table-column label="品牌" width="120">
              <template #default="scope">
                {{ scope.row.brand || '' }}
              </template>
            </el-table-column> -->
            <el-table-column label="单价" width="150">
              <template #default="scope">
                <el-input-number
                  v-model="scope.row.customPrice"
                  :min="0"
                  :precision="2"
                  @change="cartStore.updateMachine(scope.row.machineId, 'customPrice', scope.row.customPrice || 0)"
                  style="width: 100%; text-align: center;"
                  class="centered-input"
                  :controls="false"
                ></el-input-number>
              </template>
            </el-table-column>
            <el-table-column label="数量" width="150">
              <template #default="scope">
                <el-input-number
                  v-model="scope.row.quantity"
                  :min="0"
                  @change="cartStore.updateMachine(scope.row.machineId, 'quantity', scope.row.quantity || 1)"
                  style="width: 100%; text-align: center;"
                  class="centered-input"
                  :controls="false"
                ></el-input-number>
              </template>
            </el-table-column>
                                  <el-table-column label="小计" width="120">
                                    <template #default="scope">
                                      ¥{{ ((scope.row.customPrice || 0) * (scope.row.quantity || 0)).toFixed(2) }}
                                    </template>
                                  </el-table-column>
                                  <el-table-column label="操作" width="120">
                                    <template #default="scope">
                                      <el-button
                                        @click="cartStore.removeMachine(scope.row.machineId)"
                                        type="danger"
                                        size="small"
                                      >
                                        移除
                                      </el-button>
                                    </template>
                                  </el-table-column>
          </el-table>

          <div v-if="cartStore.cartData.machineList.length === 0" class="empty-cart">
            <el-empty description="购物车为空" />
          </div>
        </div>

        <!-- 自定义临时项目 -->
        <div class="temp-params-section" v-if="cartStore.cartData.machineList.length > 0">
          <h3>自定义项目</h3>
          <el-form inline @submit.prevent="addTempParamToCart" style="margin-bottom: 20px;">
            <el-input
              v-model="tempParamName"
              placeholder="项目名称（如：税费/运费/折扣）"
              style="width: 200px; margin-right: 10px;"
            ></el-input>
            <el-select
              v-model="tempParamType"
              placeholder="类型"
              style="width: 120px; margin-right: 10px;"
            >
              <el-option label="系数" value="COEFFICIENT"></el-option>
              <el-option label="固定金额" value="FIXED"></el-option>
            </el-select>
            <el-input-number
              v-model.number="tempParamValue"
              placeholder="数值"
              :min="0"
              :precision="2"
              style="width: 120px; margin-right: 10px; text-align: center;"
              class="centered-input"
              :controls="false"
            ></el-input-number>
            <el-button type="primary" @click="addTempParamToCart">添加</el-button>
          </el-form>

          <el-table
            :data="cartStore.cartData.tempParams"
            border
            style="width: 100%"
            v-if="cartStore.cartData.tempParams.length > 0"
          >
            <el-table-column prop="name" label="项目名称" width="200"></el-table-column>
            <el-table-column prop="type" label="类型" width="120">
              <template #default="scope">
                {{ scope.row.type === 'COEFFICIENT' ? '系数' : '固定金额' }}
              </template>
            </el-table-column>
            <el-table-column label="数值" width="150">
              <template #default="scope">
                <el-input
                  v-model="scope.row.value"
                  :min="0"
                  :precision="2"
                  @change="cartStore.updateTempParam(scope.row.name, scope.row.value)"
                  style="width: 100%; text-align: center;"
                  class="centered-input"
                ></el-input>
              </template>
            </el-table-column>
                        <el-table-column label="操作" width="120">
                          <template #default="scope">
                            <el-button
                              @click="cartStore.removeTempParam(scope.row.name)"
                              type="danger"
                              size="small"
                            >
                              删除
                            </el-button>
                          </template>
                        </el-table-column>          </el-table>
        </div>

        <!-- 合计和操作按钮 -->
        <div class="cart-footer" v-if="cartStore.cartData.machineList.length > 0">
          <div class="total-amount">
            最终合计：<span class="amount">¥{{ (cartStore.cartData.totalAmount || 0).toFixed(2) }}</span>
          </div>
          <div class="cart-actions">
            <el-button @click="cartStore.clearCart()">清空购物车</el-button>
            <el-button type="primary" @click="generateOrderFromModal">预览订单</el-button>
          </div>
        </div>
      </div>
    </el-dialog>


  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, FormInstance, FormRules } from 'element-plus';
import { Search, View, ShoppingCart } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';
import { hasRoutePermission, getCurrentUserRole } from '@/utils/authUtils';
import request from '@/utils/request';
import { getMachinesNew, getQuotationMachines } from '@/utils/request';
import { useQuotationCartStore } from '@/stores/quotationCartStore';

const router = useRouter();

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
  custom_attrs: string | Record<string, any>;
}

// 响应式数据
const machines = ref<Machine[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const searchQuery = ref('');

// 报价详情对话框相关
const quotationDialogVisible = ref(false);
const selectedMachine = ref<Partial<Machine> | null>(null);
const customAttrsList = ref<{key: string, value: string}[]>([]);

// 获取使用次数最多的设备列表（默认）
const fetchMostUsedMachines = async () => {
  loading.value = true;
  try {
    // 默认获取使用次数最多的10台机器
    const response = await getQuotationMachines({
      page: currentPage.value,
      per_page: pageSize.value,
      search: searchQuery.value,
      sort_by: 'added_count',  // 按使用次数排序
      order: 'desc'           // 降序排列
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
  fetchMostUsedMachines();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchMostUsedMachines();
};

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1;
  fetchMostUsedMachines();
};

const handleSearchClear = () => {
  searchQuery.value = '';
  currentPage.value = 1;
  fetchMostUsedMachines();
};

// 操作处理
const viewQuotation = async (row: Machine) => {
  selectedMachine.value = { ...row };

  // 解析自定义属性
  if (row.custom_attrs) {
    let attrsObj: Record<string, any> = {};
    if (typeof row.custom_attrs === 'string') {
      try {
        attrsObj = JSON.parse(row.custom_attrs);
      } catch (e) {
        console.error('解析自定义属性失败:', e);
        attrsObj = {};
      }
    } else if (typeof row.custom_attrs === 'object') {
      attrsObj = row.custom_attrs;
    }

    // 转换为列表格式
    customAttrsList.value = Object.entries(attrsObj).map(([key, value]) => ({
      key,
      value: String(value)
    }));
  } else {
    customAttrsList.value = [];
  }

  quotationDialogVisible.value = true;
};

const handleQuotationDialogClose = () => {
  quotationDialogVisible.value = false;
  selectedMachine.value = null;
  customAttrsList.value = [];
};

const handleRowClick = (row: Machine) => {
  viewQuotation(row);
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

// 购物车模态框相关
const showCartModal = ref(false);
const tempParamName = ref('');
const tempParamType = ref('COEFFICIENT');
const tempParamValue = ref<number | null>(null);



const cartStore = useQuotationCartStore();

const addToCart = (machine: Machine) => {
  cartStore.addMachine(machine);
};

// 确保图片路径正确的方法
const getImageUrl = (url: string) => {
  if (!url) return '/assets/Media/Machine/sample.png';

  // 如果是完整的URL（包含协议），直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }

  // 如果是以/开头的绝对路径，直接返回
  if (url.startsWith('/')) {
    return url;
  }

  // 如果是相对路径，转换为绝对路径
  return '/' + url.replace(/^\.?\//, '');
};



// 购物车模态框相关方法
const addTempParamToCart = () => {
  if (!tempParamName.value || tempParamValue.value === null || tempParamValue.value === undefined || isNaN(tempParamValue.value)) {
    ElMessage.error('请输入项目名称和数值');
    return;
  }
  const value = Number(tempParamValue.value);
  if (value < 0) {
    ElMessage.error('数值必须大于等于0');
    return;
  }
  cartStore.addTempParam(tempParamName.value, tempParamType.value, value);
  tempParamName.value = '';
  tempParamValue.value = null;
};

const generateOrderFromModal = () => {
  // 将当前购物车数据保存到临时缓存
  const tempOrder = {
    orderId: `temp_${Date.now()}`,
    machineList: JSON.parse(JSON.stringify(cartStore.cartData.machineList)),
    tempParams: JSON.parse(JSON.stringify(cartStore.cartData.tempParams)),
    totalAmount: cartStore.cartData.totalAmount,
    createdAt: new Date().toISOString()
  };

  // 保存到临时缓存
  localStorage.setItem('quotation_temp', JSON.stringify(tempOrder));

  showCartModal.value = false; // 关闭模态框

  // 在新窗口打开订单预览页面（不带订单号）
  router.push('/quotation/order');
};

// 计算属性
const isCurrentUserAdmin = () => {
  return getCurrentUserRole() === 'admin';
};

// 组件挂载时获取数据
onMounted(() => {
  fetchMostUsedMachines();
  
  // 检查URL参数，如果需要打开购物车模态框
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('openCart') === '1') {
    showCartModal.value = true;
    
    // 清除URL参数，避免刷新后重复打开
    const newUrl = window.location.pathname;
    window.history.replaceState({}, document.title, newUrl);
  }
});
</script>

<style scoped>
.quotation-management-container {
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

.quotation-details .price {
  font-weight: bold;
  color: #e74c3c;
  font-size: 16px;
}

.quotation-details h4 {
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
  margin-bottom: 10px;
  color: #333;
}

.cart-modal-content .cart-section,
.cart-modal-content .temp-params-section {
  margin-bottom: 20px;
}

.cart-modal-content .cart-section h3,
.cart-modal-content .temp-params-section h3 {
  margin-bottom: 15px;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.cart-modal-content .empty-cart {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}

.cart-modal-content .cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  margin-top: 20px;
}

.cart-modal-content .total-amount {
  font-size: 16px;
  font-weight: bold;
  color: #606266;
}

.cart-modal-content .amount {
  font-size: 24px;
  font-weight: bold;
  color: #e64340;
  margin-left: 5px;
}

.cart-modal-content .cart-actions {
  display: flex;
  gap: 10px;
}

/* 确保输入框文字居中 */
:deep(.centered-input) {
  text-align: center;
}

:deep(.centered-input input) {
  text-align: center;
}

/* 备注单元格样式 */
.remark-cell {
  cursor: pointer;
  padding: 8px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  min-height: 40px;
  max-height: 80px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-line;
  line-height: 1.4;
}

.remark-cell:hover {
  border-color: #409eff;
  background-color: #f2f6fc;
}
</style>