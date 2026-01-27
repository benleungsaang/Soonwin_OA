import requests
import json

# 测试修复后的询盘API权限验证逻辑
print("测试询盘API权限验证逻辑...")

# 尝试访问询盘API，不带认证令牌
try:
    response = requests.get('http://localhost:5001/api/inquiries')
    print(f"未认证访问状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
except Exception as e:
    print(f"连接服务器失败: {e}")
    print("请确保后端服务器正在运行在端口5001上")

# 检查数据库表结构是否正确
import sqlite3
conn = sqlite3.connect('soonwin_oa_dev.db')
cursor = conn.cursor()

# 检查Inquiry表结构
cursor.execute("PRAGMA table_info(Inquiry);")
inquiry_columns = cursor.fetchall()
print("\nInquiry表结构:")
for col in inquiry_columns:
    print(f"  {col}")

# 检查外键关系
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Inquiry';")
inquiry_table_sql = cursor.fetchone()
print(f"\nInquiry表创建SQL: {inquiry_table_sql[0] if inquiry_table_sql else 'Not found'}")

conn.close()
print("\n数据库结构验证完成")