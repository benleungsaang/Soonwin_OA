/**
 * 格式化询盘相关日志为易读的中文文本
 * @param logData - 后端返回的日志JSON数据
 * @returns 格式化后的日志文本
 */
export function formatInquiryLog(logData: any): string {
  // 处理空数据
  if (!logData || !logData.action || !logData.user) {
    return '日志数据格式异常';
  }

  // 操作类型中文映射
  const actionMap: Record<string, string> = {
    'create': '创建',
    'update': '修改',
    'delete': '删除',
    'reset_stats': '复位统计',
    'create_communication': '添加',
    'update_communication': '修改',
    'delete_communication': '删除',
    'restore': '恢复'
  };

  // 获取基础信息
  const actionText = actionMap[logData.action] || logData.action;
  const userName = logData.user || '未知用户';

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
function formatCreateLog(logData: any, userName: string, actionText: string): string {
  const data = logData.inquiry_data || {};
  return `${userName} [ ${actionText} ] 了一条来自[ ${data.area || ''} ]的询盘，询盘来源 [ ${data.inquiry_source || ''} ]，公司为[ ${data.company_name || ''} ]，联系人[ ${data.contact_person || ''} ]，电话[ ${data.phone || ''} ]，邮箱[ ${data.email || ''} ]，包装产品[ ${data.packaging_product || ''} ]，需求机器类型[ ${data.machine_type || ''} ]。`;
}

/**
 * 格式化更新询盘日志（只展示有变化的字段）
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatUpdateLog(logData: any, userName: string, actionText: string): string {
  const updatedFields = logData.updated_fields || {};
  let companyName = '';
  let changeDetails: string[] = [];

  // 筛选有实际变化的字段
  Object.entries(updatedFields).forEach(([field, value]: [string, any]) => {
    // 字段名中文映射
    const fieldMap: Record<string, string> = {
      'area': '地区',
      'inquiry_date': '询盘日期',
      'inquiry_source': '询盘来源',
      'company_name': '公司名称',
      'contact_person': '联系人',
      'phone': '电话',
      'email': '邮箱',
      'packaging_product': '包装产品',
      'machine_type': '机器类型'
    };

    const fieldText = fieldMap[field] || field;
    const oldValue = value.old || '';
    const newValue = value.new || '';

    // 只记录有变化的字段
    if (oldValue !== newValue) {
      changeDetails.push(`${fieldText}[ ${oldValue} ] => [ ${newValue} ]`);
    }

    // 记录公司名称（用于开头描述）
    if (field === 'company_name') {
      companyName = oldValue || newValue;
    }
  });

  // 处理无变化的情况
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
function formatDeleteLog(logData: any, userName: string, actionText: string): string {
  const data = logData.inquiry_data || {};
  const companyName = data.company_name || '';
  return `${userName} [ ${actionText} ] 了一条 [ ${companyName} ] 公司的询盘，地区 [ ${data.area || ''} ]，询盘来源 [ ${data.inquiry_source || ''} ]，联系人 [ ${data.contact_person || ''} ]，电话 [ ${data.phone || ''} ]。`;
}

/**
 * 格式化创建沟通记录日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatCreateCommunicationLog(logData: any, userName: string, actionText: string): string {
  const data = logData.communication_data || {};
  // 使用通信数据中的公司名称
  const companyName = data.company_name || '';
  return `${userName} [ ${actionText} ] 了一条关于 [ ${companyName} ] 公司的询盘沟通，主题[ ${data.subject || ''} ]，内容[ ${data.content || ''} ]，沟通日期[ ${data.communication_date || ''} ]。`;
}

/**
 * 格式化更新沟通记录日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatUpdateCommunicationLog(logData: any, userName: string, actionText: string): string {
  const updatedFields = logData.updated_fields || {};
  let changeDetails: string[] = [];
  let companyName = '';

  // 筛选有实际变化的沟通字段
  Object.entries(updatedFields).forEach(([field, value]: [string, any]) => {
    const fieldMap: Record<string, string> = {
      'subject': '沟通主题',
      'content': '沟通内容',
      'communication_date': '沟通日期',
      'company_name': '公司名称'
    };

    const fieldText = fieldMap[field] || field;
    const oldValue = value.old || '';
    const newValue = value.new || '';

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
function formatDeleteCommunicationLog(logData: any, userName: string, actionText: string): string {
  const data = logData.communication_data || {};
  // 使用通信数据中的公司名称
  const companyName = data.company_name || '';
  return `${userName} [ ${actionText} ] 了一条关于 [ ${companyName} ] 公司的询盘沟通记录，主题[${data.subject || ''}]，内容[${data.content || ''}]。`;
}

/**
 * 格式化复位统计日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatResetStatsLog(logData: any, userName: string, actionText: string): string {
  const resetTime = logData.reset_time ? new Date(logData.reset_time).toLocaleString('zh-CN') : '未知时间';
  const inquiryCount = logData.previous_new_inquiries || logData.inquiry_count || 0;
  const communicationCount = logData.previous_new_communications || logData.communication_count || 0;
  return `${userName} [ ${actionText} ] 统计信息 - 复位时间: ${resetTime}, 复位前新增询盘数: ${inquiryCount}, 新增沟通数: ${communicationCount}`;
}

/**
 * 格式化恢复操作日志
 * @param logData - 日志数据
 * @param userName - 操作人
 * @param actionText - 操作类型文本
 * @returns 格式化文本
 */
function formatRestoreLog(logData: any, userName: string, actionText: string): string {
  const restoredDataType = logData.restored_data_type;
  
  if (restoredDataType === 'communication' || restoredDataType === 'communication_update') {
    // 恢复沟通记录
    const communicationData = logData.restored_communication_data || {};
    const companyName = communicationData.company_name || '未知公司';
    return `${userName} [ ${actionText} ] 了一条关于[ ${companyName} ]公司的沟通记录，主题[ ${communicationData.subject || ''} ]，内容[ ${communicationData.content || ''} ]。`;
  } else if (restoredDataType === 'inquiry') {
    // 恢复询盘
    const inquiryData = logData.inquiry_data || {};
    return `${userName} [ ${actionText} ] 了一条来自[ ${inquiryData.area || ''} ]的询盘，询盘来源[ ${inquiryData.inquiry_source || ''} ]，公司为[ ${inquiryData.company_name || ''} ]，联系人[ ${inquiryData.contact_person || ''} ]，电话[ ${inquiryData.phone || ''} ]，邮箱[ ${inquiryData.email || ''} ]，包装产品[ ${inquiryData.packaging_product || ''} ]，需求机器类型[ ${inquiryData.machine_type || ''} ]。`;
  } else if (restoredDataType === 'inquiry_update') {
    // 恢复询盘修改
    const inquiryData = logData.inquiry_data || {}; 
    const restoredFields = logData.restored_fields || [];
    const companyName = inquiryData.company_name || '未知公司';
    return `${userName} [ ${actionText} ] 了[ ${companyName} ]公司的询盘修改，恢复字段: [ ${restoredFields.join(', ') || '无'} ]。`;
  } else {
    // 默认情况
    return `${userName} [ ${actionText} ] 了一条记录，类型: ${restoredDataType || '未知'}。`;
  }
}