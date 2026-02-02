from .. import db
from datetime import datetime
from sqlalchemy import and_

class Video(db.Model):
    """
    视频表模型
    """
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False, default='')  # 标题
    tags = db.Column(db.String(500), nullable=False, default='')  # 标签，多个标签用逗号分隔
    machine_id = db.Column(db.String(255), nullable=True, default='')  # 关联的机器型号
    remark = db.Column(db.Text, nullable=False, default='')  # 备注
    search_field = db.Column(db.Text, nullable=False, default='')  # 搜索字段（标题+标签+备注+机器型号等）
    uploader = db.Column(db.String(100), nullable=False)  # 上传者
    original_path = db.Column(db.String(500), nullable=True)  # 原始视频路径
    thumbnail_path = db.Column(db.String(500), nullable=True)  # 缩略图路径
    compressed_path = db.Column(db.String(500), nullable=True)  # 压缩后视频路径
    original_width = db.Column(db.Integer, nullable=True, default=0)  # 原始宽度
    original_height = db.Column(db.Integer, nullable=True, default=0)  # 原始高度
    duration = db.Column(db.Float, nullable=True, default=0.0)  # 视频时长（秒）
    file_size = db.Column(db.BigInteger, nullable=True, default=0)  # 文件大小（字节）
    compress_status = db.Column(db.String(50), nullable=False, default='pending')  # 压缩状态：pending, processing, success, failed
    upload_time = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 上传时间
    is_deleted = db.Column(db.Integer, nullable=False, default=0)  # 是否删除：0-正常，1-已删除
    delete_time = db.Column(db.DateTime, nullable=True)  # 删除时间
    delete_operator = db.Column(db.String(100), nullable=True)  # 删除操作人

    def to_dict(self, include_stats=False):
        """
        转换为字典格式
        :param include_stats: 是否包含统计信息
        """
        data = {
            'id': self.id,
            'title': self.title,
            'tags': self.tags,
            'machine_id': self.machine_id,
            'remark': self.remark,
            'uploader': self.uploader,
            'original_path': self.original_path,
            'thumbnail_path': self.thumbnail_path,
            'compressed_path': self.compressed_path,
            'original_width': self.original_width,
            'original_height': self.original_height,
            'duration': self.duration,
            'file_size': self.file_size,
            'compress_status': self.compress_status,
            'upload_time': self.upload_time.strftime('%Y-%m-%d %H:%M:%S') if self.upload_time else None,
            'is_deleted': self.is_deleted,
            'delete_time': self.delete_time.strftime('%Y-%m-%d %H:%M:%S') if self.delete_time else None,
            'delete_operator': self.delete_operator
        }
        
        if include_stats:
            # 可以添加更多统计信息
            pass
            
        return data

    @staticmethod
    def get_paginated_videos(page=1, per_page=10, search='', machine_id=None, is_admin=False, uploader=None):
        """
        分页获取视频列表
        :param page: 页码
        :param per_page: 每页数量
        :param search: 搜索关键词
        :param machine_id: 机器ID（现在可以是型号字符串或特殊值）
        :param is_admin: 是否为管理员
        :param uploader: 上传者
        :return: 分页对象
        """
        query = Video.query.filter_by(is_deleted=0)

        # 搜索功能
        if search:
            query = query.filter(Video.search_field.like(f'%{search}%'))
        
        # 机器ID筛选
        if machine_id is not None:
            if machine_id == -1 or str(machine_id) == '-1':  # 特殊情况：型号不存在，返回空结果
                query = query.filter(Video.id == -1)  # 不存在的ID，确保空结果
            elif machine_id != '' and str(machine_id) != '0' and str(machine_id) != '':  # 机器型号不为空
                # machine_id现在是机器型号字符串，直接匹配
                query = query.filter(Video.machine_id == str(machine_id))
            else:  # machine_id为空字符串或'0'，表示查找没有关联机器的项目
                query = query.filter((Video.machine_id == '') | (Video.machine_id.is_(None)))

        # 按上传时间倒序排列
        query = query.order_by(Video.upload_time.desc())

        return query.paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_video_by_id(video_id, is_admin=False, uploader=None):
        """
        根据ID获取视频信息
        :param video_id: 视频ID
        :param is_admin: 是否为管理员
        :param uploader: 上传者
        :return: 视频对象或None
        """
        query = Video.query.filter_by(id=video_id, is_deleted=0)

        return query.first()

    @staticmethod
    def get_deleted_videos_paginated(page=1, per_page=10, search='', is_admin=False, uploader=None):
        """
        分页获取已删除的视频列表
        :param page: 页码
        :param per_page: 每页数量
        :param search: 搜索关键词
        :param is_admin: 是否为管理员
        :param uploader: 上传者
        :return: 分页对象
        """
        query = Video.query.filter_by(is_deleted=1)  # 只获取已删除的视频

        # 搜索功能
        if search:
            query = query.filter(Video.search_field.like(f'%{search}%'))
        
        # 按删除时间倒序排列（如果有的话）或按上传时间
        query = query.order_by(Video.delete_time.desc().nulls_last(), Video.upload_time.desc())

        return query.paginate(
            page=page, per_page=per_page, error_out=False
        )