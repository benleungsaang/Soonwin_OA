import json
from typing import Dict, Any
from datetime import datetime
from .. import db
from sqlalchemy import Column, Integer, String, TEXT, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class Photo(db.Model):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(TEXT, nullable=False)  # 照片标题
    tags = Column(TEXT)  # 逗号分隔的标签字符串（如"故障,检修,2024"）
    machine_id = Column(Integer, ForeignKey('machines.model', ondelete='SET NULL'))  # 关联机器表，机器删除时置空
    remark = Column(TEXT)  # 备注
    search_field = Column(TEXT)  # 冗余搜索字段：标题+标签+机器型号+备注
    uploader = Column(TEXT, nullable=False)  # 上传者
    upload_time = Column(DateTime, default=datetime.utcnow)  # 上传时间
    original_path = Column(TEXT)  # 原图路径（可为空）
    thumbnail_path = Column(TEXT, nullable=False)  # 缩略图路径（必选）
    normal_path = Column(TEXT, nullable=False)  # 普通观看图路径（必选，先存原图路径）
    original_width = Column(Integer)  # 原图宽度
    original_height = Column(Integer)  # 原图高度
    file_size = Column(Integer)  # 原图文件大小（字节）
    compress_status = Column(String(20), default='pending')  # 压缩状态：pending/processing/success/failed

    # 建立与Machine表的关联关系
    machine = relationship('Machine', backref='photos', foreign_keys=[machine_id])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，输出全部字段"""
        return {
            'id': self.id,
            'title': self.title,
            'tags': self.tags,
            'machine_id': self.machine_id,
            'remark': self.remark,
            'search_field': self.search_field,
            'uploader': self.uploader,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'original_path': self.original_path,
            'thumbnail_path': self.thumbnail_path,
            'normal_path': self.normal_path,
            'original_width': self.original_width,
            'original_height': self.original_height,
            'file_size': self.file_size,
            'compress_status': self.compress_status,
            'machine_info': self.machine.to_dict() if self.machine else None  # 包含机器信息
        }