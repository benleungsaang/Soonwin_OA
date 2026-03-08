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
              <div v-html="formatRemark(scope.row.remark || '')" class="remark-display" style="cursor: pointer;" @click="openRemarkModal(scope.row, 'machine')"></div>
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
                <div v-html="formatRemark(scope.row.remark || '')" class="remark-display" style="cursor: pointer;" @click="openRemarkModal(scope.row, 'tempParam')"></div>
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
        <div class="top-buttons"><!-- 本地订单列表 -->
        <div class="local-orders-section">
          <el-select
            v-model="selectedLocalOrder"
            placeholder="选择订单"
            style="width: 100%; margin-bottom: 10px;"
            @change="loadLocalOrder"
            value-key="orderId"
          >
            <el-option
              v-for="order in localOrders"
              :key="order.orderId"
              :label="`${order.orderMark} (¥${(order.totalAmount || 0).toFixed(2)}) - ${order.updateTime} ${order.creatorId} `"
              :value="String(order.orderId)"
            />
          </el-select>
        </div>
          <el-button
            v-if="!isTempOrderId()"
            type="danger"
            @click="deleteCurrentOrder"
          >删除</el-button>
          <el-button
            v-if="!isTempOrderId()"
            type="info"
            @click="editCurrentOrderName"
          >修改名字</el-button>
        </div>
        <div class="bottom-buttons">
          <el-button type="warning" @click="loadToCart">返回购物车</el-button>
          <el-button
            v-if="!isTempOrderId()"
            type="primary"
            @click="saveOrderAs"
          >另存为</el-button>
          <el-button type="success" @click="saveOrderToLocal" :disabled="!isSaveButtonActive">保存订单</el-button>
        </div>


      </div>
    </div>
  </div>

  <!-- 备注编辑模态框 -->
  <el-dialog
    v-model="isRemarkModalVisible"
    title="编辑备注"
    width="500px"
  >
    <el-input
      v-model="currentRemark"
      type="textarea"
      :rows="6"
      placeholder="请输入备注（支持换行）"
      maxlength="500"
      show-word-limit
    />
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="cancelRemark">取消</el-button>
        <el-button type="primary" @click="saveRemark">确定</el-button>
      </span>
    </template>
  </el-dialog>

  <!-- 订单名称输入模态框 -->
  <el-dialog
    v-model="isOrderNameModalVisible"
    :title="duplicateOrder ? '检测到重复订单' : '请输入订单名称'"
    width="500px"
  >
    <div v-if="duplicateOrder" class="duplicate-order-warning">
      <p>检测到同名订单，订单信息如下：</p>
      <p><strong>订单ID：</strong>{{ duplicateOrder.orderId }}</p>
      <p><strong>创建时间：</strong>{{ new Date(duplicateOrder.createTime || duplicateOrder.createdAt).toLocaleString('zh-CN') }}</p>
      <p><strong>订单金额：</strong>¥{{ (duplicateOrder.totalAmount || 0).toFixed(2) }}</p>
      <p><strong>设备数量：</strong>{{ (duplicateOrder.machineList || []).length }}</p>
      <p><strong>自定义项目：</strong>{{ (duplicateOrder.tempParams || []).length }}</p>
      <br>
      <p>请选择操作：</p>
    </div>
    <el-input
      v-model="currentOrderName"
      placeholder="请输入订单名称"
      maxlength="100"
      show-word-limit
    />
    <template #footer>
      <span class="dialog-footer">
        <el-button v-if="duplicateOrder" @click="handleDuplicateOrder('modify')">修改名字</el-button>
        <el-button v-if="duplicateOrder" type="warning" @click="handleDuplicateOrder('overwrite')">覆盖订单</el-button>
        <el-button v-if="duplicateOrder" @click="handleDuplicateOrder('saveAs')">保存同名订单</el-button>
        <el-button v-if="!duplicateOrder" @click="cancelOrderName">取消</el-button>
        <el-button v-if="!duplicateOrder" type="primary" @click="confirmOrderName">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import CommonHeader from '@/components/CommonHeader.vue';
import { useQuotationCartStore } from '@/stores/quotationCartStore';
import { getQuotationTempList, getQuotationTemp, deleteQuotationTemp, createQuotationTemp, updateQuotationTemp } from '@/utils/request';

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
// 保存按钮状态相关
const isSaveButtonActive = ref(false); // 默认为非激活状态
// 备注编辑相关
const isRemarkModalVisible = ref(false);
const currentRemarkItem = ref<any>(null); // 当前编辑的项目
const currentRemarkType = ref<'machine' | 'tempParam'>('machine'); // 当前编辑的类型
const currentRemark = ref(''); // 当前编辑的备注内容
// 订单名称相关
const isOrderNameModalVisible = ref(false);
const currentOrderName = ref('');
const duplicateOrder = ref<any>(null); // 检测到的重复订单
const saveAction = ref<'save' | 'overwrite' | 'saveAs'>('save'); // 保存操作类型

