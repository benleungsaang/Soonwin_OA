// 操作类型枚举
export enum OperationType {
  LEAVE = 'leave',
  OVERTIME = 'overtime',
  MAKE_UP = 'make_up',
  APPEAL = 'appeal',
  BUSINESS_TRIP = 'business_trip',
  ADJUST = 'adjust'
}

// 操作状态枚举
export enum OperationStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVING = 'approving',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled'
}

// 考勤操作数据类型
export interface AttendanceOperation {
  id: string;
  emp_id: string;
  name: string;
  operation_type: OperationType;
  operation_status: OperationStatus;
  start_time: string | null;
  end_time: string | null;
  duration: number | null;
  reason: string;
  approver_id: string | null;
  approver_name: string | null;
  approve_time: string | null;
  approve_opinion: string | null;
  attachment: string[];
  extend_info: Record<string, any>; // 扩展信息（动态字段）
  create_time: string;
  update_time: string | null;
}

// 提交考勤操作的表单类型
export interface AttendanceOperationForm {
  emp_id: string; // 自动填充当前登录员工工号
  name: string; // 自动填充当前登录员工姓名
  operation_type: OperationType;
  start_time: string;
  end_time?: string;
  duration?: number;
  reason: string;
  attachment?: string[]; // 上传后的附件路径
  extend_info: Record<string, any>; // 不同操作的差异化字段
  operation_status?: OperationStatus; // 操作状态
}