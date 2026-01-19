"""
获取管理员TOTP密钥的脚本
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'soonwin-os-Python-Server'))

# 现在可以导入模块
from soonwin_os_Python_Server.app import create_app
from soonwin_os_Python_Server.extensions import db
from soonwin_os_Python_Server.app.models.totp_user import TotpUser

def get_admin_secret():
    """获取管理员TOTP密钥"""
    app = create_app()

    with app.app_context():
        try:
            # 查找管理员TOTP用户
            totp_user = TotpUser.query.filter_by(emp_id='admin').first()
            
            if totp_user:
                print(f"员工ID: {totp_user.emp_id}")
                print(f"姓名: {totp_user.name}")
                print(f"TOTP密钥: {totp_user.totp_secret}")
                return totp_user.totp_secret
            else:
                print("未找到管理员用户")
                return None
        except Exception as e:
            print(f"获取管理员TOTP密钥失败: {str(e)}")
            return None

if __name__ == "__main__":
    secret = get_admin_secret()
    if secret:
        print(f"\n密钥已获取: {secret}")
    else:
        print("\n获取密钥失败")
