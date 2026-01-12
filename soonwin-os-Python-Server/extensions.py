# extensions.py（项目根目录，与 app 目录同级）
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 初始化扩展，不绑定app（延迟绑定）
db = SQLAlchemy()
migrate = Migrate()