"""
通用JSON处理工具模块
用于处理各种数据的导入、导出操作
"""

import json
from typing import Any, Dict, List, Optional
from .. import db
from ..models.machine import Machine, PartType


def map_camelcase_to_underscore(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将驼峰命名转换为下划线命名
    例如: 'ModelName' -> 'model_name', 'OriginalModel' -> 'original_model'
    """
    def camel_to_snake(name):
        import re
        # 在大写字母前插入下划线，但不包括开头
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    return {camel_to_snake(key): value for key, value in data.items()}


def import_json_data(model_type: str, data: List[Dict[str, Any]], is_update: bool = True) -> Dict[str, Any]:
    """
    通用JSON数据导入函数
    
    Args:
        model_type: 模型类型 ('machine' 或 'part')
        data: 要导入的数据
        is_update: 是否更新已存在的记录
    
    Returns:
        导入结果统计
    """
    try:
        success_count = 0
        error_count = 0
        errors = []
        
        for item_data in data:
            try:
                if model_type == 'machine':
                    model = Machine
                    # 使用型号作为唯一标识
                    existing = model.query.filter_by(model=item_data.get('model')).first()
                    if existing and is_update:
                        # 更新现有记录
                        for key, value in item_data.items():
                            if hasattr(existing, key) and key != 'model':
                                setattr(existing, key, value)
                        db.session.merge(existing)
                    elif not existing:
                        # 创建新记录
                        new_item = model(**item_data)
                        db.session.add(new_item)
                    else:
                        # 跳过已存在且不更新的记录
                        continue
                elif model_type == 'part':
                    model = PartType
                    # 使用part_model作为唯一标识
                    existing = model.query.filter_by(part_model=item_data.get('part_model')).first()
                    if existing and is_update:
                        # 更新现有记录
                        for key, value in item_data.items():
                            if hasattr(existing, key) and key != 'part_model':
                                setattr(existing, key, value)
                        db.session.merge(existing)
                    elif not existing:
                        # 创建新记录
                        new_item = model(**item_data)
                        db.session.add(new_item)
                    else:
                        # 跳过已存在且不更新的记录
                        continue
                else:
                    raise ValueError(f'不支持的模型类型: {model_type}')
                
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"处理数据项失败: {str(e)}, 数据: {item_data}")
        
        # 提交所有更改
        db.session.commit()
        
        # 返回导入结果
        return {
            'success': True,
            'total_processed': len(data),
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
        
    except Exception as e:
        db.session.rollback()
        raise e


def export_json_data(model_type: str, filters: Optional[Dict[str, Any]] = None, is_admin: bool = True) -> List[Dict[str, Any]]:
    """
    通用JSON数据导出函数
    
    Args:
        model_type: 模型类型 ('machine' 或 'part')
        filters: 过滤条件
        is_admin: 用户是否为管理员
    
    Returns:
        导出的数据列表
    """
    try:
        if model_type == 'machine':
            query = Machine.query
            if filters:
                # 可以根据需要添加过滤条件
                pass
            items = query.all()
            return [item.to_dict(is_admin=is_admin) for item in items]
        
        elif model_type == 'part':
            query = PartType.query
            if filters:
                # 可以根据需要添加过滤条件
                pass
            items = query.all()
            return [item.to_dict(is_admin=is_admin) for item in items]
        
        else:
            raise ValueError(f'不支持的模型类型: {model_type}')
            
    except Exception as e:
        raise e