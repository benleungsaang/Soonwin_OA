"""模块可见性配置模型

用于管理员在主页上临时隐藏某些功能模块（菜单项），
而无需修改权限系统或删除模块本身。
"""
from extensions import db
from datetime import datetime


class ModuleVisibility(db.Model):
    """模块可见性配置表

    - module_key 使用 camelCase，与前端 HomeView 的 permissionMap key 直接对应
      例如：photoManage、videoManage、machineManage 等
    - hidden=true 表示该模块对全员隐藏
    - 数据库里没有记录的模块默认显示
    """
    __tablename__ = 'module_visibility'

    # camelCase 字符串，如 "photoManage"
    module_key = db.Column(db.String(50), primary_key=True)
    # 是否隐藏
    hidden = db.Column(db.Boolean, default=False, nullable=False)
    # 更新时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 更新人 emp_id（便于审计）
    updated_by = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'module_key': self.module_key,
            'hidden': bool(self.hidden),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'updated_by': self.updated_by,
        }
