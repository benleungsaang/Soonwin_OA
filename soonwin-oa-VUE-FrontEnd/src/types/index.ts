// 扩展路由元信息类型
import 'vue-router';

declare module 'vue-router' {
  interface RouteMeta {
    title?: string; // 页面标题
    requiresAuth?: boolean; // 是否需要登录权限
  }
}


// 员工信息类型
export interface Employee {
  id: number;
  name: string;
  emp_id: string;
  dept?: string;
  phone_mac: string;
  inner_ip: string;
  create_time: string;
}

// 打卡记录类型
export interface PunchRecord {
  id: number;
  emp_id: string;
  name: string;
  punch_type: '上班打卡' | '下班打卡';
  punch_time: string;
  inner_ip?: string;
  phone_mac?: string;
}

// JWT登录响应类型
export interface LoginResponse {
  token: string;
  emp_id: string;
  name: string;
}

// 通用分页参数类型
export interface PageParams {
  page: number;
  size: number;
}

// 通用分页响应类型
export interface PageResponse<T> {
  list: T[];
  total: number;
  page: number;
  size: number;
}

// 订单类型（对应数据库 order_list 表字段）
export interface OrderList {
  id: number;
  is_new?: number; // 1=新/0=旧
  area?: string; // 地区
  customer_name?: string; // 客户名称
  customer_type?: string; // 经销商/终端
  order_time?: string; // 下单时间（日期字符串）
  ship_time?: string; // 出货时间（日期字符串）
  ship_country?: string; // 发运国家
  contract_no?: string; // 合同编号
  order_no?: string; // 订单编号
  machine_no?: string; // 包装机单号
  machine_name?: string; // 设备名称
  machine_model?: string; // 机型
  machine_count?: number; // 主机数量
  unit?: string; // 单位
  contract_amount?: number; // 合同人民币金额（元）
  deposit?: number; // 定金（元）
  balance?: number; // 尾款（元）
  tax_refund_amount?: number; // 退税后总金额（元）
  currency_amount?: number; // 美金/RMB金额
  payment_received?: number; // 回款（元）
  direct_cost?: number; // 直接成本（元）
  commission?: number; // 佣金（元）
  allocated_cost?: number; // 摊分费用（元）
  custom_income?: number; // 自定义增收费用（元）
  custom_expense?: number; // 自定义减支费用（元）
  gross_profit?: number; // 毛利（元）
  net_profit?: number; // 净利（元）
  pay_type?: string; // T/T OR LC
  latest_ship_date?: string; // 最迟装运期
  expected_delivery?: string; // 预计交期
  order_dept?: string; // 下单部门
  check_requirement?: string; // 验收要求
  attachment_imgs?: string; // 验收图片路径（多图逗号分隔）
  attachment_videos?: string; // 验收视频路径（多视频逗号分隔）
  create_time?: string; // 创建时间
  update_time?: string; // 更新时间
}

// 其他原有类型（员工、打卡记录等）保持不变...