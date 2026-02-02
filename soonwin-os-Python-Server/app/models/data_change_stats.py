"""
通用数据变化统计模型
专门记录各模块（询盘/沟通/视频/图片等）的增量/累计数据变化
"""
from extensions import db
from datetime import datetime
from sqlalchemy import Index


class DataChangeStats(db.Model):
    """
    通用数据变化统计模型
    专门记录各模块（询盘/沟通/视频/图片等）的增量/累计数据变化
    """
    __tablename__ = "data_change_stats"

    # 核心字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    module = db.Column(db.String(50), nullable=False, comment="业务模块：inquiry(询盘)/communication(沟通)/video(视频)/image(图片)")
    stats_type = db.Column(db.String(50), nullable=False, comment="统计类型：new(新增)/total(累计)/reset(复位)")
    stats_value = db.Column(db.Integer, default=0, comment="统计数值（新增数/累计数）")
    reset_time = db.Column(db.DateTime, comment="最近一次复位时间（用于计算复位后增量）")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="统计记录创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="统计记录更新时间")

    # 联合索引：确保同一模块+统计类型只有一条核心记录（如询盘-累计数、询盘-新增数）
    __table_args__ = (
        Index('idx_module_stats_type', 'module', 'stats_type', unique=True),
    )

    def to_dict(self):
        """序列化方法，便于前端展示/接口返回"""
        return {
            "id": self.id,
            "module": self.module,
            "stats_type": self.stats_type,
            "stats_value": self.stats_value,
            "reset_time": self.reset_time.strftime('%Y-%m-%d %H:%M:%S') if self.reset_time else None,
            "create_time": self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            "update_time": self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

    @classmethod
    def increment_stats(cls, module, stats_type, increment=1):
        """
        通用增量统计方法（核心工具方法）
        :param module: 业务模块（inquiry/communication/video/image）
        :param stats_type: 统计类型（new/total）
        :param increment: 增量值（默认+1）
        """
        try:
            # 查找已有记录，不存在则创建
            stats_record = cls.query.filter_by(module=module, stats_type=stats_type).first()
            if not stats_record:
                stats_record = cls(
                    module=module,
                    stats_type=stats_type,
                    stats_value=0
                )
                db.session.add(stats_record)

            # 累加数值
            stats_record.stats_value += increment
            db.session.commit()
            return stats_record
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def reset_stats(cls, module, stats_type_list=None):
        """
        通用复位统计方法（核心工具方法）
        :param module: 业务模块（inquiry/communication/video/image，传'all'复位所有）
        :param stats_type_list: 要复位的统计类型列表（如['new']，None则复位该模块所有类型）
        """
        try:
            # 构建查询条件
            query = cls.query
            if module != 'all':
                query = query.filter_by(module=module)
            if stats_type_list:
                query = query.filter(cls.stats_type.in_(stats_type_list))

            # 查询需要复位的记录
            records = query.all()
            reset_time = datetime.now()

            # 复位数值为0，并记录复位时间
            for record in records:
                record.stats_value = 0
                record.reset_time = reset_time

            db.session.commit()
            return records
        except Exception as e:
            db.session.rollback()
            raise e