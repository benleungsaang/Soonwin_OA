import os

# 数据库配置（SQLite3，文件路径为backend/soonwin_oa.db）
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'soonwin_oa.db')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭不必要的修改跟踪，提升性能

# JWT配置（密钥需自定义，建议使用随机字符串）
JWT_SECRET_KEY = "OA_System_JWT_Secret_Key_2024"  # 生产环境需更换为更复杂密钥
JWT_ACCESS_TOKEN_EXPIRES = 7200  # JWT有效期（2小时，单位：秒）

# TOTP配置
TOTP_INTERVAL = 30  # 动态码有效期（30秒）
TOTP_DIGITS = 6     # 动态码位数（6位）

# Flask调试模式（开发环境开启，生产环境关闭）
DEBUG = True