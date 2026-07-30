"""待办事项（Todo）模块数据模型

设计要点：
1. 数据隔离：用户只能看到 author_id == 自己 emp_id 的 todo；管理员（user_role='admin'）可见全部
2. 留言权限：仅管理员可调用 add_message 接口创建留言
3. 红点未读：todo_message_read 表记录每个用户对每个 todo 的最后已读时间，
   未读数 = last_read_at 之后产生的未删除留言数
4. emoji 支持：SQLite 默认 UTF-8 + Python 3.12 str 原生支持 4 字节 emoji，无需特殊处理
"""
from .. import db
from datetime import datetime


class Todo(db.Model):
    """待办事项主表"""
    __tablename__ = 'todo'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.String(20), nullable=False, index=True, comment="创建人 emp_id（用于用户隔离）")
    author_name = db.Column(db.String(50), nullable=False, default='', comment="创建人姓名（冗余存储便于前端展示）")
    content = db.Column(db.Text, nullable=False, default='', comment="任务正文（支持 emoji）")
    date = db.Column(db.String(10), nullable=False, default='', comment="所属日期 YYYY-MM-DD（前端按它分组）")
    color = db.Column(db.String(20), nullable=False, default='white', comment="卡片底色：white/red/yellow/green/blue/purple")
    note = db.Column(db.Text, nullable=False, default='', comment="用户备注（修改内容弹窗可改）")
    image_url = db.Column(db.String(500), nullable=True, comment="任务附图（点击放大显示）")
    status = db.Column(db.String(20), nullable=False, default='pending', comment="pending / completed")
    completion_note = db.Column(db.Text, nullable=True, comment="完成时填的内容（与 completion_image_url 二选一必填）")
    completion_image_url = db.Column(db.String(500), nullable=True, comment="完成时填的图片")
    completed_at = db.Column(db.DateTime, nullable=True, comment="完成时间")
    is_deleted = db.Column(db.Integer, nullable=False, default=0, index=True, comment="0=正常 1=软删")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    messages = db.relationship(
        'TodoMessage', backref='todo', lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='TodoMessage.created_at.asc()'
    )
    visibilities = db.relationship(
        'TodoVisibility', backref='todo', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self, include_unread_count: int = 0, include_visibilities: bool = False):
        data = {
            'id': self.id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'content': self.content,
            'date': self.date,
            'color': self.color,
            'note': self.note or '',
            'image_url': self.image_url or '',
            'status': self.status,
            'completion_note': self.completion_note or '',
            'completion_image_url': self.completion_image_url or '',
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'is_deleted': bool(self.is_deleted),
            'unread_count': include_unread_count,
            'shared_count': self.visibilities.count(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }
        if include_visibilities:
            data['visible_to'] = [v.user_id for v in self.visibilities]
        return data


class TodoMessage(db.Model):
    """待办留言表（仅管理员可创建）"""
    __tablename__ = 'todo_message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False, index=True)
    author_id = db.Column(db.String(20), nullable=False, default='', comment="留言人 emp_id（通常为管理员）")
    author_name = db.Column(db.String(50), nullable=False, default='管理员', comment="留言人姓名")
    content = db.Column(db.Text, nullable=False, default='', comment="留言内容（支持 emoji）")
    image_url = db.Column(db.String(500), nullable=True, comment="留言附图")
    is_deleted = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'todo_id': self.todo_id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'content': self.content,
            'image_url': self.image_url or '',
            'is_deleted': bool(self.is_deleted),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class TodoMessageRead(db.Model):
    """待办留言已读表（红点未读机制）

    每用户对每个 todo 维护一条已读记录，未读数 =
    last_read_at 之后产生的、未被软删的留言数量。
    """
    __tablename__ = 'todo_message_read'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False, index=True)
    user_id = db.Column(db.String(20), nullable=False, index=True, comment="已读用户 emp_id")
    last_read_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('todo_id', 'user_id', name='uq_todo_message_read_user_todo'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'todo_id': self.todo_id,
            'user_id': self.user_id,
            'last_read_at': self.last_read_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_read_at else None,
        }
