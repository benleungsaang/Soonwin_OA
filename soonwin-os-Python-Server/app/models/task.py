"""任务跟踪功能数据模型"""
from .. import db
from datetime import datetime


class Task(db.Model):
    """任务主表"""
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.String(100), nullable=False, default='')
    author_name = db.Column(db.String(100), nullable=False, default='')
    content = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending' | 'completed'
    completion_note = db.Column(db.Text, nullable=True)
    completion_image_url = db.Column(db.String(500), nullable=True)
    todo_image_url = db.Column(db.String(500), nullable=True)
    expected_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD
    background_color = db.Column(db.String(20), nullable=True)  # hex 颜色
    like_count = db.Column(db.Integer, nullable=False, default=0)
    is_deleted = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    completed_at = db.Column(db.DateTime, nullable=True)

    # 关系
    comments = db.relationship('TaskComment', backref='task', lazy='dynamic',
                                cascade='all, delete-orphan')
    visibilities = db.relationship('TaskVisibility', backref='task', lazy='dynamic',
                                    cascade='all, delete-orphan')
    likes = db.relationship('TaskLike', backref='task', lazy='dynamic',
                             cascade='all, delete-orphan')
    histories = db.relationship('TaskHistory', backref='task', lazy='dynamic',
                                 cascade='all, delete-orphan',
                                 order_by='TaskHistory.modified_at.desc()')

    def to_dict(self, include_relations=True):
        data = {
            'id': self.id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'content': self.content,
            'status': self.status,
            'completion_note': self.completion_note or '',
            'completion_image_url': self.completion_image_url or '',
            'todo_image_url': self.todo_image_url or '',
            'expected_date': self.expected_date or '',
            'background_color': self.background_color or '',
            'like_count': self.like_count or 0,
            'is_deleted': bool(self.is_deleted),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'comment_count': self.comments.filter_by(is_deleted=0).count() if include_relations else 0,
            'history_count': self.histories.count() if include_relations else 0,
        }
        if include_relations:
            data['visibilities'] = [v.to_dict() for v in self.visibilities.all()]
        return data