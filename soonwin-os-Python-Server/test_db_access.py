import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from app.models.permission import RolePermission

def test_db_access():
    app = create_app(5001)
    with app.app_context():
        try:
            # 测试查询权限列表
            permissions = RolePermission.query.all()
            print(f"成功获取 {len(permissions)} 条权限记录")
            
            # 显示前几条记录的结构
            for i, perm in enumerate(permissions[:3]):
                print(f"记录 {i+1}: role_name={perm.role_name}, role_description={perm.role_description}, module_name={perm.module_name}")
            
            print("数据库访问正常")
        except Exception as e:
            print(f"数据库访问错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_db_access()