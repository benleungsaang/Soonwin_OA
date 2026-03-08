<template>
  <div class="quotation-management-container">
    <!-- 通用头部 -->
    <CommonHeader title="临时报价" />

  <!-- 固定在右下角的购物车按钮 -->
    <div class="floating-cart-btn">
      <el-badge :value="cartStore.cartData.machineList.length" :max="99" v-if="cartStore.cartData.machineList.length > 0">
        <el-button
          type="primary"
          :icon="ShoppingCart"
          circle
          @click="showCartModal = true"
          size="large"
          :disabled="cartStore.cartData.machineList.length === 0"
        >
        </el-button>
      </el-badge>
      <el-button
        v-else
        type="default"
        :icon="ShoppingCart"
        circle
        @click="showCartModal = true"
        size="large"
      >
      </el-button>
    </div>
    <div class="content-wrapper">
      <!-- 当前订单信息 -->
      <div class="current-order-info" v-if="cartStore.currentOrderId || cartStore.currentOrderMark">
        <el-alert
          :title="`当前订单: ${cartStore.currentOrderMark || '未命名'} (ID: ${cartStore.currentOrderId || 'N/A'})`"
          type="info"
          :closable="false"
          show-icon
        />
        <el-button size="small" @click="clearCurrentOrderInfo">
          <el-icon><DocumentAdd /></el-icon>
          创建新订单
        </el-button>
      </div>

      <!-- 卡片切换 -->
      <el-tabs v-model="activeTab" type="card" class="main-tabs">
        <!-- 设备搜索卡片 -->
        <el-tab-pane label="设备搜索" name="machines">
          <el-card class="tab-card">
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
                <!-- <el-col :span="16" class="text-right">
                  <el-button type="primary" @click="showCartModal = true">
                    <el-icon><ShoppingCart /></el-icon>
                    购物车
                    <el-badge :value="cartStore.cartData.machineList.length" :max="99" v-if="cartStore.cartData.machineList.length > 0" style="margin-left: 5px;" />
                  </el-button>
                </el-col> -->
              </el-row>
            </div>

            <!-- 设备列表表格 -->
            <el-table
              :data="machines"
              style="width: 100%; margin-top: 20px"
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
                  <!-- <el-button
                    size="small"
                    @click.stop="viewQuotation(row)"
                  >
                    <el-icon><View /></el-icon>
                    查看报价
                  </el-button> -->
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-wrapper" style="margin-top: 20px;">
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
          </el-card>
        </el-tab-pane>

        <!-- 临时报价单卡片 -->
        <el-tab-pane label="临时报价单" name="quotations">
          <el-card class="tab-card">
            <!-- 临时报价列表搜索和操作区域 -->
            <div class="search-and-actions">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-input
                    v-model="tempSearchQuery"
                    placeholder="请输入订单标识搜索"
                    clearable
                    @clear="handleTempSearchClear"
                    @keyup.enter="fetchQuotationTempList"
                  >
                    <template #append>
                      <el-button @click="fetchQuotationTempList">
                        <el-icon><Search /></el-icon>
                      </el-button>
                    </template>
                  </el-input>
                </el-col>
                <!-- <el-col :span="18" class="text-right">
                                    <el-button type="primary" @click="showCartModal = true" class="cart-btn">
                    <el-icon><ShoppingCart /></el-icon>
                    购物车
                    <el-badge :value="cartStore.cartData.machineList.length" :max="99" v-if="cartStore.cartData.machineList.length > 0" style="margin-left: 5px;" />
                  </el-button>


                </el-col> -->
              </el-row>
            </div>

            <!-- 临时报价列表表格 -->
            <el-table
              :data="quotationTemps"
              style="width: 100%; margin-top: 20px"
              v-loading="tempListLoading"
              row-key="order_id"
              :row-style="{ cursor: 'pointer' }"
              @row-click="handleTempRowClick"
            >
              <el-table-column prop="order_id" label="ID" width="80" />
              <el-table-column prop="order_mark" label="订单标识" width="200" />
              <el-table-column prop="total_amount" label="总金额" width="120">
                <template #default="{ row }">
                  ¥{{ row.total_amount || 0 }}
                </template>
              </el-table-column>
              <el-table-column prop="update_time" label="更新时间" width="160" />
              <el-table-column v-if="isCurrentUserAdmin()" prop="creator_id" label="创建人ID" width="120" />
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <!-- <el-button size="small" @click.stop="viewQuotationTemp(row)">
                    <el-icon><View /></el-icon>
                    查看
                  </el-button> -->
                  <el-button size="small" type="primary" @click.stop="loadQuotationTempToCart(row)">
                    <el-icon><ShoppingCart /></el-icon>
                    加载到购物车
                  </el-button>
                  <el-button size="small" type="danger" @click.stop="deleteQuotationTemp(row)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 临时报价列表分页 -->
            <div class="pagination-wrapper" style="margin-top: 20px;">
              <el-pagination
                v-model:current-page="tempCurrentPage"
                v-model:page-size="tempPageSize"
                :page-sizes="[10, 20, 50, 100]"
                :background="true"
                layout="total, sizes, prev, pager, next, jumper"
                :total="tempTotal"
                @size-change="handleTempSizeChange"
                @current-change="handleTempCurrentChange"
              />
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
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
      width="90%"
      top="5vh"
      :before-close="() => { showCartModal = false; }"
    >
      <div class="cart-modal-content">
        <!-- 设备列表 -->
        <div class="cart-section">
          <div class="section-header">
            <h3>设备列表</h3>
            <div class="section-stats">
              共 <span class="stats-number">{{ cartStore.cartData.machineList.length }}</span> 项设备
            </div>
          </div>

          <el-table
            :data="cartStore.cartData.machineList"
            border
            stripe
            style="width: 100%"
            header-cell-class-name="table-header"
            v-if="cartStore.cartData.machineList.length > 0"
          >
            <el-table-column label="缩略图" width="100" align="center">
              <template #default="scope">
                <el-image
                  :src="getImageUrl(scope.row.thumbUrl)"
                  style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;"
                  :preview-src-list="[getImageUrl(scope.row.thumbUrl)]"
                  :preview-teleported="true"
                  hide-on-click-modal
                ></el-image>
              </template>
            </el-table-column>
            <el-table-column label="设备型号" min-width="200">
              <template #default="scope">
                <div class="model-info">
                  <div class="primary-model">{{ scope.row.machineName || '未知设备' }}</div>
                  <div v-if="scope.row.originalModel" class="secondary-model">{{ scope.row.originalModel }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="单价" width="150" align="center">
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
            <el-table-column label="数量" width="150" align="center">
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
            <el-table-column label="小计" width="120" align="center">
              <template #default="scope">
                <span class="subtotal-text">¥{{ ((scope.row.customPrice || 0) * (scope.row.quantity || 0)).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="scope">
                <el-button
                  @click="cartStore.removeMachine(scope.row.machineId)"
                  type="danger"
                  size="small"
                  :icon="Delete"
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
          <div class="section-header">
            <h3>附加项目</h3>
            <div class="section-stats">
              共 <span class="stats-number">{{ cartStore.cartData.tempParams.length }}</span> 项附加项目
            </div>
          </div>

          <el-form
            inline
            @submit.prevent="addTempParamToCart"
            style="margin-bottom: 20px; padding: 15px; background: #f8f9fc; border-radius: 8px;"
          >
            <el-input
              v-model="tempParamName"
              placeholder="项目名称（如：税费/运费/折扣）"
              style="width: 250px; margin-right: 10px;"
              clearable
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
              :precision="4"
              style="width: 150px; margin-right: 10px; text-align: center;"
              class="centered-input"
              :controls="false"
            ></el-input-number>
            <el-button
              type="primary"
              @click="addTempParamToCart"
              :icon="Edit"
            >
              添加
            </el-button>
          </el-form>

          <el-table
            :data="cartStore.cartData.tempParams"
            border
            stripe
            style="width: 100%"
            header-cell-class-name="table-header"
            v-if="cartStore.cartData.tempParams.length > 0"
          >
            <el-table-column prop="name" label="项目名称" min-width="200">
              <template #default="scope">
                <el-input
                  v-model="scope.row.name"
                  @change="cartStore.updateTempParam(scope.row.id, scope.row.name)"
                  style="width: 100%; text-align: center;"
                  class="centered-input"
                ></el-input>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="120" align="center">
              <template #default="scope">
                <el-tag :type="scope.row.type === 'COEFFICIENT' ? 'warning' : 'success'" size="small">
                  {{ scope.row.type === 'COEFFICIENT' ? '系数' : '固定金额' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="数值" width="150" align="center">
              <template #default="scope">
                <el-input
                  v-model="scope.row.value"
                  :min="0"
                  :precision="scope.row.type === 'COEFFICIENT' ? 4 : 2"
                  :step="scope.row.type === 'COEFFICIENT' ? 0.0001 : 0.01"
                  @change="cartStore.updateTempParam(scope.row.id, scope.row.value)"
                  style="width: 100%; text-align: center;"
                  class="centered-input"
                ></el-input>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="scope">
                <el-button
                  @click="cartStore.removeTempParam(scope.row.id)"
                  type="danger"
                  size="small"
                  :icon="Delete"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 合计和操作按钮 -->
        <div class="cart-footer" v-if="cartStore.cartData.machineList.length > 0">
          <div class="total-amount">
            最终合计：<span class="amount">¥{{ (cartStore.cartData.totalAmount || 0).toFixed(2) }}</span>
          </div>
          <div class="cart-actions">
            <el-button
              @click="cartStore.clearCart()"
              :icon="Delete"
              type="danger"
            >
              清空购物车
            </el-button>
            <el-button
              type="primary"
              @click="generateOrderFromModal"
              :icon="View"
            >
              预览订单
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 临时报价预览组件 -->
    <QuotationTempPreview
      v-model="previewDialogVisible"
      :order-data="selectedQuotationTemp"
      :show-load-to-cart-button="showLoadToCartButton"
      @load-to-cart="handleLoadToCartFromPreview"
      @order-saved="handleOrderSaved"
      @order-updated="handleOrderUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus';
import { Search, View, ShoppingCart, Delete, DocumentAdd, Edit } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';
import QuotationTempPreview from '@/components/QuotationTempPreview.vue';
import { hasRoutePermission, getCurrentUserRole, getCurrentUserEmpId } from '@/utils/authUtils';
import request from '@/utils/request';
import { getMachinesNew, getQuotationMachines, getQuotationTempList, getQuotationTemp, deleteQuotationTemp as deleteQuotationTempAPI, updateQuotationTemp } from '@/utils/request';
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

// 临时报价列表数据类型
interface QuotationTemp {
  order_id: number;
  order_mark: string;
  total_amount: number;
  update_time: string;
  creator_id?: string;
}

// 响应式数据
const machines = ref<Machine[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(5);
const total = ref(0);
const searchQuery = ref('');

// 临时报价列表相关数据
const quotationTemps = ref<QuotationTemp[]>([]);
const tempListLoading = ref(false);
const tempCurrentPage = ref(1);
const tempPageSize = ref(10);
const tempTotal = ref(0);
const tempSearchQuery = ref('');

// 活动标签页
const activeTab = ref('machines'); // 默认显示设备搜索

// 临时报价预览相关数据
const previewDialogVisible = ref(false);
const selectedQuotationTemp = ref<QuotationTemp | any>({});
const showLoadToCartButton = ref(true); // 默认显示加载到购物车按钮

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

// 获取临时报价列表
const fetchQuotationTempList = async () => {
  tempListLoading.value = true;
  try {
    const response = await getQuotationTempList({
      page: tempCurrentPage.value,
      per_page: tempPageSize.value,
      search: tempSearchQuery.value
    });

    quotationTemps.value = response.quotation_temps || [];
    tempTotal.value = response.total || 0;
  } catch (error) {
    console.error('获取临时报价列表失败:', error);
    ElMessage.error('获取临时报价列表失败');
  } finally {
    tempListLoading.value = false;
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

// 临时报价列表分页处理
const handleTempSizeChange = (size: number) => {
  tempPageSize.value = size;
  tempCurrentPage.value = 1;
  fetchQuotationTempList();
};

const handleTempCurrentChange = (page: number) => {
  tempCurrentPage.value = page;
  fetchQuotationTempList();
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

// 临时报价搜索处理
const handleTempSearch = () => {
  tempCurrentPage.value = 1;
  fetchQuotationTempList();
};

const handleTempSearchClear = () => {
  tempSearchQuery.value = '';
  tempCurrentPage.value = 1;
  fetchQuotationTempList();
};

// 临时报价操作处理
const viewQuotationTemp = async (row: QuotationTemp) => {
  try {
    // 获取完整的报价单详情
    const response = await getQuotationTemp(row.order_id);
    if (response) {
      selectedQuotationTemp.value = {
        ...row,  // 包含列表中的基本信息
        ...response,  // 包含详细信息
        order_id: row.order_id,  // 确保ID正确
        orderMark: row.order_mark,  // 标准化字段名
        totalAmount: row.total_amount,  // 标准化字段名
        updateTime: row.update_time  // 标准化字段名
      };
      showLoadToCartButton.value = true; // 从列表打开时，显示加载到购物车按钮
      previewDialogVisible.value = true;
    } else {
      ElMessage.error('获取报价单详情失败');
    }
  } catch (error) {
    console.error('获取报价单详情失败:', error);
    ElMessage.error('获取报价单详情失败');
  }
};

const loadQuotationTempToCart = async (row: QuotationTemp) => {
  try {
    const response = await getQuotationTemp(row.order_id);
    if (response) {
      // 清空当前购物车
      cartStore.clearCart();

      // 添加机器到购物车
      if (response.machine_list && response.machine_list.length > 0) {
        response.machine_list.forEach((machine: any) => {
          // 先创建机器对象
          const machineToAdd = {
            id: machine.machineId,
            model: machine.machineName,
            original_model: machine.originalModel,
            image: machine.thumbUrl,
            show_price: machine.customPrice || 0,
            added_count: 0,
            brand: machine.brand || '',
            machine_weight: machine.machineWeight || '',
            dimensions: machine.dimensions || '',
            general_power: machine.generalPower || '',
            power_supply: machine.powerSupply || '',
            machine_type: machine.machineType || 0,
            remark: machine.remark || ''
          };

          // 添加到购物车（默认数量为1）
          cartStore.addMachine(machineToAdd);

          // 查找刚添加的机器并更新数量和价格
          const addedMachine = cartStore.cartData.machineList.find((item: any) => item.machineId === machine.machineId);
          if (addedMachine) {
            addedMachine.quantity = machine.quantity || 1;
            addedMachine.customPrice = machine.customPrice || 0;
            addedMachine.subtotal = (addedMachine.customPrice || 0) * (addedMachine.quantity || 1);
          }
        });
      }

      // 添加临时参数到购物车
      if (response.temp_params && response.temp_params.length > 0) {
        response.temp_params.forEach((param: any) => {
          cartStore.addTempParam(param.name, param.type, param.value, param.remark || '');
        });
      }

      // 保存订单ID和标识到购物车store
      if (response.id && response.order_mark) {
        cartStore.setCurrentOrderInfo(response.id, response.order_mark);
      }

      // 同步到本地存储
      cartStore.updateAndSync();

      ElMessage.success('报价单已加载到购物车');
      showCartModal.value = true;
    }
  } catch (error) {
    console.error('加载报价单到购物车失败:', error);
    ElMessage.error('加载报价单到购物车失败');
  }
};

const deleteQuotationTemp = async (row: QuotationTemp) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除报价单 "${row.order_mark}" 吗？此操作不可撤销。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    await deleteQuotationTempAPI(row.order_id);
    ElMessage.success('报价单删除成功');
    // 重新获取列表
    fetchQuotationTempList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除报价单失败:', error);
      ElMessage.error('删除报价单失败');
    }
  }
};

// 临时报价表格行点击事件
const handleTempRowClick = (row: QuotationTemp) => {
  viewQuotationTemp(row);
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
  // 现在addTempParam总是添加新项目，不再检查名称重复
  cartStore.addTempParam(tempParamName.value, tempParamType.value, value);
  tempParamName.value = '';
  tempParamValue.value = null;
};

const generateOrderFromModal = () => {
  // 创建当前购物车数据的预览对象
  const currentCartData = {
    id: cartStore.currentOrderId,  // 使用购物车store中的订单ID
    order_mark: cartStore.currentOrderMark,  // 使用购物车store中的订单标识
    order_id: cartStore.currentOrderId,  // 保持兼容性
    orderMark: cartStore.currentOrderMark || '当前购物车预览',  // 保持兼容性，如果没有则显示默认值
    total_amount: cartStore.cartData.totalAmount,
    totalAmount: cartStore.cartData.totalAmount,  // 保持兼容性
    update_time: new Date().toISOString(),
    creator_id: 'current_user', // 添加一个标识表示是当前购物车
    machine_list: cartStore.cartData.machineList.map((machine: any) => ({
      ...machine,
      machineName: machine.machineName || machine.model,
      originalModel: machine.originalModel || machine.original_model,
      thumbUrl: machine.thumbUrl || machine.image,
      customPrice: machine.customPrice || machine.show_price || 0,
      quantity: machine.quantity || 1,
      subtotal: machine.subtotal || (machine.customPrice || machine.show_price || 0) * (machine.quantity || 1),
      brand: machine.brand,
      remark: machine.remark || ''
    })),
    temp_params: cartStore.cartData.tempParams.map((param: any) => ({
      ...param,
      name: param.name,
      type: param.type,
      value: param.value,
      remark: param.remark || ''
    }))
  };

  selectedQuotationTemp.value = currentCartData;
  previewDialogVisible.value = true;
  showLoadToCartButton.value = false;  // 从购物车打开预览，显示返回购物车按钮
};
// 计算属性
const isCurrentUserAdmin = () => {
  return getCurrentUserRole() === 'admin';
};

// 预览组件加载到购物车事件处理
const handleLoadToCartFromPreview = () => {
  // 预览组件已经处理了加载到购物车的逻辑，这里只需要显示成功消息
  showCartModal.value = true;
};

// 清除当前订单信息
const clearCurrentOrderInfo = () => {
  cartStore.clearCurrentOrderInfo();

  // 如果预览对话框是打开的，更新当前选中的报价单数据以移除旧的订单ID
  if (previewDialogVisible.value) {
    // 更新当前选中的报价单，移除旧的订单ID
    selectedQuotationTemp.value = {
      ...selectedQuotationTemp.value,
      id: undefined,  // 使用undefined而不是null，确保检查时被识别为无效ID
      order_mark: undefined,
      order_id: undefined,
      orderMark: '新临时报价单'
    };

    // 强制刷新预览组件状态 - 关闭再打开对话框
    const wasVisible = previewDialogVisible.value;
    previewDialogVisible.value = false;

    // 使用nextTick确保对话框完全关闭后再重新打开
    nextTick(() => {
      // 重新生成订单数据，此时应该使用清空后的购物车信息
      generateOrderFromModal();
    });
  }

  ElMessage.success('当前订单信息已清除，下次保存将创建新订单');
};

// 预览组件订单更新事件处理
const handleOrderUpdated = (orderInfo: any) => {
  // 更新当前订单信息到购物车store
  if (orderInfo && orderInfo.id && orderInfo.order_mark) {
    cartStore.setCurrentOrderInfo(orderInfo.id, orderInfo.order_mark);

    // 同时更新当前选中的报价单信息
    if (selectedQuotationTemp.value) {
      selectedQuotationTemp.value.id = orderInfo.id;
      selectedQuotationTemp.value.order_mark = orderInfo.order_mark;
      selectedQuotationTemp.value.order_id = orderInfo.id;
      selectedQuotationTemp.value.orderMark = orderInfo.order_mark;
    }
  }

  // 订单更新后，刷新临时报价列表
  fetchQuotationTempList();

  // 如果当前在临时报价单标签页，也确保列表已刷新
  if (activeTab.value === 'quotations') {
    fetchQuotationTempList();
  }
};

// 处理订单保存成功事件，刷新临时报价单列表
const handleOrderSaved = () => {
  // 重新获取临时报价列表
  fetchQuotationTempList();
};

// 组件挂载时获取数据
onMounted(() => {
  // 获取临时报价列表
  fetchQuotationTempList();

  // 获取设备列表
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
  margin-bottom: 25px;
}

.cart-modal-content .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #ebeef5;
}

.cart-modal-content .section-header h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.cart-modal-content .section-stats {
  font-size: 14px;
  color: #909399;
}

.cart-modal-content .stats-number {
  font-weight: bold;
  color: #409eff;
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
  padding-top: 25px;
  border-top: 2px solid #ebeef5;
  margin-top: 25px;
}

.cart-modal-content .total-amount {
  font-size: 18px;
  font-weight: bold;
  color: #606266;
}

.cart-modal-content .amount {
  font-size: 28px;
  font-weight: bold;
  color: #e64340;
  margin-left: 5px;
}

.cart-modal-content .cart-actions {
  display: flex;
  gap: 15px;
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

/* 当前订单信息 */
.current-order-info {
  margin-bottom: 20px;
}

/* 临时报价列表和设备列表之间的分隔 */
.section-divider {
  margin: 30px 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #ebeef5;
}

.section-divider h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

/* 标签页样式 */
:deep(.main-tabs) {
  margin-top: 20px;
}

:deep(.main-tabs .el-tabs__content) {
  padding: 20px;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  min-height: 500px;
}

:deep(.tab-card) {
  border: none;
  box-shadow: none;
  background: transparent;
}

/* 固定在右下角的购物车按钮 */
.floating-cart-btn {
  position: fixed;
  right: 30px;
  bottom: 30px;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.floating-cart-btn .el-badge {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 设备型号信息 */
.model-info {
  display: flex;
  flex-direction: column;
}

.primary-model {
  font-weight: 500;
  color: #303133;
}

.secondary-model {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.subtotal-text {
  font-weight: 500;
  color: #e64340;
}

/* 表格头部样式 */
:deep(.table-header) {
  background-color: #f8f9fc !important;
  color: #606266;
  font-weight: 600;
}
</style>