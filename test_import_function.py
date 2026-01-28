import requests
import json

# 测试服务器地址
BASE_URL = "http://127.0.0.1:5001"

def test_import_machines_json():
    """测试JSON数据导入功能"""
    print("测试机器JSON数据导入功能...")
    
    # 准备测试数据
    test_data = [
        {
            "model": "TEST-IMPORT-MACHINE-001",
            "original_model": "TIM-001",
            "packing_speed": "200 units/min",
            "general_power": "7kW",
            "power_supply": "380V/50Hz",
            "air_source": "10bar",
            "machine_weight": "700kg",
            "dimensions": "1400x1200x1600mm",
            "package_material": "PVC film",
            "image": "/images/test_import_machine.jpg",
            "original_price": 70000.00,
            "show_price": 65000.00,
            "custom_attrs": json.dumps({"imported": "yes", "test": True}, ensure_ascii=False)
        }
    ]
    
    response = requests.post(f"{BASE_URL}/api/machines/import-json", json=test_data)
    print(f"导入机器响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"导入结果: {result}")
        print("机器JSON导入成功")
    else:
        print(f"导入失败: {response.text}")

def test_import_parts_json():
    """测试部件JSON数据导入功能"""
    print("\n测试部件JSON数据导入功能...")
    
    # 准备测试数据
    test_data = [
        {
            "part_model": "TEST-IMPORT-PART-001",
            "original_price": 2000.00,
            "show_price": 1800.00,
            "image": "/images/test_import_part.jpg"
        }
    ]
    
    response = requests.post(f"{BASE_URL}/api/parts/import-json", json=test_data)
    print(f"导入部件响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"导入结果: {result}")
        print("部件JSON导入成功")
    else:
        print(f"导入失败: {response.text}")

def test_get_all_machines():
    """测试获取所有机器"""
    print("\n测试获取所有机器...")
    response = requests.get(f"{BASE_URL}/api/machines")
    print(f"获取机器响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"机器总数: {data['data']['total']}")
        if data['data']['machines']:
            first_machine = data['data']['machines'][0]
            print(f"第一台机器型号: {first_machine['model']}")

def test_get_all_parts():
    """测试获取所有部件"""
    print("\n测试获取所有部件...")
    response = requests.get(f"{BASE_URL}/api/parts")
    print(f"获取部件响应: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"部件总数: {data['data']['total']}")
        if data['data']['parts']:
            first_part = data['data']['parts'][0]
            print(f"第一台部件型号: {first_part['part_model']}")

if __name__ == "__main__":
    test_import_machines_json()
    test_import_parts_json()
    test_get_all_machines()
    test_get_all_parts()