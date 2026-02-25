with open('G:/Soonwin_OA/soonwin-os-Python-Server/app/routes/user_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 替换函数体（从行331到363）
new_function_lines = [
    'def get_employees():\n',
    '    """获取所有员工列表（用于员工管理界面）"""\n',
    '    try:\n',
    '        # 使用JOIN查询获取员工及其TOTP信息\n',
    '        from sqlalchemy import and_\n',
    '        \n',
    '        # 获取所有员工及其TOTP信息\n',
    '        results = db.session.query(\n',
    '            Employee,\n',
    '            TotpUser.totp_secret\n',
    '        ).outerjoin(\n',
    '            TotpUser, \n',
    '            Employee.emp_id == TotpUser.emp_id\n',
    '        ).all()\n',
    '        \n',
    '        employee_list = []\n',
    '        for emp, totp_secret in results:\n',
    '            employee_data = {\n',
    '                \'id\': str(emp.id),  # 转换UUID为字符串\n',
    '                \'name\': emp.name,\n',
    '                \'emp_id\': emp.emp_id,\n',
    '                \'dept\': emp.dept or \'\',\n',
    '                \'device_id\': emp.device_id or \'\',\n',
    '                \'inner_ip\': emp.inner_ip,\n',
    '                \'user_role\': emp.user_role or \'sales\',\n',
    '                \'status\': emp.status or \'active\',\n',
    '                \'remarks\': emp.remarks or \'\',\n',
    '                \'last_login_time\': emp.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if emp.last_login_time else None,\n',
    '                \'login_device\': emp.login_device or \'\',\n',
    '                \'create_time\': emp.create_time.strftime("%Y-%m-%d %H:%M:%S"),\n',
    '                \'update_time\': emp.update_time.strftime("%Y-%m-%d %H:%M:%S") if emp.update_time and emp.update_time != emp.create_time else None,\n',
    '                \'totp_secret\': totp_secret or \'\'  # 添加TOTP密钥字段\n',
    '            }\n',
    '            employee_list.append(employee_data)\n',
    '\n',
    '        return jsonify({\n',
    '            "code": 200,\n',
    '            "msg": "success",\n',
    '            "data": {\n',
    '                "list": employee_list\n',
    '            }\n',
    '        })\n',
    '    except Exception as e:\n',
    '        return jsonify({\n',
    '            "code": 500,\n',
    '            "msg": f"获取员工列表失败: {str(e)}",\n',
    '            "data": None\n',
    '        }), 500\n',
    '\n'
]

# 替换原始函数（替换行330到364，即索引330到364）
lines[330:365] = new_function_lines

with open('G:/Soonwin_OA/soonwin-os-Python-Server/app/routes/user_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('成功更新 get_employees 函数')