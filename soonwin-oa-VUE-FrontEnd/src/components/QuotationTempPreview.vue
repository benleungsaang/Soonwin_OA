<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`报价单预览`"
    width="90%"
    top="5vh"
    :before-close="handleClose"
    class="preview-dialog"
  >
    <div class="order-preview-content">
      <!-- 订单头部摘要 -->
      <div class="order-summary">
        <div class="summary-item">
          <span class="summary-label">订单标识:</span>
          <span class="summary-value">{{ selectedOrderData.order_mark || selectedOrderData.orderMark || '未命名' }}</span>
        </div>
        <!-- <div class="summary-item" v-if="selectedOrderData.id">
          <span class="summary-label">订单ID:</span>
          <span class="summary-value">{{ selectedOrderData.id || selectedOrderData.order_id || 'N/A' }}</span>
        </div> -->
        <div class="summary-item">
          <span class="summary-label">总金额:</span>
          <span class="summary-value amount-highlight">{{ getCurrentCurrencySymbol() }}{{ (selectedOrderData.total_amount || selectedOrderData.totalAmount || 0).toFixed(2) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">更新时间:</span>
          <span class="summary-value">{{ formatDateTime(selectedOrderData.update_time || selectedOrderData.updateTime || selectedOrderData.create_time || selectedOrderData.createTime || '') }}</span>
        </div>
      </div>

      <!-- 设备列表 -->
      <div class="order-section">
        <div class="section-header">
          <h3>设备清单</h3>
          <div class="section-stats">
            共 <span class="stats-number">{{ machineList.length }}</span> 项设备
          </div>
        </div>
        <el-table
          :data="machineList"
          border
          stripe
          style="width: 100%"
          header-cell-class-name="table-header"
        >
          <el-table-column label="缩略图" width="120" align="center">
            <template #default="scope">
              <ErrorFallbackImage
                :src="getThumbnailPath(getImageUrl(scope.row.thumbUrl))"
                :fallback-src="getImageUrl(scope.row.thumbUrl)"
                :alt="scope.row.machineName || scope.row.model || '设备缩略图'"
                :preview-teleported="true"
                :hide-on-click-modal="true"
                fit="cover"
                style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;"
                :preview-src-list="[getImageUrl(scope.row.thumbUrl)]"
              />
            </template>
          </el-table-column>
          <!-- <el-table-column prop="brand" label="品牌" width="120">
            <template #default="scope">
              <div class="cell-content">
                <span class="brand-text">{{ scope.row.brand || 'N/A' }}</span>
              </div>
            </template>
          </el-table-column> -->
          <el-table-column prop="machineName" label="设备型号" min-width="200">
            <template #default="scope">
              <div class="model-info">
                <div class="primary-model">{{ scope.row.machineName || '未知设备' }}</div>
                <div v-if="scope.row.originalModel" class="secondary-model">{{ scope.row.originalModel }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="customPrice" label="单价" width="120" align="center">
            <template #default="scope">
              <span class="price-text">{{ getCurrentCurrencySymbol() }}{{ (scope.row.customPrice || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="100" align="center">
            <template #default="scope">
              <span class="quantity-text">{{ scope.row.quantity || 1 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="subtotal" label="小计" width="140" align="center">
            <template #default="scope">
              <span class="subtotal-text">{{ getCurrentCurrencySymbol() }}{{ (scope.row.subtotal || (scope.row.customPrice || 0) * (scope.row.quantity || 1)).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="200" align="center">
            <template #default="scope">
              <div
                v-if="!scope.row.editingRemark"
                @click="!showLoadToCartButton && startEditingRemark(scope.row, 'machine', scope.$index)"
                :style="!showLoadToCartButton ? 'cursor: pointer;' : 'cursor: default;'"
                class="remark-display"
                :class="{ 'has-remark': scope.row.remark }"
                v-html="formatRemark(scope.row.remark || (!showLoadToCartButton ? '点击添加备注' : ''))"
                align="left"
              ></div>
              <el-input
                ref="textareaRef"
                v-else
                v-model="scope.row.remark"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
                placeholder="请输入备注（支持换行）"
                @blur="stopEditingRemark(scope.row, 'machine')"
                @keyup.enter.stop
                @keydown.esc="cancelEditingRemark(scope.row, 'machine')"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 自定义临时项目 -->
      <div class="temp-params-section" v-if="tempParams && tempParams.length > 0">
        <div class="section-header">
          <h3>附加项目</h3>
          <div class="section-stats">
            共 <span class="stats-number">{{ tempParams.length }}</span> 项附加项目
          </div>
        </div>
        <el-table
          :data="tempParams"
          border
          stripe
          style="width: 100%"
          header-cell-class-name="table-header"
        >
          <el-table-column prop="name" label="项目名称" min-width="200">
            <template #default="scope">
              <div class="param-name">
                {{ scope.row.name }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="120" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.type === 'COEFFICIENT' ? 'warning' : 'success'" size="small">
                {{ scope.row.type === 'COEFFICIENT' ? '系数' : '固定金额' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="数值" width="120" align="right">
            <template #default="scope">
              <span class="param-value">
                {{ scope.row.type === 'COEFFICIENT' ? scope.row.value.toFixed(4) : getCurrentCurrencySymbol() + scope.row.value.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="200">
            <template #default="scope">
              <div
                v-if="!scope.row.editingRemark"
                @click="!showLoadToCartButton && startEditingRemark(scope.row, 'tempParam', scope.$index)"
                :style="!showLoadToCartButton ? 'cursor: pointer;' : 'cursor: default;'"
                class="remark-display"
                :class="{ 'has-remark': scope.row.remark }"
                v-html="formatRemark(scope.row.remark || (!showLoadToCartButton ? '点击添加备注' : ''))"
              ></div>
              <el-input
                ref="textareaRef"
                v-else
                v-model="scope.row.remark"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
                placeholder="请输入备注（支持换行）"
                @blur="stopEditingRemark(scope.row, 'tempParam')"
                @keyup.enter.stop
                @keydown.esc="cancelEditingRemark(scope.row, 'tempParam')"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 合计信息 -->
      <div class="total-section">
        <div class="total-wrapper">
          <div class="total-label">最终合计</div>
          <div class="total-amount">
            <span class="currency">{{ getCurrentCurrencySymbol() }}</span>
            <span class="amount">{{ (orderData.total_amount || orderData.totalAmount || 0).toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose" :icon="CircleClose">关闭</el-button>
        <div class="dialog-footer-content">
          <el-checkbox v-model="isPublic" :true-value="1" :false-value="0" v-if="isShowPublicCheckbox" style="margin-right: 20px;">
            设为公开
          </el-checkbox>
          <div class="button-group">
            <template v-if="showLoadToCartButton">
              <!-- 从列表项打开时显示的按钮 -->
              <el-button @click="saveAsNewOrder" :icon="CopyDocument">复制为新订单</el-button>
              <el-button
                type="primary"
                :icon="Download"
                @click="loadToCart"
              >
                加载到购物车
              </el-button>
            </template>
            <template v-else>
              <!-- 从购物车打开时显示的按钮 -->
              <el-button
                type="primary"
                :icon="Edit"
                @click="returnToCart"
              >
                返回购物车
              </el-button>
              <el-button
                v-if="hasSavedOrder"
                :icon="CopyDocument"
                @click="saveAsNewOrder"
                type="warning"
              >
                另存为
              </el-button>
              <el-button
                :disabled="saveButtonDisabled"
                :loading="isSaving"
                :icon="Upload"
                type="success"
                @click="saveOrder"
              >
                {{ hasSavedOrder ? '更新订单' : '保存订单' }}
              </el-button>
            </template>
          </div>
        </div>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { CircleClose, Download, CopyDocument, Upload, Check, Edit, Delete } from '@element-plus/icons-vue';
import { useQuotationCartStore } from '@/stores/quotationCartStore';
import { createQuotationTemp, updateQuotationTemp } from '@/utils/request';
import { isNumber } from 'element-plus/es/utils/types.mjs';
import { getCurrentUserEmpId, getCurrentUserRole } from '@/utils/authUtils';
import ErrorFallbackImage from '@/components/ErrorFallbackImage.vue';

// 获取当前货币符号的函数
const getCurrentCurrencySymbol = () => {
  try {
    // 从 localStorage 获取货币设置
    const currencySettings = localStorage.getItem('quotationCurrencySettings');

    if (currencySettings) {
      const settings = JSON.parse(currencySettings);

      // 1. 校验是否有选中的货币编码
      if (settings.selectedCurrency && Array.isArray(settings.currencies)) {
        // 2. 在 currencies 数组中查找对应编码的货币对象
        const matchedCurrency = settings.currencies.find(
          (currency) => currency.code === settings.selectedCurrency
        );

        // 3. 找到则返回对应符号，否则返回选中的编码（兜底）
        if (matchedCurrency && matchedCurrency.symbol) {
          return matchedCurrency.symbol;
        }
      }
    }
  } catch (error) {
    // 捕获 JSON 解析失败、localStorage 访问异常等错误
    console.error('获取货币符号失败:', error);
  }

  // 默认返回人民币符号
  return '¥';
};


// 获取当前货币信息的函数
const getCurrentCurrencyInfo = () => {
  try {
    // 从 localStorage 获取货币设置
    const currencySettings = localStorage.getItem('quotationCurrencySettings');
    if (currencySettings) {
      const settings = JSON.parse(currencySettings);
      if (settings.selectedCurrency) {
        const currencyCode = settings.selectedCurrency;
        const matchedCurrency = settings.currencies?.find((c: any) => c.code === currencyCode);
        if (matchedCurrency) {
          return {
            code: currencyCode,
            name: matchedCurrency.name || currencyCode,
            symbol: matchedCurrency.symbol || currencyCode,
            rate: matchedCurrency.rate || 1.0
          };
        }
      }
    }
  } catch (error) {
    // 捕获 JSON 解析失败、localStorage 访问异常等错误
    console.error('获取货币信息失败:', error);
  }

  // 默认返回人民币信息
  return {
    code: 'CNY',
    name: '人民币',
    symbol: '¥',
    rate: 1.0
  };
};

// 接收 props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  orderData: {
    type: Object,
    default: () => ({})
  },
  showLoadToCartButton: {
    type: Boolean,
    default: true  // 默认显示加载到购物车按钮
  }
});

// 定义 emit
const emit = defineEmits(['update:modelValue', 'load-to-cart', 'order-saved', 'order-updated']);

// 更新货币设置的函数
const updateCurrencySettings = (currencyInfo: any) => {
  if (!currencyInfo) return;

  // 获取当前货币设置
  const currentCurrencySettings = localStorage.getItem('quotationCurrencySettings');
  let settings;
  if (currentCurrencySettings) {
    settings = JSON.parse(currentCurrencySettings);
  } else {
    settings = { currencies: [], selectedCurrency: 'CNY' };
  }

  // 更新选中的货币
  settings.selectedCurrency = currencyInfo.code;

  // 如果货币不在列表中，则添加
  const existingCurrencyIndex = settings.currencies.findIndex((c: any) => c.code === currencyInfo.code);
  if (existingCurrencyIndex === -1) {
    settings.currencies.push(currencyInfo);
  } else {
    settings.currencies[existingCurrencyIndex] = currencyInfo;
  }

  // 保存到localStorage
  localStorage.setItem('quotationCurrencySettings', JSON.stringify(settings));
};

// 引用购物车 store
const cartStore = useQuotationCartStore();

// 响应式数据
const dialogVisible = ref(false);
const machineList = ref<any[]>([]);
const tempParams = ref<any[]>([]);
const textareaRef = ref(); // 添加textarea引用
const selectedOrderData = ref<any>({}); // 用于存储最新的订单数据，包括保存后返回的ID
const showLoadToCartButton = computed(() => props.showLoadToCartButton); // 直接使用props中的值


// 保存功能相关数据
const isSaving = ref(false);
const isSaved = ref(false); // 是否已保存
const savedOrderId = ref<number | null>(null); // 已保存的订单ID
const saveButtonDisabled = ref(false); // 保存按钮是否禁用
const isEditingOrderMark = ref(false); // 是否正在编辑订单标识
const newOrderMark = ref(''); // 新的订单标识
const isPublic = ref(0); // 是否公开报价单，默认不公开

// 监听 dialogVisible 变化
watch(() => props.modelValue, (newVal) => {
  dialogVisible.value = newVal;
  if (newVal) {
    updateOrderData();

    // 重置保存状态
    resetSaveStatus();
    // 设置当前订单标识，只在有有效订单ID时设置
    const currentOrderIdFromStorage = localStorage.getItem('quotation_current_order_id');
    const currentOrderMarkFromStorage = localStorage.getItem('quotation_current_order_mark');

    const isValidOrderId = currentOrderIdFromStorage &&
                           !isNaN(Number(currentOrderIdFromStorage)) &&
                           Number.isInteger(Number(currentOrderIdFromStorage)) &&
                           Number(currentOrderIdFromStorage) > 0;

    if (isValidOrderId && currentOrderMarkFromStorage && currentOrderMarkFromStorage !== '当前购物车预览') {
      newOrderMark.value = currentOrderMarkFromStorage;
    }
  }
});

// 监听订单数据变化
watch(() => props.orderData, () => {
  updateOrderData();
  resetSaveStatus();
  // 设置当前订单标识，只在有有效订单ID时设置
  const currentOrderIdFromStorage = localStorage.getItem('quotation_current_order_id');
  const currentOrderMarkFromStorage = localStorage.getItem('quotation_current_order_mark');

  const isValidOrderId = currentOrderIdFromStorage &&
                         !isNaN(Number(currentOrderIdFromStorage)) &&
                         Number.isInteger(Number(currentOrderIdFromStorage)) &&
                         Number(currentOrderIdFromStorage) > 0;

  if (isValidOrderId && currentOrderMarkFromStorage && currentOrderMarkFromStorage !== '当前购物车预览') {
    newOrderMark.value = currentOrderMarkFromStorage;
  }

  // 如果订单数据包含货币信息，则更新当前货币设置
  if (props.orderData && props.orderData.currency_info) {
    updateCurrencySettings(props.orderData.currency_info);
  }
}, { deep: true });

// 监听数据变化以启用保存按钮

watch([machineList, tempParams], () => {

  if (isSaved.value) {

    saveButtonDisabled.value = false; // 有修改时启用保存按钮

  }

}, { deep: true });

// 添加一个标志来区分是否是初始化状态
const isInitializing = ref(true);

// 监听isPublic值变化
watch(() => isPublic.value, async (newIsPublic) => {
  // 如果是初始化阶段，跳过API调用
  if (isInitializing.value) {
    isInitializing.value = false;
    return;
  }

  // 如果showLoadToCartButton为true，直接发送请求到后端更新对应报价单的公开状态
  if (props.showLoadToCartButton) {
    // 检查是否有有效的订单ID
    if (props.orderData && props.orderData.id) {
      try {
        // 调用后端API更新报价单的公开状态
        await updateQuotationTemp(props.orderData.id, {
          is_public: newIsPublic,
          // 保持其他字段不变
          order_mark: props.orderData.order_mark || props.orderData.orderMark,
          machine_list: props.orderData.machine_list || props.orderData.machineList || [],
          temp_params: props.orderData.temp_params || props.orderData.tempParams || [],
          total_amount: props.orderData.total_amount || props.orderData.totalAmount || 0,
          remark: props.orderData.remark || '',
          currency_info: props.orderData.currency_info || getCurrentCurrencyInfo()
        });

        // 更新cartStore中的is_public值
        cartStore.cartData.is_public = newIsPublic;
        cartStore.syncLocal(); // 立即同步到localStorage

        ElMessage.success(`报价单公开状态已${newIsPublic ? '设置为公开' : '设置为私有'}`);
      } catch (error) {
        console.error('更新报价单公开状态失败:', error);
        // 恢复原来的值
        isPublic.value = props.orderData.is_public || 0;
        ElMessage.error('更新报价单公开状态失败');
      }
    }
  }
  // 如果showLoadToCartButton为false，则不立即更新，等待保存时统一更新
});


// 计算属性：判断是否有已保存的订单
const hasSavedOrder = computed(() => {
  // 直接从localStorage检查是否有CurrentOrderInfo，以确保获取最新数据
  const currentOrderIdFromStorage = localStorage.getItem('quotation_current_order_id');
  return currentOrderIdFromStorage &&
         !isNaN(Number(currentOrderIdFromStorage)) &&
         Number.isInteger(Number(currentOrderIdFromStorage)) &&
         Number(currentOrderIdFromStorage) > 0;
});

// 计算属性：判断是否显示公开复选框
// 对非当前用户自己创建的订单在前端不显示是否设置公开的复选框，管理员不受限制
const isShowPublicCheckbox = computed(() => {
  // 如果是管理员，始终显示复选框
  const userRole = getCurrentUserRole();
  if (userRole === 'admin') {
    return true;
  }

  // 检查订单数据中是否有creator_id
  if (props.orderData && props.orderData.creator_id) {
    // 获取当前用户的员工ID
    const currentUserEmpId = getCurrentUserEmpId();
    // 如果当前用户ID与订单创建者ID匹配，或者订单没有创建者ID，则显示复选框
    return props.orderData.creator_id === currentUserEmpId || !props.orderData.creator_id;
  }

  // 默认情况下显示复选框
  return true;
});



// 重置保存状态
const resetSaveStatus = () => {
  // 直接从localStorage检查是否有CurrentOrderInfo，以确保获取最新数据
  const currentOrderIdFromStorage = localStorage.getItem('quotation_current_order_id');

  const hasLocalOrderInfo = currentOrderIdFromStorage &&
                            !isNaN(Number(currentOrderIdFromStorage)) &&
                            Number.isInteger(Number(currentOrderIdFromStorage)) &&
                            Number(currentOrderIdFromStorage) > 0;

  if (hasLocalOrderInfo) {
    isSaved.value = true;
    savedOrderId.value = Number(currentOrderIdFromStorage); // 确保保存为数字类型
    saveButtonDisabled.value = true; // 已有订单，初始时按钮为灰色（因为没有修改）
  } else {
    isSaved.value = false;
    savedOrderId.value = null;
    saveButtonDisabled.value = false; // 新订单可以保存
  }
};

// 更新订单数据显示
const updateOrderData = () => {
  const data = props.orderData || {};

  // 根据不同数据格式处理设备列表
  if (data.machine_list) {
    // 后端格式
    machineList.value = data.machine_list.map((item: any) => ({
      ...item,
      machineName: item.machineName || item.model || item.name || '未知设备',
      originalModel: item.originalModel || item.original_model || '',
      customPrice: item.customPrice || item.custom_price || item.price || 0,
      quantity: item.quantity || 1,
      thumbUrl: item.thumbUrl || item.image || '',
      brand: item.brand || '',
      subtotal: item.subtotal || (item.customPrice || item.price || 0) * (item.quantity || 1),
      editingRemark: false // 添加编辑状态
    }));
  } else if (data.machineList) {
    // 前端格式
    machineList.value = data.machineList.map((item: any) => ({
      ...item,
      subtotal: item.subtotal || (item.customPrice || 0) * (item.quantity || 1),
      editingRemark: false // 添加编辑状态
    }));
  } else {
    machineList.value = [];
  }

  // 根据不同数据格式处理临时参数
  if (data.temp_params) {
    // 后端格式
    tempParams.value = data.temp_params.map((item: any) => ({
      ...item,
      name: item.name || item.paramName || '未知项目',
      type: item.type || item.paramType || 'FIXED',
      value: item.value || 0,
      editingRemark: false // 添加编辑状态
    }));
  } else if (data.tempParams) {
    // 前端格式
    tempParams.value = data.tempParams.map((item: any) => ({
      ...item,
      editingRemark: false // 添加编辑状态
    }));
  } else {
    tempParams.value = [];
  }

  // 更新isPublic值 - 如果orderData中有is_public则使用，否则从cartStore读取，最后使用默认值0
  isPublic.value = data.is_public !== undefined && data.is_public !== null
    ? data.is_public
    : cartStore.cartData.is_public || 0;

  // 更新selectedOrderData
  selectedOrderData.value = { ...props.orderData };
};

// 开始编辑备注
const startEditingRemark = (row: any, type: 'machine' | 'tempParam', index: number) => {
  // 只有当showLoadToCartButton为false时（在购物车中打开预览时）才允许编辑
  if (showLoadToCartButton.value) {
    return; // 如果showLoadToCartButton为true，则不允许编辑
  }

  // 为当前行添加编辑状态
  row.editingRemark = true;
  // 重新赋值以确保响应性
  if (type === 'machine') {
    machineList.value[index] = { ...machineList.value[index] };
  } else {
    tempParams.value[index] = { ...tempParams.value[index] };
  }

  // 在下一个tick后聚焦到textarea
  nextTick(() => {
    // 获取当前页面上所有textarea元素
    const textareas = document.querySelectorAll('textarea');
    if (textareas.length > 0) {
      // 选择最后一个textarea（即最新渲染的那个）
      const lastTextarea = textareas[textareas.length - 1];
      lastTextarea.focus();
      // 将光标移动到文本末尾
      lastTextarea.setSelectionRange(lastTextarea.value.length, lastTextarea.value.length);
    }
  });
};
// 停止编辑备注
const stopEditingRemark = (row: any, type: 'machine' | 'tempParam') => {
  // 删除末尾的空行
  if (row.remark) {
    row.remark = row.remark.replace(/\s+$/, '');
  }

  // 将更新后的数据写入本地缓存
  updateCartData();

  row.editingRemark = false;
};

// 取消编辑备注
const cancelEditingRemark = (row: any, type: 'machine' | 'tempParam') => {
  row.editingRemark = false;
};

// 更新购物车数据到本地缓存
const updateCartData = () => {
  // 更新购物车store中的数据
  // 更新机器列表中的备注
  machineList.value.forEach((updatedMachine: any) => {
    const storeMachine = cartStore.cartData.machineList.find((m: any) => m.machineId === updatedMachine.machineId);
    if (storeMachine) {
      storeMachine.remark = updatedMachine.remark || '';
    }
  });

  // 更新临时参数中的备注
  tempParams.value.forEach((updatedParam: any) => {
    const storeParam = cartStore.cartData.tempParams.find((p: any) => p.id === updatedParam.id);
    if (storeParam) {
      storeParam.remark = updatedParam.remark || '';
    }
  });

  // 同步到本地缓存
  cartStore.syncLocal();
};

// 保存订单
const saveOrder = async () => {
  isSaving.value = true;

  try {
    // 准备保存的数据
    const orderDataToSave = {
      machine_list: machineList.value,
      temp_params: tempParams.value,
      total_amount: props.orderData.total_amount || 0,
      remark: props.orderData.remark || '',
      currency_info: getCurrentCurrencyInfo(),
      is_public: isPublic.value  // 添加是否公开字段
    };

    // 直接从localStorage检查是否有CurrentOrderInfo，以确保获取最新数据
    const currentOrderIdFromStorage = localStorage.getItem('quotation_current_order_id');
    const currentOrderMarkFromStorage = localStorage.getItem('quotation_current_order_mark');

    const hasLocalOrderInfo = currentOrderIdFromStorage &&
                              !isNaN(Number(currentOrderIdFromStorage)) &&
                              Number.isInteger(Number(currentOrderIdFromStorage)) &&
                              Number(currentOrderIdFromStorage) > 0;

    if (hasLocalOrderInfo) {
      // 更新已存在的订单
      const orderId = Number(currentOrderIdFromStorage);
      await updateQuotationTemp(orderId, {
        order_mark: currentOrderMarkFromStorage || newOrderMark.value,
        machine_list: orderDataToSave.machine_list,
        temp_params: orderDataToSave.temp_params,
        total_amount: orderDataToSave.total_amount,
        remark: orderDataToSave.remark,
        currency_info: orderDataToSave.currency_info,
        is_public: orderDataToSave.is_public  // 添加是否公开字段
      });

      ElMessage.success('订单更新成功');
      saveButtonDisabled.value = true; // 更新成功后禁用保存按钮
      isSaved.value = true; // 确保状态正确
      savedOrderId.value = orderId; // 确保订单ID正确设置

      // 更新本地订单信息
      cartStore.setCurrentOrderInfo(orderId, currentOrderMarkFromStorage || newOrderMark.value);
    } else {
      // 检查是否需要输入订单标识
      // if (!newOrderMark.value.trim()) {
        const currentOrderMark = props.orderData.order_mark || props.orderData.orderMark || '新订单';
        // 提示用户输入订单标识
        const mark = await showOrderMarkDialog();
        if (!mark) {
          return; // 用户取消
        }
        newOrderMark.value = mark;
      // }

      // 创建新订单（直接创建，不再检查重名）
      const response = await createQuotationTemp({
        order_mark: newOrderMark.value,
        machine_list: orderDataToSave.machine_list,
        temp_params: orderDataToSave.temp_params,
        total_amount: orderDataToSave.total_amount,
        remark: orderDataToSave.remark,
        currency_info: orderDataToSave.currency_info,
        is_public: orderDataToSave.is_public  // 添加是否公开字段
      });

      ElMessage.success('订单保存成功');
      isSaved.value = true;
      // 从响应中获取新创建订单的ID
      if (response && response.id) {
        savedOrderId.value = response.id;
        // 更新本地orderData对象，确保显示正确的ID
        selectedOrderData.value = { ...props.orderData, id: response.id, order_mark: newOrderMark.value };
        // 触发事件通知父组件更新
        emit('order-updated', { ...props.orderData, id: response.id, order_mark: newOrderMark.value });

        // 保存新创建的订单信息到本地
        cartStore.setCurrentOrderInfo(response.id, newOrderMark.value);
      }
      saveButtonDisabled.value = true; // 保存成功后禁用保存按钮
    }
    // 触发订单保存成功的事件，通知父组件刷新列表
    emit('order-saved');
  } catch (error) {
    console.error('保存订单失败:', error);
    ElMessage.error('保存订单失败: ' + (error.message || '未知错误'));
  } finally {
    isSaving.value = false;
  }
};

// 另存为新订单
const saveAsNewOrder = async () => {
  try {
    // 提示用户输入新订单标识
    const mark = await showOrderMarkDialog();
    if (!mark) {
      return; // 用户取消
    }

    // 准备保存的数据
    const orderDataToSave = {
      order_mark: mark,
      machine_list: machineList.value,
      temp_params: tempParams.value,
      total_amount: props.orderData.total_amount || 0,
      remark: props.orderData.remark || '',
      currency_info: getCurrentCurrencyInfo(),
      is_public: isPublic.value  // 添加是否公开字段
    };

    // 创建新订单（直接创建，不再检查重名）
    await createQuotationTemp(orderDataToSave);

    ElMessage.success('新订单保存成功');

    // 重新加载列表或更新UI
    // 这里可以触发一个事件来通知父组件刷新列表
    emit('order-saved');
  } catch (error) {
    console.error('另存为订单失败:', error);
    ElMessage.error('另存为订单失败: ' + (error.message || '未知错误'));
  }
};

// 显示订单标识输入对话框
const showOrderMarkDialog = (): Promise<string | null> => {
  return new Promise((resolve: (value: string | null) => void) => {
    // 这里需要创建一个简单的输入对话框
    // 使用Element Plus的ElMessageBox
    ElMessageBox.prompt('请输入订单标识', '保存订单', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S/,
      inputErrorMessage: '订单标识不能为空',
      inputValue: newOrderMark.value || '' // 使用当前的订单标识作为默认值
    })
    .then(({ value }) => {
      resolve(value || null);
    })
    .catch(() => {
      // 用户取消
      resolve(null);
    });
  });
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

// 格式化备注（处理换行）
const formatRemark = (remark: string) => {
  if (!remark) return '';
  return remark.replace(/\n/g, '<br>');
};

// 格式化日期时间，只显示日期和时分
const formatDateTime = (dateTimeString: string) => {
  if (!dateTimeString) return '';
  try {
    const date = new Date(dateTimeString);
    if (isNaN(date.getTime())) {
      return dateTimeString; // 如果无法解析，则返回原始字符串
    }
    return date.getFullYear() + '-' +
           String(date.getMonth() + 1).padStart(2, '0') + '-' +
           String(date.getDate()).padStart(2, '0') + ' ' +
           String(date.getHours()).padStart(2, '0') + ':' +
           String(date.getMinutes()).padStart(2, '0');
  } catch (error) {
    console.error('格式化日期时间失败:', error);
    return dateTimeString;
  }
};

// 格式化时间（仅显示日期和时分）
const formatTime = (timeStr: string) => {
  if (!timeStr) return '';
  try {
    const date = new Date(timeStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch (e) {
    // 如果格式化失败，返回原始字符串
    return timeStr;
  }
};

// 返回购物车
const returnToCart = () => {
  handleClose(); // 只是关闭对话框，不执行加载到购物车操作
};

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false);
};

// 加载到购物车
const loadToCart = () => {
  try {
    // 清空当前购物车
    cartStore.clearCart();

    // 添加设备到购物车
    if (machineList.value && machineList.value.length > 0) {
      machineList.value.forEach((machine: any) => {
        // 使用正确的参数调用addMachine方法
        // 注意：cartStore.addMachine只接受一个machine参数
        const machineToAdd = {
          id: machine.machineId || machine.id,
          model: machine.machineName || machine.model || '未知设备',
          original_model: machine.originalModel || machine.original_model || '',
          image: machine.thumbUrl || machine.image || '',
          show_price: machine.customPrice || machine.price || 0,
          added_count: 0,
          brand: machine.brand || '',
          machine_weight: machine.machineWeight || machine.machine_weight || '',
          dimensions: machine.dimensions || '',
          general_power: machine.generalPower || machine.general_power || '',
          power_supply: machine.powerSupply || machine.power_supply || '',
          machine_type: machine.machineType || machine.machine_type || 0,
          remark: machine.remark || ''
        };

        // 先添加到购物车（默认数量为1）
        cartStore.addMachine(machineToAdd);

        // 然后获取刚添加的设备并更新数量和价格
        // normalizeInputMachine会将传入的id映射为machineId，所以查找时使用原始的id值
        const addedMachine = cartStore.cartData.machineList.find((item: any) => item.machineId === machineToAdd.id);
        if (addedMachine) {
          // 更新数量
          addedMachine.quantity = machine.quantity || 1;
          // 更新价格
          addedMachine.customPrice = machine.customPrice || machine.price || 0;
          // 更新小计
          addedMachine.subtotal = (addedMachine.customPrice || 0) * (addedMachine.quantity || 1);
        }
      });
    }

    // 添加临时参数到购物车
    if (tempParams.value && tempParams.value.length > 0) {
      tempParams.value.forEach((param: any) => {
        cartStore.addTempParam(param.name, param.type, param.value, param.remark || '');
      });
    }

    // 保存当前订单ID和标识到购物车
    const orderId = props.orderData?.id || props.orderData?.order_id;
    const orderMark = props.orderData?.order_mark || props.orderData?.orderMark;

    // 只有當orderId是有效數字時才保存到購物車
    if (orderId && !isNaN(Number(orderId)) && Number.isInteger(Number(orderId)) && Number(orderId) > 0) {
      cartStore.setCurrentOrderInfo(orderId, orderMark);
    }

    // 如果订单有货币信息，则恢复货币设置
    if (props.orderData.currency_info) {
      // 保存当前货币设置到localStorage
      const currentCurrencySettings = localStorage.getItem('quotationCurrencySettings');
      let settings;
      if (currentCurrencySettings) {
        settings = JSON.parse(currentCurrencySettings);
      } else {
        settings = { currencies: [], selectedCurrency: 'CNY' };
      }

      // 更新选中的货币
      settings.selectedCurrency = props.orderData.currency_info.code;

      // 如果货币不在列表中，则添加
      const existingCurrencyIndex = settings.currencies.findIndex((c: any) => c.code === props.orderData.currency_info.code);
      if (existingCurrencyIndex === -1) {
        settings.currencies.push(props.orderData.currency_info);
      } else {
        settings.currencies[existingCurrencyIndex] = props.orderData.currency_info;
      }

      localStorage.setItem('quotationCurrencySettings', JSON.stringify(settings));
    }

    // 触发同步到本地存储
    cartStore.updateAndSync();

    ElMessage.success('报价单已加载到购物车');
    handleClose();
    emit('load-to-cart');
  } catch (error) {
    console.error('加载到购物车失败:', error);
    ElMessage.error('加载到购物车失败');
  }
};</script>

<style scoped>
.order-preview-content {
  max-height: 75vh;
  overflow-y: auto;
  padding: 10px 0;
}

/* 订单摘要区域 */
.order-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.summary-item {
  display: flex;
  flex-direction: column;
  min-width: 200px;
}

.summary-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.amount-highlight {
  color: #e64340;
  font-size: 18px;
}

/* 区块头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #ebeef5;
}

.section-header h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.section-stats {
  font-size: 14px;
  color: #909399;
}

.stats-number {
  font-weight: bold;
  color: #409eff;
}

/* 表格样式 */
:deep(.table-header) {
  background-color: #f8f9fc !important;
  color: #606266;
  font-weight: 600;
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

/* 品牌文字样式 */
.brand-text {
  font-weight: 500;
  color: #606266;
}

/* 数量和价格文字样式 */
.quantity-text, .price-text, .subtotal-text {
  font-weight: 500;
}

.price-text, .subtotal-text {
  color: #e64340;
}

/* 附加项目 */
.param-name {
  font-weight: 500;
  color: #303133;
}

.param-value {
  font-weight: 500;
  color: #67c23a;
}

/* 备注显示 */
.remark-display {
  white-space: pre-line;
  word-break: break-word;
  line-height: 1.4;
  padding: 6px 8px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  min-height: 20px;
  max-height: 60px;
  overflow-y: auto;
  transition: all 0.3s;
  color: #606266;
  font-size: 13px;
}

.remark-display:hover {
  border-color: #409eff;
  background-color: #f2f6fc;
}

.remark-display.has-remark {
  border-style: solid;
  border-color: #409eff;
  background-color: #ecf5ff;
}

.remark-display:empty::before {
  content: attr(data-placeholder);
  color: #c0c4cc;
  font-style: italic;
}

/* 单元格内容 */
.cell-content {
  display: flex;
  align-items: center;
}

/* 合计区域 */
.total-section {
  margin-top: 30px;
  padding: 25px 20px;
  background: linear-gradient(135deg, #2b58af 0%, #3a7bd5 100%);
  border-radius: 8px;
  color: white;
  box-shadow: 0 4px 12px rgba(43, 88, 175, 0.3);
}

.total-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-label {
  font-size: 18px;
  font-weight: 500;
}

.total-amount {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.currency {
  font-size: 20px;
}

.amount {
  font-size: 32px;
  font-weight: bold;
  letter-spacing: 1px;
}

/* 对话框整体样式 */
:deep(.preview-dialog) {
  --el-dialog-border-radius: 10px;
}

/* 底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer-content {
  display: flex;
  align-items: center;
}

.button-group {
  display: flex;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .order-summary {
    flex-direction: column;
    gap: 15px;
  }

  .summary-item {
    min-width: auto;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .total-wrapper {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }

  .button-group {
    width: 100%;
    justify-content: center;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .order-summary {
    flex-direction: column;
    gap: 15px;
  }

  .summary-item {
    min-width: auto;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .total-wrapper {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
}
</style>