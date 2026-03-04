// 定义类型接口
interface OperatorInfo {
  name?: string;
  id?: string;
  role?: string;
}

interface GenericLog {
  module?: string;
  operation_type?: string;
  operation_details?: Record<string, any>;
  operator_info?: OperatorInfo;
  biz_id?: string;
  // 旧格式字段
  action?: string;
  user?: string;
  // 复位统计相关
  reset_time?: string;
  previous_new_inquiries?: number;
  inquiry_count?: number;
  previous_new_communications?: number;
  communication_count?: number;
  // 恢复操作相关
  restored_data_type?: string;
  restored_communication_data?: Record<string, any>;
  inquiry_data?: Record<string, any>;
  restored_fields?: string[];
  // 通用字段
  [key: string]: any;
}

interface LogFieldMap {
  [key: string]: string;
}

// 模块配置：模块名 -> 格式化策略 + 基础配置
const MODULE_CONFIGS = {
  inquiry: {
    name: '询盘',
    actionMap: {
      create: '创建',
      update: '修改',
      delete: '删除',
      reset_stats: '复位统计',
      create_communication: '添加',
      update_communication: '修改',
      delete_communication: '删除',
      restore: '恢复'
    } as const,
    fieldMap: {
      area: '地区',
      inquiry_date: '询盘日期',
      inquiry_source: '询盘来源',
      company_name: '公司名称',
      contact_person: '联系人',
      phone: '电话',
      email: '邮箱',
      packaging_product: '包装产品',
      machine_type: '机器类型'
    } as const
  },
  video: {
    name: '视频',
    actionMap: {
      create: '上传',
      upload: '上传',
      update: '修改',
      delete: '删除',
      restore: '恢复',
      physical_delete: '彻底删除'
    } as const
  },
  photo: {
    name: '图片',
    actionMap: {
      create: '上传',
      upload: '上传',
      update: '修改',
      delete: '删除',
      restore: '恢复'
    } as const,
    fieldMap: {
      title: '标题',
      tags: '标签',
      machine_id: '机器型号',
      remark: '备注'
    } as const
  },
  employee: {
    name: '人员',
    actionMap: {
      create: '创建',
      update: '修改',
      delete: '删除',
      change_role: '更改角色',
      restore: '恢复'
    } as const
  },
  order: {
    name: '订单',
    actionMap: {
      create: '创建',
      update: '修改',
      delete: '删除',
      restore: '恢复'
    } as const,
    fieldMap: {
      area: '地区',
      customer_name: '客户名称',
      customer_type: '客户类型',
      order_time: '下单时间',
      ship_time: '出货时间',
      ship_country: '发运国家',
      contract_no: '合同编号',
      order_no: '订单编号',
      machine_name: '机器名称',
      machine_model: '机器型号',
      machine_count: '主机数量',
      contract_amount: '合同金额',
      deposit: '定金',
      balance: '尾款',
      tax_rate: '税率',
      tax_refund_amount: '退税金额',
      currency_amount: '原始发票价',
      payment_received: '回款',
      machine_cost: '机器成本',
      net_profit: '净利',
      gross_profit: '毛利',
      pay_type: '付款方式',
      commission: '佣金',
      proportionate_cost: '摊分费用',
      individual_cost: '个别费用',
      latest_ship_date: '最迟装运期',
      expected_delivery: '预计交期',
      order_dept: '下单部门'
    } as const
  }
} as const;

// 通用操作类型映射（用于 getOperationTypeText 函数）
const GENERAL_ACTION_MAP = {
  'create': '创建',
  'update': '更新',
  'delete': '删除',
  'restore': '恢复',
  'create_communication': '创建沟通记录',
  'update_communication': '更新沟通记录',
  'delete_communication': '删除沟通记录',
  'reset_stats': '复位统计数字',
  'upload': '上传',
  'physical_delete': '彻底删除',
  'change_role': '更改角色'
} as const;

/**
 * 安全的日期格式化
 * @param dateStr 日期字符串
 * @returns 格式化后的中文日期，失败返回'未知时间'
 */
const formatDateSafely = (dateStr?: string): string => {
  if (!dateStr) return '未知时间';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '未知时间';
    return date.toLocaleString('zh-CN');
  } catch (e) {
    return '未知时间';
  }
};

