import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

// 基础配置
const CONFIG = { MIN_QUANTITY: 1, MIN_PRICE: -Infinity }

export const useQuotationCartStore = defineStore('quotationCart', {
  state: () => {
    // 从localStorage获取数据并确保数据格式正确
    const storedData = JSON.parse(localStorage.getItem('quotation_cart_temp') || JSON.stringify({
      machineList: [], // 设备列表
      tempParams: [],  // 自定义临时项目（税费/运费/折扣等）
      totalAmount: 0   // 最终合计
    }))

    // 获取本地保存的订单列表
    const storedOrders = JSON.parse(localStorage.getItem('quotation_orders') || '[]');

    // 获取当前订单ID
    const currentOrderIdStr = localStorage.getItem('quotation_current_order_id');
    // 如果localStorage中的值是"null"字符串或"undefined"字符串，转换为null
    const currentOrderId = (currentOrderIdStr && currentOrderIdStr !== 'null' && currentOrderIdStr !== 'undefined')
      ? currentOrderIdStr
      : null;

    // 获取当前订单标识
    const currentOrderMark = localStorage.getItem('quotation_current_order_mark');
    // 如果localStorage中的值是"null"字符串或"undefined"字符串，转换为''
    const currentOrderMarkValue = (currentOrderMark && currentOrderMark !== 'null' && currentOrderMark !== 'undefined')
      ? currentOrderMark
      : '';

    // 确保数值字段被正确转换为数字
    return {
      cartData: {
        machineList: storedData.machineList.map(normalizeMachineItem),
        tempParams: ensureTempParamIds(storedData.tempParams || []),
        totalAmount: parseFloat(storedData.totalAmount) || 0
      },
      orders: storedOrders.map((order: any) => {
        // 确保订单中的数据格式正确
        return {
          ...order,
          machineList: order.machineList?.map(normalizeMachineItem) || [],
          tempParams: ensureTempParamIds(order.tempParams || [])
        };
      }),
      currentOrderId: currentOrderId,
      currentOrderMark: currentOrderMarkValue
    }
  },
  actions: {
    // 1. 添加设备到购物车
    addMachine(machine: any) {
      const normalizedMachine = normalizeInputMachine(machine);
      const exist = this.cartData.machineList.find((item: any) => item.machineId === normalizedMachine.machineId)

      if (exist) {
        exist.quantity = (parseInt(exist.quantity) || 1) + 1
        exist.subtotal = parseFloat(exist.customPrice) * parseInt(exist.quantity)
      } else {
        this.cartData.machineList.push(normalizedMachine)
      }

      this.updateAndSync()
      ElMessage.success(exist ? `${normalizedMachine.machineName}数量+1` : `${normalizedMachine.machineName}已加入购物车`)
    },

    // 2. 移除单台设备/清空购物车
    removeMachine(machineId: number) {
      this.cartData.machineList = this.cartData.machineList.filter((item: any) => item.machineId !== machineId)
      this.updateAndSync()
      ElMessage.success('设备已移除')
    },

    clearCart() {
      this.cartData.machineList = []
      this.cartData.tempParams = []
      this.updateAndSync()
      ElMessage.warning('购物车已清空')
    },

    // 3. 修改设备数量/单价（带数值校验）
    updateMachine(machineId: number, key: string, value: number) {
      const machine = this.cartData.machineList.find((item: any) => item.machineId === machineId)
      if (!machine) return

      // 数值校验
      if (key === 'quantity' && (isNaN(value) || value < CONFIG.MIN_QUANTITY)) {
        return ElMessage.error(`数量需≥${CONFIG.MIN_QUANTITY}`)
      }
      if (key === 'customPrice' && isNaN(value)) {
        return ElMessage.error('单价必须是数字')
      }

      machine[key] = Number(value)
      machine.subtotal = parseFloat(machine.customPrice) * parseInt(machine.quantity)
      this.updateAndSync()
      ElMessage.info(`修改成功，当前合计：¥${this.cartData.totalAmount.toFixed(2)}`)
    },

    // 4. 自定义临时项目（系数/固定金额）
    addTempParam(name: string, type: string, value: number, remark?: string) {
      if (!name || isNaN(value) || value < 0) {
        return ElMessage.error('项目名称不能为空，数值需≥0')
      }

      // 为新项目生成唯一ID
      const uniqueId = `temp_param_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      this.cartData.tempParams.push({
        id: uniqueId,
        name,
        type,
        value: Number(value),
        remark: remark || ''  // 添加remark字段
      })

      this.updateAndSync()
      ElMessage.success(`已添加【${name}】`)
    },

    // 更新自定义临时项目数值
    updateTempParam(id: string, value: number) {
      const param = this.cartData.tempParams.find((item: any) => item.id === id);
      if (!param) return;

      if (isNaN(value) || value < 0) {
        return ElMessage.error('数值需≥0');
      }

      param.value = Number(value);
      this.updateAndSync();
    },

    // 更新自定义临时项目备注
    updateTempParamRemark(id: string, remark: string) {
      const param = this.cartData.tempParams.find((item: any) => item.id === id);
      if (!param) return;

      param.remark = remark || '';
      this.updateAndSync();
    },

    removeTempParam(id: string) {
      this.cartData.tempParams = this.cartData.tempParams.filter((item: any) => item.id !== id)
      this.updateAndSync()
    },

    // 5. 计算合计（设备总额 + 临时项目）
    calcTotal() {
      // 设备总额
      const machineTotal = this.cartData.machineList.reduce((sum: number, item: any) => sum + (parseFloat(item.subtotal) || 0), 0)
      // 叠加临时项目（系数：相乘，固定金额：相加）
      const finalTotal = this.cartData.tempParams.reduce((total: number, param: any) => {
        return param.type === 'COEFFICIENT'
          ? total * (parseFloat(param.value) || 1)
          : total + (parseFloat(param.value) || 0)
      }, machineTotal)

      this.cartData.totalAmount = finalTotal
    },

    // 6. 生成订单（本地缓存）
    generateOrder() {
      if (this.cartData.machineList.length === 0) {
        ElMessage.error('购物车为空')
        return null
      }

      const order = {
        orderId: `order_${Date.now()}`,
        machineList: JSON.parse(JSON.stringify(this.cartData.machineList)), // 深拷贝避免引用问题
        tempParams: JSON.parse(JSON.stringify(this.cartData.tempParams)), // 深拷贝避免引用问题
        totalAmount: this.cartData.totalAmount,
        createdAt: new Date().toISOString()
      }

      // 保存到订单列表
      this.orders.push(order);
      this.saveOrdersToStorage();

      ElMessage.success(`订单生成成功！合计：¥${order.totalAmount.toFixed(2)}`)
      return order
    },

    // 7. 保存订单到本地存储
    saveOrdersToStorage() {
      localStorage.setItem('quotation_orders', JSON.stringify(this.orders));
    },

    // 设置当前订单信息
    setCurrentOrderInfo(orderId: string | number | null, orderMark: string) {
      this.currentOrderId = orderId;
      this.currentOrderMark = orderMark;
      
      // 立即同步到本地存储
      if (orderId !== null && orderId !== undefined) {
        localStorage.setItem('quotation_current_order_id', String(orderId));
      } else {
        localStorage.removeItem('quotation_current_order_id');
      }
      
      if (orderMark) {
        localStorage.setItem('quotation_current_order_mark', orderMark);
      } else {
        localStorage.removeItem('quotation_current_order_mark');
      }
    },

    // 统一更新和同步方法
    updateAndSync() {
      this.calcTotal()
      this.syncLocal()
    },

    // 辅助：同步到本地缓存
    syncLocal() {
      const dataToSave = {
        ...this.cartData,
        machineList: this.cartData.machineList.map(normalizeMachineItem)
      }
      localStorage.setItem('quotation_cart_temp', JSON.stringify(dataToSave))

      // 同步当前订单信息到本地存储
      if (this.currentOrderId !== null && this.currentOrderId !== undefined) {
        localStorage.setItem('quotation_current_order_id', String(this.currentOrderId));
      } else {
        localStorage.removeItem('quotation_current_order_id');
      }

      if (this.currentOrderMark) {
        localStorage.setItem('quotation_current_order_mark', this.currentOrderMark);
      } else {
        localStorage.removeItem('quotation_current_order_mark');
      }
    },

    // 清除当前订单信息
    clearCurrentOrderInfo() {
      this.currentOrderId = null;
      this.currentOrderMark = '';
      localStorage.removeItem('quotation_current_order_id');
      localStorage.removeItem('quotation_current_order_mark');
    },

    // 更新当前订单标识
    updateCurrentOrderMark(mark: string) {
      this.currentOrderMark = mark;
      localStorage.setItem('quotation_current_order_mark', mark);
    }
  }
})

// 工具函数：为临时参数添加ID（如果不存在）
function ensureTempParamIds(tempParams: any[]) {
  return tempParams.map(param => {
    if (!param.id) {
      // 生成唯一ID
      return {
        ...param,
        id: `temp_param_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      };
    }
    return param;
  });
}

// 工具函数：规范化机器项数据
function normalizeMachineItem(item: any) {
  return {
    ...item,
    customPrice: parseFloat(item.customPrice) || 0,
    quantity: parseInt(item.quantity) || 1,
    subtotal: parseFloat(item.subtotal) || 0
  }
}

// 工具函数：将输入机器数据规范化为购物车项格式
function normalizeInputMachine(machine: any) {
  return {
    machineId: machine.id,
    machineName: machine.model || machine.machineName || '未知设备',
    originalModel: machine.original_model || '',
    thumbUrl: machine.image || './assets/Media/Machine/sample.png',
    customPrice: parseFloat(machine.show_price) || parseFloat(machine.price) || 0,
    quantity: 1,
    subtotal: parseFloat(machine.show_price) || parseFloat(machine.price) || 0,
    brand: machine.brand || '',
    machineType: machine.machine_type || 0
  }
}