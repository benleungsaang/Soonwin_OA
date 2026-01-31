/**
 * 认证相关的工具函数
 */

/**
 * 检查当前用户是否为管理员
 * @returns boolean - 是否为管理员
 */
export function isCurrentUserAdmin(): boolean {
  const token = localStorage.getItem('oa_token');
  if (!token) {
    return false;
  }
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.user_role === 'admin';
  } catch (error) {
    console.error('解析用户信息失败:', error);
    return false;
  }
}

/**
 * 检查用户是否已登录
 * @returns boolean - 是否已登录
 */
export function hasToken(): boolean {
  return !!localStorage.getItem('oa_token');
}

/**
 * 获取当前用户的用户角色
 * @returns string | null - 用户角色，如果无法获取则返回null
 */
export function getCurrentUserRole(): string | null {
  const token = localStorage.getItem('oa_token');
  if (!token) {
    return null;
  }
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.user_role || null;
  } catch (error) {
    console.error('解析用户角色失败:', error);
    return null;
  }
}

/**
 * 获取当前用户的员工ID
 * @returns string | null - 员工ID，如果无法获取则返回null
 */
export function getCurrentUserEmpId(): string | null {
  const token = localStorage.getItem('oa_token');
  if (!token) {
    return null;
  }
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.emp_id || null;
  } catch (error) {
    console.error('解析用户员工ID失败:', error);
    return null;
  }
}

/**
 * 获取当前用户的姓名
 * @returns string | null - 用户姓名，如果无法获取则返回null
 */
export function getCurrentUserName(): string | null {
  const token = localStorage.getItem('oa_token');
  if (!token) {
    return null;
  }
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.user_name || null;
  } catch (error) {
    console.error('解析用户名失败:', error);
    return null;
  }
}