/**
 * 统一空值兜底
 * @param value 待处理值
 * @param fallback 兜底值，默认'未知'
 * @returns 处理后的值
 */
const fallbackValue = (value: any, fallback = '未知'): string => {
  return value === undefined || value === null || value === '' ? fallback : String(value);
};

/**
 * 获取操作类型的中文文本
 * @param module 模块名
 * @param operationType 操作类型
 * @returns 中文文本
 */
const getActionText = (module: string, operationType: string): string => {
  const moduleConfig = MODULE_CONFIGS[module as keyof typeof MODULE_CONFIGS];
  return moduleConfig?.actionMap[operationType as keyof typeof moduleConfig['actionMap']] || operationType;
};

/**
 * 格式化更新字段的通用逻辑
 * @param updatedFields 更新字段
 * @param fieldMap 字段映射表
 * @returns 格式化后的变更详情
 */
const formatUpdatedFields = (updatedFields?: Record<string, any>, fieldMap?: LogFieldMap): {
  changeDetails: string[];
  companyName: string;
  customerName: string;
} => {
  const changeDetails: string[] = [];
  let companyName = '';
  let customerName = '';
  if (!updatedFields || !fieldMap) return { changeDetails, companyName, customerName };

  // 定义 value 的类型
  interface FieldValue {
    old?: any;
    new?: any;
  }

  Object.entries(updatedFields).forEach(([field, value]) => {
    const fieldText = fieldMap[field] || field;
    const typedValue = value as FieldValue;
    const oldValue = fallbackValue(typedValue.old, '');
    const newValue = fallbackValue(typedValue.new, '');

    if (oldValue !== newValue) {
      changeDetails.push(`${fieldText}[ ${oldValue} ] => [ ${newValue} ]`);
    }

    if (field === 'company_name') {
      companyName = oldValue || newValue;
    }
    
    if (field === 'customer_name') {
      customerName = oldValue || newValue;
    }
  });

  return { changeDetails, companyName, customerName };
};

// 策略模式 - 模块格式化策略
const LOG_FORMAT_STRATEGIES = {
  inquiry: {
    generic: formatInquiryLogFromGeneric,
    legacy: formatInquiryLogLegacy
  },
  video: {
    generic: formatVideoLogFromGeneric,
    legacy: formatDefaultLog
  },
  photo: {
    generic: formatPhotoLogFromGeneric,
    legacy: formatDefaultLog
  },
  employee: {
    generic: formatEmployeeLogFromGeneric,
    legacy: formatDefaultLog
  },
  order: {
    generic: formatOrderLogFromGeneric,
    legacy: formatDefaultLog
  }
} as const;

/**
 * 格式化通用业务操作日志为易读的中文文本
 * @param logData - 后端返回的日志JSON数据
 * @returns 格式化后的日志文本
 */
export function formatBusinessLog(logData: GenericLog): string {
  // 1. 基础空值校验
  if (!logData) {
    return '日志数据格式异常';
  }

  // 2. 识别日志格式（新/旧）
  const isGenericFormat = !!logData.operation_details;
  const module = fallbackValue(logData.module || logData.action, 'unknown');
  const strategy = LOG_FORMAT_STRATEGIES[module as keyof typeof LOG_FORMAT_STRATEGIES];

  // 3. 执行对应格式化策略
  try {
    if (isGenericFormat) {
      const userName = fallbackValue(logData.operator_info?.name, '未知用户');
      const operationType = fallbackValue(logData.operation_type, 'unknown');
      return strategy?.generic?.(logData, userName, operationType) || formatDefaultGenericLog(logData);
    } else {
      return strategy?.legacy?.(logData) || formatDefaultLog(logData);
    }
  } catch (e) {
    console.error('日志格式化失败:', e, logData);
    return `日志格式化异常: ${(e as Error).message || '未知错误'}`;
  }
}

// 导出操作类型文本映射函数
export const getOperationTypeText = (operationType: string): string => {
  return GENERAL_ACTION_MAP[operationType as keyof typeof GENERAL_ACTION_MAP] || operationType;
};

// 格式化操作详情的函数
export const formatOperationDetails = (details: string): string => {
  try {
    const parsedDetails = JSON.parse(details);
    if (typeof parsedDetails === 'object') {
      return formatBusinessLog(parsedDetails); // 复用现有格式化逻辑
    }
  } catch (e) {
    console.error('解析操作详情失败:', e);
  }
  return details;
};

