"""
管理员账号初始化脚本
使用方法: python init_admin_script.py
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from app.models.employee import Employee
from app.models.totp_user import TotpUser
from datetime import datetime
import pyotp

def init_admin():
    """初始化管理员账号"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查是否已存在管理员账号
            existing_admin = Employee.query.filter_by(emp_id='admin').first()
            if existing_admin:
                print("管理员账号已存在")
                return False

            # 创建TOTP密钥
            totp_secret = pyotp.random_base32()

            # 创建管理员员工记录
            admin_employee = Employee(
                name="管理员",
                emp_id="admin",
                dept="系统管理",
                phone_mac="00-00-00-00-00-00",  # 管理员默认值
                inner_ip="127.0.0.1",  # 管理员默认值
                user_role="admin",
                status="active"
            )
            db.session.add(admin_employee)

            # 创建TOTP用户记录
            totp_user = TotpUser(
                emp_id="admin",
                name="管理员",
                totp_secret=totp_secret,
                create_time=datetime.now()
            )
            db.session.add(totp_user)
            db.session.commit()

            print("管理员账户初始化成功")
            print(f"员工ID: {admin_employee.emp_id}")
            print(f"姓名: {admin_employee.name}")
            print(f"部门: {admin_employee.dept}")
            print(f"角色: {admin_employee.user_role}")
            print(f"TOTP密钥: {totp_secret}")
            print("\n请使用此TOTP密钥在您的TOTP应用（如Google Authenticator）中添加账户")
            
            return True
        except Exception as e:
            db.session.rollback()
            print(f"初始化管理员账户失败: {str(e)}")
            return False

if __name__ == "__main__":
    success = init_admin()
    if success:
        print("\n管理员账号初始化完成！")
    else:
        print("\n管理员账号初始化失败或已存在。")