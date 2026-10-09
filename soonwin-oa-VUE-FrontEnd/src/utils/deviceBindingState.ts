export type BindingStatus = 'waiting_scan' | 'scanned' | 'pending' | 'approved' | 'rejected' | 'expired' | 'cancelled';

export const bindingStatusText: Record<BindingStatus, string> = {
  waiting_scan: '等待扫码', scanned: '已扫码', pending: '待管理员审批',
  approved: '绑定成功', rejected: '申请已拒绝', expired: '二维码已过期', cancelled: '二维码已失效',
};

export const isTerminalBindingStatus = (status: string): boolean => ['approved', 'rejected', 'expired', 'cancelled'].includes(status);

export const secondsToExpiry = (expiresAt: string, now = Date.now()): number => Math.max(0, Math.ceil((new Date(expiresAt).getTime() - now) / 1000));
export const formatBindingCountdown = (seconds: number): string => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;

export const isExpiredSessionResponse = (httpStatus?: number): boolean => httpStatus === 410;
