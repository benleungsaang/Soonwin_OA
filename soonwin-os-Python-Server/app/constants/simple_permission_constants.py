"""简化版权限常量定义

⚠️ 新增权限路由时的同步修改清单：
============================================================
当你新增一个路由权限时，需要同时修改以下 3 个地方：

1. 本文件（simple_permission_constants.py）← 你在这里！
   → 添加 ROUTE_XXX_MANAGE = "xxx_manage" 常量
   → 将常量添加到 ALL_ROUTES 列表中

2. app/routes/user_routes.py → get_all_routes() 函数
   → 在 route_labels 字典中添加中文名称映射（如 "xxx_manage": "某某管理"）
   → 否则前端将显示英文 fallback（下划线转空格 + 首字母大写）

3. soonwin-oa-VUE-FrontEnd/src/utils/authUtils.ts
   → 在 RouteName 类型联合中添加新的路由名称字符串
============================================================
"""

# 全体共有权限的路由
ROUTE_DISPLAY_FILE_MANAGE = "display_file_manage"  # 文件展示
ROUTE_PHOTO_MANAGE = "photo_manage"                # 照片管理
ROUTE_PUNCH_MANAGE = "punch_manage"                # 打卡
ROUTE_UPLOAD_MANAGE = "upload_manage"              # 文件上传模块
ROUTE_VIDEO_MANAGE = "video_manage"                # 视频管理
ROUTE_MACHINE_LIST = "machine_list"                # 设备列表
ROUTE_ATTENDANCE_MANAGE = "attendance_manage"      # 考勤管理

# 销售角色权限
ROUTE_INQUIRY_MANAGE = "inquiry_manage"            # 询盘管理
ROUTE_ORDER_MANAGE = "order_manage"                # 订单管理
ROUTE_ORDER_STATUS_MANAGE = "order_status_manage"  # 订单状态
ROUTE_QUOTATION_MANAGE = "quotation_manage"        # 报价管理

# 管理员独有权限
ROUTE_EXPENSE_MANAGE = "expense_manage"            # 费用管理
ROUTE_LOG_MANAGE = "log_manage"                    # 日志管理
ROUTE_MACHINE_MANAGE = "machine_manage"            # 设备管理
ROUTE_USER_MANAGE = "user_manage"                  # 员工信息/管理
ROUTE_PERMISSION_MANAGE = "permission_manage"      # 权限管理（如果保留的话）
ROUTE_ORDER_RECORD_MANAGE = "order_record_manage"  # 订单记录管理

# 业务员权限
ROUTE_CUSTOMER_MANAGE = "customer_manage"           # 客户信息管理

# 博客管理（全体共有）
ROUTE_BLOG_MANAGE = "blog_manage"                   # 博客管理

# 货柜排布（全员共有：销售/跟单/业务员通用）
ROUTE_CONTAINER_LAYOUT_MANAGE = "container_layout_manage"  # 货柜排布

# 任务跟踪（全员共有）
ROUTE_TASK_TRACK_MANAGE = "task_track_manage"  # 任务跟踪

# 为了兼容性，添加旧的命名方式
ROUTE_DISPLAY_FILE = ROUTE_DISPLAY_FILE_MANAGE
ROUTE_PHOTO = ROUTE_PHOTO_MANAGE
ROUTE_PUNCH = ROUTE_PUNCH_MANAGE
ROUTE_UPLOAD = ROUTE_UPLOAD_MANAGE
ROUTE_VIDEO = ROUTE_VIDEO_MANAGE
ROUTE_INQUIRY = ROUTE_INQUIRY_MANAGE
ROUTE_ORDER = ROUTE_ORDER_MANAGE
ROUTE_ORDER_STATUS = ROUTE_ORDER_STATUS_MANAGE
ROUTE_EXPENSE = ROUTE_EXPENSE_MANAGE
ROUTE_LOG = ROUTE_LOG_MANAGE
ROUTE_MACHINE = ROUTE_MACHINE_MANAGE
ROUTE_USER = ROUTE_USER_MANAGE
ROUTE_PERMISSION = ROUTE_PERMISSION_MANAGE
ROUTE_ATTENDANCE = ROUTE_ATTENDANCE_MANAGE  # 考勤管理
ROUTE_QUOTATION = ROUTE_QUOTATION_MANAGE  # 报价管理

# 所有路由列表
ALL_ROUTES = [
    ROUTE_DISPLAY_FILE_MANAGE,
    ROUTE_PHOTO_MANAGE,
    ROUTE_PUNCH_MANAGE,
    ROUTE_UPLOAD_MANAGE,
    ROUTE_VIDEO_MANAGE,
    ROUTE_INQUIRY_MANAGE,
    ROUTE_ORDER_MANAGE,
    ROUTE_ORDER_STATUS_MANAGE,
    ROUTE_EXPENSE_MANAGE,
    ROUTE_LOG_MANAGE,
    ROUTE_MACHINE_MANAGE,
    ROUTE_MACHINE_LIST,
    ROUTE_USER_MANAGE,
    ROUTE_PERMISSION_MANAGE,
    ROUTE_ATTENDANCE_MANAGE,
    ROUTE_QUOTATION_MANAGE,
    ROUTE_ORDER_RECORD_MANAGE,
    ROUTE_CUSTOMER_MANAGE,
    ROUTE_BLOG_MANAGE,
    ROUTE_CONTAINER_LAYOUT_MANAGE,
    ROUTE_TASK_TRACK_MANAGE
]