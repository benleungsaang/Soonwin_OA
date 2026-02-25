"""获取所有员工列表（用于员工管理界面）"""
@user_bp.route('/employees', methods=['GET'])
@route_permission(ROUTE_USER_MANAGE)
def get_employees():
    """获取所有员工列表（用于员工管理界面）"""
    try:
        # 使用JOIN查询获取员工及其TOTP信息
        from sqlalchemy import and_
        
        # 获取所有员工及其TOTP信息
        results = db.session.query(
            Employee,
            TotpUser.totp_secret
        ).outerjoin(
            TotpUser, 
            Employee.emp_id == TotpUser.emp_id
        ).all()
        
        employee_list = []
        for emp, totp_secret in results:
            employee_data = {
                'emp_id': emp.emp_id,
                'name': emp.name,
                'dept': emp.dept or '',
                'user_role': emp.user_role or 'sales',
                'status': emp.status or 'active',
                'create_time': emp.create_time.strftime("%Y-%m-%d %H:%M:%S") if emp.create_time else None,
                'update_time': emp.update_time.strftime("%Y-%m-%d %H:%M:%S") if emp.update_time and emp.update_time != emp.create_time else None,
                'last_login_time': emp.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if emp.last_login_time else None,
                'login_device': emp.login_device or '',
                'remarks': emp.remarks or '',
                'totp_secret': totp_secret or ''  # 添加TOTP密钥字段
            }
            employee_list.append(employee_data)

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": {
                "list": employee_list
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取员工列表失败: {str(e)}",
            "data": None
        }), 500