from sqlalchemy import Column, TEXT, DECIMAL
from .. import db
from decimal import Decimal


class SystemConfig(db.Model):
    """系统配置表（存储动态调整的参数）"""
    __tablename__ = 'system_configs'
    
    key = Column(TEXT, primary_key=True, comment="配置键名")
    value = Column(TEXT, comment="配置值")
    description = Column(TEXT, comment="配置说明")
    
    @classmethod
    def get_config(cls, config_key: str, default_value: str = "") -> str:
        """获取配置值"""
        config = cls.query.filter_by(key=config_key).first()
        return config.value if config else default_value
    
    @classmethod
    def set_config(cls, config_key: str, value: str, description: str = "", db_session=None) -> bool:
        """设置配置值"""
        try:
            config = cls.query.filter_by(key=config_key).first()
            if not config:
                config = cls(key=config_key)
            
            config.value = value
            if description:
                config.description = description
            
            if db_session:
                db_session.add(config)
                db_session.commit()
            else:
                db.session.add(config)
                db.session.commit()
            return True
        except Exception as e:
            if db_session:
                db_session.rollback()
            else:
                db.session.rollback()
            print(f"设置配置失败：{e}")
            return False