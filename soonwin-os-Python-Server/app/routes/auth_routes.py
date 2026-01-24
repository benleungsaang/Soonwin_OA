from flask import Blueprint, request, jsonify
from extensions import db
from app.models.employee import Employee
from app.utils.auth_utils import require_auth_with_leeway
from datetime import datetime, timedelta
import jwt
import config

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/refresh', methods=['POST'])
@require_auth_with_leeway  # 允许过期token在宽限时间内使用
def refresh_token():
    """
    刷新JWT令牌
    使用当前的过期token来换取一个新的有效token
    """
    try:
        # 从请求头获取token
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
            # 尝试解码token，允许小范围的过期（比如5分钟内）
            # 使用 leeway 参数允许一点时间差异
            payload = jwt.decode(
                token,
                config.Config.JWT_SECRET_KEY,
                algorithms=['HS256'],
                options={
                    "verify_exp": True  # 仍然验证过期时间，但允许小的leeway
                },
                leeway=timedelta(minutes=5)  # 允许5分钟的宽限时间
            )

            # 检查员工是否仍然存在且有效（使用大小写不敏感的查询）
            emp_id_lower = payload['emp_id'].lower()
            employee = Employee.query.filter(db.func.lower(Employee.emp_id) == emp_id_lower).first()
            if not employee:
                return jsonify({
                    "code": 401,
                    "msg": "员工信息不存在",
                    "data": None
                }), 401

            # 生成新的JWT令牌 (2小时有效期)
            new_payload = {
                'emp_id': employee.emp_id,
                'name': employee.name,
                'user_role': employee.user_role,
                'exp': datetime.now() + timedelta(hours=2)  # 2小时后过期
            }
            new_token = jwt.encode(new_payload, config.Config.JWT_SECRET_KEY, algorithm='HS256')

            return jsonify({
                "code": 200,
                "msg": "令牌刷新成功",
                "data": {
                    "token": new_token
                }
            })

        except jwt.ExpiredSignatureError:
            # Token已过期超过宽限时间，不允许刷新
            return jsonify({
                "code": 401,
                "msg": "令牌已过期，无法刷新，请重新登录",
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
            "msg": f"令牌刷新失败: {str(e)}",
            "data": None
        }), 500