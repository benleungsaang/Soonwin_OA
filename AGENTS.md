# Soonwin OA 系统智能代理指南

## 项目概述

Soonwin OA 是一个基于前后端分离架构的企业办公自动化系统，包含完整的员工管理、考勤管理、费用管理、询价管理、设备管理、订单管理等功能模块。

### 技术栈

**前端 (soonwin-oa-VUE-FrontEnd):**
- Vue 3 (Composition API)
- TypeScript
- Element Plus UI 组件库
- Vite 构建工具
- Pinia 状态管理
- Vue Router 路由管理
- 按需加载配置 (AutoImport + Components + ElementPlusResolver)
- 包体积分析 (rollup-plugin-visualizer)

**后端 (soonwin-os-Python-Server):**
- Python 3.12
- Flask Web 框架
- SQLAlchemy ORM
- SQLite 数据库
- Alembic 数据库迁移

## 构建和优化配置

### 按需加载配置
项目已配置 Element Plus 按需加载功能，通过以下配置实现：

**vite.config.ts 配置：**
- AutoImport: 自动导入 Vue 相关 API（如 ref、reactive、onMounted 等）以及 Element Plus API（如 ElMessage）
- Components: 自动导入组件（包括 Element Plus 组件）
- ElementPlusResolver: 自动识别并导入 Element Plus 组件
- 生成类型声明文件（auto-imports.d.ts 和 components.d.ts）

**TypeScript 配置：**
- 更新 tsconfig.json 以包含自动生成的类型文件

### 包体积分析配置
项目已配置 rollup-plugin-visualizer 进行包体积分析：

**vite.config.ts 配置：**
- 生成分析报告文件 (dist/stats.html)
- 分析模式：treemap（树形图）
- 开启 gzip 和 brotli 体积分析
- 打包完成后自动打开报告页面
- 优化打包分包策略（element-plus、vue、pdfjs 等独立分包）

## 项目架构

### 前端目录结构
```
soonwin-oa-VUE-FrontEnd/
├── src/
│   ├── components/       # 可复用组件
│   ├── views/           # 页面视图组件
│   ├── api/             # API 请求封装
│   ├── utils/           # 工具函数
│   ├── stores/          # Pinia 状态管理
│   ├── router/          # 路由配置
│   └── assets/          # 静态资源
├── public/              # 静态资源
├── package.json         # 项目依赖配置
└── vite.config.ts       # Vite 构建配置
```

### 后端目录结构
```
soonwin-os-Python-Server/
├── app/
│   ├── models/          # 数据模型
│   ├── routes/          # API 路由
│   └── utils/           # 工具函数
├── migrations/          # 数据库迁移脚本
├── assets/              # 文件存储目录
├── requirements.txt     # Python 依赖
└── run.py               # 应用启动文件
```

## 核心功能模块

### 1. 员工管理 (Employee Management)
- 员工信息维护
- 权限管理 (管理员/普通员工)
- 登录认证

### 2. 考勤管理 (Attendance System)
- 考勤申请 (请假、加班、外出等)
- 审批流程管理
- 考勤记录查询

### 3. 费用管理 (Expense Management)
- 费用申请与审批
- 按年份统计
- 收支分类管理

### 4. 询价管理 (Inquiry Management)
- 客户询价单管理
- 沟通记录跟踪
- 附件管理

### 5. 设备管理 (Machine Management)
- 设备信息维护
- 设备图片上传与缩略图生成
- 设备参数管理
- ErrorFallbackImage 组件：支持图片加载失败时的降级处理

### 6. 报价管理 (Quotation Management)
- 报价单创建与管理
- 设备购物车功能
- 报价单预览与导出
- ErrorFallbackImage 组件：在设备缩略图中使用

### 7. 订单管理 (Order Management)
- 订单状态跟踪
- 订单统计报表
- 订单流程管理


### 应用位置
- QuotationManagementView.vue
- QuotationTempPreview.vue
- 以及其他需要图片加载错误处理的组件

## 开发环境配置

### 前端启动
```bash
cd soonwin-oa-VUE-FrontEnd
npm install
npm run dev
```

### 后端启动
```bash
cd soonwin-os-Python-Server
pip install -r requirements.txt
python run.py
```

