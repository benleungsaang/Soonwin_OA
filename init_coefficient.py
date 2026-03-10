from decimal import Decimal
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'soonwin-os-Python-Server'))

from app.models.system_config import SystemConfig
from app import db

def init_price_coefficient():
    """初始化价格系数配置"""
    try:
        # 设置初始系数1.05
        success = SystemConfig.set_config(
            config_key="show_price_coefficient",
            value="1.05",
            description="设备展示价格系数（展示价格=原始价格×系数）"
        )
        
        if success:
            print("价格系数配置初始化成功！")
            print("系数键名: show_price_coefficient")
            print("默认值: 1.05")
            print("说明: 展示价格 = 原始价格 × 系数")
        else:
            print("价格系数配置初始化失败！")
    except Exception as e:
        print(f"初始化过程中出现错误: {e}")

if __name__ == "__main__":
    # 需要先创建应用上下文
    from app import create_app
    app = create_app(5000)  # 使用默认端口
    
    with app.app_context():
        init_price_coefficient()