/**
 * 从通用日志格式格式化询盘日志
 */
function formatInquiryLogFromGeneric(logData: GenericLog, userName: string, operationType: string): string {
  const details = logData.operation_details || {};
  const bizId = fallbackValue(logData.biz_id);
  const actionText = getActionText('inquiry', operationType);

  switch (operationType) {
    case 'create':
      return formatCreateLog(details, userName, actionText);
    case 'update':
      return formatUpdateLog(details, userName, actionText);
    case 'delete':
      return formatDeleteLog(details, userName, actionText);
    case 'reset_stats':
      return formatResetStatsLog(details, userName, actionText);
    case 'create_communication':
      return formatCreateCommunicationLog(details, userName, actionText);
    case 'update_communication':
      return formatUpdateCommunicationLog(details, userName, actionText);
    case 'delete_communication':
      return formatDeleteCommunicationLog(details, userName, actionText);
    case 'restore':
      return formatRestoreLog(details, userName, actionText);
    default:
      return `${userName} 对询盘ID为 ${bizId} 的记录执行了 [${actionText}] 操作`;
  }
}

/**
 * 从通用日志格式格式化视频日志
 */
function formatVideoLogFromGeneric(logData: GenericLog, userName: string, operationType: string): string {
  const details = logData.operation_details || {};
  const title = fallbackValue(details.title || details.video_data?.title);
  const empId = fallbackValue(logData.operator_info?.id, '未知员工');
  const actionText = getActionText('video', operationType);

  return `[ ${empId} ] [ ${actionText} ] 了 [ ${title} ] 视频`;
}

/**
 * 从通用日志格式格式化图片日志
 */
function formatPhotoLogFromGeneric(logData: GenericLog, userName: string, operationType: string): string {
  const details = logData.operation_details || {};
  const title = fallbackValue(details.title || details.photo_data?.title);
  const empId = fallbackValue(logData.operator_info?.id, '未知员工');
  const actionText = getActionText('photo', operationType);

  switch (operationType) {
    case 'upload':
    case 'create':
      return `[ ${empId} ] [ ${actionText} ] 了 [ ${title} ] 照片`;
    case 'update':
      return formatPhotoUpdateLog(details, empId, actionText);
    case 'delete':
      return `[ ${empId} ] [ ${actionText} ] 了 [ ${title} ] 照片`;
    case 'restore':
      return `[ ${empId} ] [ ${actionText} ] 了 [ ${title} ] 照片`;
    default:
      return `[ ${empId} ] [ ${actionText} ] 了 [ ${title} ] 照片`;
  }
}

/**
 * 格式化照片更新日志
 */
function formatPhotoUpdateLog(details: Record<string, any>, userName: string, actionText: string): string {
  const { changeDetails, companyName } = formatUpdatedFields(details.updated_fields, MODULE_CONFIGS.photo.fieldMap);

  if (changeDetails.length === 0) {
    const title = fallbackValue(details.title || details.photo_data?.title || '');
    return `${userName} [ ${actionText} ] 了 [ ${title} ] 照片，但未修改任何内容。`;
  }

  const title = fallbackValue(details.title || details.photo_data?.title || '');
  return `${userName} [ ${actionText} ] 了 [ ${title} ] 照片，具体修改如下：${changeDetails.join('，')}。`;
}

/**
 * 从通用日志格式格式化人员日志
 */
function formatEmployeeLogFromGeneric(logData: GenericLog, userName: string, operationType: string): string {
  const details = logData.operation_details || {};
  const bizId = fallbackValue(logData.biz_id, 'unknown');
  const actionText = getActionText('employee', operationType);

  switch (operationType) {
    case 'create':
      return `${userName} [${actionText}] 了ID为 ${bizId} 的员工，姓名: ${fallbackValue(details.name, '未知')}，员工ID: ${fallbackValue(details.emp_id, '未知')}`;
    case 'update':
      return `${userName} [${actionText}] 了ID为 ${bizId} 的员工信息`;
    case 'delete':
      return `${userName} [${actionText}] 了ID为 ${bizId} 的员工`;
    case 'change_role':
      return `${userName} [${actionText}] 了ID为 ${bizId} 的员工角色`;
    case 'restore':
      return `${userName} [${actionText}] 了ID为 ${bizId} 的员工`;
    default:
      return `${userName} 对员工ID为 ${bizId} 的记录执行了 [${actionText}] 操作`;
  }
}

