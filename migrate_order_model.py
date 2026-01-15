"""
数据库模型迁移脚本
用于更新订单模型，添加年度目标和个别费用相关表
"""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from extensions import db

def migrate():
    """
    执行数据库迁移
    1. 创建AnnualTarget表
    2. 创建IndividualExpense表
    3. 修改Order表结构
    """
    print("开始执行数据库迁移...")
    
    # 创建AnnualTarget表
    print("创建AnnualTarget表...")
    try:
        # 检查AnnualTarget表是否存在
        from app.models.expense import AnnualTarget
        AnnualTarget.__table__.create(db.engine, checkfirst=True)
        print("AnnualTarget表创建成功")
    except Exception as e:
        print(f"创建AnnualTarget表失败: {e}")
    
    # 创建IndividualExpense表
    print("创建IndividualExpense表...")
    try:
        # 检查IndividualExpense表是否存在
        from app.models.expense import IndividualExpense
        IndividualExpense.__table__.create(db.engine, checkfirst=True)
        print("IndividualExpense表创建成功")
    except Exception as e:
        print(f"创建IndividualExpense表失败: {e}")
    
    # 修改Order表结构
    print("修改Order表结构...")
    try:
        # 添加proportionate_cost和individual_cost字段，删除operational_cost字段
        with db.engine.connect() as conn:
            # 检查字段是否存在，如果不存在则添加
            # 首先添加新字段
            try:
                conn.execute(db.text("ALTER TABLE `Order` ADD COLUMN proportionate_cost DECIMAL(12, 2) DEFAULT 0 COMMENT '摊分费用'"))
                print("proportionate_cost字段添加成功")
            except Exception as e:
                print(f"proportionate_cost字段已存在或添加失败: {e}")
            
            try:
                conn.execute(db.text("ALTER TABLE `Order` ADD COLUMN individual_cost DECIMAL(12, 2) DEFAULT 0 COMMENT '个别费用之和'"))
                print("individual_cost字段添加成功")
            except Exception as e:
                print(f"individual_cost字段已存在或添加失败: {e}")
            
            # 删除旧字段
            try:
                conn.execute(db.text("ALTER TABLE `Order` DROP COLUMN operational_cost"))
                print("operational_cost字段删除成功")
            except Exception as e:
                print(f"operational_cost字段删除失败或不存在: {e}")
            
            conn.commit()
    except Exception as e:
        print(f"修改Order表结构失败: {e}")
    
    print("数据库迁移完成！")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        migrate()