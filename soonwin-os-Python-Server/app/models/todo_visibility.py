"""待办事项可见性模型

记录管理员将某条 Todo 共享给哪些员工。
- 若某 todo 没有对应的 TodoVisibility 记录，则仅创建人 + 管理员可见（默认策略）
- 若有一条或多条记录，则这些员工 + 创建人 + 管理员可见
"""
from .. import db
from datetime import datetime


class TodoVisibility(db.Model):
    """待办事项可见性配置表"""
    __tablename__ = 'todo_visibility'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    todo_id = db.Column(
        db.Integer,
        db.ForeignKey('todo.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="关联 todo id"
    )
    user_id = db.Column(
        db.String(20),
        nullable=False,
        index=True,
        comment="可见员工 emp_id"
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('todo_id', 'user_id', name='uq_todo_visibility'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'todo_id': self.todo_id,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
