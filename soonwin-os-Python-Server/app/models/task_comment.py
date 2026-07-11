"""任务留言模型"""
from .. import db
from datetime import datetime


class TaskComment(db.Model):
    """任务留言表"""
    __tablename__ = 'task_comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    author_id = db.Column(db.String(100), nullable=True, default='')
    author_name = db.Column(db.String(100), nullable=False, default='匿名')
    content = db.Column(db.Text, nullable=False, default='')
    is_deleted = db.Column(db.Integer, nullable=False, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'author_id': self.author_id or '',
            'author_name': self.author_name,
            'content': self.content,
            'is_deleted': bool(self.is_deleted),
            'deleted_at': self.deleted_at.strftime('%Y-%m-%d %H:%M:%S') if self.deleted_at else None,
            'deleted_by': self.deleted_by or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }