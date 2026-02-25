"""简化版权限验证工具"""
from functools import wraps
from flask import jsonify, request
from app.models.simple_permission import user_can_access_route


def route_permission(route_name):
    """
    简化版路由权限验证装饰器
    :param route_name: 路由名称
    :return: 装饰器
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否有访问该路由的权限
            if not user_can_access_route(route_name):
                return jsonify({
                    "code": 403,
                    "msg": f"无访问{route_name}模块的权限",
                    "data": None
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_auth_simple(f):
    """
    简化版基本认证装饰器（仅验证token有效性，不检查具体权限）
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.utils.auth_utils import get_user_role_from_token
        user_role = get_user_role_from_token()
        if not user_role:
            return jsonify({
                "code": 401,
                "msg": "认证失败，请重新登录",
                "data": None
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function