### 构建生产版本
```bash
# 前端构建（支持按需加载和包体积分析）
cd soonwin-oa-VUE-FrontEnd
npm run build

# 后端部署
cd soonwin-os-Python-Server
# 配置生产环境参数
```

## 代码规范

### 前端规范
- 使用 TypeScript 进行类型检查
- 遵循 Vue 3 Composition API 模式
- 使用 Element Plus 组件库进行 UI 开发
- 使用 ESLint 和 Prettier 进行代码格式化
- 实现按需加载以优化包体积
- 使用 ErrorFallbackImage 组件处理图片加载失败

### 后端规范
- 使用 Flask 作为 Web 框架
- 使用 SQLAlchemy 进行数据库操作
- 使用 Alembic 进行数据库迁移
- 遵循 RESTful API 设计原则

## 数据库模型

### 主要模型
- **Employee**: 员工信息模型
- **AttendanceOperation**: 考勤操作模型
- **Expense**: 费用信息模型
- **Inquiry**: 询价单模型
- **Machine**: 设备信息模型
- **Order**: 订单信息模型

## API 接口

### 主要 API 端点
- `/api/auth` - 认证相关接口
- `/api/employees` - 员工管理接口
- `/api/attendance` - 考勤管理接口
- `/api/expenses` - 费用管理接口
- `/api/inquiries` - 询价管理接口
- `/api/machines` - 设备管理接口
- `/api/orders` - 订单管理接口

## 部署说明

### 生产环境部署
1. 确保服务器已安装 Python 3.12 和 Node.js
2. 配置后端环境变量
3. 构建前端静态文件（包含按需加载优化）
4. 配置 Nginx 反向代理
5. 使用 Gunicorn 或其他 WSGI 服务器部署后端

### 环境变量配置
- `FLASK_ENV` - 环境模式 (development/production)
- `DATABASE_URL` - 数据库连接字符串
- `SECRET_KEY` - 应用密钥

## 维护说明

- 定期备份数据库
- 监控服务器资源使用情况
- 定期更新依赖包
- 检查安全漏洞
- 使用包体积分析工具监控前端性能

## 个人添加情况说明

- 生产服务器IP为：http://192.168.30.64/，前端端口5183，后端端口5000
- 开发服务器IP为：http://192.168.110.13/
- 开发项目前端项目位置@soonwin-oa-VUE-FrontEnd，开发端口 5173，模拟生产端口5183
- 开发项目后端项目位置@soonwin-os-Python-Server，开发端口 5001，模拟生产端口5000

- 模型文件夹 ./app/models
- 路由文件夹 ./app/routes
- 当前的数据库文件 ./soonwin-os-Python-Server/soonwin_oa_dev.db


- 提醒：
- 1、前端 request.ts 自动解包响应为 res.data，使用response = await request时需注意；DELETE/PUT 请求成功后可能返回 undefined / 空对象（无 data 字段），不修改 request.ts 解包逻辑，适配该机制即可；
- 2、后端数据库模型 / 字段变更后，完成数据迁移并生效再执行后续操作；
- 3、前端代码符合 TypeScript 规范，修改后不执行 Validate with frontend-tester；
- 4、页面常规按钮（添加 / 删除 / 修改 / 查询等）用图标按钮，同级多按钮时图标 + 简短文字（如<el-icon><Search /></el-icon>）；
- 5、测试前端的测试服务使用后及时关闭，不占用 5173 端口；
- 6、Python 测试脚本使用后立即删除；
- 7、实现前端功能可新建布局，未经要求不修改原有布局 / 样式；
- 8、创建变量 / 方法 / 函数前，先确认当前文件无重复定义；
- 9、处理前后端错误时，先在预估代码位置加前端 console.log/ 后端 print 调试监控，再精准修改；
- 10、错误处理优先用 try-catch 捕获异常，而非依赖响应内容判断成功状态。
- 11、设计功能时需适配前后端代码、数据格式，前端方法需按后端返回数据格式设计。

- 注意每次回复我都在结尾加“领导，处理好了，请注意查收！”

---

**注意**: 本系统为持续开发项目，功能和架构可能会随时间演变。建议在开发前查看最新的代码和文档。