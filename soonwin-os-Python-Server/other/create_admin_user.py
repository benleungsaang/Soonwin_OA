"""
管理员账号初始化脚本
使用方法: python create_admin_user.py
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from extensions import db
from app.models.employee import Employee, UserStatus
from app.models.totp_user import TotpUser
from datetime import datetime
import pyotp
import uuid

def init_admin():
    """初始化管理员账号"""
    app = create_app()

    with app.app_context():
        try:
            # 检查是否已存在管理员账号
            existing_admin = Employee.query.filter_by(emp_id='admin').first()
            if existing_admin:
                print("管理员账号已存在")
                print(f"员工ID: {existing_admin.emp_id}")
                print(f"姓名: {existing_admin.name}")
                print(f"角色: {existing_admin.user_role}")
                print(f"状态: {existing_admin.status}")
                return False

            # 生成唯一的phone_mac值，避免唯一性约束冲突
            # 生成基于管理员ID和随机数的唯一MAC地址
            unique_mac = f"FF:{str(uuid.uuid4()).split('-')[0][:2]}:{str(uuid.uuid4()).split('-')[1][:2]}:{str(uuid.uuid4()).split('-')[2][:2]}:{str(uuid.uuid4()).split('-')[3][:2]}:FE".upper()

            # 创建TOTP密钥
            totp_secret = pyotp.random_base32()

            # 创建管理员员工记录
            admin_employee = Employee(
                name="管理员",
                emp_id="admin",
                dept="系统管理",
                phone_mac=unique_mac,  # 使用生成的唯一MAC地址
                inner_ip="127.0.0.1",  # 管理员默认值
                user_role="admin",
                status=UserStatus.PENDING_BINDING  # 设置为待绑定状态
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
            print(f"状态: {admin_employee.status}")
            print(f"手机MAC地址: {admin_employee.phone_mac}")
            print(f"TOTP密钥: {totp_secret}")
            print("\n请使用此TOTP密钥在您的TOTP应用（如Google Authenticator）中添加账户")
            print("注意: 管理员账户初始状态为'待绑定'，需要通过TOTP验证后才能激活")

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