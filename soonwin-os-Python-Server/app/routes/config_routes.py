from flask import Blueprint, request, jsonify
from decimal import Decimal
from app.models.system_config import SystemConfig
from app import db

config_bp = Blueprint('config', __name__)


@config_bp.route('/config/show_price_coefficient', methods=['GET'])
def get_show_price_coefficient():
    """获取展示价格系数"""
    try:
        coefficient = SystemConfig.get_config("show_price_coefficient", "1.05")
        return jsonify({
            "success": True,
            "data": {
                "coefficient": coefficient
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取系数失败：{str(e)}"
        }), 500


@config_bp.route('/config/show_price_coefficient', methods=['POST'])
def update_show_price_coefficient():
    """更新展示价格系数"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "请求数据不能为空"
            }), 400

        new_coefficient = data.get('coefficient')
        if new_coefficient is None:
            return jsonify({
                "success": False,
                "message": "系数值不能为空"
            }), 400

        # 验证系数格式和范围
        try:
            coeff_decimal = Decimal(str(new_coefficient))
            if coeff_decimal <= 0:
                return jsonify({
                    "success": False,
                    "message": "系数必须大于0"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "系数格式不正确"
            }), 400

        # 更新系数
        success = SystemConfig.set_config(
            config_key="show_price_coefficient",
            value=str(new_coefficient),
            description="设备展示价格系数（展示价格=原始价格×系数）",
            db_session=db.session
        )

        if success:
            return jsonify({
                "success": True,
                "message": "系数更新成功",
                "data": {
                    "coefficient": str(new_coefficient)
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "系数更新失败"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"更新系数失败：{str(e)}"
        }), 500