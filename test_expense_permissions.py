"""
测试脚本：验证个别费用相关API的权限控制
"""
import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:5001"

# 示例token（需要替换为实际的用户token）
USER_TOKEN = "your_user_token_here"

def test_get_individual_expenses():
    """测试获取个别费用列表"""
    headers = {
        'Authorization': f'Bearer {USER_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f'{BASE_URL}/api/orders/individual-expenses', headers=headers)
    print(f"GET /api/orders/individual-expenses: {response.status_code}")
    print(f"Response: {response.json()}")


def test_get_individual_expenses_by_order():
    """测试获取指定订单的个别费用"""
    headers = {
        'Authorization': f'Bearer {USER_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # 使用一个存在的订单ID进行测试
    order_id = 1
    response = requests.get(f'{BASE_URL}/api/orders/{order_id}/individual-expenses', headers=headers)
    print(f"GET /api/orders/{order_id}/individual-expenses: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    print("Testing expense permissions...")
    # 注意：需要先设置有效的USER_TOKEN才能运行测试
    # test_get_individual_expenses()
    # test_get_individual_expenses_by_order()
    print("Please set a valid USER_TOKEN to run the tests.")