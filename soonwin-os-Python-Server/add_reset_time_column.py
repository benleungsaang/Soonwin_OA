import sqlite3

# 连接数据库
conn = sqlite3.connect('soonwin_oa_dev.db')
cursor = conn.cursor()

# 检查字段是否已存在
cursor.execute("PRAGMA table_info(InquiryLog);")
columns = [col[1] for col in cursor.fetchall()]

if 'reset_time' not in columns:
    # 添加 reset_time 字段
    cursor.execute("ALTER TABLE InquiryLog ADD COLUMN reset_time DATETIME;")
    print("✅ 已添加 reset_time 字段到 InquiryLog 表")
else:
    print("ℹ️  reset_time 字段已存在于 InquiryLog 表中")

conn.commit()
conn.close()
print("✅ 数据库结构更新完成")