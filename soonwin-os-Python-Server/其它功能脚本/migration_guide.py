"""
数据库迁移指南和脚本

推荐的数据库迁移流程：
1. 修改模型文件
2. 生成迁移文件: flask db migrate -m "描述"
3. 检查迁移文件
4. 应用迁移: flask db upgrade

如果flask命令不可用，可使用此脚本的辅助功能
"""

import os
import sys
from datetime import datetime

def print_migration_guide():
    """打印数据库迁移指南"""
    guide = """
# 数据库迁移指南

## 标准迁移流程（推荐）

1. 修改模型文件（如 app/models/employee.py）

2. 生成迁移文件：
   ```bash
   # 激活虚拟环境
   venv\\Scripts\\activate
   
   # 生成迁移文件
   flask db migrate -m "添加登录设备和时间字段到Employee表"
   ```

3. 检查生成的迁移文件（在 migrations/versions/ 目录下）

4. 应用迁移：
   ```bash
   flask db upgrade
   ```

## 如果flask命令不可用，使用以下方法：

### 方法1：使用此脚本
```bash
python db_migrate.py check    # 检查数据库结构
python db_migrate.py migrate  # 执行迁移
```

### 方法2：手动执行SQL
```python
import sqlite3
conn = sqlite3.connect('soonwin_oa.db')
cursor = conn.cursor()

# 添加新列的示例
cursor.execute('ALTER TABLE Employee ADD COLUMN last_login_time DATETIME;')
cursor.execute('ALTER TABLE Employee ADD COLUMN login_device VARCHAR(100);')

conn.commit()
conn.close()
```

## 配置Flask-Migrate（如果尚未配置）

在项目根目录下（soonwin-os-Python-Server/）执行：
```bash
# 初始化（只需执行一次）
flask db init

# 生成第一个迁移文件
flask db migrate -m "Initial migration"
```

## 重要提示

1. **迁移前备份数据库**：
   ```bash
   copy soonwin_oa.db soonwin_oa.db.backup
   ```

2. **开发环境迁移**：
   - 可以使用 `flask db upgrade` 或手动SQL
   - 迁移前确保后端服务未运行

3. **生产环境迁移**：
   - 必须先备份数据库
   - 在维护窗口期间执行
   - 仔细检查迁移文件

4. **常见问题**：
   - 如果遇到Alembic配置问题，使用手动SQL方法
   - 确保虚拟环境已激活
   - 检查PYTHONPATH是否正确设置
   """

    print(guide)

def create_sample_migration():
    """创建一个示例迁移文件"""
    migration_content = f'''
"""添加登录设备和时间字段

Revision ID: {datetime.now().strftime("%Y%m%d_%H%M%S")}
Revises: b43ce6da1d5b  # 这应该是最新的revision ID
Create Date: {datetime.now()}

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '{datetime.now().strftime("%Y%m%d_%H%M%S")}'
down_revision = 'b43ce6da1d5b'  # 更新为实际的最新版本
branch_labels = None
depends_on = None


def upgrade():
    # 为Employee表添加新列
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login_time', sa.DateTime(), nullable=True, comment="上次登录时间"))
        batch_op.add_column(sa.Column('login_device', sa.String(length=100), nullable=True, comment="登录设备"))


def downgrade():
    # 删除Employee表的新列
    with op.batch_alter_table('Employee', schema=None) as batch_op:
        batch_op.drop_column('login_device')
        batch_op.drop_column('last_login_time')
'''
    
    # 生成文件名
    filename = f"migrations/versions/{datetime.now().strftime('%Y%m%d_%H%M%S')}_add_login_fields.py"
    
    print(f"示例迁移文件内容 ({filename}):")
    print(migration_content)
    
    # 询问是否要创建文件
    response = input("是否要创建此迁移文件? (y/N): ")
    if response.lower() == 'y':
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(migration_content)
        print(f"迁移文件已创建: {filename}")

def main():
    if len(sys.argv) < 2:
        print_migration_guide()
        return
    
    command = sys.argv[1]
    
    if command == "guide":
        print_migration_guide()
    elif command == "create-sample":
        create_sample_migration()
    else:
        print("未知命令。可用命令：")
        print("  python migration_guide.py guide          - 显示迁移指南")
        print("  python migration_guide.py create-sample  - 创建示例迁移文件")

if __name__ == "__main__":
    main()