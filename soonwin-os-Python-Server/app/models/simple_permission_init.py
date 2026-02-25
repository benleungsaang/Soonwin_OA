"""初始化简化版权限数据"""
from app.models.simple_permission import SimpleRole as Role, SimpleRolePermission as RolePermission
from app.constants.simple_permission_constants import ROLE_PERMISSIONS
from extensions import db


def init_simple_permissions():
    """初始化简化版权限系统"""
    print("开始初始化简化版权限系统...")
    
    # 创建角色并分配权限
    for role_name, route_list in ROLE_PERMISSIONS.items():
        # 检查角色是否已存在
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            # 创建新角色
            role_remark_map = {
                "admin": "管理员",
                "sales": "销售",
                "design": "设计",
                "user": "跟单"
            }
            role = Role(name=role_name, remark=role_remark_map.get(role_name, role_name))
            db.session.add(role)
            db.session.flush()  # 获取角色ID
            print(f"创建角色: {role_name}")
        
        # 获取该角色当前的所有权限
        current_permissions = RolePermission.query.filter_by(role_id=role.id).all()
        current_routes = {perm.route_name for perm in current_permissions}
        
        # 添加新增的权限
        for route_name in route_list:
            if route_name not in current_routes:
                new_permission = RolePermission(role_id=role.id, route_name=route_name)
                db.session.add(new_permission)
                print(f"为角色 {role_name} 添加权限: {route_name}")
        
        # 删除不再需要的权限
        for perm in current_permissions:
            if perm.route_name not in route_list:
                db.session.delete(perm)
                print(f"删除角色 {role_name} 的权限: {perm.route_name}")
    
    db.session.commit()
    print("简化版权限系统初始化完成！")


def create_roles_if_not_exist():
    """创建基础角色（如果不存在）"""
    base_roles = [
        {"name": "admin", "remark": "管理员"},
        {"name": "sales", "remark": "销售"},
        {"name": "design", "remark": "设计"},
        {"name": "user", "remark": "跟单"}
    ]
    
    for role_data in base_roles:
        role = Role.query.filter_by(name=role_data["name"]).first()
        if not role:
            role = Role(name=role_data["name"], remark=role_data["remark"])
            db.session.add(role)
            print(f"创建基础角色: {role_data['name']}")
    
    db.session.commit()