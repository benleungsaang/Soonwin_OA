from functools import wraps
from flask import request, jsonify
import jwt
import config
from app.models.employee import Employee
from extensions import db
from datetime import timedelta


def require_admin(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                "code": 401,
                "msg": "缺少访问令牌",
                "data": None
            }), 401
            
        # 移除 "Bearer " 前缀
        if token.startswith("Bearer "):
            token = token[7:]
        
        try:
            # 解码JWT令牌
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
            emp_id = payload['emp_id']
            
            # 查询员工信息
            employee = Employee.query.filter_by(emp_id=emp_id).first()
            if not employee:
                return jsonify({
                    "code": 401,
                    "msg": "员工信息不存在",
                    "data": None
                }), 401
            
            # 检查是否为管理员
            if employee.user_role != 'admin':
                return jsonify({
                    "code": 403,
                    "msg": "权限不足，仅管理员可访问",
                    "data": None
                }), 403
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                "code": 401,
                "msg": "令牌已过期",
                "data": None
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "code": 401,
                "msg": "无效的令牌",
                "data": None
            }), 401
        except Exception as e:
            return jsonify({
                "code": 500,
                "msg": f"权限验证失败: {str(e)}",
                "data": None
            }), 500
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_auth(f):
    """基本认证装饰器 - 不允许过期token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                "code": 401,
                "msg": "缺少访问令牌",
                "data": None
            }), 401
            
        # 移除 "Bearer " 前缀
        if token.startswith("Bearer "):
            token = token[7:]
        
        try:
            # 解码JWT令牌
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
            emp_id = payload['emp_id']
            
            # 查询员工信息
            employee = Employee.query.filter_by(emp_id=emp_id).first()
            if not employee:
                return jsonify({
                    "code": 401,
                    "msg": "员工信息不存在",
                    "data": None
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                "code": 401,
                "msg": "令牌已过期",
                "data": None
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "code": 401,
                "msg": "无效的令牌",
                "data": None
            }), 401
        except Exception as e:
            return jsonify({
                "code": 500,
                "msg": f"认证失败: {str(e)}",
                "data": None
            }), 500
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_auth_with_leeway(f):
    """基本认证装饰器 - 允许过期token在一定宽限时间内使用（用于token刷新）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                "code": 401,
                "msg": "缺少访问令牌",
                "data": None
            }), 401
            
        # 移除 "Bearer " 前缀
        if token.startswith("Bearer "):
            token = token[7:]
        
        try:
            # 解码JWT令牌，允许5分钟宽限期
            payload = jwt.decode(
                token, 
                config.JWT_SECRET_KEY, 
                algorithms=['HS256'],
                options={
                    "verify_exp": True
                },
                leeway=timedelta(minutes=5)  # 允许5分钟的宽限时间
            )
            emp_id = payload['emp_id']
            
            # 查询员工信息
            employee = Employee.query.filter_by(emp_id=emp_id).first()
            if not employee:
                return jsonify({
                    "code": 401,
                    "msg": "员工信息不存在",
                    "data": None
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                "code": 401,
                "msg": "令牌已过期超过宽限时间",
                "data": None
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "code": 401,
                "msg": "无效的令牌",
                "data": None
            }), 401
        except Exception as e:
            return jsonify({
                "code": 500,
                "msg": f"认证失败: {str(e)}",
                "data": None
            }), 500
        
        return f(*args, **kwargs)
    
    return decorated_function