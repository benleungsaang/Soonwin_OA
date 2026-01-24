import os

# 数据库配置 - 使用函数动态设置，将在create_app中确定
def get_database_uri(port=5000):
    """根据端口返回对应的数据库URI"""
    if port == 5001:
        db_name = 'soonwin_oa_dev.db'
    else:
        db_name = 'soonwin_oa.db'
    return f"sqlite:///{os.path.join(os.path.dirname(__file__), db_name)}"

# Flask配置类
class Config:
    # 数据库URI将在create_app函数中动态设置
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭不必要的修改跟踪，提升性能

    # JWT配置（密钥需自定义，建议使用随机字符串）
    JWT_SECRET_KEY = "OA_System_JWT_Secret_Key_2024"  # 生产环境需更换为更复杂密钥
    JWT_ACCESS_TOKEN_EXPIRES = 7200  # JWT有效期（2小时，单位：秒）

    # TOTP配置
    TOTP_INTERVAL = 30  # 动态码有效期（30秒）
    TOTP_DIGITS = 6     # 动态码位数（6位）

    # Flask调试模式（开发环境开启，生产环境关闭）
    DEBUG = False