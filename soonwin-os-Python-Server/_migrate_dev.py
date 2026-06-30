"""一次性脚本：仅在开发库 (port=5001) 上执行 alembic 迁移。

WARNING: 不要在生产库 (port=5000) 运行此脚本。
生产库迁移应通过 run.py 自动启动流程执行（或 wsgi.py）。
"""
import sys
from app import create_app
from flask_migrate import upgrade as alembic_upgrade

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        from flask_migrate import downgrade as alembic_downgrade
        target = sys.argv[2] if len(sys.argv) > 2 else '-1'
        app = create_app(port=5001)
        with app.app_context():
            print(f'[DOWN] rolling back dev DB to {target} ...')
            alembic_downgrade(revision=target)
            print('[OK] rollback done')
        sys.exit(0)

    target = sys.argv[1] if len(sys.argv) > 1 else 'head'
    app = create_app(port=5001)  # 关键：显式指定开发端口
    with app.app_context():
        print(f'[UP] upgrading dev DB to {target} ...')
        alembic_upgrade(revision=target)
        print('[OK] upgrade done')

