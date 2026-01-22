import sqlite3

def update_db_version():
    conn = sqlite3.connect('instance/oa_system.db')
    cursor = conn.cursor()

    # 检查alembic_version表的当前状态
    cursor.execute('SELECT * FROM alembic_version')
    current_versions = cursor.fetchall()
    print('当前alembic版本:', current_versions)

    # 更新到最新的版本
    cursor.execute('UPDATE alembic_version SET version_num = "005" WHERE version_num = "003"')

    conn.commit()
    conn.close()
    print('版本已更新到005')

if __name__ == "__main__":
    update_db_version()