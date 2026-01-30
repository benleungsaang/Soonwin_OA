import sqlite3

# 直接连接SQLite数据库检查
conn = sqlite3.connect('instance/oa_system.db')
cursor = conn.cursor()

# 检查Inquiry表结构
cursor.execute('PRAGMA table_info(Inquiry);')
columns = cursor.fetchall()
print('Inquiry table structure from SQLite:')
for col in columns:
    print(f'  Column: {col[1]}, Type: {col[2]}, Not Null: {col[3]}, Default: {col[4]}, Primary Key: {col[5]}')

conn.close()

print("\nChecking for search_field column specifically:")
column_names = [col[1] for col in columns]
if 'search_field' in column_names:
    print("✓ search_field column exists in the database")
else:
    print("✗ search_field column does NOT exist in the database")
    
    # 尝试添加列
    try:
        conn = sqlite3.connect('instance/oa_system.db')
        cursor = conn.cursor()
        cursor.execute('ALTER TABLE Inquiry ADD COLUMN search_field TEXT;')
        conn.commit()
        print("Added search_field column to database")
        conn.close()
    except Exception as e:
        print(f"Error adding column: {e}")