from flask import Flask, request
from flask_cors import CORS
import config
import sys
import os
# 从 extensions.py 导入扩展（而非本地初始化）
from extensions import db, migrate

def create_app(port=5000):
    app = Flask(__name__, static_folder='../assets', static_url_path='/assets')

    # 根据端口动态设置数据库URI
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get_database_uri(port)
    app.config.from_object(config.Config)

    # 绑定扩展与app（核心：延迟绑定，避免循环）
    db.init_app(app)
    migrate.init_app(app, db)

    # 解决跨域
    CORS(app, resources=r"/*")

    # 添加静态文件服务路由，用于提供媒体文件服务
    @app.route('/assets/Media/<path:filepath>')
    def serve_media_file(filepath):
        """提供媒体文件服务"""
        import os
        from flask import send_file, abort
        # 构建完整的文件路径 - 相对于app目录，assets在同级的父目录中
        file_path = os.path.join(app.root_path, '..', 'assets', 'Media', filepath)

        # 防止路径遍历攻击，确保路径在指定目录内
        file_path = os.path.abspath(file_path)
        assets_media_path = os.path.abspath(os.path.join(app.root_path, '..', 'assets', 'Media'))

        if not file_path.startswith(assets_media_path):
            abort(404)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            resp = send_file(file_path, conditional=True)
            resp.headers['Accept-Ranges'] = 'bytes'
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
        else:
            abort(404)


    # 博客媒体由 Flask 内置静态文件服务提供（static_folder='../assets', url_prefix='/assets'）
    # 访问路径 /assets/PostsMedia/... → 实际路径 assets/PostsMedia/...
    # 生产环境由 nginx 直接发送（sendfile），与视频管理 /assets/Media/Videos/ 一致

    # 关键：在 create_app 内部导入模型（延迟导入，打破循环）
    with app.app_context():
        from .models.employee import Employee
        from .models.employee_device import EmployeeDevice
        from .models.punch_record import PunchRecord
        from .models.order import Order
        from .models.cost_allocation import CostAllocation
        from .models.totp_user import TotpUser
        from .models.expense import Expense, ExpenseAllocation, ExpenseCalculationRecord, AnnualTarget, IndividualExpense
        from .models.display_file import DisplayFile
        from .models.inquiry import Inquiry, InquiryCommunication
        from .models.inquiry_communication_media import InquiryCommunicationMedia
        from .models.machine_new import MachineNew
        from .models.photo import Photo
        from .models.video import Video
        from .models.business_operation_log import BusinessOperationLog
        from .models.data_change_stats import DataChangeStats
        from .models.order_status import OrderStatus, OrderStatusLog, StatusTask, TaskMediaFile
        from .models.attendance_operation import AttendanceOperation
        from .models.quotation_temp import QuotationTemp
        from .models.order_record import OrderRecord, OrderRecordIncome, OrderRecordExpense
        from .models.customer import Customer
        from .models.blog import BlogPost, BlogMedia, BlogEditHistory, BlogComment, BlogLike
        # 任务跟踪模块
        from .models.task import Task
        from .models.task_comment import TaskComment
        from .models.task_visibility import TaskVisibility
        from .models.task_like import TaskLike
        from .models.task_history import TaskHistory
        # 待办事项模块（todo）
        from .models.todo import Todo, TodoMessage, TodoMessageRead
        from .models.todo_visibility import TodoVisibility
        # 模块可见性配置（管理员可在主页隐藏某些模块菜单项）
        from .models.module_visibility import ModuleVisibility
        # from .models.permission import RolePermission, init_default_permissions  # 已删除，使用简化版权限模型
        # 导入简化权限模型
        from .models.simple_permission import SimpleRole as Role, SimpleRolePermission as SimpleRolePermission

        # 初始化数据库表（如果不存在）
        db.create_all()
        # 注册路由蓝图
        from .routes.punch_routes import punch_bp
        app.register_blueprint(punch_bp)

        # 注册用户管理路由蓝图
        from .routes.user_routes import user_bp
        app.register_blueprint(user_bp, url_prefix='/api')  # 恢复url_prefix

        # 注册订单管理路由蓝图
        from .routes.order_routes import order_bp
        app.register_blueprint(order_bp, url_prefix='/api')

        # 注册费用管理路由蓝图
        from .routes.expense_routes import expense_bp
        app.register_blueprint(expense_bp, url_prefix='/api')

        # 注册认证相关路由蓝图
        from .routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')

        # 注册上传相关路由蓝图
        from .routes.upload_routes import upload_bp
        app.register_blueprint(upload_bp, url_prefix='/api')

        # 注册展示文件相关路由蓝图
        from .routes.display_file_routes import display_file_bp
        app.register_blueprint(display_file_bp, url_prefix='/api')

        # 注册询盘管理相关路由蓝图
        from .routes.inquiry_routes import inquiry_bp
        app.register_blueprint(inquiry_bp, url_prefix='/api')

        # 注册机器管理相关路由蓝图
        from .routes.machine_routes import machine_bp
        from .routes.quotation_routes import quotation_bp
        from .routes.quotation_temp_routes import quotation_temp_bp
        app.register_blueprint(machine_bp, url_prefix='/api')
        app.register_blueprint(quotation_bp, url_prefix='/api')
        app.register_blueprint(quotation_temp_bp, url_prefix='/api')
        # 注册照片管理相关路由蓝图
        from .routes.photo_routes import photo_bp
        app.register_blueprint(photo_bp, url_prefix='/api')

        # 注册视频管理相关路由蓝图
        from .routes.video_routes import video_bp
        app.register_blueprint(video_bp, url_prefix='/api')

        # 注册通用日志管理相关路由蓝图
        from .routes.log_routes import log_bp
        app.register_blueprint(log_bp, url_prefix='/api')

        # 注册订单状态管理相关路由蓝图
        from .routes.order_status_routes import order_status_bp
        app.register_blueprint(order_status_bp, url_prefix='/api')

        # 注册订单记录管理相关路由蓝图
        from .routes.order_record_routes import order_record_bp
        app.register_blueprint(order_record_bp, url_prefix='/api')

        # 注册客户信息管理相关路由蓝图
        from .routes.customer_routes import customer_bp
        app.register_blueprint(customer_bp, url_prefix='/api')

        # 注册权限管理相关路由蓝图
        from .routes.permission_routes import permission_bp
        app.register_blueprint(permission_bp)

        # 注册考勤管理相关路由蓝图
        from .routes.attendance_routes import attendance_bp
        app.register_blueprint(attendance_bp, url_prefix='/api')

        # 注册系统配置相关路由蓝图
        from .routes.config_routes import config_bp
        app.register_blueprint(config_bp, url_prefix='/api')

        # 注册货柜排布相关路由蓝图
        from .routes.container_layout_routes import container_layout_bp
        app.register_blueprint(container_layout_bp, url_prefix='/api')

        # 设置照片压缩功能的应用实例
        from .routes.photo_routes import set_app_instance
        set_app_instance(app)

        # 设置视频处理功能的应用实例
        from .routes.video_routes import set_app_instance as set_video_app_instance
        set_video_app_instance(app)

        # 设置通用上传队列的应用实例
        from .routes.upload_routes import set_app_instance as set_upload_app_instance
        set_upload_app_instance(app)

        # 注册博客管理相关路由蓝图
        from .routes.blog_routes import blog_bp
        app.register_blueprint(blog_bp, url_prefix='/api')

        # 注册任务跟踪相关路由蓝图
        from .routes.task_routes import task_bp
        app.register_blueprint(task_bp, url_prefix='/api')

        # 注册待办事项相关路由蓝图
        from .routes.todo_routes import todo_bp
        app.register_blueprint(todo_bp, url_prefix='/api')

        # 注册管理员模块可见性路由蓝图（主页模块隐藏/显示开关）
        from .routes.admin_module_routes import admin_module_bp
        app.register_blueprint(admin_module_bp)

        # 设置博客功能的处理队列
        from .routes.blog_routes import set_app_instance as set_blog_app_instance
        set_blog_app_instance(app)

    # ========== 版本号接口 ==========
    # 开发/生产环境均返回，前端用于确认当前版本与开发端是否一致
    @app.route('/api/version', methods=['GET'])
    def app_version():
        """返回后端服务版本号（日期+当日序号，如 2026.08.03-1）"""
        from app.constants.app_version import APP_VERSION
        return {"version": APP_VERSION}

    # ========== 管理端点：远程重启服务 ==========
    # 仅在非开发端口启用（5001 留给本地调试用，不需要重启能力）
    if port != 5001:
        @app.route('/api/admin/restart', methods=['POST'])
        def admin_restart():
            """远程重启服务：调用独立脚本处理备份/同步/启停全流程"""
            import subprocess
            from datetime import datetime

            data = request.get_json() or {}
            if data.get('key') != 'SoonwinOA_Restart_Key_2026':
                return {"success": False, "msg": "密钥错误"}, 403

            # restart_services.py 在 app/ 的上级目录（项目根目录）
            script = os.path.abspath(os.path.join(
                os.path.dirname(__file__), '..', 'restart_services.py'))
            script_dir = os.path.dirname(script)

            log_path = os.path.join(script_dir, 'restart_output.log')
            try:
                # 父进程仅留一个快速标记（子进程启动后自己写详细日志）
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 远程重启触发\n")
                    f.write(f"{'='*60}\n\n")

                # 完全脱离父进程启动子进程（restart_services.py 自己管理日志文件）
                # DETACHED_PROCESS = 不继承控制台，不受父进程作业对象影响
                # CREATE_NEW_PROCESS_GROUP = 新进程组，防止被 Ctrl+C/服务关闭波及
                flags = 0
                if sys.platform == 'win32':
                    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                proc = subprocess.Popen(
                    [sys.executable, '-u', script],  # -u 无缓冲，即时刷入日志
                    cwd=script_dir,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=flags,
                    close_fds=True,
                )

                # 父进程在日志追加 PID 标记（子进程启动后会接力写日志）
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"[Parent] 子进程 PID: {proc.pid} 已投递\n")

                print(f"[Restart] 重启脚本已启动, PID={proc.pid}, 日志: {log_path}")
                return {"success": True, "msg": "重启命令已提交，约15秒后完成",
                        "pid": proc.pid, "log": "restart_output.log"}
            except Exception as e:
                print(f"[Restart] 启动重启脚本失败: {e}")
                return {"success": False, "msg": f"启动重启脚本失败: {e}"}, 500

    return app

# 暴露app实例（供flask命令识别）
# 注意：现在application需要指定端口，所以不再在这里创建
# application = create_app()

if __name__ == "__main__":
    application = create_app(5000)  # 默认端口5000，使用主数据库
    application.run(host="0.0.0.0", port=5000, debug=True)