"""权限模块名称常量（统一管理，避免硬编码）"""

# 员工管理模块
MODULE_EMPLOYEE_MANAGE = "employee_manage"
# 设备管理模块
MODULE_DEVICE_MANAGE = "device_manage"
# 权限管理模块
MODULE_PERMISSION_MANAGE = "permission_manage"
# 日志管理模块
MODULE_LOG_MANAGE = "log_manage"
# 报表统计模块
MODULE_REPORT_STAT = "report_stat"
# 费用管理模块
MODULE_EXPENSE_MANAGE = "expense_manage"
# 询盘管理模块
MODULE_INQUIRY_MANAGE = "inquiry_manage"
# 机器管理模块
MODULE_MACHINE_MANAGE = "machine_manage"
# 订单管理模块
MODULE_ORDER_MANAGE = "order_manage"
# 订单状态管理模块
MODULE_ORDER_STATUS_MANAGE = "order_status_manage"
# 照片管理模块
MODULE_PHOTO_MANAGE = "photo_manage"
# 视频管理模块
MODULE_VIDEO_MANAGE = "video_manage"
# 打卡管理模块
MODULE_PUNCH_MANAGE = "punch_manage"
# 用户管理模块
MODULE_USER_MANAGE = "user_manage"
# 展示文件管理模块
MODULE_DISPLAY_FILE_MANAGE = "display_file_manage"


# 所有模块列表（用于权限初始化/校验）
ALL_MODULES = [
    MODULE_EMPLOYEE_MANAGE,
    MODULE_DEVICE_MANAGE,
    MODULE_PERMISSION_MANAGE,
    MODULE_LOG_MANAGE,
    MODULE_REPORT_STAT,
    MODULE_EXPENSE_MANAGE,
    MODULE_INQUIRY_MANAGE,
    MODULE_MACHINE_MANAGE,
    MODULE_ORDER_MANAGE,
    MODULE_ORDER_STATUS_MANAGE,
    MODULE_PHOTO_MANAGE,
    MODULE_VIDEO_MANAGE,
    MODULE_PUNCH_MANAGE,
    MODULE_USER_MANAGE,
    MODULE_DISPLAY_FILE_MANAGE
]