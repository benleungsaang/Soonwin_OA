"""
API测试脚本
用于测试新增的年度目标和个别费用功能
"""
import requests
import json

# 设置基础URL
BASE_URL = "http://127.0.0.1:5000/api"

# 模拟管理员token（实际使用时需要真实token）
HEADERS = {
    "Content-Type": "application/json"
}

def test_annual_target_api():
    """测试年度目标API"""
    print("=== 测试年度目标API ===")
    
    # 获取特定年份的年度目标
    print("1. 获取2026年年度目标...")
    try:
        response = requests.get(f"{BASE_URL}/annual-targets/year/2026", headers=HEADERS)
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"获取年度目标失败: {e}")
    
    # 尝试更新年度目标（需要管理员权限，预期会失败）
    print("\n2. 尝试更新年度目标...")
    try:
        response = requests.put(
            f"{BASE_URL}/annual-targets/year/2026", 
            headers=HEADERS,
            json={"target_amount": 12000000.00}
        )
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"更新年度目标失败: {e}")


def test_individual_expense_api():
    """测试个别费用API"""
    print("\n=== 测试个别费用API ===")
    
    # 获取个别费用列表
    print("1. 获取个别费用列表...")
    try:
        response = requests.get(f"{BASE_URL}/individual-expenses", headers=HEADERS)
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"获取个别费用列表失败: {e}")


def test_order_proportionate_cost_api():
    """测试订单摊分费用API"""
    print("\n=== 测试订单摊分费用API ===")
    
    # 获取订单费用汇总
    print("1. 获取订单费用汇总...")
    try:
        response = requests.get(f"{BASE_URL}/orders/expense-summary?year=2026", headers=HEADERS)
        print(f"响应状态: {response.status_code}")
        data = response.json()
        print(f"年份: {data.get('data', {}).get('year')}")
        print(f"年度目标: {data.get('data', {}).get('annual_target')}")
        print(f"订单总数: {data.get('data', {}).get('total_orders')}")
    except Exception as e:
        print(f"获取订单费用汇总失败: {e}")
    
    # 尝试更新订单摊分费用（需要管理员权限）
    print("\n2. 尝试更新订单摊分费用...")
    try:
        response = requests.post(
            f"{BASE_URL}/orders/update-proportionate-cost",
            headers=HEADERS,
            json={"target_year": 2026}
        )
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"更新订单摊分费用失败: {e}")


if __name__ == "__main__":
    print("开始API功能测试...")
    test_annual_target_api()
    test_individual_expense_api()
    test_order_proportionate_cost_api()
    print("\nAPI功能测试完成！")
