from sqlalchemy import Column, TEXT, Integer, DECIMAL, DateTime
from decimal import Decimal  # 补充缺失的导入
from .. import db
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from .system_config import SystemConfig  # 导入配置模型

class MachineNew(db.Model):
    __tablename__ = 'machines_new'  # 使用小写表名，符合约定

    # 模型原生字段定义（不变）
    id = db.Column(Integer, primary_key=True, autoincrement=True)  # 自增主键
    model = Column(TEXT)  # 设备型号
    original_model = Column(TEXT)  # 原厂型号
    machine_weight = Column(TEXT)  # 设备重量
    dimensions = Column(TEXT)  # 设备尺寸
    general_power = Column(TEXT)  # 总功率
    power_supply = Column(TEXT)  # 供电规格
    image = Column(TEXT, default='./assets/Media/Machine/sample.png')  # 缩略图路径
    added_count = Column(Integer, default=0)  # 计数字段
    show_price = Column(DECIMAL(10, 2), nullable=True)  # 展示价格（允许为空）
    original_price = Column(DECIMAL(10, 2))  # 原始价格
    machine_type = Column(Integer, default=0)  # 设备类型
    remark = Column(TEXT, default='')  # 备注
    brand = Column(TEXT, default='')  # 品牌
    search_key = Column(TEXT, default='')  # 搜索关键词
    custom_attrs = Column(TEXT, default='')  # 差异化字段（JSON文本）
    is_deleted = Column(Integer, default=0)  # 0=正常，1=已删除
    delete_time = Column(DateTime)  # 删除时间
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")  # 新增：创建时间
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")  # 新增：更新时间

    # ---------------------- 新增核心标识字段 ----------------------
    # 标记show_price是否为人工修改（1=人工，0=自动，默认0）
    is_show_price_manual = Column(Integer, default=0, comment="展示价格是否人工修改：0=自动计算，1=人工修改")

    # 创建者字段（记录创建/导入人的emp_id）
    creator = Column(db.String(20), nullable=True, comment="创建人/导入人的emp_id")

    # ---------------------- 新增：字段映射配置（核心适配） ----------------------
    FIELD_MAPPING = {
        'Model': 'model',
        'OriginalModel': 'original_model',
        'MachineWeight': 'machine_weight',
        'Dimensions': 'dimensions',
        'GeneralPower': 'general_power',
        'PowerSupply': 'power_supply',
        'addedCount': 'added_count',
        'ShowPrice': 'show_price',
        'OriginalPrice': 'original_price',
        'machine_type': 'machine_type',
        'brand': 'brand',
        'image': 'image'
    }

    # 2. 模型原生字段集合（用于识别非原生字段）
    @classmethod
    def get_native_fields(cls) -> set:
        """获取模型原生字段集合（排除内部字段）"""
        native_fields = {
            'model', 'original_model', 'machine_weight', 'dimensions',
            'general_power', 'power_supply', 'image', 'added_count',
            'show_price', 'original_price', 'machine_type', 'remark',
            'brand', 'search_key', 'custom_attrs', 'creator'
        }
        return native_fields

    # ---------------------- 核心：价格计算逻辑（基于标识字段） ----------------------
    @staticmethod
    def get_show_price_coefficient() -> Decimal:
        try:
            coeff_str = SystemConfig.get_config("show_price_coefficient", "1.05")
            coeff = Decimal(coeff_str)
            return coeff if coeff > 0 else Decimal("1.05")
        except (ValueError, TypeError):
            return Decimal("1.05")

    def calculate_show_price(self) -> Decimal:
        """
        计算最终展示价格（核心规则）：
        1. 人工修改过（is_show_price_manual=1）→ 直接返回存储的show_price
        2. 自动生成（is_show_price_manual=0）→ 用original_price×系数计算
        """
        # 人工修改过，优先返回存储值
        if self.is_show_price_manual == 1:
            return self.show_price.quantize(Decimal('0.01')) if self.show_price is not None else Decimal('0.00')

        # 自动计算逻辑
        if self.original_price is not None and self.original_price > 0:
            coeff = self.get_show_price_coefficient()
            return (self.original_price * coeff).quantize(Decimal('0.01'))

        return Decimal('0.00')

    # ---------------------- 改造：预处理逻辑（初始化标识字段） ----------------------
    @classmethod
    def preprocess_import_data(cls, raw_import_data: dict, creator_id: str = None) -> dict:
        if not isinstance(raw_import_data, dict):
            return {}

        # 1. 字段映射
        mapped_data = {}
        for import_key, value in raw_import_data.items():
            model_key = cls.FIELD_MAPPING.get(import_key, import_key)
            mapped_data[model_key] = value

        # 2. 初始化标识字段（关键）
        # 导入时填写了show_price → 标记为人工；未填写 → 标记为自动
        if mapped_data.get('show_price') is not None:
            mapped_data['is_show_price_manual'] = 1  # 人工导入show_price
        else:
            mapped_data['is_show_price_manual'] = 0  # 自动计算
            # 自动填充show_price（仅当未填写时）
            if mapped_data.get('original_price') is not None:
                try:
                    original_price = Decimal(str(mapped_data['original_price']))
                    if original_price > 0:
                        coeff = cls.get_show_price_coefficient()
                        mapped_data['show_price'] = (original_price * coeff).quantize(Decimal('0.01'))
                except (ValueError, TypeError):
                    mapped_data['show_price'] = Decimal('0.00')

        # 3. 添加创建者信息
        if creator_id is not None:
            mapped_data['creator'] = creator_id

        # 4. 分离原生/非原生字段（原有逻辑）
        native_fields = cls.get_native_fields()
        native_data = {}
        custom_data = {}
        for key, value in mapped_data.items():
            if key in native_fields or key == 'creator':
                native_data[key] = value
            else:
                custom_data[key] = value

        # 合并custom_attrs
        original_custom_attrs = native_data.get('custom_attrs', {})
        if isinstance(original_custom_attrs, str) and original_custom_attrs.strip():
            try:
                original_custom_attrs = json.loads(original_custom_attrs)
            except json.JSONDecodeError:
                original_custom_attrs = {}
        elif not isinstance(original_custom_attrs, dict):
            original_custom_attrs = {}
        original_custom_attrs.update(custom_data)
        native_data['custom_attrs'] = original_custom_attrs

        return native_data

    # ---------------------- 改造：更新方法（保护标识字段） ----------------------
    @classmethod
    def update_machine(cls, machine_id: int, update_data: dict, db_session) -> tuple[bool, str, 'MachineNew | None']:
        """
        更新设备数据（核心：仅修改指定字段，保护价格标识）
        :param machine_id: 设备ID
        :param update_data: 要更新的字段（如{'brand': '新品牌', 'remark': '新备注'}）
        :param db_session: 数据库会话
        :return: (是否成功, 提示信息, 更新后的对象)
        """
        # 1. 查询原数据
        machine = db_session.query(cls).filter(cls.id == machine_id, cls.is_deleted == 0).first()
        if not machine:
            return False, '设备不存在', None

        # 2. 过滤掉不应更新的字段（自动生成的字段）
        protected_fields = {'id', 'create_time', 'search_key'}  # 不应更新的字段
        filtered_update_data = {k: v for k, v in update_data.items()
                                if k not in protected_fields}

        # 3. 检查是否用户明确设置了is_show_price_manual
        user_set_is_manual = 'is_show_price_manual' in filtered_update_data
        user_manual_value = filtered_update_data.get('is_show_price_manual')

        # 4. 提取要更新的字段，区分是否修改了show_price
        update_show_price = False
        new_show_price = None
        if 'show_price' in filtered_update_data:
            update_show_price = True
            new_show_price = filtered_update_data.pop('show_price')  # 移除show_price，单独处理

        # 5. 更新非价格字段（不修改价格标识）
        for key, value in filtered_update_data.items():
            if hasattr(machine, key) and key != 'id':
                setattr(machine, key, value)

        # 6. 处理show_price更新
        if update_show_price:
            # 验证show_price格式
            try:
                if new_show_price is not None:
                    new_show_price = Decimal(str(new_show_price))
                    machine.show_price = new_show_price if new_show_price >= 0 else Decimal('0.00')
                else:
                    machine.show_price = None
                # 如果用户没有明确设置is_show_price_manual，则当主动修改show_price时，标记为人工
                if not user_set_is_manual:
                    machine.is_show_price_manual = 1
            except (ValueError, TypeError):
                db_session.rollback()
                return False, '展示价格格式错误', None

        # 7. 如果用户明确设置了is_show_price_manual，则使用用户设置的值
        if user_set_is_manual:
            try:
                machine.is_show_price_manual = int(user_manual_value)
            except (ValueError, TypeError):
                db_session.rollback()
                return False, '价格标识格式错误', None

        # 8. 重新生成搜索关键词
        machine.search_key = machine._generate_search_key()

        # 9. 保存更新
        try:
            db_session.commit()
            return True, '更新成功', machine
        except Exception as e:
            db_session.rollback()
            return False, f'更新失败：{str(e)}', None
    # ---------------------- 数据清洗（兼容show_price为空的情况） ----------------------
    @staticmethod
    def clean_data(raw_data: dict) -> dict:
        """清洗原始数据（兼容预处理后的导入数据）"""
        cleaned = {}

        # 1. 字符串字段处理
        str_fields = ['model', 'original_model', 'machine_weight', 'dimensions',
                      'general_power', 'power_supply', 'image', 'remark', 'brand']
        for field in str_fields:
            value = raw_data.get(field, '').strip() if raw_data.get(field) is not None else ''
            cleaned[field] = value

        # 2. 数值字段处理（show_price允许为空）
        # original_price处理
        if raw_data.get('original_price') is not None:
            try:
                price = Decimal(str(raw_data['original_price']))
                cleaned['original_price'] = price if price >= 0 else Decimal('0.00')
            except (ValueError, TypeError):
                cleaned['original_price'] = Decimal('0.00')
        else:
            cleaned['original_price'] = Decimal('0.00')

        # show_price处理（保留None值，区分人工未设置）
        if raw_data.get('show_price') is not None:
            try:
                price = Decimal(str(raw_data['show_price']))
                cleaned['show_price'] = price if price >= 0 else Decimal('0.00')
            except (ValueError, TypeError):
                cleaned['show_price'] = Decimal('0.00')
        else:
            cleaned['show_price'] = None  # 明确标记为未设置

        # 3. 整数字段转换
        int_fields = ['added_count', 'machine_type', 'is_show_price_manual']  # 新增标识字段
        for field in int_fields:
            try:
                cleaned[field] = int(raw_data.get(field, 0))
            except (ValueError, TypeError):
                cleaned[field] = 0

        # 4. 自定义属性处理
        custom_attrs = raw_data.get('custom_attrs', {})
        if isinstance(custom_attrs, dict):
            cleaned['custom_attrs'] = json.dumps(custom_attrs, ensure_ascii=False)
        elif isinstance(custom_attrs, str) and custom_attrs.strip():
            try:
                json.loads(custom_attrs)
                cleaned['custom_attrs'] = custom_attrs
            except json.JSONDecodeError:
                cleaned['custom_attrs'] = ''
        else:
            cleaned['custom_attrs'] = ''

        return cleaned

    # ---------------------- 创建/批量创建（复用原有逻辑，已兼容show_price） ----------------------
    @classmethod
    def create(cls, raw_data: dict, db_session, creator_id: str = None) -> tuple[bool, str, 'MachineNew | None']:
        preprocessed_data = cls.preprocess_import_data(raw_data, creator_id)
        if not preprocessed_data:
            return False, '导入数据格式错误', None

        cleaned_data = cls.clean_data(preprocessed_data)

        if not cleaned_data['model']:
            return False, '设备型号不能为空', None

        try:
            machine = cls(**cleaned_data)
            machine.search_key = machine._generate_search_key()
            db_session.add(machine)
            db_session.commit()
            return True, '创建成功', machine
        except Exception as e:
            db_session.rollback()
            return False, f'创建失败：{str(e)}', None

    @classmethod
    def batch_create(cls, raw_datas: list[dict], db_session, creator_id: str = None, batch_size: int = 100) -> tuple[bool, str, list]:
        if not raw_datas:
            return False, '批量导入数据不能为空', []

        preprocessed_datas = []
        for data in raw_datas:
            preprocessed = cls.preprocess_import_data(data, creator_id)
            preprocessed_datas.append(preprocessed)

        failed_datas = []
        cleaned_machines = []
        for idx, preprocessed_data in enumerate(preprocessed_datas):
            try:
                cleaned_data = cls.clean_data(preprocessed_data)
                model = cleaned_data['model']
                if not model:
                    failed_datas.append({'index': idx, 'data': raw_datas[idx], 'reason': '型号为空'})
                    continue

                machine = cls(**cleaned_data)
                machine.search_key = machine._generate_search_key()
                cleaned_machines.append(machine)

            except Exception as e:
                failed_datas.append({'index': idx, 'data': raw_datas[idx], 'reason': f'数据清洗失败：{str(e)}'})

        if cleaned_machines:
            try:
                for i in range(0, len(cleaned_machines), batch_size):
                    batch = cleaned_machines[i:i+batch_size]
                    db_session.add_all(batch)
                    db_session.flush()
                db_session.commit()
            except Exception as e:
                db_session.rollback()
                return False, f'批量插入数据库失败：{str(e)}', failed_datas

        if failed_datas:
            success_msg = f'批量导入完成，成功{len(cleaned_machines)}条，失败{len(failed_datas)}条'
            return True, success_msg, failed_datas
        else:
            return True, f'批量导入成功，共{len(cleaned_machines)}条', []

    # ---------------------- 序列化方法（使用新的calculate_show_price） ----------------------
    def to_dict(self, include_price=True, is_admin=None) -> Dict[str, Any]:
        """转换为字典格式（优先使用人工设置的show_price）"""
        if is_admin is not None:
            include_price = (is_admin == 'admin' or is_admin == True)

        # 解析自定义属性
        custom_attrs_dict = {}
        if self.custom_attrs:
            try:
                custom_attrs_dict = json.loads(self.custom_attrs)
            except (json.JSONDecodeError, TypeError):
                custom_attrs_dict = {}

        # 核心：使用calculate_show_price，自动区分人工/自动值
        final_show_price = self.calculate_show_price()

        result = {
            'id': self.id,
            'model': self.model,
            'original_model': self.original_model,
            'machine_weight': self.machine_weight,
            'dimensions': self.dimensions,
            'general_power': self.general_power,
            'power_supply': self.power_supply,
            'image': self.image,
            'added_count': self.added_count,
            'show_price': float(final_show_price),  # 最终展示价格
            'machine_type': self.machine_type,
            'remark': self.remark,
            'brand': self.brand,
            'search_key': self.search_key,
            'custom_attrs': custom_attrs_dict,
            'creator': self.creator,  # 添加创建者信息
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'is_show_price_manual': self.is_show_price_manual  # 返回价格标识，便于前端区分显示
        }

        # 原始价格展示
        if include_price:
            result['original_price'] = float(self.original_price) if self.original_price is not None else 0.00
            # 可选：返回原始的show_price值，便于前端查看是否人工设置
            result['manual_show_price'] = float(self.show_price) if self.show_price is not None else None

        return result

    def to_full_dict(self) -> Dict[str, Any]:
        """返回包含逻辑删除字段的完整字典"""
        base_dict = self.to_dict()
        base_dict.update({
            'is_deleted': self.is_deleted,
            'delete_time': self.delete_time.isoformat() if self.delete_time else None,
            'raw_show_price': float(self.show_price) if self.show_price is not None else None,  # 原始存储值
            'creator': self.creator  # 添加创建者信息到完整字典
        })
        return base_dict

    # ---------------------- 原有辅助方法 ----------------------
    def _generate_search_key(self) -> str:
        """生成搜索关键词"""
        search_fields = [
            self.model,
            self.original_model,
            self.brand,
            self.remark,
        ]

        valid_values = [str(v).strip() for v in search_fields if v and str(v).strip()]
        return ' '.join(valid_values)

    def save(self, db_session):
        """自定义保存方法"""
        self.search_key = self._generate_search_key()
        db_session.add(self)
        db_session.commit()