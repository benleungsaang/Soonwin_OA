from functools import wraps
from flask import jsonify, request
from app.models.employee import Employee
from app.models.simple_permission import user_can_access_route


def route_permission(route_name):
    """
    权限装饰器
    admin角色直接放行所有权限，其他角色按分配权限控制
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 检查用户是否有访问此路由的权限
            if user_can_access_route(route_name):
                return f(*args, **kwargs)
            else:
                return jsonify({"code": 403, "msg": f"无此模块权限: {route_name}"}), 403

        return wrapper
    return decorator