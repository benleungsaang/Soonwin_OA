import json
from typing import Dict, Any
from .. import db
from sqlalchemy import Column, String, Integer, DECIMAL, TEXT, UniqueConstraint


class Machine(db.Model):
    __tablename__ = 'machines'

    model = Column(TEXT, primary_key=True)  # 设备型号（唯一标识，核心查询键）
    original_model = Column(TEXT)  # 原厂型号（通用）
    packing_speed = Column(TEXT)  # 包装速度（通用）
    general_power = Column(TEXT)  # 总功率（通用）
    power_supply = Column(TEXT)  # 供电规格（通用）
    air_source = Column(TEXT)  # 气源要求（通用）
    machine_weight = Column(TEXT)  # 设备重量（通用）
    dimensions = Column(TEXT)  # 设备尺寸（通用）
    package_material = Column(TEXT)  # 包装材料（通用）
    image = Column(TEXT)  # 缩略图路径（通用）
    added_count = Column(Integer, default=0)  # 计数字段（通用）
    original_price = Column(DECIMAL(10, 2))  # 原始价格（通用）
    show_price = Column(DECIMAL(10, 2))  # 展示价格（通用）
    custom_attrs = Column(TEXT)  # 差异化字段（JSON文本）

    def to_dict(self, is_admin: bool = True) -> Dict[str, Any]:
        """转换为字典格式，根据用户权限控制字段显示"""
        # 解析自定义属性
        custom_attrs_dict = {}
        if self.custom_attrs:
            try:
                custom_attrs_dict = json.loads(self.custom_attrs)
            except (json.JSONDecodeError, TypeError):
                custom_attrs_dict = {}
        
        if is_admin:
            # 管理员视图：包含所有字段
            return {
                'model': self.model,
                'original_model': self.original_model,
                'packing_speed': self.packing_speed,
                'general_power': self.general_power,
                'power_supply': self.power_supply,
                'air_source': self.air_source,
                'machine_weight': self.machine_weight,
                'dimensions': self.dimensions,
                'package_material': self.package_material,
                'image': self.image,
                'added_count': self.added_count,
                'original_price': self.original_price,
                'show_price': self.show_price,
                'custom_attrs': custom_attrs_dict
            }
        else:
            # 普通用户视图：不包含原始价格
            return {
                'model': self.model,
                'original_model': self.original_model,
                'packing_speed': self.packing_speed,
                'general_power': self.general_power,
                'power_supply': self.power_supply,
                'air_source': self.air_source,
                'machine_weight': self.machine_weight,
                'dimensions': self.dimensions,
                'package_material': self.package_material,
                'image': self.image,
                'added_count': self.added_count,
                'show_price': self.show_price,
                'custom_attrs': custom_attrs_dict
            }


class PartType(db.Model):
    __tablename__ = 'part_types'

    part_type_id = Column(Integer, primary_key=True, autoincrement=True)  # 部件类型唯一ID
    part_model = Column(TEXT, unique=True, nullable=False)  # 部件型号（如MOTOR-001、SEAL-006，全局唯一）
    original_price = Column(DECIMAL(10, 2))  # 原始价格（通用）
    show_price = Column(DECIMAL(10, 2))  # 展示价格（通用）
    image = Column(TEXT)  # 缩略图路径（通用）

    def to_dict(self, is_admin: bool = True) -> Dict[str, Any]:
        """转换为字典格式，根据用户权限控制字段显示"""
        if is_admin:
            # 管理员视图：包含所有字段
            return {
                'part_type_id': self.part_type_id,
                'part_model': self.part_model,
                'original_price': self.original_price,
                'show_price': self.show_price,
                'image': self.image
            }
        else:
            # 普通用户视图：不包含原始价格
            return {
                'part_type_id': self.part_type_id,
                'part_model': self.part_model,
                'show_price': self.show_price,
                'image': self.image
            }