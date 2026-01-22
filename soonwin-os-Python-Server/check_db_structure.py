import sqlite3

def check_db_structure():
    conn = sqlite3.connect('instance/oa_system.db')
    cursor = conn.cursor()

    # 检查OrderInspection表结构
    cursor.execute('PRAGMA table_info(OrderInspection)')
    columns = cursor.fetchall()
    print('OrderInspection表结构:')
    for col in columns:
        print(f'  {col[1]} ({col[2]}) - {col[5]}')

    print()

    # 检查OrderInspectionStatusLog表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='OrderInspectionStatusLog'")
    tables = cursor.fetchall()
    print('OrderInspectionStatusLog表存在:', len(tables) > 0)

    conn.close()

if __name__ == "__main__":
    check_db_structure()