from app import create_app
from extensions import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # 检查并创建所有表
        db.create_all()
        
        # 验证Inquiry表是否存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"All tables: {tables}")
        
        if 'Inquiry' in tables:
            print("Inquiry table exists")
            # 检查列信息
            columns = inspector.get_columns('Inquiry')
            column_names = [col['name'] for col in columns]
            print(f"Inquiry table columns: {column_names}")
            
            if 'search_field' not in column_names:
                print("search_field column is missing, need to add it manually")
                
                # 关闭现有连接
                db.engine.dispose()
                
                # 使用原生SQL添加列
                import sqlite3
                conn = sqlite3.connect('instance/oa_system.db')
                cursor = conn.cursor()
                
                # 检查是否已存在该列
                cursor.execute("PRAGMA table_info(Inquiry);")
                existing_columns = [col[1] for col in cursor.fetchall()]
                
                if 'search_field' not in existing_columns:
                    try:
                        cursor.execute("ALTER TABLE Inquiry ADD COLUMN search_field TEXT;")
                        conn.commit()
                        print("Added search_field column to Inquiry table")
                    except Exception as e:
                        print(f"Error adding column: {e}")
                else:
                    print("search_field column already exists")
                
                conn.close()
            else:
                print("search_field column already exists")
        else:
            print("Inquiry table does not exist")