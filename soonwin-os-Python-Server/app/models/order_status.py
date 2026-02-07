from extensions import db
from datetime import datetime
from .order import Order
import uuid


class OrderStatus(db.Model):
    """
    订单进度主表（原OrderInspection/OrderCheck）
    """
    __tablename__ = "order_status"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_id = db.Column(db.Integer, db.ForeignKey('Order.id'), nullable=False, comment="关联订单ID")
    remarks = db.Column(db.Text, comment="备注信息")

    # 当前状态：与order_status_log的status字段映射（1-下单, 2-排产, 3-完成生产, 4-验收阶段, 5-发货）
    current_status = db.Column(db.Integer, default=1, comment="当前订单状态: 1-下单, 2-排产, 3-完成生产, 4-验收阶段, 5-发货")
    current_status_time = db.Column(db.DateTime, comment="当前状态更新时间")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 进度相关字段（冗余存储，避免频繁联表查询）
    progress_status = db.Column(db.String(20), default='pending', comment="进度状态: pending(待开始), in_progress(进行中), completed(已完成)")
    progress_percent = db.Column(db.Integer, default=0, comment="进度百分比（0-100）")
    total_tasks = db.Column(db.Integer, default=0, comment="总任务项数")
    completed_tasks = db.Column(db.Integer, default=0, comment="已完成任务项数")

    # 关联订单
    order = db.relationship('Order', backref=db.backref('order_statuses', lazy=True))

    def to_dict(self):
        order_data = self.order.to_dict() if self.order else {}
        return {
            "id": self.id,
            "order_id": self.order_id,
            "progress_status": self.progress_status,
            "progress_percent": self.progress_percent,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "remarks": self.remarks,
            "current_status": self.current_status,
            "current_status_time": self.current_status_time.strftime('%Y-%m-%d') if self.current_status_time else None,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            # 订单基础信息
            "contract_no": order_data.get('contract_no', ''),
            "order_no": order_data.get('order_no', ''),
            "machine_no": order_data.get('machine_no', ''),
            "machine_name": order_data.get('machine_name', ''),
            "machine_model": order_data.get('machine_model', ''),
            "machine_count": order_data.get('machine_count', 0),
            "order_time": order_data.get('order_time', ''),
            "ship_time": order_data.get('ship_time', ''),
        }

    def sync_progress(self):
        """同步进度（任务项状态变更时调用）"""
        from sqlalchemy import func
        # 统计当前进度单下所有任务项的完成情况
        stats = db.session.query(
            func.count(StatusTask.id).label('total'),
            func.sum(StatusTask.is_completed.cast(db.Integer)).label('completed')
        ).filter(StatusTask.order_status_id == self.id).first()

        self.total_tasks = stats.total or 0
        self.completed_tasks = stats.completed or 0
        # 计算进度百分比
        if self.total_tasks > 0:
            self.progress_percent = int((self.completed_tasks / self.total_tasks) * 100)
            # 更新进度状态
            if self.progress_percent == 100:
                self.progress_status = 'completed'
            elif self.completed_tasks > 0:
                self.progress_status = 'in_progress'
            else:
                self.progress_status = 'pending'
        else:
            self.progress_percent = 0
            self.progress_status = 'pending'
        db.session.commit()