onMounted(async () => {
  try {
    // 读取当前订单ID
    const currentOrderId = localStorage.getItem('quotation_current_order_id');

    if (!currentOrderId) {
      // 如果没有当前订单ID，尝试加载临时订单数据
      try {
        // 尝试从localStorage获取临时订单数据
        const tempOrderStr = localStorage.getItem('quotation_temp');
        if (tempOrderStr) {
          const tempOrder = JSON.parse(tempOrderStr);
          if (tempOrder && tempOrder.orderId) {
            orderData.value = tempOrder;
            orderId.value = tempOrder.orderId;
            // 优先使用 updateTime，如果没有则使用 createTime
            const timeToUse = tempOrder.updateTime || tempOrder.createTime || tempOrder.update_time || tempOrder.create_time || Date.now();
            orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');

            // 设置当前订单为选中项
            if (tempOrder.orderId) {
              selectedLocalOrder.value = tempOrder.orderId;
            }
          }
        }
      } catch (e) {
        console.error('从localStorage获取临时订单数据失败:', e);
      }

      // 如果仍然没有订单数据，尝试从购物车加载
      if (!orderData.value.machineList || (Array.isArray(orderData.value.machineList) && orderData.value.machineList.length === 0)) {
        // 从购物车存储加载数据
        if (cartStore.cartData && cartStore.cartData.machineList && cartStore.cartData.machineList.length > 0) {
          // 创建临时订单数据结构
          const tempOrderId = `temp_${Date.now()}`;
          const cartOrderData = {
            orderId: tempOrderId,
            machineList: cartStore.cartData.machineList || [],
            tempParams: cartStore.cartData.tempParams || [],
            totalAmount: cartStore.cartData.totalAmount || 0,
            createTime: new Date().toISOString(),
            updateTime: new Date().toISOString(),
            orderMark: '临时订单',
            remark: cartStore.cartData.remark || '',
            creatorId: 'current_user' // 可以从authUtils获取实际用户ID
          };

          orderData.value = cartOrderData;
          orderId.value = cartOrderData.orderId;
          orderDate.value = new Date().toLocaleString('zh-CN');

          // 激活保存按钮，因为这是从购物车加载的新数据
          isSaveButtonActive.value = true;

          // 将数据保存到临时存储，以便后续访问
          localStorage.setItem('quotation_temp', JSON.stringify(cartOrderData));
          localStorage.setItem('quotation_current_order_id', cartOrderData.orderId);

          // 更新选中项
          selectedLocalOrder.value = tempOrderId;
        }
      }

      // 加载本地订单列表
      await loadLocalOrders();

      return;
    }

    // 检查当前订单ID是否为临时ID
    const isTempId = currentOrderId.startsWith('temp_');

    // 如果是临时ID，激活保存按钮
    isSaveButtonActive.value = isTempId;

    if (isTempId) {
      // 如果是临时ID，从localStorage获取临时订单数据，而不是后端API
      try {
        const tempOrderStr = localStorage.getItem('quotation_temp');
        if (tempOrderStr) {
          const tempOrder = JSON.parse(tempOrderStr);
          if (tempOrder && tempOrder.orderId) {
            // 检查ID是否匹配
            if (String(tempOrder.orderId) === String(currentOrderId)) {
              orderData.value = tempOrder;
              orderId.value = tempOrder.orderId;
              // 优先使用 updateTime，如果没有则使用 createTime
              const timeToUse = tempOrder.updateTime || tempOrder.createTime || tempOrder.update_time || tempOrder.create_time || Date.now();
              orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');

              // 确保选中项设置正确
              selectedLocalOrder.value = tempOrder.orderId;
            } else {
              // ID不匹配，尝试从后端获取（虽然这种情况不太可能）
              console.log('本地临时订单ID与当前订单ID不匹配，尝试从后端获取');
              const backendId = parseInt(currentOrderId.replace('temp_', ''));
              if (!isNaN(backendId)) {
                const tempOrder = await getQuotationTemp(backendId);
                if (tempOrder) {
                  orderData.value = {
                    ...tempOrder,
                    orderId: `temp_${tempOrder.id}`, // 后端ID转为前端临时ID格式
                    orderMark: tempOrder.order_mark,
                    // 确保数组字段使用前端格式
                    machineList: tempOrder.machine_list || [],
                    tempParams: tempOrder.temp_params || []
                  };
                  orderId.value = `temp_${tempOrder.id}`;
                  // 优先使用 updateTime，如果没有则使用 createTime
                  const timeToUse = tempOrder.update_time || tempOrder.create_time || tempOrder.updateTime || tempOrder.createTime || Date.now();
                  orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');

                  // 设置当前订单为选中项
                  if (tempOrder.id) {
                    selectedLocalOrder.value = `temp_${tempOrder.id}`;
                  }
                } else {
                  ElMessage.error('临时订单数据不完整');
                }
              } else {
                ElMessage.error('无效的临时订单ID');
              }
            }
          } else {
            ElMessage.error('临时订单数据不完整');
          }
        } else {
          ElMessage.error('未找到临时订单数据');
        }
      } catch (e) {
        console.error('从localStorage获取临时订单数据失败:', e);
        ElMessage.error('加载临时订单数据失败');
      }
    } else {
      // 如果不是临时ID，使用 loadLocalOrder 函数加载订单
      await loadLocalOrder(currentOrderId);
    }

    // 检查是否成功加载了订单数据，如果没有，则尝试从购物车加载
    if (!orderData.value.machineList || (Array.isArray(orderData.value.machineList) && orderData.value.machineList.length === 0)) {
      console.log('订单数据为空，尝试从购物车加载');
      // 从购物车存储加载数据
      if (cartStore.cartData && cartStore.cartData.machineList && cartStore.cartData.machineList.length > 0) {
        // 创建临时订单数据结构
        const tempOrderId = `temp_${Date.now()}`;
        const cartOrderData = {
          orderId: tempOrderId,
          machineList: cartStore.cartData.machineList || [],
          tempParams: cartStore.cartData.tempParams || [],
          totalAmount: cartStore.cartData.totalAmount || 0,
          createTime: new Date().toISOString(),
          updateTime: new Date().toISOString(),
          orderMark: '临时订单',
          remark: cartStore.cartData.remark || '',
          creatorId: 'current_user' // 可以从authUtils获取实际用户ID
        };

        orderData.value = cartOrderData;
        orderId.value = cartOrderData.orderId;
        orderDate.value = new Date().toLocaleString('zh-CN');

        // 激活保存按钮，因为这是从购物车加载的新数据
        isSaveButtonActive.value = true;

        // 将数据保存到临时存储，以便后续访问
        localStorage.setItem('quotation_temp', JSON.stringify(cartOrderData));
        localStorage.setItem('quotation_current_order_id', cartOrderData.orderId);

        // 更新选中项
        selectedLocalOrder.value = tempOrderId;
      }
    }

    // 加载本地订单列表
    await loadLocalOrders();
  } catch (error) {
    console.error('初始化页面失败:', error);
    ElMessage.error('页面初始化失败');
  }
});

