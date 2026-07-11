"""管理员模块可见性相关路由

仅管理员可调用，用于临时隐藏/恢复主页上的功能模块菜单项。
模块可见性配置存储在 module_visibility 表中。
"""
from flask import Blueprint, request, jsonify
from extensions import db
from app.models.module_visibility import ModuleVisibility
from app.models.simple_permission import get_user_role_from_token

admin_module_bp = Blueprint('admin_module', __name__, url_prefix='/api/admin')


def _require_admin():
    """检查当前请求是否来自管理员用户。

    返回 (ok, payload, http_status)：
    - ok=True 时 payload 为 None（校验通过）
    - ok=False 时 payload 为已经构造好的 jsonify 响应元组 (body, status)
    """
    user_role = get_user_role_from_token()
    if not user_role:
        return False, (jsonify({
            "code": 401,
            "msg": "未登录或登录已过期",
            "data": None
        }), 401)
    if user_role != 'admin':
        return False, (jsonify({
            "code": 403,
            "msg": "权限不足，仅管理员可访问",
            "data": None
        }), 403)
    return True, None


@admin_module_bp.route('/module-visibility', methods=['GET'])
def get_module_visibility():
    """获取所有已配置的模块可见性（仅 admin）

    返回数据库中所有有记录的模块的 hidden 状态。
    数据库里没有记录的模块默认显示（前端在前端处理），
    所以这里只返回已有记录项。
    """
    try:
        ok, err = _require_admin()
        if not ok:
            return err

        records = ModuleVisibility.query.all()
        # 这里返回 camelCase key + 隐藏状态值
        # 例如：{ "photoManage": true, "videoManage": false }
        data = {rec.module_key: bool(rec.hidden) for rec in records}

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": data
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取模块可见性失败: {str(e)}",
            "data": None
        }), 500


@admin_module_bp.route('/module-visibility/batch', methods=['POST'])
def batch_update_module_visibility():
    """批量设置模块可见性（仅 admin）

    请求体：{ "photoManage": false, "videoManage": true, ... }
    - key 为 camelCase 模块名（必须与前端 HomeView 的 permissionMap 一致）
    - value 为 bool，true=隐藏，false=显示

    行为：upsert，数据库里有则更新，没有则插入。
    """
    try:
        ok, err = _require_admin()
        if not ok:
            return err

        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空，且必须是对象格式",
                "data": None
            }), 400

        # 获取当前操作人 emp_id（用于审计 updated_by 字段）
        operator_emp_id = None
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            try:
                import jwt
                import config
                payload = jwt.decode(auth[7:], config.Config.JWT_SECRET_KEY, algorithms=['HS256'])
                operator_emp_id = payload.get('emp_id')
            except Exception:
                # 解码失败时仍然允许保存，但 updated_by 留空
                pass

        updated_keys = []
        for module_key, hidden in data.items():
            if not isinstance(module_key, str) or not module_key.strip():
                continue
            # 只接受 bool 值；其他类型当作显示处理
            hidden_bool = bool(hidden)

            record = ModuleVisibility.query.filter_by(module_key=module_key).first()
            if record:
                record.hidden = hidden_bool
                record.updated_by = operator_emp_id
            else:
                record = ModuleVisibility(
                    module_key=module_key,
                    hidden=hidden_bool,
                    updated_by=operator_emp_id
                )
                db.session.add(record)
            updated_keys.append(module_key)

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "模块可见性保存成功",
            "data": {
                "updated_count": len(updated_keys),
                "updated_keys": updated_keys
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"保存模块可见性失败: {str(e)}",
            "data": None
        }), 500
