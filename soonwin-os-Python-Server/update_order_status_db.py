from app import create_app
from app.models.order_inspection import OrderInspection
from extensions import db
from datetime import datetime

def update_existing_records():
    """
    更新现有记录的默认状态值
    """
    app = create_app()
    
    with app.app_context():
        # 为所有现有记录设置默认状态
        inspections = OrderInspection.query.all()
        
        for inspection in inspections:
            if inspection.current_status is None:
                inspection.current_status = 1  # 设置为"下单"状态
            if inspection.current_status_time is None:
                inspection.current_status_time = datetime.now()  # 设置为当前时间
        
        db.session.commit()
        print(f"已更新 {len(inspections)} 条验收记录的状态字段")

if __name__ == "__main__":
    update_existing_records()