// 加载本地订单列表
const loadLocalOrders = async () => {
  try {
    // 从后端获取临时订单列表
    const tempOrdersRes = await getQuotationTempList({ per_page: 100 });
    const tempOrders = (tempOrdersRes.quotation_temps || []).map((temp: any) => ({
      orderId: temp.order_id,  // 使用前端临时ID格式
      orderMark: temp.order_mark,
      totalAmount: temp.total_amount,
      updateTime: temp.update_time,
      createTime: temp.create_time,
      creatorId: temp.creator_id,
      // 注意：这里只包含列表显示需要的字段，详细数据需要单独获取
    }));

    // 从本地存储获取正式订单
    const orders = JSON.parse(localStorage.getItem('quotation_orders') || '[]');

    // 合并临时订单和正式订单
    // localOrders.value = [...tempOrders, ...orders];
    localStorage.setItem('quotation_orders', JSON.stringify(tempOrders));
    let currentId = localStorage.getItem('quotation_current_order_id')
    if(!currentId){
      currentId = String(tempOrders[0].orderId)
    }
    localStorage.setItem('quotation_current_order_id', currentId);
    localOrders.value = tempOrders
  } catch (error) {
    console.error('加载本地订单失败:', error);
    localOrders.value = [];
  }
};

// 加载选中的本地订单
const loadLocalOrder = async (selectedOrderId: any) => {
  // 确保 selectedOrderId 是字符串类型
  let orderIdStr: string;

  if (!selectedOrderId) {
    // 如果没有传入选中ID，使用当前存储的订单ID
    orderIdStr = localStorage.getItem('quotation_current_order_id') || '';
    if (!orderIdStr) return;
  } else {
    // 确保 selectedOrderId 是字符串类型
    orderIdStr = String(selectedOrderId);
  }

  try {
    // 检查是否为临时订单ID
    if (orderIdStr.startsWith('temp_')) {
      // 从localStorage获取临时订单数据，而不是后端API
      const tempOrderStr = localStorage.getItem('quotation_temp');
      if (tempOrderStr) {
        const tempOrder = JSON.parse(tempOrderStr);
        if (tempOrder && String(tempOrder.orderId) === String(orderIdStr)) {
          // ID匹配，使用本地临时订单数据
          orderData.value = tempOrder;
          orderId.value = tempOrder.orderId;
          // 优先使用 updateTime，如果没有则使用 createTime
          const timeToUse = tempOrder.updateTime || tempOrder.createTime || tempOrder.update_time || tempOrder.create_time || Date.now();
          orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');
        } else {
          // ID不匹配，尝试从后端获取
          console.log('本地临时订单ID与选中ID不匹配，尝试从后端获取');
          const backendId = parseInt(orderIdStr.replace('temp_', ''));
          if (!isNaN(backendId)) {
            const tempOrder = await getQuotationTemp(backendId);
            if (tempOrder) {
              orderData.value = {
                ...tempOrder,
                orderId: `temp_${tempOrder.id}`, // 后端ID转为前端临时ID格式
                orderMark: tempOrder.order_mark,
                // 确保数组字段使用前端格式
                machineList: tempOrder.machine_list || [],
                tempParams: tempOrder.temp_params || []
              };
              orderId.value = `temp_${tempOrder.id}`;
              // 优先使用 updateTime，如果没有则使用 create_time
              const timeToUse = tempOrder.update_time || tempOrder.create_time || tempOrder.updateTime || tempOrder.createTime || Date.now();
              orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');
            } else {
              ElMessage.error('未找到指定的临时订单');
              return;
            }
          } else {
            ElMessage.error('无效的临时订单ID');
            return;
          }
        }
      } else {
        // 从后端获取临时订单数据
        const backendId = parseInt(orderIdStr.replace('temp_', ''));
        if (!isNaN(backendId)) {
          const tempOrder = await getQuotationTemp(backendId);
          if (tempOrder) {
            orderData.value = {
              ...tempOrder,
              orderId: `temp_${tempOrder.id}`, // 后端ID转为前端临时ID格式
              orderMark: tempOrder.order_mark,
              // 确保数组字段使用前端格式
              machineList: tempOrder.machine_list || [],
              tempParams: tempOrder.temp_params || []
            };
            orderId.value = `temp_${tempOrder.id}`;
            // 优先使用 updateTime，如果没有则使用 create_time
            const timeToUse = tempOrder.update_time || tempOrder.create_time || tempOrder.updateTime || tempOrder.createTime || Date.now();
            orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');
          } else {
            ElMessage.error('未找到指定的临时订单');
            return;
          }
        } else {
          ElMessage.error('无效的临时订单ID');
          return;
        }
      }
    } else {
      // 对于正式订单，从后端获取完整订单数据
      try {
        // 尝试从后端API获取完整订单数据
        const backendId = parseInt(orderIdStr);
        if (!isNaN(backendId)) {
          const fullOrderData = await getQuotationTemp(backendId);
          if (fullOrderData) {
            // 将后端数据格式转换为本地存储格式（全部使用前端驼峰命名）
            const formattedOrder = {
              orderId: fullOrderData.id, // 使用后端返回的ID
              orderMark: fullOrderData.order_mark,
              totalAmount: fullOrderData.total_amount,
              updateTime: fullOrderData.update_time,
              createTime: fullOrderData.create_time,
              creatorId: fullOrderData.creator_id,
              remark: fullOrderData.remark || '',
              // 确保数组字段使用前端格式
              machineList: fullOrderData.machine_list || [],
              tempParams: fullOrderData.temp_params || [],
              // 确保其他可能的字段也使用驼峰命名
              id: fullOrderData.id, // 保留原始ID
              order_id: fullOrderData.id // 保留后端格式以防万一
            };

            // 更新订单数据
            orderData.value = formattedOrder;
            orderId.value = formattedOrder.orderId;
            // 优先使用 updateTime，如果没有则使用 createTime
            const timeToUse = formattedOrder.updateTime || formattedOrder.createTime || Date.now();
            orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');

            // 更新 quotation_orders 中的对应订单
            const orders = JSON.parse(localStorage.getItem('quotation_orders') || '[]');
            const orderIndex = orders.findIndex((o: any) => String(o.orderId) === String(orderIdStr));
            if (orderIndex !== -1) {
              // 更新现有订单
              orders[orderIndex] = formattedOrder;
            } else {
              // 如果不存在，则添加到订单列表
              orders.push(formattedOrder);
            }

            // 保存更新后的订单列表到本地存储
            localStorage.setItem('quotation_orders', JSON.stringify(orders));
          } else {
            ElMessage.error('未找到指定订单');
            return;
          }
        } else {
          ElMessage.error('无效的订单ID');
          return;
        }
      } catch (apiError) {
        console.error('从后端获取订单数据失败:', apiError);
        // 如果后端获取失败，尝试从本地存储中查找
        const orders = JSON.parse(localStorage.getItem('quotation_orders') || '[]');
        const order = orders.find((o: any) => String(o.orderId) === String(orderIdStr));
        if (order) {
          orderData.value = order;
          orderId.value = order.orderId;  // 使用外部响应式变量的.value
          // 优先使用 updateTime，如果没有则使用 createdAt
          const timeToUse = order.updateTime || order.createdAt || Date.now();
          orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');
        } else {
          // 如果在列表中找不到，尝试从localStorage中直接加载
          const orderFromStorage = JSON.parse(localStorage.getItem(`quotation_order_${orderIdStr}`) || '{}');
          if (orderFromStorage && orderFromStorage.orderId) {
            orderData.value = orderFromStorage;
            orderId.value = orderFromStorage.orderId;  // 使用外部响应式变量的.value
            // 优先使用 updateTime，如果没有则使用 createdAt
            const timeToUse = orderFromStorage.updateTime || orderFromStorage.createdAt || Date.now();
            orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');
          } else {
            ElMessage.error('未找到指定订单');
          }
        }
      }
    }
    localStorage.setItem('quotation_current_order_id', orderIdStr);

    // 更新当前选中项
    selectedLocalOrder.value = orderIdStr;
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

// 判断当前订单ID是否为临时ID
const isTempOrderId = () => {
  const currentOrderId = localStorage.getItem('quotation_current_order_id');
  return currentOrderId && currentOrderId.startsWith('temp_');
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

// 打开备注编辑模态框
const openRemarkModal = (item: any, type: 'machine' | 'tempParam') => {
  currentRemarkItem.value = item;
  currentRemarkType.value = type;
  currentRemark.value = item.remark || '';
  isRemarkModalVisible.value = true;
};

// 保存备注
const saveRemark = () => {
  if (currentRemarkItem.value) {
    // 更新备注内容
    currentRemarkItem.value.remark = currentRemark.value;

    // 激活保存按钮
    isSaveButtonActive.value = true;

    // 关闭模态框
    isRemarkModalVisible.value = false;

    ElMessage.success('备注已保存到缓存');
  }
};

// 取消备注编辑
const cancelRemark = () => {
  isRemarkModalVisible.value = false;
  currentRemark.value = currentRemarkItem.value?.remark || '';
};

// 检查订单名称是否重复
const checkDuplicateOrderName = (name: string): any => {
  if (!name) return null;

  // 检查是否在本地订单中有相同名称的订单
  const orders = JSON.parse(localStorage.getItem('quotation_orders') || '[]');
  const duplicate = orders.find((order: any) => order.orderMark === name);

  return duplicate || null;
};

// 打开订单名称输入模态框
const openOrderNameModal = (action: 'save' | 'overwrite' | 'saveAs' = 'save') => {
  saveAction.value = action;

  // 如果当前订单有orderMark，使用它作为默认值
  if (orderData.value.orderMark) {
    currentOrderName.value = orderData.value.orderMark;
  } else {
    // 否则使用默认名称
    currentOrderName.value = `订单_${new Date().toLocaleDateString('zh-CN')}`;
  }

  isOrderNameModalVisible.value = true;
};

// 确认订单名称
const confirmOrderName = () => {
  if (!currentOrderName.value.trim()) {
    ElMessage.error('订单名称不能为空');
    return;
  }

  // 检查是否有重复订单名称
  const duplicate = checkDuplicateOrderName(currentOrderName.value.trim());

  if (duplicate && saveAction.value !== 'overwrite') {
    duplicateOrder.value = duplicate;
    return;
  }

  // 如果没有重复或选择覆盖，执行保存操作
  executeSaveOrder(currentOrderName.value.trim());
};

// 处理重复订单
const handleDuplicateOrder = (action: 'modify' | 'overwrite' | 'saveAs') => {
  if (action === 'modify') {
    // 修改名字：保持模态框打开，清空重复订单信息
    duplicateOrder.value = null;
  } else if (action === 'overwrite') {
    // 覆盖订单：执行保存，使用覆盖模式
    saveAction.value = 'overwrite';
    executeSaveOrder(currentOrderName.value.trim());
  } else if (action === 'saveAs') {
    // 保存同名订单：执行保存，不检查重复
    executeSaveOrder(currentOrderName.value.trim());
  }
};

// 取消订单名称输入
const cancelOrderName = () => {
  isOrderNameModalVisible.value = false;
  currentOrderName.value = '';
  duplicateOrder.value = null;
};

// 执行保存订单
const executeSaveOrder = async (orderName: string) => {
  // 获取当前订单ID
  const currentOrderId = localStorage.getItem('quotation_current_order_id');

  if (!currentOrderId) {
    ElMessage.error('没有找到当前订单ID');
    return;
  }

  // 检查当前订单ID是否为临时ID
  const isTempId = currentOrderId.startsWith('temp_');

  if (isTempId) {
    // 如果是临时ID，需要先从localStorage获取临时订单数据
    const tempOrderStr = localStorage.getItem('quotation_temp');
    if (!tempOrderStr) {
      ElMessage.error('没有找到临时订单数据');
      return;
    }

    let tempOrder;
    try {
      tempOrder = JSON.parse(tempOrderStr);
    } catch (error) {
      console.error('解析临时订单数据失败:', error);
      ElMessage.error('临时订单数据格式错误');
      return;
    }

    // 检查是否有重名订单
    const duplicate = checkDuplicateOrderName(orderName);

    if (duplicate && saveAction.value !== 'overwrite') {
      duplicateOrder.value = duplicate;
      currentOrderName.value = orderName;
      return;
    }

    // 没有重名或选择覆盖，向后端发送POST请求创建订单
    try {
      // 准备发送到后端的数据
      const requestData = {
        order_mark: orderName,
        machine_list: tempOrder.machineList || [],
        temp_params: tempOrder.tempParams || [],
        total_amount: tempOrder.totalAmount || 0,
        remark: tempOrder.remark || '',
        save_action: saveAction.value  // 传递操作类型
      };

      // 发送POST请求到后端
      const response = await createQuotationTemp(requestData);

      if (response) {
        // 生成正式订单ID
        const orderId = `order_${Date.now()}`;

        // 创建订单对象，使用从临时订单获取的数据，并添加订单名称
        const orderToSave = {
          ...tempOrder,  // 复制临时订单的所有字段
          orderId: orderId,
          orderMark: orderName, // 使用输入的订单名称
          createTime: new Date().toISOString(), // 使用新的创建时间
          updateTime: new Date().toISOString(), // 使用新的更新时间
        };

        // 读取当前的订单列表，仅用于添加新订单
        let orders = [];
        try {
          const ordersStr = localStorage.getItem('quotation_orders');
          if (ordersStr) {
            orders = JSON.parse(ordersStr);
            if (!Array.isArray(orders)) {
              orders = [];
            }
          }
        } catch (e) {
          console.error('解析订单列表失败:', e);
          orders = [];
        }

        // 添加新订单到列表
        orders.push(orderToSave);

        // 保存更新后的订单列表到localStorage
        localStorage.setItem('quotation_orders', JSON.stringify(orders));

        // 同步到store
        cartStore.orders = orders;

        // 设置为当前订单ID
        cartStore.currentOrderId = orderToSave.orderId;
        localStorage.setItem('quotation_current_order_id', String(orderToSave.orderId));

        // 删除 quotation_temp 数据
        localStorage.removeItem('quotation_temp');
      }
    } catch (error) {
      // 检查是否为重名错误 (409 Conflict)
      if (error.response?.status === 409) {
        // 处理重名情况
        const duplicateData = error.response.data.duplicate_order;
        if (duplicateData) {
          duplicateOrder.value = duplicateData;
          currentOrderName.value = orderName;
          return;
        }
      }

      console.error('保存订单到后端失败:', error);
      ElMessage.error('保存订单到后端失败: ' + (error.response?.data?.message || error.message));
      return;
    }
  } else {
    // 如果不是临时ID，则处理正式订单的保存
    // 首先读取当前存储的订单列表
    let orders = [];
    try {
      const ordersStr = localStorage.getItem('quotation_orders');
      if (ordersStr) {
        orders = JSON.parse(ordersStr);
        if (!Array.isArray(orders)) {
          orders = [];
        }
      }
    } catch (e) {
      console.error('解析订单列表失败:', e);
      orders = [];
    }

    // 查找当前订单在列表中的位置
    const orderIndex = orders.findIndex((order: any) => String(order.orderId) === String(currentOrderId));

    if (saveAction.value === 'overwrite' && orderIndex !== -1) {
      // 覆盖操作：替换现有的订单数据
      const updatedOrder = {
        orderId: currentOrderId,
        machineList: JSON.parse(JSON.stringify(orderData.value.machineList || [])),
        tempParams: JSON.parse(JSON.stringify(orderData.value.tempParams || [])),
        totalAmount: orderData.value.totalAmount || 0,
        createTime: orders[orderIndex].createTime || orders[orderIndex].createdAt, // 保持原始创建时间
        updateTime: new Date().toISOString(), // 更新时间
        orderMark: orderName // 更新订单名称
      };

      try {
        // 尝试更新后端数据
        const backendId = parseInt(currentOrderId);
        if (!isNaN(backendId)) {
          const result = await updateQuotationTemp(backendId, {
            order_mark: orderName,
            machine_list: orderData.value.machineList || [],
            temp_params: orderData.value.tempParams || [],
            total_amount: orderData.value.totalAmount || 0,
            remark: orderData.value.remark || ''
          });

          // 更新订单列表中的订单
          orders[orderIndex] = updatedOrder;
          // 保存更新后的订单列表到localStorage
          localStorage.setItem('quotation_orders', JSON.stringify(orders));
          // 同步到store
          cartStore.orders = orders;
          ElMessage.success('订单已更新到服务器');
        } else {
          // 如果ID无效，降级到本地更新
          orders[orderIndex] = updatedOrder;
          // 保存更新后的订单列表到localStorage
          localStorage.setItem('quotation_orders', JSON.stringify(orders));
          // 同步到store
          cartStore.orders = orders;
        }
      } catch (apiError) {
        console.error('更新后端订单失败:', apiError);
        // 如果API失败，仍更新本地数据
        orders[orderIndex] = updatedOrder;
        // 保存更新后的订单列表到localStorage
        localStorage.setItem('quotation_orders', JSON.stringify(orders));
        // 同步到store
        cartStore.orders = orders;
        ElMessage.warning('订单已更新到本地（服务器更新失败）');
      }
    } else if (saveAction.value === 'saveAs' || orderIndex === -1) {
      // 另存为操作或当前订单不在列表中：创建新订单
      const newOrderId = `order_${Date.now()}`;

      const newOrder = {
        orderId: newOrderId,
        machineList: JSON.parse(JSON.stringify(orderData.value.machineList || [])),
        tempParams: JSON.parse(JSON.stringify(orderData.value.tempParams || [])),
        totalAmount: orderData.value.totalAmount || 0,
        createTime: new Date().toISOString(), // 创建时间
        updateTime: new Date().toISOString(), // 更新时间
        orderMark: orderName // 使用输入的订单名称
      };

      try {
        // 尝试创建后端数据
        const result = await createQuotationTemp({
          order_mark: orderName,
          machine_list: orderData.value.machineList || [],
          temp_params: orderData.value.tempParams || [],
          total_amount: orderData.value.totalAmount || 0,
          remark: orderData.value.remark || '',
          save_action: 'saveAs'
        });

        // 添加到订单列表
        orders.push(newOrder);

        // 更新当前订单ID为新创建的ID
        cartStore.currentOrderId = newOrder.orderId;
        localStorage.setItem('quotation_current_order_id', String(newOrder.orderId));

        ElMessage.success('新订单已保存到服务器');
      } catch (apiError) {
        console.error('创建后端订单失败:', apiError);
        // 如果API失败，仍更新本地数据
        orders.push(newOrder);
        cartStore.currentOrderId = newOrder.orderId;
        localStorage.setItem('quotation_current_order_id', String(newOrder.orderId));
        ElMessage.warning('新订单已保存到本地（服务器创建失败）');
      }
    } else {
      // 默认更新操作：更新当前订单数据
      const updatedOrder = {
        orderId: currentOrderId,
        machineList: JSON.parse(JSON.stringify(orderData.value.machineList || [])),
        tempParams: JSON.parse(JSON.stringify(orderData.value.tempParams || [])),
        totalAmount: orderData.value.totalAmount || 0,
        createTime: orderData.value.createTime || orderData.value.createdAt || new Date().toISOString(), // 保持原始创建时间
        updateTime: new Date().toISOString(), // 更新时间
        orderMark: orderName // 更新订单名称
      };

      try {
        // 尝试更新后端数据
        const backendId = parseInt(currentOrderId);
        if (!isNaN(backendId)) {
          const result = await updateQuotationTemp(backendId, {
            order_mark: orderName,
            machine_list: orderData.value.machineList || [],
            temp_params: orderData.value.tempParams || [],
            total_amount: orderData.value.totalAmount || 0,
            remark: orderData.value.remark || ''
          });

          // 更新订单列表中的订单
          orders[orderIndex] = updatedOrder;
          // 保存更新后的订单列表到localStorage
          localStorage.setItem('quotation_orders', JSON.stringify(orders));
          // 同步到store
          cartStore.orders = orders;
          ElMessage.success('订单已更新到服务器');
        } else {
          // 如果ID无效，降级到本地更新
          orders[orderIndex] = updatedOrder;
          // 保存更新后的订单列表到localStorage
          localStorage.setItem('quotation_orders', JSON.stringify(orders));
          // 同步到store
          cartStore.orders = orders;
        }
      } catch (apiError) {
        console.error('更新后端订单失败:', apiError);
        // 如果API失败，仍更新本地数据
        orders[orderIndex] = updatedOrder;
        // 保存更新后的订单列表到localStorage
        localStorage.setItem('quotation_orders', JSON.stringify(orders));
        // 同步到store
        cartStore.orders = orders;
        ElMessage.warning('订单已更新到本地（服务器更新失败）');
      }
    }

    // 保存更新后的订单列表到localStorage
    localStorage.setItem('quotation_orders', JSON.stringify(orders));

    // 同步到store
    cartStore.orders = orders;
  }

  // 关闭模态框
  isOrderNameModalVisible.value = false;
  currentOrderName.value = '';
  duplicateOrder.value = null;

  // 重新加载本地订单列表 - 这是关键，确保列表正确更新
  await loadLocalOrders();

  // 获取新的当前订单ID并更新选中项
  const newCurrentOrderId = localStorage.getItem('quotation_current_order_id');
  if (newCurrentOrderId) {
    selectedLocalOrder.value = newCurrentOrderId;
  }

  if (isTempId || saveAction.value === 'save' || saveAction.value === 'saveAs') {
    ElMessage.success('订单已保存到本地');
  }

  // 保存成功后灰度保存按钮
  isSaveButtonActive.value = false;
};

// 保存订单到本地
const saveOrderToLocal = async () => {
  // 获取当前订单ID
  const currentOrderId = localStorage.getItem('quotation_current_order_id');

  if (!currentOrderId) {
    ElMessage.error('没有找到当前订单ID');
    return;
  }

  // 检查当前订单ID是否为临时ID
  const isTempId = currentOrderId.startsWith('temp_');

  // 如果是临时订单，要求输入名称
  if (isTempId) {
    openOrderNameModal('save');
  } else {
    // 对于正式订单，直接执行保存
    // 使用当前订单的名称，如果没有则使用默认名称
    const orderNameToUse = orderData.value.orderMark || `订单_${new Date().toLocaleDateString('zh-CN')}`;
    await executeSaveOrder(orderNameToUse);
  }
};

// 另存为功能
const saveOrderAs = async () => {
  // 只有正式订单才允许另存为
  const currentOrderId = localStorage.getItem('quotation_current_order_id');
  if (!currentOrderId || currentOrderId.startsWith('temp_')) {
    ElMessage.error('只能对正式订单进行另存为操作');
    return;
  }

  // 强制打开输入名字框
  openOrderNameModal('saveAs');
};

// 删除当前订单功能
const deleteCurrentOrder = async () => {
  const currentOrderId = localStorage.getItem('quotation_current_order_id');
  if (!currentOrderId) {
    ElMessage.error('没有找到当前订单');
    return;
  }

  try {
    // 确认删除操作
    await ElMessageBox.confirm(
      '确定要删除当前订单吗？此操作不可撤销。',
      '删除订单',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    if (currentOrderId.startsWith('temp_')) {
      // 如果是临时订单，从后端删除
      const backendId = parseInt(currentOrderId.replace('temp_', ''));
      if (!isNaN(backendId)) {
        try {
          await deleteQuotationTemp(backendId);
          localStorage.removeItem('quotation_current_order_id');
          ElMessage.success('临时订单已删除');

          // 跳转到购物车页面
          router.push('/quotation-management');
          return;
        } catch (apiError) {
          console.error('删除后端临时订单失败:', apiError);
          ElMessage.error('删除临时订单失败');
          return;
        }
      } else {
        ElMessage.error('无效的临时订单ID');
        return;
      }
    }

    // 对于正式订单，从后端API删除
    const backendId = parseInt(currentOrderId);
    if (!isNaN(backendId)) {
      try {
        // 调用后端API删除正式订单
        const result = await deleteQuotationTemp(backendId);

        // 从本地订单列表中删除
        let orders = [];
        try {
          const ordersStr = localStorage.getItem('quotation_orders');
          if (ordersStr) {
            orders = JSON.parse(ordersStr);
            if (!Array.isArray(orders)) {
              orders = [];
            }
          }
        } catch (e) {
          console.error('解析订单列表失败:', e);
          orders = [];
        }

        const orderIndex = orders.findIndex((order: any) => String(order.orderId) === String(currentOrderId));

        if (orderIndex !== -1) {
          // 从数组中移除订单
          orders.splice(orderIndex, 1);
          // 更新本地存储
          localStorage.setItem('quotation_orders', JSON.stringify(orders));
          // 同步到store
          cartStore.orders = orders;

          // 更新本地订单列表
          loadLocalOrders();

          // 尝试加载前一个订单，如果没有则返回购物车
          if (orders.length > 0) {
            // 找到前一个订单（使用最新的订单）
            const previousOrder = orders[orders.length - 1]; // 取最后一个订单作为前一个订单
            if (previousOrder) {
              // 设置为当前订单
              localStorage.setItem('quotation_current_order_id', String(previousOrder.orderId));

              // 更新当前页面显示
              orderData.value = previousOrder;
              orderId.value = previousOrder.orderId;
              // 优先使用 updateTime，如果没有则使用 createdAt
              const timeToUse = previousOrder.updateTime || previousOrder.createdAt || Date.now();
              orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');

              // 更新下拉选中项
              selectedLocalOrder.value = previousOrder.orderId;
            }
          } else {
            // 如果没有其他订单了，清除当前订单ID并跳转到购物车
            localStorage.removeItem('quotation_current_order_id');
            router.push('/quotation-management');
          }

          ElMessage.success('订单已删除');
        } else {
          ElMessage.error('未找到当前订单');
        }
      } catch (apiError) {
        console.error('删除后端正式订单失败:', apiError);
        // 如果API失败，降级到本地删除
        let orders = [];
        try {
          const ordersStr = localStorage.getItem('quotation_orders');
          if (ordersStr) {
            orders = JSON.parse(ordersStr);
            if (!Array.isArray(orders)) {
              orders = [];
            }
          }
        } catch (e) {
          console.error('解析订单列表失败:', e);
          orders = [];
        }

        const orderIndex = orders.findIndex((order: any) => String(order.orderId) === String(currentOrderId));

        if (orderIndex !== -1) {
          // 从数组中移除订单
          orders.splice(orderIndex, 1);
          // 更新本地存储
          localStorage.setItem('quotation_orders', JSON.stringify(orders));
          // 同步到store
          cartStore.orders = orders;

          // 更新本地订单列表
          loadLocalOrders();

          // 尝试加载前一个订单，如果没有则返回购物车
          if (orders.length > 0) {
            // 找到前一个订单（使用最新的订单）
            const previousOrder = orders[orders.length - 1]; // 取最后一个订单作为前一个订单
            if (previousOrder) {
              // 设置为当前订单
              localStorage.setItem('quotation_current_order_id', String(previousOrder.orderId));

              // 更新当前页面显示
              orderData.value = previousOrder;
              orderId.value = previousOrder.orderId;
              // 优先使用 updateTime，如果没有则使用 createdAt
              const timeToUse = previousOrder.updateTime || previousOrder.createdAt || Date.now();
              orderDate.value = new Date(timeToUse).toLocaleString('zh-CN');

              // 更新下拉选中项
              selectedLocalOrder.value = previousOrder.orderId;
            }
          } else {
            // 如果没有其他订单了，清除当前订单ID并跳转到购物车
            localStorage.removeItem('quotation_current_order_id');
            router.push('/quotation-management');
          }

          ElMessage.warning('订单已从本地删除（API调用失败）');
        } else {
          ElMessage.error('未找到当前订单');
        }
      }
    } else {
      ElMessage.error('无效的订单ID');
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除订单失败');
    }
  }
};
// 修改当前订单名字功能
const editCurrentOrderName = () => {
  const currentOrderId = localStorage.getItem('quotation_current_order_id');
  if (!currentOrderId) {
    ElMessage.error('没有找到当前订单');
    return;
  }

  if (currentOrderId.startsWith('temp_')) {
    ElMessage.warning('不能修改临时订单的名称');
    return;
  }

  // 打开订单名称输入模态框，带当前名称
  openOrderNameModal('overwrite');
};




</script>

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
  align-items: flex-end; /* 靠右对齐 */
  gap: 15px;
  padding-top: 20px;
  margin-top: 20px;
  border-top: 1px solid #ebeef5;
}

.top-buttons, .bottom-buttons {
  display: flex;
  gap: 10px;
}

.top-buttons {
  justify-content: flex-end;
  width: 100%;
}

.bottom-buttons {
  justify-content: flex-end;
  width: 100%;
  flex-wrap: wrap; /* 如果按钮过多，允许换行 */
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
  padding: 8px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  min-height: 20px;
  max-height: 80px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-line;
  line-height: 1.4;
  transition: all 0.3s;
}

.remark-display:hover {
  border-color: #409eff;
  background-color: #f2f6fc;
  cursor: pointer;
}

.duplicate-order-warning {
  margin-bottom: 15px;
}
</style>