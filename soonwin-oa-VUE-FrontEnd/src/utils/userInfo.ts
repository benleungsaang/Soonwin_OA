/**
 * 全局用户信息管理模块
 * 提供在应用任何地方都能访问用户信息的功能
 */

import { 
  getCurrentUserInfo as getAuthUserInfo,
  CurrentUserInfo 
} from '@/utils/authUtils';

// 定义用户信息接口
export interface UserInfo {
  empId: string | null;
  name: string | null;
  role: string | null;
}

// 当前用户信息
let currentUserInfo: UserInfo | null = null;

/**
 * 获取当前用户信息
 * @returns UserInfo | null - 用户信息，如果未登录则返回null
 */
export function getCurrentUserInfo(): UserInfo | null {
  const authUserInfo = getAuthUserInfo();
  
  if (authUserInfo && (authUserInfo.emp_id || authUserInfo.user_name || authUserInfo.user_role)) {
    currentUserInfo = {
      empId: authUserInfo.emp_id,
      name: authUserInfo.user_name,
      role: authUserInfo.user_role
    };
    return currentUserInfo;
  }
  
  return null;
}

/**
 * 更新当前用户信息
 */
export function updateCurrentUserInfo(): void {
  const authUserInfo = getAuthUserInfo();
  
  if (authUserInfo) {
    currentUserInfo = {
      empId: authUserInfo.emp_id,
      name: authUserInfo.user_name,
      role: authUserInfo.user_role
    };
  } else {
    currentUserInfo = null;
  }
}

/**
 * 获取当前用户员工ID
 * @returns string | null - 员工ID，如果未登录则返回null
 */
export function getCurrentEmpId(): string | null {
  if (!currentUserInfo) {
    getCurrentUserInfo();
  }
  return currentUserInfo?.empId || null;
}

/**
 * 获取当前用户姓名
 * @returns string | null - 姓名，如果未登录则返回null
 */
export function getCurrentName(): string | null {
  if (!currentUserInfo) {
    getCurrentUserInfo();
  }
  return currentUserInfo?.name || null;
}

/**
 * 获取当前用户角色
 * @returns string | null - 角色，如果未登录则返回null
 */
export function getCurrentRole(): string | null {
  if (!currentUserInfo) {
    getCurrentUserInfo();
  }
  return currentUserInfo?.role || null;
}

/**
 * 清空当前用户信息
 */
export function clearCurrentUserInfo(): void {
  currentUserInfo = null;
}