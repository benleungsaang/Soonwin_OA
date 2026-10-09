export interface ConfirmedPunchRecord {
  record_id: number;
  emp_id: string;
  name: string;
  punch_type: string;
  punch_time: string;
  status: 'created' | 'already_punched';
  msg?: string;
  device_id?: string;
}

export type PunchResponseDisposition =
  | { kind: 'binding-required' }
  | { kind: 'pending-approval' }
  | { kind: 'confirmed'; record: ConfirmedPunchRecord }
  | { kind: 'invalid' };

const PUNCH_TYPES = new Set(['上班打卡', '下班打卡', '非打卡时间打卡']);

/** 仅识别打卡接口返回的明确设备授权拒绝，避免把一般 403 当成设备问题。 */
export const isDeviceBindingRequiredHttpError = (value: unknown): boolean => {
  if (!value || typeof value !== 'object') return false;

  const error = value as Record<string, any>;
  const url = error.config?.url;
  const status = error.response?.status;
  const businessStatus = error.response?.data?.data?.status;

  return (
    typeof url === 'string' && url.includes('/api/device-clock-in') &&
    status === 403 &&
    (businessStatus === 'device_binding_required' || businessStatus === 'device_change_required')
  );
};

/** Classify the unwrapped API response. Only a persisted record can be success. */
export const classifyPunchResponse = (
  value: unknown,
  expectedEmpId: string
): PunchResponseDisposition => {
  if (!value || typeof value !== 'object') return { kind: 'invalid' };

  const response = value as Record<string, unknown>;
  if (response.status === 'device_binding_required' || response.status === 'device_change_required') {
    return { kind: 'binding-required' };
  }
  if (response.status === 'pending_approval') return { kind: 'pending-approval' };

  const recordId = response.record_id;
  const empId = response.emp_id;
  const name = response.name;
  const punchType = response.punch_type;
  const punchTime = response.punch_time;
  const status = response.status;

  if (
    !Number.isSafeInteger(recordId) || Number(recordId) <= 0 ||
    typeof empId !== 'string' || empId.toLowerCase() !== expectedEmpId.toLowerCase() ||
    typeof name !== 'string' || !name.trim() || name === '未知用户' ||
    typeof punchType !== 'string' || !PUNCH_TYPES.has(punchType) || punchType === '未知类型' ||
    typeof punchTime !== 'string' || !Number.isFinite(Date.parse(punchTime)) ||
    (status !== 'created' && status !== 'already_punched') ||
    'response' in response || response.isAxiosError === true
  ) {
    return { kind: 'invalid' };
  }

  return {
    kind: 'confirmed',
    record: response as unknown as ConfirmedPunchRecord
  };
};
