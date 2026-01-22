from extensions import db
from datetime import datetime
import uuid


class DisplayFile(db.Model):
    __tablename__ = "DisplayFile"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), comment="文件唯一标识")
    title = db.Column(db.String(200), nullable=False, comment="文件标题")
    file_type = db.Column(db.String(10), nullable=False, comment="文件类型（image_group/pdf）")
    file_path = db.Column(db.Text, nullable=False, comment="文件存储路径")
    original_filename = db.Column(db.String(200), nullable=False, comment="原始文件名")
    page_count = db.Column(db.Integer, nullable=True, comment="页数")  # 新增页数字段，允许为空
    created_by = db.Column(db.String(50), nullable=False, comment="上传者")
    created_at = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def to_dict(self):
        return {
            "id": self.id,
            "uuid": self.uuid,
            "title": self.title,
            "file_type": self.file_type,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "page_count": self.page_count,  # 返回页数字段
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }