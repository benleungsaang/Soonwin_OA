from flask import Flask
from flask_cors import CORS
import config
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
            return send_file(file_path)
        else:
            abort(404)

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

        # 设置博客功能的处理队列
        from .routes.blog_routes import set_app_instance as set_blog_app_instance
        set_blog_app_instance(app)

    return app

# 暴露app实例（供flask命令识别）
# 注意：现在application需要指定端口，所以不再在这里创建
# application = create_app()

if __name__ == "__main__":
    application = create_app(5000)  # 默认端口5000，使用主数据库
    application.run(host="0.0.0.0", port=5000, debug=True)