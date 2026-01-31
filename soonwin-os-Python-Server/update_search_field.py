#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新现有订单的search_field字段
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.order import Order
from extensions import db

def update_all_orders_search_field():
    """更新所有订单的search_field字段"""
    app = create_app()
    
    with app.app_context():
        print("开始更新所有订单的search_field字段...")
        
        # 获取所有订单
        orders = Order.query.all()
        updated_count = 0
        
        for order in orders:
            # 生成新的搜索字段值
            order.search_field = order.generate_search_field()
            updated_count += 1
            
            # 每100个订单提交一次，避免内存问题
            if updated_count % 100 == 0:
                db.session.commit()
                print(f"已更新 {updated_count} 个订单的search_field字段")
        
        # 提交剩余的更改
        db.session.commit()
        
        print(f"完成！总共更新了 {updated_count} 个订单的search_field字段")

if __name__ == "__main__":
    update_all_orders_search_field()