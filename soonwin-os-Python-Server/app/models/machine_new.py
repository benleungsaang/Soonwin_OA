from sqlalchemy import Column, TEXT, Integer, DECIMAL, DateTime
from decimal import Decimal  # 补充缺失的导入
from .. import db
import json
from typing import Dict, Any
from sqlalchemy.orm import Session


class MachineNew(db.Model):
    __tablename__ = 'machines_new'  # 使用小写表名，符合约定

    # 模型原生字段定义（不变）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键
    model = Column(TEXT, unique=True)  # 设备型号
    original_model = Column(TEXT)  # 原厂型号
    machine_weight = Column(TEXT)  # 设备重量
    dimensions = Column(TEXT)  # 设备尺寸
    general_power = Column(TEXT)  # 总功率
    power_supply = Column(TEXT)  # 供电规格
    image = Column(TEXT, default='./assets/Media/Machine/sample.png')  # 缩略图路径
    added_count = Column(Integer, default=0)  # 计数字段
    show_price = Column(DECIMAL(10, 2))  # 展示价格
    original_price = Column(DECIMAL(10, 2))  # 原始价格
    machine_type = Column(Integer, default=0)  # 设备类型
    remark = Column(TEXT, default='')  # 备注
    brand = Column(TEXT, default='')  # 品牌
    search_key = Column(TEXT, default='')  # 搜索关键词
    custom_attrs = Column(TEXT, default='')  # 差异化字段（JSON文本）
    is_deleted = Column(Integer, default=0)  # 0=正常，1=已删除
    delete_time = Column(DateTime)  # 删除时间

    # ---------------------- 新增：字段映射配置（核心适配） ----------------------
    # 1. 导入数据字段 → 模型原生字段的映射（处理大小写/驼峰命名）
    FIELD_MAPPING = {
        # 首字母大写 → 小写下划线
        'Model': 'model',
        'OriginalModel': 'original_model',
        'MachineWeight': 'machine_weight',
        'Dimensions': 'dimensions',
        'GeneralPower': 'general_power',
        'PowerSupply': 'power_supply',
        # 驼峰命名 → 小写下划线
        'addedCount': 'added_count',
        'ShowPrice': 'show_price',
        'OriginalPrice': 'original_price',
        'machine_type': 'machine_type',  # 兼容小写
        'brand': 'brand',  # 兼容小写
        'image': 'image'   # 兼容小写
    }

    # 2. 模型原生字段集合（用于识别非原生字段）
    @classmethod
    def get_native_fields(cls) -> set:
        """获取模型原生字段集合（排除内部字段）"""
        native_fields = {
            'model', 'original_model', 'machine_weight', 'dimensions',
            'general_power', 'power_supply', 'image', 'added_count',
            'show_price', 'original_price', 'machine_type', 'remark',
            'brand', 'search_key', 'custom_attrs'
        }
        return native_fields

    # ---------------------- 改造：数据预处理（适配导入格式） ----------------------
    @classmethod
    def preprocess_import_data(cls, raw_import_data: dict) -> dict:
        """
        预处理导入数据：
        1. 字段名映射（首字母大写/驼峰 → 小写下划线）
        2. 提取非原生字段，存入custom_attrs临时字段
        """
        if not isinstance(raw_import_data, dict):
            return {}

        # 1. 字段名映射转换
        mapped_data = {}
        for import_key, value in raw_import_data.items():
            # 优先按映射表转换，无映射则保留原键（后续处理）
            model_key = cls.FIELD_MAPPING.get(import_key, import_key)
            mapped_data[model_key] = value

        # 2. 分离原生字段和非原生字段
        native_fields = cls.get_native_fields()
        native_data = {}  # 模型原生字段数据
        custom_data = {}  # 非原生字段数据（要存入custom_attrs）

        for key, value in mapped_data.items():
            if key in native_fields:
                native_data[key] = value
            else:
                # 非原生字段存入custom_data（后续转JSON）
                custom_data[key] = value

        # 3. 将非原生字段合并到custom_attrs（如果原有custom_attrs则合并）
        original_custom_attrs = native_data.get('custom_attrs', {})
        if isinstance(original_custom_attrs, str) and original_custom_attrs.strip():
            try:
                original_custom_attrs = json.loads(original_custom_attrs)
            except json.JSONDecodeError:
                original_custom_attrs = {}
        elif not isinstance(original_custom_attrs, dict):
            original_custom_attrs = {}

        # 合并非原生字段到custom_attrs
        original_custom_attrs.update(custom_data)
        native_data['custom_attrs'] = original_custom_attrs

        return native_data

    # ---------------------- 改造：clean_data（兼容预处理后的数据） ----------------------
    @staticmethod
    def clean_data(raw_data: dict) -> dict:
        """
        清洗原始数据（兼容预处理后的导入数据）
        :param raw_data: 预处理后的原始请求数据
        :return: 清洗后的合法数据
        """
        cleaned = {}

        # 1. 字符串字段去空格 + 空值处理
        str_fields = ['model', 'original_model', 'machine_weight', 'dimensions',
                      'general_power', 'power_supply', 'image', 'remark', 'brand']
        for field in str_fields:
            value = raw_data.get(field, '').strip() if raw_data.get(field) is not None else ''
            cleaned[field] = value

        # 2. 数值字段类型转换 + 合法性校验
        if raw_data.get('original_price') is not None:
            try:
                price = Decimal(str(raw_data['original_price']))
                cleaned['original_price'] = price if price >= 0 else Decimal('0.00')
            except (ValueError, TypeError):
                cleaned['original_price'] = Decimal('0.00')

        if raw_data.get('show_price') is not None:
            try:
                price = Decimal(str(raw_data['show_price']))
                cleaned['show_price'] = price if price >= 0 else Decimal('0.00')
            except (ValueError, TypeError):
                cleaned['show_price'] = Decimal('0.00')

        # 3. 整数字段转换
        int_fields = ['added_count', 'machine_type']
        for field in int_fields:
            try:
                cleaned[field] = int(raw_data.get(field, 0))
            except (ValueError, TypeError):
                cleaned[field] = 0

        # 4. 自定义属性JSON解析（此时custom_attrs是合并后的字典）
        custom_attrs = raw_data.get('custom_attrs', {})
        if isinstance(custom_attrs, dict):
            cleaned['custom_attrs'] = json.dumps(custom_attrs, ensure_ascii=False)
        elif isinstance(custom_attrs, str) and custom_attrs.strip():
            try:
                json.loads(custom_attrs)  # 校验格式
                cleaned['custom_attrs'] = custom_attrs
            except json.JSONDecodeError:
                cleaned['custom_attrs'] = ''
        else:
            cleaned['custom_attrs'] = ''

        return cleaned

    # ---------------------- 改造：create（新增预处理步骤） ----------------------
    @classmethod
    def create(cls, raw_data: dict, db_session) -> tuple[bool, str, 'MachineNew | None']:
        """
        模型内封装创建逻辑（适配导入数据）
        :param raw_data: 原始导入数据（首字母大写/驼峰格式）
        :param db_session: 数据库会话
        :return: (是否成功, 提示信息, 创建后的对象/None)
        """
        # 新增：预处理导入数据（字段映射+非原生字段提取）
        preprocessed_data = cls.preprocess_import_data(raw_data)
        if not preprocessed_data:
            return False, '导入数据格式错误', None

        # 原有逻辑（数据清洗）
        cleaned_data = cls.clean_data(preprocessed_data)

        # 2. 业务规则校验（型号唯一性）
        if not cleaned_data['model']:
            return False, '设备型号不能为空', None

        if db_session.query(cls).filter_by(model=cleaned_data['model']).first():
            return False, '设备型号已存在', None

        # 3. 创建对象
        try:
            machine = cls(**cleaned_data)
            # 4. 自动填充search_key
            machine.search_key = machine._generate_search_key()
            # 5. 保存到数据库
            db_session.add(machine)
            db_session.commit()
            return True, '创建成功', machine
        except Exception as e:
            db_session.rollback()
            return False, f'创建失败：{str(e)}', None

    # ---------------------- 改造：batch_create（新增预处理步骤） ----------------------
    @classmethod
    def batch_create(cls, raw_datas: list[dict], db_session, batch_size: int = 100) -> tuple[bool, str, list]:
        """
        批量创建机器（适配导入数据格式）
        :param raw_datas: 原始导入数据列表（首字母大写/驼峰格式）
        :param db_session: 数据库会话
        :param batch_size: 每批次插入的数量
        :return: (是否全部成功, 提示信息, 失败数据列表)
        """
        if not raw_datas:
            return False, '批量导入数据不能为空', []

        # 1. 预处理所有导入数据（字段映射+非原生字段提取）
        preprocessed_datas = []
        for data in raw_datas:
            preprocessed = cls.preprocess_import_data(data)
            preprocessed_datas.append(preprocessed)

        # 2. 前置：批量校验型号唯一性（只查一次数据库）
        all_models = [d.get('model', '').strip() for d in preprocessed_datas if d.get('model')]
        valid_models = [m for m in all_models if m]  # 过滤空型号
        if not valid_models:
            return False, '所有数据型号均为空', raw_datas

        # 批量查询已存在的型号
        existing_models = db_session.query(cls.model).filter(cls.model.in_(valid_models)).all()
        existing_model_set = {m[0] for m in existing_models}

        # 3. 数据清洗 + 过滤无效数据
        failed_datas = []
        cleaned_machines = []
        for idx, preprocessed_data in enumerate(preprocessed_datas):
            try:
                # 复用清洗逻辑
                cleaned_data = cls.clean_data(preprocessed_data)

                # 校验型号
                model = cleaned_data['model']
                if not model:
                    failed_datas.append({'index': idx, 'data': raw_datas[idx], 'reason': '型号为空'})
                    continue
                if model in existing_model_set:
                    failed_datas.append({'index': idx, 'data': raw_datas[idx], 'reason': '型号已存在'})
                    continue

                # 创建对象
                machine = cls(**cleaned_data)
                machine.search_key = machine._generate_search_key()
                cleaned_machines.append(machine)

            except Exception as e:
                failed_datas.append({'index': idx, 'data': raw_datas[idx], 'reason': f'数据清洗失败：{str(e)}'})

        # 4. 批量插入数据库
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

        # 5. 返回结果
        if failed_datas:
            success_msg = f'批量导入完成，成功{len(cleaned_machines)}条，失败{len(failed_datas)}条'
            return True, success_msg, failed_datas
        else:
            return True, f'批量导入成功，共{len(cleaned_machines)}条', []

    # ---------------------- 原有方法（不变） ----------------------
    def to_dict(self, include_price=True, is_admin=None) -> Dict[str, Any]:
        """转换为字典格式（输出业务字段，键名可根据需求调整）"""
        # 如果is_admin参数被提供，优先使用它来决定是否包含价格
        if is_admin is not None:
            include_price = (is_admin == 'admin' or is_admin == True)

        # 解析自定义属性
        custom_attrs_dict = {}
        if self.custom_attrs:
            try:
                custom_attrs_dict = json.loads(self.custom_attrs)
            except (json.JSONDecodeError, TypeError):
                custom_attrs_dict = {}

        result = {
            # 如果你需要对外返回首字母大写的键名，可在这里映射（如 'Model': self.model）
            'id': self.id,
            'model': self.model,
            'original_model': self.original_model,
            'machine_weight': self.machine_weight,
            'dimensions': self.dimensions,
            'general_power': self.general_power,
            'power_supply': self.power_supply,
            'image': self.image,  # 修正字段名
            'added_count': self.added_count,
            'show_price': self.show_price,
            'machine_type': self.machine_type,
            'remark': self.remark,
            'brand': self.brand,
            'search_key': self.search_key,
            'custom_attrs': custom_attrs_dict
        }

        # 根据参数决定是否包含原始价格
        if include_price:
            result['original_price'] = self.original_price

        return result

    def to_full_dict(self) -> Dict[str, Any]:
        """返回包含逻辑删除字段的完整字典"""
        base_dict = self.to_dict()
        base_dict.update({
            'is_deleted': self.is_deleted,
            'delete_time': self.delete_time.isoformat() if self.delete_time else None
        })
        return base_dict

    def _generate_search_key(self) -> str:
        """生成搜索关键词"""
        search_fields = [
            self.model,
            self.original_model,
            self.brand,
            self.remark,
        ]

        # try:
        #     custom_attrs_dict = json.loads(self.custom_attrs) if self.custom_attrs else {}
        #     search_fields.extend([str(v) for v in custom_attrs_dict.values()])
        # except (json.JSONDecodeError, TypeError):
        #     pass

        valid_values = [str(v).strip() for v in search_fields if v and str(v).strip()]
        return ' '.join(valid_values)

    def save(self, db_session):
        """自定义保存方法"""
        self.search_key = self._generate_search_key()
        db_session.add(self)
        db_session.commit()