/**
 * 兼容旧格式的询盘日志格式化函数
 */
function formatInquiryLogLegacy(logData: GenericLog): string {
  // 处理空数据
  if (!logData || !logData.action || !logData.user) {
    return '日志数据格式异常';
  }

  // 获取基础信息
  const actionText = getActionText('inquiry', logData.action);
  const userName = fallbackValue(logData.user, '未知用户');

  // 根据不同操作类型处理
  switch (logData.action) {
    case 'create':
      return formatCreateLog(logData, userName, actionText);
    case 'update':
      return formatUpdateLog(logData, userName, actionText);
    case 'delete':
      return formatDeleteLog(logData, userName, actionText);
    case 'reset_stats':
      return formatResetStatsLog(logData, userName, actionText);
    case 'create_communication':
      return formatCreateCommunicationLog(logData, userName, actionText);
    case 'update_communication':
      return formatUpdateCommunicationLog(logData, userName, actionText);
    case 'delete_communication':
      return formatDeleteCommunicationLog(logData, userName, actionText);
    case 'restore':
      return formatRestoreLog(logData, userName, actionText);
    default:
      return `${userName} [ ${actionText} ] 了一条未知类型的记录`;
  }
}

/**
 * 格式化创建询盘日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatCreateLog(logData: GenericLog, userName: string, actionText: string): string {
  const data = logData.inquiry_data || {};
  return `${userName} [ ${actionText} ] 了一条来自[ ${fallbackValue(data.area, '')} ]的询盘，询盘来源 [ ${fallbackValue(data.inquiry_source, '')} ]，公司为[ ${fallbackValue(data.company_name, '')} ]，联系人[ ${fallbackValue(data.contact_person, '')} ]，电话[ ${fallbackValue(data.phone, '')} ]，邮箱[ ${fallbackValue(data.email, '')} ]，包装产品[ ${fallbackValue(data.packaging_product, '')} ]，需求机器类型[ ${fallbackValue(data.machine_type, '')} ]。`;
}

/**
 * 格式化更新询盘日志（只展示有变化的字段）
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatUpdateLog(logData: GenericLog, userName: string, actionText: string): string {
  const { changeDetails, companyName } = formatUpdatedFields(logData.updated_fields, MODULE_CONFIGS.inquiry.fieldMap);

  if (changeDetails.length === 0) {
    return `${userName} [ ${actionText} ] 了一条 [ ${companyName || ''} ] 公司的询盘，但未修改任何内容。`;
  }

  return `${userName} [ ${actionText} ] 了一条 [ ${companyName || ''} ] 公司的询盘，具体修改如下：${changeDetails.join('，')}。`;
}

/**
 * 格式化删除询盘日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatDeleteLog(logData: GenericLog, userName: string, actionText: string): string {
  const data = logData.inquiry_data || {};
  const companyName = fallbackValue(data.company_name, '');
  return `${userName} [ ${actionText} ] 了一条 [ ${companyName} ] 公司的询盘，地区 [ ${fallbackValue(data.area, '')} ]，询盘来源 [ ${fallbackValue(data.inquiry_source, '')} ]，联系人 [ ${fallbackValue(data.contact_person, '')} ]，电话 [ ${fallbackValue(data.phone, '')} ]。`;
}

/**
 * 格式化创建沟通记录日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatCreateCommunicationLog(logData: GenericLog, userName: string, actionText: string): string {
  const data = logData.communication_data || {};
  // 使用通信数据中的公司名称
  const companyName = fallbackValue(data.company_name, '');
  return `${userName} [ ${actionText} ] 了一条关于 [ ${companyName} ] 公司的询盘沟通，主题[ ${fallbackValue(data.subject, '')} ]，内容[ ${fallbackValue(data.content, '')} ]，沟通日期[ ${fallbackValue(data.communication_date, '')} ]。`;
}

/**
 * 格式化更新沟通记录日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatUpdateCommunicationLog(logData: GenericLog, userName: string, actionText: string): string {
  const updatedFields = logData.updated_fields || {};
  let changeDetails: string[] = [];
  let companyName = '';

  // 定义 value 的类型
  interface FieldValue {
    old?: any;
    new?: any;
  }

  // 筛选有实际变化的沟通字段
  Object.entries(updatedFields).forEach(([field, value]) => {
    const fieldMap: Record<string, string> = {
      'subject': '沟通主题',
      'content': '沟通内容',
      'communication_date': '沟通日期',
      'company_name': '公司名称'
    };

    const fieldText = fieldMap[field] || field;
    const typedValue = value as FieldValue;
    const oldValue = fallbackValue(typedValue.old, '');
    const newValue = fallbackValue(typedValue.new, '');

    if (oldValue !== newValue) {
      changeDetails.push(`${fieldText}[ ${oldValue} ] => [ ${newValue} ]`);
    }

    // 记录公司名称（用于开头描述）
    if (field === 'company_name') {
      companyName = oldValue || newValue;
    }
  });

  if (changeDetails.length === 0) {
    return `${userName} [ ${actionText} ] 了一条关于 [ ${companyName || ''} ] 公司的询盘沟通记录，但未修改任何内容。`;
  }

  return `${userName} [ ${actionText} ] 了一条关于 [ ${companyName || ''} ] 公司的询盘沟通记录，具体修改如下：${changeDetails.join('，')}。`;
}

/**
 * 格式化删除沟通记录日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatDeleteCommunicationLog(logData: GenericLog, userName: string, actionText: string): string {
  const data = logData.communication_data || {};
  // 使用通信数据中的公司名称
  const companyName = fallbackValue(data.company_name, '');
  return `${userName} [ ${actionText} ] 了一条关于 [ ${companyName} ] 公司的询盘沟通记录，主题[${fallbackValue(data.subject, '')}]，内容[${fallbackValue(data.content, '')}]。`;
}

/**
 * 格式化复位统计日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatResetStatsLog(logData: GenericLog, userName: string, actionText: string): string {
  const resetTime = formatDateSafely(logData.reset_time);
  const inquiryCount = fallbackValue(logData.previous_new_inquiries || logData.inquiry_count, '0');
  const communicationCount = fallbackValue(logData.previous_new_communications || logData.communication_count, '0');
  return `${userName} [ ${actionText} ] 统计信息 - 复位时间: ${resetTime}, 复位前新增询盘数: ${inquiryCount}, 新增沟通数: ${communicationCount}`;
}

/**
 * 格式化恢复操作日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatRestoreLog(logData: GenericLog, userName: string, actionText: string): string {
  const restoredDataType = logData.restored_data_type;

  if (restoredDataType === 'communication' || restoredDataType === 'communication_update') {
    // 恢复沟通记录
    const communicationData = logData.restored_communication_data || {};
    const companyName = fallbackValue(communicationData.company_name, '未知公司');
    return `${userName} [ ${actionText} ] 了一条关于[ ${companyName} ]公司的沟通记录，主题[ ${fallbackValue(communicationData.subject, '')} ]，内容[ ${fallbackValue(communicationData.content, '')} ]。`;
  } else if (restoredDataType === 'inquiry') {
    // 恢复询盘
    const inquiryData = logData.inquiry_data || {};
    return `${userName} [ ${actionText} ] 了一条来自[ ${fallbackValue(inquiryData.area, '')} ]的询盘，询盘来源[ ${fallbackValue(inquiryData.inquiry_source, '')} ]，公司为[ ${fallbackValue(inquiryData.company_name, '')} ]，联系人[ ${fallbackValue(inquiryData.contact_person, '')} ]，电话[ ${fallbackValue(inquiryData.phone, '')} ]，邮箱[ ${fallbackValue(inquiryData.email, '')} ]，包装产品[ ${fallbackValue(inquiryData.packaging_product, '')} ]，需求机器类型[ ${fallbackValue(inquiryData.machine_type, '')} ]。`;
  } else if (restoredDataType === 'inquiry_update') {
    // 恢复询盘修改
    const inquiryData = logData.inquiry_data || {};
    const restoredFields = logData.restored_fields || [];
    const companyName = fallbackValue(inquiryData.company_name, '未知公司');
    return `${userName} [ ${actionText} ] 了[ ${companyName} ]公司的询盘修改，恢复字段: [ ${restoredFields.join(', ') || '无'} ]。`;
  } else {
    // 默认情况
    return `${userName} [ ${actionText} ] 了一条记录，类型: ${fallbackValue(restoredDataType, '未知')}。`;
  }
}

// 默认兜底函数（兼容未配置的模块）
function formatDefaultGenericLog(logData: GenericLog): string {
  const userName = fallbackValue(logData.operator_info?.name, '未知用户');
  const module = fallbackValue(logData.module, '未知模块');
  const operationType = fallbackValue(logData.operation_type, '未知操作');
  const bizId = fallbackValue(logData.biz_id, '未知ID');

  return `${userName} 对 ${module} 模块的ID为 ${bizId} 的记录执行了 [${operationType}] 操作`;
}

/**
 * 从通用日志格式格式化订单日志
 */
