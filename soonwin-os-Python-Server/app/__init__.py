from flask import Flask
from flask_cors import CORS
import config
# 从 extensions.py 导入扩展（而非本地初始化）
from extensions import db, migrate

def create_app():
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config)

    # 绑定扩展与app（核心：延迟绑定，避免循环）
    db.init_app(app)
    migrate.init_app(app, db)

    # 解决跨域
    CORS(app, resources=r"/*")

    # 关键：在 create_app 内部导入模型（延迟导入，打破循环）
    with app.app_context():
        from .models.employee import Employee
        from .models.punch_record import PunchRecord
        from .models.order_list import OrderList
        from .models.cost_allocation import CostAllocation
        from .models.totp_user import TotpUser
        # 注册路由蓝图
        from .routes.punch_routes import punch_bp
        app.register_blueprint(punch_bp)

    return app

# 暴露app实例（供flask命令识别）
application = create_app()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)