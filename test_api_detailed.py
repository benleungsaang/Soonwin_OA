import requests
import json

def test_api_detailed():
    url = 'http://localhost:5001/api/orders/3/progress'
    response = requests.get(url)
    data = response.json()

    print('API响应:')
    print(json.dumps(data, ensure_ascii=False, indent=2))

    if 'data' in data and 'progress_items' in data['data']:
        items = data['data']['progress_items']
        print(f'\n进度项数量: {len(items)}')
        for item in items:
            print(f"  - ID: {item.get('id')}, 标题: {item.get('title')}, 状态: {item.get('status')}")
        
    if 'data' in data and 'progress_info' in data['data']:
        progress_info = data['data']['progress_info']
        print(f"\n进度表ID: {progress_info.get('id')}")
        print(f"当前状态: {progress_info.get('current_status')}")

if __name__ == "__main__":
    test_api_detailed()