function formatOrderLogFromGeneric(logData: GenericLog, userName: string, operationType: string): string {
  const details = logData.operation_details || {};
  const bizId = fallbackValue(logData.biz_id);
  const actionText = getActionText('order', operationType);

  switch (operationType) {
    case 'create':
      return formatOrderCreateLog(details, userName, actionText);
    case 'update':
      return formatOrderUpdateLog(details, userName, actionText);
    case 'delete':
      return formatOrderDeleteLog(details, userName, actionText);
    case 'restore':
      return formatOrderRestoreLog(details, userName, actionText);
    default:
      return `${userName} 对订单ID为 ${bizId} 的记录执行了 [${actionText}] 操作`;
  }
}

/**
 * 格式化创建订单日志
 */
function formatOrderCreateLog(details: Record<string, any>, userName: string, actionText: string): string {
  const data = details.order_data || {};
  const customerName = fallbackValue(data.customer_name, '');
  const area = fallbackValue(data.area, '');
  const contractNo = fallbackValue(data.contract_no, '');
  const contractAmount = fallbackValue(data.contract_amount, '0');

  return `${userName} [ ${actionText} ] 了 ${area} 地区的订单，客户为 [ ${customerName} ]，合同编号 [ ${contractNo} ]，合同金额 [ ${contractAmount} ]。`;
}

