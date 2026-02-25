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
    is_deleted = Column(Integer, default=0)  # 0=正常，1=已删除（逻辑删除）
    delete_time = Column(DateTime, nullable=True)  # 删除时间
    delete_operator = Column(String(100), nullable=True)  # 删除操作人

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
            'is_deleted': self.is_deleted,
            'delete_time': self.delete_time.isoformat() if self.delete_time else None,
            'delete_operator': self.delete_operator,
            'machine_info': self.machine.to_dict() if self.machine else None  # 包含机器信息
        }

    @staticmethod
    def get_paginated_photos(page=1, per_page=10, search='', machine_id=None, is_admin=False, uploader=None, is_deleted=0):
        """
        分页获取照片列表
        :param page: 页码
        :param per_page: 每页数量
        :param search: 搜索关键词
        :param machine_id: 机器ID
        :param is_admin: 是否为管理员
        :param uploader: 上传者
        :param is_deleted: 是否已删除（0=正常，1=已删除-回收站）
        :return: 分页对象
        """
        # 根据 is_deleted 参数决定查询正常照片还是已删除照片
        if is_deleted == 0:
            query = Photo.query.filter_by(is_deleted=0)  # 正常照片
        else:
            query = Photo.query.filter_by(is_deleted=1)  # 已删除照片（回收站）

        # 搜索功能
        if search:
            query = query.filter(Photo.search_field.like(f'%{search}%'))

        # 机器ID筛选
        if machine_id is not None:
            if machine_id == -1 or str(machine_id) == '-1':  # 特殊情况：型号不存在，返回空结果
                query = query.filter(Photo.id == -1)  # 不存在的ID，确保空结果
            elif machine_id != '' and str(machine_id) != '0' and str(machine_id) != '':  # 机器型号不为空
                query = query.filter(Photo.machine_id == machine_id)
            else:  # machine_id为空字符串或'0'，表示查找没有关联机器的项目
                query = query.filter((Photo.machine_id == 0) | (Photo.machine_id.is_(None)))

        # 按上传时间倒序排列
        if is_deleted == 1:
            # 已删除照片按删除时间倒序排列（如果有的话）或按上传时间
            query = query.order_by(Photo.delete_time.desc().nulls_last(), Photo.upload_time.desc())
        else:
            query = query.order_by(Photo.upload_time.desc())

        return query.paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_photo_by_id(photo_id, is_admin=False, uploader=None, check_deleted=False):
        """
        根据ID获取照片信息
        :param photo_id: 照片ID
        :param is_admin: 是否为管理员
        :param uploader: 上传者
        :param check_deleted: 是否检查已删除的照片
        :return: 照片对象或None
        """
        if check_deleted:
            query = Photo.query.filter_by(id=photo_id)  # 包括已删除的照片
        else:
            query = Photo.query.filter_by(id=photo_id, is_deleted=0)  # 只获取正常照片

        return query.first()