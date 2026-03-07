<template>
  <div class="order-preview-container">
    <!-- 通用头部 -->
    <!-- <CommonHeader title="订单预览" /> -->

    <div class="content-wrapper">
      <div class="order-header">
        <h2>报价订单 #{{ orderId }}</h2>
        <div class="order-date">创建时间：{{ orderDate }}</div>
      </div>

      <!-- 设备列表 -->
      <div class="order-section">
        <h3>设备清单</h3>
        <el-table
          :data="orderData.machineList"
          border
          style="width: 100%"
        >
                    <el-table-column label="缩略图" width="120">
                      <template #default="scope">
                        <el-image
                          :src="getImageUrl(scope.row.thumbUrl)"
                          style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;"
                          :preview-src-list="[getImageUrl(scope.row.thumbUrl)]"
                          :preview-teleported="true"
                          hide-on-click-modal
                        ></el-image>
                      </template>
                    </el-table-column><el-table-column prop="brand" label="品牌" width="120"></el-table-column>
          <el-table-column prop="machineName" label="设备型号" width="200">
              <template #default="scope">
                  {{ scope.row.machineName || '未知设备' }}
                  <div style="font-size: 12px; color: #999;">{{  scope.row.originalModel }}</div>
                </template>
          </el-table-column>
          <!-- <el-table-column prop="originalModel" label="原厂型号" width="150"></el-table-column> -->

          <el-table-column prop="customPrice" label="单价" width="120">
            <template #default="scope">
              ¥{{ (scope.row.customPrice || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="100"></el-table-column>
          <el-table-column prop="subtotal" label="小计" width="120">
            <template #default="scope">
              ¥{{ (scope.row.subtotal || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="备注" width="200">
            <template #default="scope">
              <div v-html="formatRemark(scope.row.remark || '')" class="remark-display"></div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 自定义临时项目 -->
        <div class="temp-params-section" v-if="orderData.tempParams && orderData.tempParams.length > 0">
          <h3>自定义项目</h3>
          <el-table
            :data="orderData.tempParams"
            border
            style="width: 100%"
          >
            <el-table-column prop="name" label="项目名称" width="200"></el-table-column>
            <el-table-column prop="type" label="类型" width="120">
              <template #default="scope">
                {{ scope.row.type === 'COEFFICIENT' ? '系数' : '固定金额' }}
              </template>
            </el-table-column>
            <el-table-column prop="value" label="数值" width="120">
              <template #default="scope">
                {{ scope.row.type === 'COEFFICIENT' ? scope.row.value.toFixed(2) : scope.row.value.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="备注" width="200">
              <template #default="scope">
                <div v-html="formatRemark(scope.row.remark || '')" class="remark-display"></div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 合计信息 -->
      <div class="total-section">
        <div class="total-amount">
          最终合计：<span class="amount">¥{{ (orderData.totalAmount || 0).toFixed(2) }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="order-actions">
        <!-- <el-button @click="goBackToQuotation">返回临时报价</el-button> -->
        <el-button @click="goBackToCart" type="primary" plain>返回购物车修改</el-button>
        <el-button type="warning" @click="loadToCart">加载到购物车</el-button>
        <!-- <el-button type="success" @click="confirmOrder" :disabled="isConfirming">确认订单</el-button> -->
        <el-button type="success" @click="saveOrderToLocal">保存订单到本地</el-button>

        <!-- 本地订单列表 -->
        <div class="local-orders-section">
          <h4>本地订单列表</h4>
          <el-select
            v-model="selectedLocalOrder"
            placeholder="选择本地订单"
            style="width: 100%; margin-bottom: 10px;"
            @change="loadLocalOrder"
          >
            <el-option
              v-for="order in localOrders"
              :key="order.orderId"
              :label="`${order.orderId} (¥${(order.totalAmount || 0).toFixed(2)})`"
              :value="order.orderId"
            />
          </el-select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import CommonHeader from '@/components/CommonHeader.vue';
import { useQuotationCartStore } from '@/stores/quotationCartStore';

const router = useRouter();
const route = useRoute();
const cartStore = useQuotationCartStore();
const orderData = ref<any>({});
const orderId = ref('');
const orderDate = ref('');
const isConfirming = ref(false);
// 本地订单相关
const localOrders = ref<any[]>([]);
const selectedLocalOrder = ref<string>('');

onMounted(() => {
  // 优先加载临时订单数据
  try {
    const tempOrderStr = localStorage.getItem('quotation_temp');
    if (tempOrderStr) {
      const tempOrder = JSON.parse(tempOrderStr);
      if (tempOrder && tempOrder.orderId) {
        orderData.value = tempOrder;
        orderId.value = tempOrder.orderId;
        orderDate.value = new Date(tempOrder.createdAt || Date.now()).toLocaleString('zh-CN');

        // 加载本地订单列表
        loadLocalOrders();

        // 设置当前订单为选中项
        if (tempOrder.orderId) {
          selectedLocalOrder.value = tempOrder.orderId;
        }

        return; // 成功加载临时订单，直接返回
      }
    }
  } catch (e) {
    console.error('解析临时订单数据失败:', e);
  }

  // 如果没有临时订单，尝试从路由参数获取订单ID
  const orderIdFromRoute = route.params.orderId as string;

  if (orderIdFromRoute) {
    let order = null;

    // 首先尝试从订单列表中查找
    try {
      const storedOrders = JSON.parse(localStorage.getItem('quotation_orders') || '[]');
      order = storedOrders.find((o: any) => o.orderId === orderIdFromRoute) || null;
    } catch (e) {
      console.error('解析订单列表失败:', e);
    }

    // 如果还没有找到，尝试从单独的订单存储中加载（向后兼容）
    if (!order) {
      try {
        order = JSON.parse(localStorage.getItem(`quotation_order_${orderIdFromRoute}`) || '{}');
      } catch (e) {
        console.error('解析单独订单数据失败:', e);
      }
    }

    if (order && order.orderId) {
      orderData.value = order;
      orderId.value = order.orderId;
      orderDate.value = new Date(order.createdAt || Date.now()).toLocaleString('zh-CN');
    } else {
      // 如果没有找到订单，返回购物车页面
      ElMessage.error('订单不存在');
      router.push('/quotation-management');
    }
  } else {
    // 如果没有订单ID，也没有临时订单，返回购物车页面
    ElMessage.error('没有可显示的订单');
    router.push('/quotation-management');
  }

  // 加载本地订单列表
  loadLocalOrders();

  // 设置当前订单为选中项（如果有的话）
  if (orderId.value) {
    selectedLocalOrder.value = orderId.value;
  }
});

// 加载本地订单列表
const loadLocalOrders = () => {
  try {
    const orders = JSON.parse(localStorage.getItem('quotation_orders') || '[]');
    
    // 检查是否有临时订单
    try {
      const tempOrderStr = localStorage.getItem('quotation_temp');
      if (tempOrderStr) {
        const tempOrder = JSON.parse(tempOrderStr);
        if (tempOrder && tempOrder.orderId) {
          // 将临时订单添加到订单列表的开头
          localOrders.value = [tempOrder, ...orders];
        } else {
          localOrders.value = orders;
        }
      } else {
        localOrders.value = orders;
      }
    } catch (tempError) {
      console.error('解析临时订单失败:', tempError);
      localOrders.value = orders; // 如果临时订单有问题，只显示常规订单
    }
  } catch (error) {
    console.error('加载本地订单失败:', error);
    localOrders.value = [];
  }
};

// 加载选中的本地订单
const loadLocalOrder = (selectedOrderId: string) => {
  if (!selectedOrderId) return;

  try {
    // 从本地订单列表中查找订单
    const order = localOrders.value.find((o: any) => o.orderId === selectedOrderId);
    if (order) {
      orderData.value = order;
      orderId.value = order.orderId;  // 使用外部响应式变量的.value
      orderDate.value = new Date(order.createdAt || Date.now()).toLocaleString('zh-CN');
    } else {
      // 如果在列表中找不到，尝试从localStorage中直接加载
      const orderFromStorage = JSON.parse(localStorage.getItem(`quotation_order_${selectedOrderId}`) || '{}');
      if (orderFromStorage && orderFromStorage.orderId) {
        orderData.value = orderFromStorage;
        orderId.value = orderFromStorage.orderId;  // 使用外部响应式变量的.value
        orderDate.value = new Date(orderFromStorage.createdAt || Date.now()).toLocaleString('zh-CN');
      } else {
        ElMessage.error('未找到指定订单');
      }
    }
  } catch (error) {
    console.error('加载订单失败:', error);
    ElMessage.error('加载订单失败');
  }
};



const goBackToQuotation = () => {
  router.push('/quotation-management');
};

const goBackToCart = () => {
  // 返回到临时报价页面，并通过查询参数指示打开购物车模态框
  router.push('/quotation-management?openCart=1');
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

// 加载当前订单到购物车
const loadToCart = () => {
  // 清空当前购物车
  cartStore.cartData.machineList = [];
  cartStore.cartData.tempParams = [];
  
  // 添加当前订单的设备到购物车
  if (orderData.value.machineList && orderData.value.machineList.length > 0) {
    orderData.value.machineList.forEach((machine: any) => {
      cartStore.cartData.machineList.push({
        ...machine
      });
    });
  }
  
  // 添加当前订单的临时参数到购物车
  if (orderData.value.tempParams && orderData.value.tempParams.length > 0) {
    orderData.value.tempParams.forEach((param: any) => {
      cartStore.cartData.tempParams.push({
        ...param
      });
    });
  }
  
  // 更新购物车总额
  cartStore.cartData.totalAmount = orderData.value.totalAmount || 0;
  
  // 同步到本地存储
  cartStore.syncLocal();
  
  ElMessage.success('订单已加载到购物车');
  
  // 返回到临时报价页面
  router.push('/quotation-management?openCart=1');
};

// 保存订单到本地
const saveOrderToLocal = () => {
  // 创建新订单，生成新ID
  const orderToSave = {
    orderId: `order_${Date.now()}`,  // 生成新ID
    machineList: JSON.parse(JSON.stringify(orderData.value.machineList || [])),
    tempParams: JSON.parse(JSON.stringify(orderData.value.tempParams || [])),
    totalAmount: orderData.value.totalAmount || 0,
    createdAt: new Date().toISOString()
  };

  // 添加到store的订单列表
  cartStore.orders.push(orderToSave);
  cartStore.saveOrdersToStorage();

  // 设置为当前订单ID
  cartStore.currentOrderId = orderToSave.orderId;
  localStorage.setItem('quotation_current_order_id', orderToSave.orderId);

  // 重新加载本地订单列表
  loadLocalOrders();

  // 更新当前选中项
  selectedLocalOrder.value = orderToSave.orderId;

  ElMessage.success('订单已保存到本地');
};

const confirmOrder = async () => {
  try {
    isConfirming.value = true;
    await ElMessageBox.confirm(
      `确认此订单？总金额为 ¥${(orderData.value.totalAmount || 0).toFixed(2)}，此操作不可撤销。`,
      '确认订单',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    // 这里可以添加实际订单提交逻辑
    ElMessage.success('订单已确认！');
    router.push('/quotation-management'); // 返回报价管理页面
  } catch (error) {
    if (error !== 'cancel') {
      console.error('确认订单失败:', error);
      ElMessage.error('操作失败');
    }
  } finally {
    isConfirming.value = false;
  }
};</script>

<style scoped>
.order-preview-container {
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

.order-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.order-header h2 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 24px;
}

.order-date {
  color: #909399;
  font-size: 14px;
}

.order-section h3 {
  margin-bottom: 15px;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.temp-params-section {
  margin-top: 20px;
}

.temp-params-section h3 {
  margin-bottom: 15px;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.total-section {
  text-align: right;
  padding: 20px 0;
  border-top: 1px solid #ebeef5;
  margin-top: 20px;
}

.total-amount {
  font-size: 18px;
  font-weight: bold;
  color: #606266;
}

.amount {
  font-size: 28px;
  font-weight: bold;
  color: #e64340;
  margin-left: 10px;
}

.order-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid #ebeef5;
}

.local-orders-section {
  width: 100%;
  max-width: 400px;
}

.local-orders-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.remark-display {
  white-space: pre-line;
  word-break: break-word;
  line-height: 1.4;
}
</style>