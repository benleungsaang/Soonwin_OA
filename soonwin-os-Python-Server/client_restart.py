"""OA 远程重启客户端 - 从本地发送重启命令到服务器"""
import urllib.request
import json

SERVER_URL = "http://192.168.30.64:5183/api/admin/restart"
SECRET_KEY = "SoonwinOA_Restart_Key_2026"

data = json.dumps({"key": SECRET_KEY, "cmd": "restart"}).encode("utf-8")
req = urllib.request.Request(SERVER_URL, data=data, headers={"Content-Type": "application/json"},
                              method="POST")
try:
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read())
    print(f"服务器响应: {result}")
except Exception as e:
    print(f"请求失败: {e}")