/**
 * 格式化更新订单日志
 */
function formatOrderUpdateLog(details: Record<string, any>, userName: string, actionText: string): string {
  const { changeDetails, customerName: extractedCustomerName } = formatUpdatedFields(details.updated_fields, MODULE_CONFIGS.order.fieldMap);
  
  // 优先使用从字段变更中提取的客户名称，如果没有则从order_data中获取
  const customerName = extractedCustomerName || fallbackValue(details.customer_name || details.order_data?.customer_name || '', '');
  
  if (changeDetails.length === 0) {
    return `${userName} [ ${actionText} ] 了 [ ${customerName || ''} ] 公司的订单，但未修改任何内容。`;
  }

  return `${userName} [ ${actionText} ] 了 [ ${customerName || ''} ] 公司的订单，具体修改如下：${changeDetails.join('，')}。`;
}

/**
 * 格式化删除订单日志
 */
function formatOrderDeleteLog(details: Record<string, any>, userName: string, actionText: string): string {
  const data = details.order_data || {};
  const customerName = fallbackValue(data.customer_name, '');
  const area = fallbackValue(data.area, '');
  const contractNo = fallbackValue(data.contract_no, '');
  const contractAmount = fallbackValue(data.contract_amount, '0');

  return `${userName} [ ${actionText} ] 了 ${area} 地区的订单，客户为 [ ${customerName} ]，合同编号 [ ${contractNo} ]，合同金额 [ ${contractAmount} ]。`;
}

/**
 * 格式化恢复订单日志
 */
function formatOrderRestoreLog(details: Record<string, any>, userName: string, actionText: string): string {
  const data = details.order_data || {};
  const customerName = fallbackValue(data.customer_name, '');
  const area = fallbackValue(data.area, '');
  const contractNo = fallbackValue(data.contract_no, '');

  return `${userName} [ ${actionText} ] 了 ${area} 地区的订单，客户为 [ ${customerName} ]，合同编号 [ ${contractNo} ]。`;
}

function formatDefaultLog(logData: GenericLog): string {
  const userName = fallbackValue(logData.user, '未知用户');
  const action = fallbackValue(logData.action, '未知操作');

  return `${userName} [ ${action} ] 了一条未知类型的记录`;
}