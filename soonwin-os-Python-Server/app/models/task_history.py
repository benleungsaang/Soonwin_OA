"""任务修改历史模型"""
from .. import db
from datetime import datetime


class TaskHistory(db.Model):
    """任务修改历史表（每次修改保存完整 JSON 快照）

    - snapshot_json 字段保存修改前的完整 task JSON 快照
    - 用于追踪任务的所有变更记录
    """
    __tablename__ = 'task_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    snapshot_json = db.Column(db.Text, nullable=False, default='')
    modified_by = db.Column(db.String(100), nullable=True, default='')
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self, include_snapshot=False):
        data = {
            'id': self.id,
            'task_id': self.task_id,
            'modified_by': self.modified_by or '',
            'modified_at': self.modified_at.strftime('%Y-%m-%d %H:%M:%S') if self.modified_at else None,
        }
        if include_snapshot:
            data['snapshot'] = self.snapshot_json
        return data