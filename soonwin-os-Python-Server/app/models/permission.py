from extensions import db
import uuid
from datetime import datetime

class RolePermission(db.Model):
    """角色-权限关联表（多对多）"""
    __tablename__ = "RolePermission"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID主键")
    role_name = db.Column(db.String(50), nullable=False, comment="角色名称（admin/sales/user）")
    role_description = db.Column(db.String(100), nullable=True, comment="角色描述名称（中文）")
    module_name = db.Column(db.String(50), nullable=False, comment="模块名称（如：employee_manage、device_manage）")
    can_view = db.Column(db.Boolean, default=True, comment="是否可查看")
    can_edit = db.Column(db.Boolean, default=False, comment="是否可编辑")
    can_delete = db.Column(db.Boolean, default=False, comment="是否可删除")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, onupdate=datetime.now, comment="更新时间")

    # 联合唯一索引：一个角色对一个模块只能有一条权限记录
    __table_args__ = (
        db.UniqueConstraint('role_name', 'module_name', name='uq_role_module'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "role_name": self.role_name,
            "role_description": self.role_description,
            "module_name": self.module_name,
            "can_view": self.can_view,
            "can_edit": self.can_edit,
            "can_delete": self.can_delete,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None
        }

# 初始化默认权限（可在项目启动时调用）
def init_default_permissions():
    """初始化系统默认权限"""
    default_permissions = [
        # 管理员权限：所有模块都有全部权限
        {"role_name": "admin", "module_name": "employee_manage", "can_view": True, "can_edit": True, "can_delete": True},
        {"role_name": "admin", "module_name": "device_manage", "can_view": True, "can_edit": True, "can_delete": True},
        {"role_name": "admin", "module_name": "permission_manage", "can_view": True, "can_edit": True, "can_delete": True},

        # 销售权限：只能查看和编辑设备管理，不能删除
        {"role_name": "sales", "module_name": "device_manage", "can_view": True, "can_edit": True, "can_delete": False},
        {"role_name": "sales", "module_name": "employee_manage", "can_view": True, "can_edit": False, "can_delete": False},

        # 普通用户权限：只能查看自己相关的信息
        {"role_name": "user", "module_name": "device_manage", "can_view": True, "can_edit": False, "can_delete": False},
    ]

    for perm in default_permissions:
        existing = RolePermission.query.filter_by(
            role_name=perm["role_name"],
            module_name=perm["module_name"]
        ).first()
        if not existing:
            new_perm = RolePermission(**perm)
            db.session.add(new_perm)

    db.session.commit()