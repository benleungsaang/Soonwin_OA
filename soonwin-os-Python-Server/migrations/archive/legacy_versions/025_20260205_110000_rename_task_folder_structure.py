"""rename task folder structure to use pure IDs

Revision ID: 025_20260205_110000
Revises: 024_20260204_100000_add_order_status_tables
Create Date: 2026-02-05 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import os
import shutil
from app.models.order_status import OrderStatus, OrderStatusLog, StatusTask
from app.models.order import Order
from extensions import db
import logging

# revision identifiers
revision = '025_20260205_110000_rename_task_folder_structure'
down_revision = '024_20260204_100000_add_order_status_tables'
branch_labels = None
depends_on = None

logger = logging.getLogger('alembic')

def upgrade():
    """迁移文件夹结构，从使用名称到仅使用ID"""
    # 这里我们不直接修改数据库结构，而是执行文件夹重命名操作
    print("开始迁移文件夹结构到纯ID路径...")
    
    # 从数据库获取所有相关的订单、状态日志和任务
    try:
        UPLOAD_FOLDER = 'assets/OrderStatus'
        
        # 查询所有状态任务
        tasks = db.session.query(StatusTask).all()
        
        for task in tasks:
            # 获取关联的订单状态日志
            status_log = db.session.query(OrderStatusLog).get(task.status_log_id)
            if not status_log:
                continue
                
            # 获取关联的订单状态和订单
            order_status = db.session.query(OrderStatus).get(status_log.order_status_id)
            if not order_status:
                continue
                
            order = db.session.query(Order).get(order_status.order_id)
            if not order:
                continue
                
            # 构建旧路径（使用名称）
            old_contract_no = order.contract_no.replace('/', '_').replace(chr(92), '_')
            old_status_log_folder = f"{status_log.id}_{status_log.status.replace('/', '_').replace(chr(92), '_')}"
            old_task_folder = f"{task.id}_{task.name.replace('/', '_').replace(chr(92), '_')}"
            
            old_upload_dir = os.path.join(UPLOAD_FOLDER, old_contract_no, old_status_log_folder, old_task_folder)
            
            # 构建新路径（仅使用ID）
            new_status_log_folder = str(status_log.id)
            new_task_folder = str(task.id)
            
            new_upload_dir = os.path.join(UPLOAD_FOLDER, old_contract_no, new_status_log_folder, new_task_folder)
            
            # 检查旧路径是否存在
            if os.path.exists(old_upload_dir):
                # 创建新路径的父目录
                os.makedirs(os.path.dirname(new_upload_dir), exist_ok=True)
                
                # 移动文件夹
                try:
                    shutil.move(old_upload_dir, new_upload_dir)
                    print(f"已迁移文件夹: {old_upload_dir} -> {new_upload_dir}")
                except Exception as e:
                    print(f"迁移文件夹失败 {old_upload_dir}: {str(e)}")
            else:
                # 检查新路径是否已存在（可能已经有按新结构存储的文件）
                if not os.path.exists(new_upload_dir):
                    # 创建新路径
                    os.makedirs(new_upload_dir, exist_ok=True)
                    print(f"创建新路径: {new_upload_dir}")
        
        # 同时处理状态日志级别的文件夹
        status_logs = db.session.query(OrderStatusLog).all()
        
        for status_log in status_logs:
            # 获取关联的订单状态和订单
            order_status = db.session.query(OrderStatus).get(status_log.order_status_id)
            if not order_status:
                continue
                
            order = db.session.query(Order).get(order_status.order_id)
            if not order:
                continue
                
            # 构建旧路径（使用名称）
            old_contract_no = order.contract_no.replace('/', '_').replace(chr(92), '_')
            old_status_log_folder = f"{status_log.id}_{status_log.status.replace('/', '_').replace(chr(92), '_')}"
            
            old_dir = os.path.join(UPLOAD_FOLDER, old_contract_no, old_status_log_folder)
            
            # 构建新路径（仅使用ID）
            new_status_log_folder = str(status_log.id)
            
            new_dir = os.path.join(UPLOAD_FOLDER, old_contract_no, new_status_log_folder)
            
            # 检查旧路径是否存在
            if os.path.exists(old_dir) and not os.path.exists(new_dir):
                # 如果旧路径存在但新路径不存在，尝试移动
                try:
                    # 检查新路径的父目录是否存在
                    parent_dir = os.path.dirname(new_dir)
                    os.makedirs(parent_dir, exist_ok=True)
                    
                    # 移动文件夹
                    shutil.move(old_dir, new_dir)
                    print(f"已迁移状态日志文件夹: {old_dir} -> {new_dir}")
                except Exception as e:
                    print(f"迁移状态日志文件夹失败 {old_dir}: {str(e)}")
        
        print("文件夹结构迁移完成")
    except Exception as e:
        print(f"迁移过程中出现错误: {str(e)}")
        raise e


def downgrade():
    """还原文件夹结构到使用名称"""
    print("开始还原文件夹结构...")
    
    # 这个操作理论上也可以被还原，但会更复杂
    # 由于名称可能会变化，我们无法准确知道原始名称
    # 所以通常不建议完全还原这个操作
    print("警告: 文件夹结构迁移不可完全逆向还原")
    pass
