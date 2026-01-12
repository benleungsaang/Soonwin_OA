import os
import sys
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from app.models.employee import Employee
from app.models.punch_record import PunchRecord

def init_db():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        print("数据库表创建成功！")
        
        # 可以添加初始数据
        # 检查是否已存在测试员工
        test_emp = Employee.query.filter_by(emp_id="TEST001").first()
        if not test_emp:
            test_employee = Employee(
                name="测试员工",
                emp_id="TEST001",
                dept="测试部门",
                phone_mac="aa:bb:cc:dd:ee:ff",
                inner_ip="192.168.31.100"
            )
            db.session.add(test_employee)
            db.session.commit()
            print("已添加测试员工数据")

if __name__ == "__main__":
    init_db()