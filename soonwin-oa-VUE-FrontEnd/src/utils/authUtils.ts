/**
 * 认证相关的工具函数
 */

// 定义模块权限类型
export type PermissionType = 'view' | 'edit' | 'delete';

// 定义模块名称常量（与后端保持一致）
export const ModuleNames = {
  EMPLOYEE_MANAGE: 'employee_manage',
  DEVICE_MANAGE: 'device_manage',
  EXPENSE_MANAGE: 'expense_manage',
  MACHINE_MANAGE: 'machine_manage',
  PHOTO_MANAGE: 'photo_manage',
  VIDEO_MANAGE: 'video_manage',
  ORDER_MANAGE: 'order_manage',
  INQUIRY_MANAGE: 'inquiry_manage',
  ORDER_STATUS_MANAGE: 'order_status_manage',
  PUNCH_MANAGE: 'punch_manage',
  DISPLAY_FILES_MANAGE: 'display_file_manage',
  PERMISSION_MANAGE: 'permission_manage',
  LOG_MANAGE: 'log_manage',
  REPORT_STAT: 'report_stat',
  ORDER_PROGRESS_MANAGE: 'order_progress_manage',
  USER_MANAGE: 'user_manage'
} as const;

// 定义权限配置接口
interface ModulePermission {
  id: string;
  role_name: string;
  module_name: string;
  can_view: boolean;
  can_edit: boolean;
  can_delete: boolean;
  create_time: string;
  update_time: string | null;
}

// 模拟从后端获取的权限配置（实际项目中应从接口获取）
// 生产环境建议：登录后请求 /api/user/permissions 获取当前用户的权限列表并缓存
let userPermissions: ModulePermission[] = [];

/**
 * 初始化用户权限（登录后调用）
 * @param permissions 从后端获取的权限列表
 */
export function initUserPermissions(permissions: ModulePermission[]): void {
  userPermissions = permissions;
}

/**
 * 清空用户权限（退出登录时调用）
 */
export function clearUserPermissions(): void {
  userPermissions = [];
}

/**
 * 获取当前用户的认证令牌
 * @returns string | null - 认证令牌，如果不存在则返回null
 */
export function getToken(): string | null {
  return localStorage.getItem('oa_token');
}

/**
 * 检查用户是否已登录
 * @returns boolean - 是否已登录
 */
export function hasToken(): boolean {
  return !!getToken();
}

/**
 * 获取当前用户的用户角色
 * @returns string | null - 用户角色，如果无法获取则返回null
 */
export function getCurrentUserRole(): string | null {
  const token = getToken();
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
 * 检查当前用户是否拥有指定模块的指定权限
 * @param moduleName 模块名称
 * @param permissionType 权限类型（view/edit/delete）
 * @returns boolean - 是否拥有该权限
 */
export function hasModulePermission(
  moduleName: string,
  permissionType: PermissionType = 'view'
): boolean {
  // 未登录用户无任何权限
  if (!hasToken()) {
    return false;
  }

  // 管理员拥有所有权限
  const userRole = getCurrentUserRole();
  if (userRole === 'admin') {
    return true;
  }

  // 查找该模块的权限配置
  const modulePerm = userPermissions.find(item => item.module_name === moduleName);

  if (!modulePerm) {
    return false;
  }

  // 根据权限类型返回结果
  switch (permissionType) {
    case 'view':
      return modulePerm.can_view;
    case 'edit':
      return modulePerm.can_edit;
    case 'delete':
      return modulePerm.can_delete;
    default:
      return false;
  }
}

/**
 * 获取当前用户的员工ID
 * @returns string | null - 员工ID，如果无法获取则返回null
 */
export function getCurrentUserEmpId(): string | null {
  const token = getToken();
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
  const token = getToken();
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

/**
 * 获取当前用户的完整信息
 * @returns object | null - 包含emp_id、user_name、user_role的用户信息对象，如果无法获取则返回null
 */
export interface CurrentUserInfo {
  emp_id: string | null;
  user_name: string | null;
  user_role: string | null;
}

export function getCurrentUserInfo(): CurrentUserInfo | null {
  const token = getToken();
  if (!token) {
    return null;
  }

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      emp_id: payload.emp_id || null,
      user_name: payload.user_name || null,
      user_role: payload.user_role || null
    };
  } catch (error) {
    console.error('解析用户信息失败:', error);
    return null;
  }
}

/**
 * 从后端加载用户权限（实际项目中调用此函数）
 */
export async function loadUserPermissions(): Promise<void> {
  if (!hasToken()) {
    clearUserPermissions();
    return;
  }

  try {
    // 从 request.ts 导入（匹配后端API返回的数据格式）
    const request = (await import('@/utils/request')).default;

    const response: any = await request.get('/api/user/permissions');

    if (response && Array.isArray(response)) {
      initUserPermissions(response);
    } else {
      console.error('权限数据格式错误:', response);
      initUserPermissions([]);
    }
  } catch (error) {
    console.error('加载用户权限失败:', error);
    // 降级处理：基于角色赋予默认权限
    const userRole = getCurrentUserRole();
    const defaultPermissions: ModulePermission[] = [];

    // 为不同角色设置默认权限
    if (userRole === 'sales') {
      defaultPermissions.push(
        {
          id: '',
          role_name: 'sales',
          module_name: ModuleNames.ORDER_MANAGE,
          can_view: true,
          can_edit: true,
          can_delete: false,
          create_time: new Date().toISOString(),
          update_time: null
        },
        {
          id: '',
          role_name: 'sales',
          module_name: ModuleNames.INQUIRY_MANAGE,
          can_view: true,
          can_edit: true,
          can_delete: false,
          create_time: new Date().toISOString(),
          update_time: null
        },
        {
          id: '',
          role_name: 'sales',
          module_name: ModuleNames.PHOTO_MANAGE,
          can_view: true,
          can_edit: false,
          can_delete: false,
          create_time: new Date().toISOString(),
          update_time: null
        },
        {
          id: '',
          role_name: 'sales',
          module_name: ModuleNames.VIDEO_MANAGE,
          can_view: true,
          can_edit: false,
          can_delete: false,
          create_time: new Date().toISOString(),
          update_time: null
        }
      );
    } else if (userRole === 'user') {
      defaultPermissions.push(
        {
          id: '',
          role_name: 'user',
          module_name: ModuleNames.PUNCH_MANAGE,
          can_view: true,
          can_edit: false,
          can_delete: false,
          create_time: new Date().toISOString(),
          update_time: null
        },
        {
          id: '',
          role_name: 'user',
          module_name: ModuleNames.DISPLAY_FILES_MANAGE,
          can_view: true,
          can_edit: false,
          can_delete: false,
          create_time: new Date().toISOString(),
          update_time: null
        },
        {
          id: '',
          role_name: 'user',
          module_name: ModuleNames.ORDER_MANAGE,
          can_view: true,
          can_edit: false,
          can_delete: false,
          create_time: new Date().toISOString(),
          update_time: null
        }
      );
    }

    initUserPermissions(defaultPermissions);
  }
}