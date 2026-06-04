/**
 * 认证相关的工具函数
 *
 * ⚠️ 新增权限路由时的同步修改清单：
 * ============================================================
 * 当你新增一个路由权限时，需要同时修改以下 3 个地方：
 *
 * 1. 本文件（authUtils.ts）← 你在这里！
 *    → 在下方 RouteName 类型联合中添加新的路由名称字符串
 *
 * 2. soonwin-os-Python-Server/app/constants/simple_permission_constants.py
 *    → 添加 ROUTE_XXX_MANAGE = "xxx_manage" 常量
 *    → 将常量添加到 ALL_ROUTES 列表中
 *
 * 3. soonwin-os-Python-Server/app/routes/user_routes.py → get_all_routes() 函数
 *    → 在 route_labels 字典中添加中文名称映射（如 "xxx_manage": "某某管理"）
 *    → 否则前端将显示英文 fallback（下划线转空格 + 首字母大写）
 * ============================================================
 */

// 定义路由权限类型（与后端 simple_permission_constants.py 的 ALL_ROUTES 保持一致）
export type RouteName =
  | 'display_file_manage'      // 文件展示 - 全员共有
  | 'photo_manage'             // 照片管理 - 全员共有
  | 'punch_manage'             // 打卡 - 全员共有
  | 'upload_manage'            // 文件上传 - 全员共有
  | 'video_manage'             // 视频管理 - 全员共有
  | 'inquiry_manage'           // 询盘管理 - 销售
  | 'order_manage'             // 订单管理 - 销售
  | 'order_status_manage'      // 订单状态 - 销售, 跟单
  | 'expense_manage'           // 费用管理 - 仅管理员
  | 'log_manage'               // 日志管理 - 仅管理员
  | 'machine_manage'           // 设备管理 - 仅管理员
  | 'machine_list'             // 设备列表 - 全员共有
  | 'user_manage'              // 员工管理 - 仅管理员
  | 'permission_manage'        // 权限管理 - 仅管理员
  | 'attendance_manage'        // 考勤管理 - 全员共有
  | 'quotation_manage'         // 报价管理 - 销售
  | 'order_record_manage'      // 订单快速记录 - 仅管理员
  | 'customer_manage'          // 客户信息管理 - 业务员

// 为了向后兼容：定义模块名称（虽然新的权限系统使用路由名）
export const ModuleNames = {
  EMPLOYEE_MANAGE: 'user_manage' as RouteName,  // 员工管理对应user_manage路由
  ORDER_MANAGE: 'order_manage' as RouteName,    // 订单管理对应order_manage路由
  INQUIRY_MANAGE: 'inquiry_manage' as RouteName, // 询盘管理对应inquiry_manage路由
  MACHINE_MANAGE: 'machine_manage' as RouteName, // 设备管理对应machine_manage路由
  PHOTO_MANAGE: 'photo_manage' as RouteName,     // 照片管理对应photo_manage路由
  VIDEO_MANAGE: 'video_manage' as RouteName,     // 视频管理对应video_manage路由
  DISPLAY_FILE_MANAGE: 'display_file_manage' as RouteName, // 文件展示对应display_file_manage路由
  PUNCH_MANAGE: 'punch_manage' as RouteName,     // 打卡对应punch_manage路由
  UPLOAD_MANAGE: 'upload_manage' as RouteName,   // 文件上传对应upload_manage路由
  ORDER_STATUS_MANAGE: 'order_status_manage' as RouteName, // 订单状态对应order_status_manage路由
  EXPENSE_MANAGE: 'expense_manage' as RouteName, // 费用管理对应expense_manage路由
  LOG_MANAGE: 'log_manage' as RouteName          // 日志管理对应log_manage路由
};

// 为了向后兼容：模拟hasModulePermission函数，将其转换为hasRoutePermission
export function hasModulePermission(moduleName: RouteName, action: string = 'view'): boolean {
  // 将模块名映射到路由权限检查
  return hasRoutePermission(moduleName);
}

// 定义权限配置接口
interface RoutePermission {
  id: string;
  role_name: string;
  route_name: string;
  create_time: string;
  update_time: string | null;
}

// 模拟从后端获取的权限配置（实际项目中应从接口获取）
// 生产环境建议：登录后请求后端API获取当前用户的权限列表并缓存
let userRoutePermissions: string[] = [];

/**
 * 初始化用户权限（登录后调用）
 * @param permissions 从后端获取的权限列表
 */
export function initUserPermissions(permissions: RoutePermission[]): void {
  userRoutePermissions = permissions.map(item => item.route_name);
}

/**
 * 清空用户权限（退出登录时调用）
 */
export function clearUserPermissions(): void {
  userRoutePermissions = [];
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
 * 检查当前用户是否拥有指定路由的权限
 * @param routeName 路由名称
 * @returns boolean - 是否拥有该权限
 */
export function hasRoutePermission(routeName: RouteName): boolean {
  // 未登录用户无任何权限
  if (!hasToken()) {
    return false;
  }

  // 管理员拥有所有权限
  const userRole = getCurrentUserRole();
  if (userRole === 'admin') {
    return true;
  }

  // 检查用户是否有该路由的权限
  return userRoutePermissions.includes(routeName);
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
    return payload.name || payload.user_name || null;
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
      // 假设后端返回的权限数据格式为包含 route_name 字段的数组
      initUserPermissions(response);
    } else {
      console.error('权限数据格式错误:', response);
      initUserPermissions([]);
    }
  } catch (error) {
    console.error('加载用户权限失败:', error);
    // 如果无法获取权限数据，初始化为空权限
    initUserPermissions([]);
  }
}