class OrderStatusLog(db.Model):
    """
    订单状态流水表（原OrderInspectionStatusLog/OrderCheckStatusLog）
    """
    __tablename__ = "order_status_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_status_id = db.Column(db.Integer, db.ForeignKey('order_status.id'), nullable=False, comment="关联进度主表ID")
    # 状态值与OrderStatus的current_status映射：下单(1)、排产(2)、完成生产(3)、验收阶段(4)、发货(5)
    status = db.Column(db.String(50), nullable=False, comment="状态值: 下单、排产、完成生产、验收阶段、发货")
    start_time = db.Column(db.DateTime, comment="状态开始时间")
    expected_completion_time = db.Column(db.DateTime, comment="预计完成时间")
    actual_completion_time = db.Column(db.DateTime, comment="实际完成时间")

    # 关联进度主表和任务项
    order_status = db.relationship('OrderStatus', backref=db.backref('status_logs', lazy=True))
    status_tasks = db.relationship('StatusTask', backref=db.backref('status_log', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "order_status_id": self.order_status_id,
            "status": self.status,
            "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            "expected_completion_time": self.expected_completion_time.strftime('%Y-%m-%d %H:%M:%S') if self.expected_completion_time else None,
            "actual_completion_time": self.actual_completion_time.strftime('%Y-%m-%d %H:%M:%S') if self.actual_completion_time else None,
        }


class StatusTask(db.Model):
    """
    进度任务项表（原InspectionItem/CheckItem）
    """
    __tablename__ = "status_task"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    order_status_id = db.Column(db.Integer, db.ForeignKey('order_status.id'), nullable=False, comment="关联进度主表ID")
    # 关联到具体的状态流水记录
    status_log_id = db.Column(db.Integer, db.ForeignKey('order_status_log.id'), nullable=False, comment="关联状态流水ID")
    category = db.Column(db.String(50), nullable=False, comment="任务类别（如：配件、外观、性能等）")
    
    name = db.Column(db.String(200), nullable=False, comment="任务名称（如：部件1、角度1、运行速度等）")
    is_completed = db.Column(db.Boolean, default=False, comment="是否完成任务：False-未完成，True-完成")
    # 移除原有的 photo_path/thumb_photo_path 字段
    description = db.Column(db.Text, comment="描述（可记录任务结果、异常信息等）")
    sort = db.Column(db.Integer, default=0, comment="排序序号")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        # 关联查询多媒体文件
        media_files = [mf.to_dict() for mf in self.media_files if not mf.is_deleted]
        # 区分图片和视频
        images = [mf for mf in media_files if mf['file_type'] == 'image']
        videos = [mf for mf in media_files if mf['file_type'] == 'video']
        
        return {
            "id": self.id,
            "order_status_id": self.order_status_id,
            "status_log_id": self.status_log_id,
            "category": self.category,
            "name": self.name,
            "is_completed": self.is_completed,
            "description": self.description,
            "sort": self.sort,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            # 新增多媒体信息
            "media_files": media_files,
            "images": images,
            "videos": videos,
            "image_count": len(images),
            "video_count": len(videos)
        }


class TaskMediaFile(db.Model):
    """
    任务项多媒体文件表（存储图片/视频）
    """
    __tablename__ = "task_media_file"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    status_task_id = db.Column(db.Integer, db.ForeignKey('status_task.id'), nullable=False, comment="关联进度任务项ID")
    file_type = db.Column(db.String(20), nullable=False, comment="文件类型：image(图片)、video(视频)")
    file_format = db.Column(db.String(20), comment="文件格式：jpg、png、mp4、avi、mov等")
    file_size = db.Column(db.BigInteger, comment="文件大小（字节）")
    file_path = db.Column(db.String(500), nullable=False, comment="文件存储路径（全路径）")
    # 修正：缩略图路径（图片/视频均支持，视频缩略图为封面图）
    thumb_path = db.Column(db.String(500), comment="缩略图路径（图片：压缩图；视频：封面图）")
    file_name = db.Column(db.String(200), comment="原始文件名")
    # 新增：视频特有字段（按需扩展）
    duration = db.Column(db.Integer, comment="视频时长（秒），图片此字段为null")
    upload_time = db.Column(db.DateTime, default=datetime.now, comment="上传时间")
    sort = db.Column(db.Integer, default=0, comment="展示排序序号")
    is_deleted = db.Column(db.Boolean, default=False, comment="是否软删除")

    # 关联回任务项
    status_task = db.relationship('StatusTask', backref=db.backref('media_files', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "status_task_id": self.status_task_id,
            "file_type": self.file_type,
            "file_format": self.file_format,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "thumb_path": self.thumb_path,
            "file_name": self.file_name,
            "duration": self.duration,  # 视频时长，图片返回null
            "upload_time": self.upload_time.strftime('%Y-%m-%d %H:%M:%S') if self.upload_time else None,
            "sort": self.sort
        }