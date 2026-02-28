import request from '@/utils/request';
import { AttendanceOperation, AttendanceOperationForm, OperationType, OperationStatus } from '@/types/attendance';

// 提交考勤操作申请
export function submitOperation(data: AttendanceOperationForm) {
  return request.post<AttendanceOperation>('/api/attendance/operation', data);
}

// 上传考勤附件
export function uploadAttendanceAttachment(file: File, empId: string, operationType: string) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('emp_id', empId);
  formData.append('operation_type', operationType);
  
  return request.post('/api/upload/attendance', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

// 管理员获取待审批列表
export function getApprovalList(params: { status?: OperationStatus }) {
  return request.get<AttendanceOperation[]>('/api/attendance/approval-list', { params });
}

// 审批考勤操作
export function approveOperation(id: string, data: {
  status: OperationStatus;
  opinion?: string;
}) {
  return request.put(`/api/attendance/operation/${id}/approve`, data);
}

// 管理员手动调整考勤记录
export function adjustOperation(id: string, data: Partial<AttendanceOperation>) {
  return request.put(`/api/attendance/operation/${id}/adjust`, data);
}

// 获取考勤操作列表（根据用户角色返回不同数据：管理员返回所有，普通用户返回自己的）
export function getOperations(params: {
  emp_id?: string;
  operation_type?: OperationType;
  status?: OperationStatus;
  start_time?: string;
  end_time?: string;
}) {
  return request.get<AttendanceOperation[]>('/api/attendance/operations', { params });
}

// 获取所有考勤操作记录（管理员专用）
export function getAllOperations(params: {
  emp_id?: string;
  operation_type?: OperationType;
  status?: OperationStatus;
  start_time?: string;
  end_time?: string;
}) {
  return request.get<AttendanceOperation[]>('/api/attendance/operations', { params });
}

// 删除考勤操作
export function deleteOperation(id: string) {
  return request.delete(`/api/attendance/operation/${id}`);
}