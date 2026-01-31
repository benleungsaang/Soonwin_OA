"""
直接在数据库中添加缺失的列
解决 InquiryLog 表缺少 company_name 字段的问题
"""
import sqlite3

def add_missing_columns():
    """添加缺失的列到 InquiryLog 表"""
    db_path = 'soonwin_oa_dev.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查当前表结构
        cursor.execute("PRAGMA table_info(InquiryLog);")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 InquiryLog 表的列: {columns}")
        
        # 添加 company_name 列（如果不存在）
        if 'company_name' not in columns:
            cursor.execute("ALTER TABLE InquiryLog ADD COLUMN company_name VARCHAR(200);")
            print("✅ 已添加 company_name 列")
        else:
            print("ℹ️  company_name 列已存在")
        
        # 检查统计字段是否为新名称
        if 'new_inquiries_count' not in columns:
            # 重命名字段或添加新字段
            if 'new_inquiries' in columns and 'new_communications' in columns:
                # 尝试重命名字段
                try:
                    # SQLite 不支持直接重命名列，所以我们需要创建新列并复制数据
                    cursor.execute("ALTER TABLE InquiryLog ADD COLUMN new_inquiries_count INTEGER;")
                    cursor.execute("ALTER TABLE InquiryLog ADD COLUMN new_communications_count INTEGER;")
                    
                    # 将旧数据复制到新列（如果需要）
                    cursor.execute("""
                        UPDATE InquiryLog 
                        SET new_inquiries_count = new_inquiries, 
                            new_communications_count = new_communications
                    """)
                    
                    print("✅ 已添加新的统计字段: new_inquiries_count, new_communications_count")
                except sqlite3.Error as e:
                    print(f"⚠️  重命名统计字段时出错: {e}")
        
        conn.commit()
        
        # 验证更新后的表结构
        cursor.execute("PRAGMA table_info(InquiryLog);")
        updated_columns = [col[1] for col in cursor.fetchall()]
        print(f"更新后 InquiryLog 表的列: {updated_columns}")
        
        conn.close()
        print("\n✅ 数据库结构更新完成！")
        
    except Exception as e:
        print(f"❌ 更新数据库结构失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_missing_columns()
