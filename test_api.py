import requests
import json

# 测试服务器地址
base_url = "http://192.168.110.13:5001"

# 获取所有机器
def get_machines():
    try:
        headers = {
            'Authorization': 'Bearer your_admin_token_here',  # 替换为实际的管理员token
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{base_url}/api/machines", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

# 如果没有有效的token，先尝试登录获取token
def test_login():
    try:
        # 请替换为实际的管理员账号信息
        login_data = {
            "emp_id": "admin",  # 或其他管理员账号
            "totp_code": "123456"  # 替换为实际的TOTP码
        }
        response = requests.post(f"{base_url}/api/totp/login", json=login_data)
        print(f"Login Status Code: {response.status_code}")
        print(f"Login Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json().get('data', {}).get('token')
    except Exception as e:
        print(f"Login Error: {e}")
        return None

if __name__ == "__main__":
    print("正在测试API响应...")
    token = test_login()
    if token:
        print(f"\n获取到的token: {token[:20]}...")
        # 使用获取到的token测试获取机器列表
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{base_url}/api/machines", headers=headers)
        print(f"\n获取机器列表 - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'machines' in data['data'] and len(data['data']['machines']) > 0:
                first_machine = data['data']['machines'][0]
                print(f"第一个机器数据: {json.dumps(first_machine, indent=2, ensure_ascii=False)}")
                if 'original_price' in first_machine:
                    print("\n✅ 成功获取到 original_price 字段！")
                else:
                    print("\n❌ 未找到 original_price 字段")
            else:
                print("没有返回任何机器数据")
        else:
            print(f"API 请求失败: {response.text}")
    else:
        print("无法获取有效的管理员token，请确认管理员账号和TOTP码是否正确")