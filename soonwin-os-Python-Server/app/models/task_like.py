"""任务点赞模型"""
from .. import db
from datetime import datetime


class TaskLike(db.Model):
    """任务点赞表（复合主键：task_id + user_id）"""
    __tablename__ = 'task_like'

    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), primary_key=True, nullable=False)
    user_id = db.Column(db.String(100), primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('task_id', 'user_id', name='uq_task_user_like'),
    )