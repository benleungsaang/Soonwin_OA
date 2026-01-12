# 第2阶段NFC打卡模块开发文档

## 1. 开发任务完成情况

### 1.1 后端打卡接口开发
- 实现了IP/MAC获取功能：通过`arp -a`命令获取设备MAC地址
- 实现了内网IP校验功能，只允许192.168.x.x、10.x.x.x、172.x.x.x网段访问
- 实现了员工匹配逻辑，优先匹配MAC地址，其次匹配IP地址
- 实现了首次打卡时自动创建临时员工记录的功能
- 实现了打卡类型判断（6:00-12:00为上班打卡，12:00-22:00为下班打卡）
- 实现了30分钟内的重复打卡限制功能
- 实现了打卡记录存储到数据库的功能

### 1.2 前端打卡成功页面
- 确认前端打卡成功页(PunchSuccessView.vue)已存在并正确显示员工姓名、打卡类型和打卡时间

### 1.3 重定向配置
- 实现了后端到前端开发服务器(5173端口)的重定向功能
- 在测试阶段，后端会重定向到前端开发服务器的打卡成功页面

### 1.4 NFC贴纸地址配置
- 配置了NFC贴纸地址为`http://192.168.31.15:5000/punch`（普通地址）

### 1.5 异常场景测试
- 外网访问测试：正确返回403错误，提示"非公司内网设备，禁止打卡！"
- 重复打卡测试：30分钟内重复打卡被正确拒绝
- 未绑定设备测试：首次访问时自动创建临时员工记录并允许打卡

## 2. 文件创建与修改

### 2.1 创建的文件：

#### 后端路由文件：
- `E:\Soonwin_OA\soonwin-os-Python-Server\app\routes\punch_routes.py` - 打卡接口路由实现
- `E:\Soonwin_OA\soonwin-os-Python-Server\app\routes\__init__.py` - 路由初始化文件

#### 测试脚本文件：
- `E:\Soonwin_OA\soonwin-os-Python-Server\init_db.py` - 数据库初始化脚本
- `E:\Soonwin_OA\soonwin-os-Python-Server\test_punch.py` - 打卡功能测试脚本
- `E:\Soonwin_OA\soonwin-os-Python-Server\check_records.py` - 检查打卡记录脚本
- `E:\Soonwin_OA\soonwin-os-Python-Server\test_exceptions.py` - 异常场景测试脚本
- `E:\Soonwin_OA\soonwin-os-Python-Server\test_duplicate.py` - 重复打卡测试脚本
- `E:\Soonwin_OA\soonwin-os-Python-Server\clear_records.py` - 清空记录脚本
- `E:\Soonwin_OA\soonwin-os-Python-Server\test_unbound.py` - 未绑定设备测试脚本

### 2.2 修改的文件：
- `E:\Soonwin_OA\soonwin-os-Python-Server\app\__init__.py` - 注册新的路由蓝图
- `E:\Soonwin_OA\soonwin-os-Python-Server\app\routes\punch_routes.py` - 更新IP获取逻辑

## 3. 打卡完整流程路径

### 3.1 流程详解：
1. **触发点**：用户使用手机NFC贴纸，跳转到 `http://192.168.31.15:5000/punch`
2. **后端路由**：`E:\Soonwin_OA\soonwin-os-Python-Server\app\routes\punch_routes.py` 中的 `punch()` 函数处理
3. **IP获取**：从 `request.headers.get('X-Forwarded-For')` 获取真实IP，或使用 `request.remote_addr`
4. **内网验证**：`is_inner_net()` 函数验证是否为内网IP（192.168.31.15 属于内网）
5. **MAC获取**：`get_mac_by_ip()` 函数通过 `arp -a` 命令获取设备MAC地址
6. **员工匹配**：
   - 先按 `phone_mac` 字段匹配
   - 若未找到，按 `inner_ip` 字段匹配
   - 若都未找到，创建临时员工记录
7. **打卡时间判断**：根据当前小时判断打卡类型（6-12点为上班，12-22点为下班）
8. **重复打卡检查**：检查30分钟内是否有相同类型打卡记录
9. **数据存储**：创建 `PunchRecord` 记录并保存到数据库
10. **重定向前端**：返回302重定向到 `http://192.168.31.15:5173/punch-success?name=...&emp_id=...&punch_type=...&punch_time=...`
11. **前端展示**：`E:\Soonwin_OA\soonwin-oa-VUE-FrontEnd\src\views\PunchSuccessView.vue` 解析URL参数并显示打卡信息

### 3.2 参数传递路径：
- 后端 `punch()` 函数 → 生成重定向URL → 前端 `PunchSuccessView.vue` 解析URL参数
- 传递参数：`name`（员工姓名）、`emp_id`（员工工号）、`punch_type`（打卡类型）、`punch_time`（打卡时间）

### 3.3 端口确认：
- 后端服务运行在 `192.168.31.15:5000` 端口
- 前端开发服务器运行在 `localhost:5173` 端口
- 打卡接口路径：`http://192.168.31.15:5000/punch`
- 重定向路径：`http://192.168.31.15:5173/punch-success`
- 所有参数都通过URL查询字符串传递，确保前端能够正确接收和显示打卡信息

## 4. 测试方法

### 4.1 启动服务测试：
1. 启动后端：`cd "E:\Soonwin_OA\soonwin-os-Python-Server"; python run.py`
2. 启动前端：`cd "E:\Soonwin_OA\soonwin-oa-VUE-FrontEnd"; npm run dev`
3. NFC打卡测试：在手机上使用NFC标签访问 `http://192.168.31.15:5000/punch`

### 4.2 API测试：
1. 内网打卡（模拟）：`curl -H "X-Forwarded-For: 192.168.31.100" http://192.168.31.15:5000/punch`
2. 外网访问测试：`curl -H "X-Forwarded-For: 8.8.8.8" http://192.168.31.15:5000/punch`
3. 检查打卡记录：`cd "E:\Soonwin_OA\soonwin-os-Python-Server"; python check_records.py`

### 4.3 功能验证：
- 内网打卡功能测试通过
- 异常场景测试通过（外网访问、重复打卡）
- 打卡记录正确存储到数据库验证通过

## 5. 功能特点

1. **安全性**：只允许内网设备打卡，有效防止外网访问
2. **灵活性**：首次打卡时自动创建临时员工记录，后续由管理员绑定
3. **防重复**：30分钟内的重复打卡被限制
4. **测试友好**：在开发阶段自动重定向到前端开发服务器
5. **数据完整性**：打卡记录包含完整的员工信息、时间和设备信息

## 6. 数据库记录

打卡记录存储在 `PunchRecord` 表中，包含以下字段：
- id: 自增主键
- emp_id: 员工工号
- name: 员工姓名
- punch_type: 打卡类型（上班/下班）
- punch_time: 打卡时间
- inner_ip: 打卡设备IP
- phone_mac: 打卡设备MAC地址

## 7. 验证结果

所有功能已按要求实现并经过测试，系统可以正常运行。在测试阶段，当用户使用NFC标签打卡时，系统会验证设备为内网IP，获取MAC地址，检查是否为重复打卡，然后将打卡记录存储到数据库，并重定向到前端的打卡成功页面显示相关信息。