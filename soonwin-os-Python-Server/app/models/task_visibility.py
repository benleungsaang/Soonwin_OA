"""任务可见性模型"""
from .. import db
from datetime import datetime


class TaskVisibility(db.Model):
    """任务可见性配置表

    一条 Task 可以有多条 visibility 记录，表示谁可以看见。
    - visibility_type='role' 表示按角色可见，visibility_value 为角色名
    - visibility_type='employee' 表示按员工可见，visibility_value 为 emp_id

    若没有任何 visibility 记录，则只对创建人和管理员可见（默认策略）。
    """
    __tablename__ = 'task_visibility'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    visibility_type = db.Column(db.String(20), nullable=False)  # 'role' | 'employee'
    visibility_value = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'visibility_type': self.visibility_type,
            'visibility_value': self.visibility_value,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }