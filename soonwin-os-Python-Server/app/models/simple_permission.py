"""简化版权限模型"""
from extensions import db
from datetime import datetime


class SimpleRole(db.Model): 
    """角色表"""
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, comment='角色名')
    remark = db.Column(db.String(200), default='', comment='备注')

    # 该角色拥有的权限路由列表
    permissions = db.relationship('SimpleRolePermission', backref='role', lazy=True, cascade='all, delete-orphan')

    def has_route(self, route_name: str) -> bool:
        """判断是否有这个路由权限"""
        return any(p.route_name == route_name for p in self.permissions)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "remark": self.remark
        }


class SimpleRolePermission(db.Model):
    """角色-路由权限关联表"""
    __tablename__ = 'role_permission_simple'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    route_name = db.Column(db.String(100), nullable=False, comment='路由名：如 user、order、design')

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.id,
            "route_name": self.route_name
        }


def get_user_role_from_token():
    """从JWT token中获取用户角色信息（兼容现有系统）"""
    from flask import request
    import jwt
    import config
    from app.models.employee import Employee

    token = request.headers.get('Authorization')
    if not token:
        return None

    # 移除 "Bearer " 前缀
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # 解码JWT令牌
        payload = jwt.decode(token, config.Config.JWT_SECRET_KEY, algorithms=['HS256'])
        emp_id = payload['emp_id']

        # 查询员工信息
        employee = Employee.query.filter_by(emp_id=emp_id).first()
        if not employee:
            return None

        return employee.user_role

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def user_can_access_route(route_name: str) -> bool:
    """检查当前用户是否有访问路由的权限"""
    user_role = get_user_role_from_token()
    if not user_role:
        return False

    # 管理员拥有所有权限
    if user_role == 'admin':
        return True

    # 查询角色权限
    role = SimpleRole.query.filter_by(name=user_role).first()
    if not role:
        return False

    return role.has_route(route_name)