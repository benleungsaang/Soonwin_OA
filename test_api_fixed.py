import requests
import json

def test_api():
    # 测试API端点
    url = 'http://localhost:5001/api/orders/3/progress'
    try:
        response = requests.get(url)
        print(f'API响应状态码: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('API响应数据:')
            print(json.dumps(data, ensure_ascii=False, indent=2))
            
            if 'data' in data and 'progress_info' in data['data']:
                progress_info = data['data']['progress_info']
                print(f'\n进度表ID: {progress_info.get("id")}')
                print(f'当前状态: {progress_info.get("current_status")}')
                
            if 'data' in data and 'progress_items' in data['data']:
                items = data['data']['progress_items']
                print(f'\n进度项数量: {len(items)}')
                for item in items:
                    print(f'  - ID: {item.get("id")}, 标题: {item.get("title")}, 状态: {item.get("status")}')
            else:
                print('未找到进度项数据')
        else:
            print(f'API请求失败: {response.text}')
    except Exception as e:
        print(f'请求API时出错: {e}')
        print('请确保后端服务正在运行（端口5001）')

if __name__ == "__main__":
    test_api()