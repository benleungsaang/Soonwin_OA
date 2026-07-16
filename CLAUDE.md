# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Soonwin OA 是一个基于前后端分离架构的企业办公自动化系统，包含员工管理、考勤管理、费用管理、询价管理、设备管理、订单管理等功能模块。

### 技术栈

**前端 (soonwin-oa-VUE-FrontEnd):**
- Vue 3 (Composition API) + TypeScript
- Element Plus UI
- Vite (使用 rolldown-vite)
- Pinia 状态管理
- Vue Router

**后端 (soonwin-os-Python-Server):**
- Python 3.12 + Flask
- SQLAlchemy ORM
- SQLite 数据库
- Alembic 数据库迁移

---

## 常用命令

### 前端

```bash
cd soonwin-oa-VUE-FrontEnd
npm install          # 安装依赖
npm run dev         # 开发模式启动 (端口 5173)
npm run serve:prod  # 生产模式启动 (端口 5183)
npm run build       # 构建生产版本
```

### 后端

```bash
cd soonwin-os-Python-Server
pip install -r requirements.txt   # 安装依赖
python run.py                    # 启动开发服务器 (端口 5001)
python run.py --port 5000        # 启动生产服务器 (端口 5000)
```

### 数据库迁移

```bash
cd soonwin-os-Python-Server
flask db migrate -m "migration message"  # 创建迁移
flask db upgrade                          # 执行迁移
```

**⚠️ 重要：数据库文件区分**

| 环境 | 数据库文件 | 端口 |
|------|-----------|------|
| 开发环境 | `soonwin_oa_dev.db` | 5001 |
| 生产环境 | `soonwin_oa.db` | 5000 |

执行数据库迁移或直接修改表结构前，**必须确认当前使用的是哪个数据库**：
- 开发时连接：`python run.py` → 端口 5001 → 使用 `soonwin_oa_dev.db`
- 生产时连接：`python run.py --port 5000` → 端口 5000 → 使用 `soonwin_oa.db`

使用 sqlite3 直接修改表结构时，命令示例：
```bash
# 开发数据库
sqlite3 soonwin_oa_dev.db "ALTER TABLE xxx ADD COLUMN yyy ..."

# 生产数据库
sqlite3 soonwin_oa.db "ALTER TABLE xxx ADD COLUMN yyy ..."
```

---

## 架构说明

### 前端目录结构

```
soonwin-oa-VUE-FrontEnd/src/
├── api/          # API 请求封装 (基于 axios)
├── components/   # 可复用组件
├── views/        # 页面视图组件
├── stores/       # Pinia 状态管理
├── router/       # 路由配置
├── utils/        # 工具函数
└── types/        # TypeScript 类型定义
```

### 后端目录结构

```
soonwin-os-Python-Server/
├── app/
│   ├── models/   # SQLAlchemy 数据模型
│   ├── routes/  # Flask 路由/API 端点
│   └── utils/   # 工具函数
├── migrations/   # Alembic 数据库迁移脚本
├── assets/       # 文件存储目录
└── run.py        # 应用启动入口
```

### 核心 API 端点

| 模块 | 路由文件 | 主要功能 |
|------|----------|----------|
| 员工管理 | user_routes.py | 员工CRUD、登录认证 |
| 考勤管理 | attendance_routes.py, punch_routes.py | 考勤申请、审批、打卡 |
| 费用管理 | expense_routes.py | 费用申请与统计 |
| 询价管理 | inquiry_routes.py | 询价单、沟通记录 |
| 设备管理 | machine_routes.py | 设备信息、图片上传 |
| 订单管理 | order_routes.py, order_status_routes.py | 订单、状态跟踪 |
| 媒体管理 | photo_routes.py, video_routes.py | 图片、视频文件管理 |

---

## 开发注意事项

### 数据库变更流程
后端数据库模型/字段变更后，必须执行数据库迁移并生效后再继续其他操作。

### 前端请求封装
`request.ts` 自动解包响应为 `res.data`。使用 `response = await request` 时需注意这点。DELETE/PUT 请求成功后可能返回 undefined/空对象（无 data 字段）。

### 错误处理
处理前后端错误时，先在预估代码位置加 `console.log`（前端）或 `print`（后端）调试监控，再精准修改。优先用 try-catch 捕获异常，而非依赖响应内容判断成功状态。

### 前端开发规范
- 使用 TypeScript 进行类型检查
- 页面常规按钮（添加/删除/修改/查询等）用图标按钮，同级多按钮时图标+简短文字
- 实现前端功能可新建布局，未经要求不修改原有布局/样式
- 创建变量/方法/函数前，先确认当前文件无重复定义

### 输入框组件标准（RichInput）

新模块需要输入框（文本 + emoji + 图片上传 + 粘贴检测）时，**优先使用** `src/components/RichInput.vue`，而非重新实现。

⚠️ **触发规则**：用户说"开发带输入框的模块"或类似表述时（即使未提 emoji/图片），必须主动询问：
1. 是否使用 RichInput 通用组件？
2. 需要启用哪些功能（emoji？图片上传？粘贴检测？）
3. 图片存储路径是什么？

```vue
<RichInput v-model="note" :features="{ emoji: true, image: true, paste: true }"
  :upload="{ api: myUploadApi }" />
```

- `features: { emoji?, image?, paste? }` — 选配功能
- `upload: { api: (file) => Promise<{url, thumbnailUrl?}>, maxSizeMB?, accept? }` — 上传函数由各模块注入（控制存储路径）
- `size: 'small' | 'default'`、`toolbar: 'none' | 'bottom'`、`customClass`
- Events: `@image-uploaded`, `@emoji-select`, `@paste-image`, `@image-error`
- Expose: `focus, blur, reset, triggerImageUpload, getImageUrl`
- 完整文档见 `src/components/RichInput.md`

### 新增功能模块时的权限配置

⚠️ 新增路由权限需同步修改 3 个文件（代码中搜索 `同步修改清单` 找具体位置）：
1. `app/constants/simple_permission_constants.py` → 常量 + ALL_ROUTES
2. `app/routes/user_routes.py` → route_labels 中文名（最容易遗漏！）
3. `src/utils/authUtils.ts` → RouteName 类型

详见 [[permission-setup-checklist]]

### Tailwind CSS 注意

⚠️ 本项目使用 Element Plus，`tailwind.config.js` 必须保持 `preflight: false`。核心布局用 scoped CSS，勿依赖 Tailwind 工具类。详见 [[tailwind-element-plus-conflict]]

### 服务器配置
- 开发服务器: `http://192.168.110.13/`，前端端口 5173，后端端口 5001
- 生产服务器: `http://192.168.30.64/`，前端端口 5183，后端端口 5000
- 开发数据库: `soonwin_oa_dev.db` (端口 5001)
- 生产数据库: `soonwin_oa.db` (端口 5000)
