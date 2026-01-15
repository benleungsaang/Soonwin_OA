import os
import sqlite3
from datetime import datetime

def migrate_order_table():
    """将OrderList表重命名为Order表"""
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'soonwin-os-Python-Server', 'soonwin_oa.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        print("正在创建数据库和表...")
        create_db_tables(db_path)
        return True
    
    print("开始数据库迁移...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查OrderList表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='OrderList';")
        orderlist_exists = cursor.fetchone() is not None
        
        if orderlist_exists:
            print("检测到OrderList表，正在重命名...")
            
            # 检查是否已经存在Order表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Order';")
            order_exists = cursor.fetchone() is not None
            
            if not order_exists:
                # 创建新表结构
                cursor.execute("""
                    CREATE TABLE "Order" (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        is_new INTEGER,
                        area VARCHAR(50) NOT NULL,
                        customer_name VARCHAR(100) NOT NULL,
                        customer_type VARCHAR(20) NOT NULL,
                        order_time DATE NOT NULL,
                        ship_time DATE,
                        ship_country VARCHAR(50),
                        contract_no VARCHAR(50) NOT NULL,
                        order_no VARCHAR(50),
                        machine_no VARCHAR(50),
                        machine_name VARCHAR(100) NOT NULL DEFAULT '包装机',
                        machine_model VARCHAR(50) NOT NULL,
                        machine_count INTEGER NOT NULL DEFAULT 1,
                        unit VARCHAR(10) NOT NULL DEFAULT 'set',
                        contract_amount NUMERIC(12, 2) DEFAULT 0,
                        deposit NUMERIC(12, 2) DEFAULT 0,
                        balance NUMERIC(12, 2) DEFAULT 0,
                        tax_rate NUMERIC(5, 2) DEFAULT 13.0,
                        tax_refund_amount NUMERIC(12, 2) DEFAULT 0,
                        currency_amount NUMERIC(12, 2) DEFAULT 0,
                        payment_received NUMERIC(12, 2) DEFAULT 0,
                        machine_cost NUMERIC(12, 2) DEFAULT 0,
                        net_profit NUMERIC(12, 2) DEFAULT 0,
                        operational_cost NUMERIC(12, 2) DEFAULT 0,
                        gross_profit NUMERIC(12, 2) DEFAULT 0,
                        pay_type VARCHAR(20) DEFAULT 'T/T',
                        commission NUMERIC(12, 2) DEFAULT 0,
                        latest_ship_date DATE,
                        expected_delivery DATE,
                        order_dept VARCHAR(50),
                        check_requirement TEXT,
                        attachment_imgs VARCHAR(500),
                        attachment_videos VARCHAR(500),
                        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        update_time DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # 查询OrderList表的列信息，以了解旧表的结构
                cursor.execute("PRAGMA table_info(OrderList);")
                old_columns = [row[1] for row in cursor.fetchall()]
                print(f"旧表列: {old_columns}")
                
                # 构建迁移数据的SQL
                # 从旧表复制数据到新表，处理字段映射
                if 'direct_cost' in old_columns and 'allocated_cost' in old_columns:
                    # 如果旧表包含direct_cost和allocated_cost，则映射到新字段
                    cursor.execute("""
                        INSERT INTO "Order" (
                            id, is_new, area, customer_name, customer_type, order_time, ship_time, 
                            ship_country, contract_no, order_no, machine_no, machine_name, 
                            machine_model, machine_count, unit, contract_amount, deposit, 
                            balance, tax_refund_amount, currency_amount, payment_received, 
                            machine_cost, net_profit, operational_cost, gross_profit, pay_type, 
                            commission, latest_ship_date, expected_delivery, order_dept, 
                            check_requirement, attachment_imgs, attachment_videos, 
                            create_time, update_time
                        )
                        SELECT 
                            id, is_new, area, customer_name, customer_type, order_time, ship_time, 
                            ship_country, contract_no, order_no, machine_no, machine_name, 
                            machine_model, machine_count, unit, contract_amount, deposit, 
                            balance, tax_refund_amount, currency_amount, payment_received, 
                            direct_cost, net_profit, allocated_cost, gross_profit, pay_type, 
                            commission, latest_ship_date, expected_delivery, order_dept, 
                            check_requirement, attachment_imgs, attachment_videos, 
                            create_time, update_time
                        FROM OrderList;
                    """)
                else:
                    # 如果旧表不包含这些列，使用默认值
                    cursor.execute("""
                        INSERT INTO "Order" (
                            id, is_new, area, customer_name, customer_type, order_time, ship_time, 
                            ship_country, contract_no, order_no, machine_no, machine_name, 
                            machine_model, machine_count, unit, contract_amount, deposit, 
                            balance, tax_refund_amount, currency_amount, payment_received, 
                            machine_cost, net_profit, operational_cost, gross_profit, pay_type, 
                            commission, latest_ship_date, expected_delivery, order_dept, 
                            check_requirement, attachment_imgs, attachment_videos, 
                            create_time, update_time
                        )
                        SELECT 
                            id, is_new, area, customer_name, customer_type, order_time, ship_time, 
                            ship_country, contract_no, order_no, machine_no, machine_name, 
                            machine_model, machine_count, unit, contract_amount, deposit, 
                            balance, tax_refund_amount, currency_amount, payment_received, 
                            COALESCE(direct_cost, 0), net_profit, COALESCE(allocated_cost, 0), gross_profit, pay_type, 
                            commission, latest_ship_date, expected_delivery, order_dept, 
                            check_requirement, attachment_imgs, attachment_videos, 
                            create_time, update_time
                        FROM OrderList;
                    """)
                
                print("✅ 数据迁移完成！")
            else:
                print("Order表已存在，跳过创建")
                
            # 删除旧表（注释掉以防数据丢失）
            # cursor.execute("DROP TABLE OrderList;")
            print("注意：保留原OrderList表以防万一")
        else:
            print("未找到OrderList表，检查是否已迁移或使用不同表名...")
        
        # 检查迁移结果
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"当前数据库中的表: {tables}")
        
        conn.commit()
        conn.close()
        print("✅ 数据库迁移脚本执行完成！")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库迁移失败: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False
    except Exception as e:
        print(f"❌ 迁移过程中发生错误: {str(e)}")
        return False

def create_db_tables(db_path):
    """创建数据库表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建Order表
        cursor.execute("""
            CREATE TABLE "Order" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                is_new INTEGER,
                area VARCHAR(50) NOT NULL,
                customer_name VARCHAR(100) NOT NULL,
                customer_type VARCHAR(20) NOT NULL,
                order_time DATE NOT NULL,
                ship_time DATE,
                ship_country VARCHAR(50),
                contract_no VARCHAR(50) NOT NULL,
                order_no VARCHAR(50),
                machine_no VARCHAR(50),
                machine_name VARCHAR(100) NOT NULL DEFAULT '包装机',
                machine_model VARCHAR(50) NOT NULL,
                machine_count INTEGER NOT NULL DEFAULT 1,
                unit VARCHAR(10) NOT NULL DEFAULT 'set',
                contract_amount NUMERIC(12, 2) DEFAULT 0,
                deposit NUMERIC(12, 2) DEFAULT 0,
                balance NUMERIC(12, 2) DEFAULT 0,
                tax_rate NUMERIC(5, 2) DEFAULT 13.0,
                tax_refund_amount NUMERIC(12, 2) DEFAULT 0,
                currency_amount NUMERIC(12, 2) DEFAULT 0,
                payment_received NUMERIC(12, 2) DEFAULT 0,
                machine_cost NUMERIC(12, 2) DEFAULT 0,
                net_profit NUMERIC(12, 2) DEFAULT 0,
                operational_cost NUMERIC(12, 2) DEFAULT 0,
                gross_profit NUMERIC(12, 2) DEFAULT 0,
                pay_type VARCHAR(20) DEFAULT 'T/T',
                commission NUMERIC(12, 2) DEFAULT 0,
                latest_ship_date DATE,
                expected_delivery DATE,
                order_dept VARCHAR(50),
                check_requirement TEXT,
                attachment_imgs VARCHAR(500),
                attachment_videos VARCHAR(500),
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 创建其他必要的表
        cursor.execute("""
            CREATE TABLE "Expense" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                amount NUMERIC(12, 2) NOT NULL,
                expense_direction VARCHAR(10) NOT NULL DEFAULT '支出',
                expense_type VARCHAR(20) NOT NULL DEFAULT '按比例分摊',
                target_year INTEGER NOT NULL,
                target_amount NUMERIC(12, 2),
                remark TEXT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE "ExpenseAllocation" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                allocated_amount NUMERIC(12, 2) NOT NULL,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expense_id) REFERENCES Expense(id),
                FOREIGN KEY (order_id) REFERENCES "Order"(id)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE "ExpenseCalculationRecord" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calculation_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                target_year INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'completed',
                remark TEXT
            );
        """)
        
        conn.commit()
        conn.close()
        print("✅ 数据库和表创建成功！")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 创建数据库失败: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_order_table()