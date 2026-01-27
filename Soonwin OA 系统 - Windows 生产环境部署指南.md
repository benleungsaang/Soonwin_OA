# Soonwin OA 系统 - Windows 生产环境部署指南

## 1. 系统要求

### 1.1 硬件要求

- 操作系统：Windows 7/10/11 (推荐 Windows 10/11)
- 内存：至少 4GB RAM（前后端同时运行建议8GB）
- 存储：至少 5GB 可用空间（包含数据库和上传文件）
- 网络：可访问外部网络（用于安装依赖包）

### 1.2 软件要求

- Python 版本：3.8 - 3.12（推荐 Python 3.10 或 3.11）
- Node.js 版本：16.x 或更高版本（用于前端构建）
- npm 或 yarn 包管理器
- pip 包管理器（随 Python 自动安装）
- Git（可选，用于版本控制）

## 2. 部署前准备

### 2.1 前端静态文件构建

在开发环境中，进入前端目录并构建静态文件：

```cmd
cd E:\Soonwin_OA\soonwin-oa-VUE-FrontEnd
yarn 本地安装依赖
yarn build:prod 生成静态文件给nginx使用
```

### 2.2 后端部署包准备

将从开发环境同步的 "OA后端迁移包" 复制到生产服务器，包含以下目录和文件：

1. 后端源代码和依赖
2. 配置文件
3. 数据库文件
4. 构建好的前端静态文件（从 `dist` 目录复制）

### 2.3 部署目录结构

部署后应包含以下目录和文件：

```
OA_System/
├── run.py              # 主程序入口
├── config.py           # 配置文件
├── extensions.py       # Flask扩展配置
├── requirements.txt    # 依赖包列表
├── alembic.ini         # 数据库迁移配置
│   └── ...
├── app/                # 应用核心代码
│   ├── __init__.py
│   ├── models/         # 数据模型
│   ├── routes/         # 路由定义
│   └── utils/          # 工具函数
├── migrations/         # 数据库迁移文件
├── assets/             # 上传文件存储
├── instance/           # 数据库文件
└── other/              # 工具脚本
```

## 3. 环境配置

### 3.1 创建虚拟环境

打开命令行，进入项目目录，执行以下命令创建虚拟环境：

```cmd
cd C:\OA_System
python -m venv venv
```

### 3.2 激活虚拟环境

```cmd
venv\Scripts\activate
```

### 3.3 安装依赖包

在激活虚拟环境后，安装项目所需依赖：

```cmd
pip install -r requirements.txt
```

或者逐个安装：

```cmd
pip install alembic==1.18.0
pip install Flask==3.1.2
pip install flask_cors==6.0.2
pip install flask_migrate==4.1.0
pip install flask_sqlalchemy==3.1.1
pip install PyJWT==2.10.1
pip install pyotp==2.9.0
pip install requests==2.32.5
pip install SQLAlchemy==2.0.45
```

## 4. 数据库配置与初始化

### 4.1 数据库初始化

如果使用新的数据库，需要执行以下步骤：

1. **创建数据库文件**（如果不存在）
   - 系统会自动在 `instance/` 目录下创建 `soonwin_oa.db` 文件

2. **执行数据库迁移**（如果已有数据库结构）

   ```bash
   python -m flask db upgrade
   ```

   或者使用项目自带的迁移功能：

   ```bash
   python run.py
   ```

### 4.2 数据库备份与恢复

- **备份位置**：`instance/oa_system.db.backup`
- **恢复方法**：将备份文件复制为 `instance/soonwin_oa.db`

## 5. 安全配置

### 5.1 修改JWT密钥

在 `config.py` 中修改JWT密钥：

```python
JWT_SECRET_KEY = "请在此处设置一个复杂且唯一的密钥"
```

建议使用随机字符串生成器创建一个强密钥。

### 5.2 调试模式设置

确保在生产环境中禁用调试模式：

```python
DEBUG = False
```

## 6. 启动服务

### 6.1 命令行启动

在虚拟环境激活状态下，运行：

```cmd
python run.py
```

### 6.2 指定端口启动

默认端口为 5000，可通过 --port 参数指定：

```cmd
python run.py --port 8080
```

### 6.3 生产环境启动（推荐）

对于生产环境，建议使用生产级WSGI服务器，如waitress：

```cmd
# 安装 waitress
pip install waitress

# 启动服务
waitress-serve --host=0.0.0.0 --port=5000 wsgi:application
```

## 7. 访问系统

### 7.1 本地访问

- 默认地址：http://localhost:5000
- 局域网访问：http://[服务器IP]:5000

## 8. 部署后配置注意事项

### 8.1 端口配置

检查 `config.py` 文件中的端口设置，确保没有与其他服务冲突：

- 默认后端端口：5000
- 可通过 `--port` 参数修改：`python run.py --port 8080`

### 8.2 路径配置

确认所有文件路径在目标环境中正确：

- 数据库文件路径
- 静态文件路径
- 上传文件路径（`assets` 目录）

### 8.3 环境变量配置

如需使用环境变量，可在项目根目录创建 `.env` 文件：

```env
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/soonwin_oa.db
```

### 8.4 前端与后端通信配置

如果前端需要通过特定路径访问后端API，请检查：

- API请求的基础URL
- 跨域设置（CORS）是否正确配置

## 9. 维护与更新

### 9.1 更新系统

1. 停止当前服务
2. 替换项目文件
3. 检查并安装新的依赖
4. 执行数据库迁移（如有必要）
5. 重启服务

### 9.2 日志管理

- 应用日志：在生产环境中，建议配置日志记录到文件

### 9.3 备份策略

- 数据库备份：定期备份 `instance/soonwin_oa.db`
- 配置文件备份：备份 `config.py` 等重要配置
- 上传文件备份：定期备份 `assets/` 目录

## 10. 故障排除

### 10.1 常见启动错误

- **端口被占用**：检查是否有其他进程使用相同端口
- **依赖包缺失**：重新执行 `pip install -r requirements.txt`
- **数据库连接错误**：检查数据库文件路径和权限

### 10.2 性能优化

- 使用生产级 WSGI 服务器（如 Gunicorn）
- 配置数据库连接池
- 优化静态文件服务

## 11. 安全建议

- 定期更新 Python 和依赖包
- 使用防火墙限制访问端口
- 定期备份数据
- 定期审查日志文件
- 为敏感配置使用环境变量

---

**注意**：本指南适用于 Soonwin OA 系统的生产环境部署。在正式部署前，请在测试环境中验证所有步骤。

总步骤：
1、执行 pip install -r requirements.txt 生成requirements，复制 python基础文件；
2、yarn build:prod生成静态文件，供 nginx使用；
3、复制 启动服务器.bat，run_server.py；
4、根据 启动要求布置新位置的文件夹名，nginx 1.28.1等；
5、启动服务；

【 开发环境 】 目录结构

Soonwin_OA/
├── nginx-1.28.1 # 主程序入口
├── soonwin-oa-VUE-FrontEnd/ # 应用核心代码
│ ├── conf
│ ┼──
├── config.py # 配置文件
├── extensions.py # Flask扩展配置
├── requirements.txt # 依赖包列表
├── alembic.ini # 数据库迁移配置
│ └── ...
├── soonwin-oa-VUE-FrontEnd/ # 应用核心代码
│ ├── **init**.py
│ ├── models/ # 数据模型
│ ├── routes/ # 路由定义
│ └── utils/ # 工具函数
├── soonwin-os-Python-Server/ # 应用核心代码
├── migrations/ # 数据库迁移文件
├── assets/ # 上传文件存储
├── instance/ # 数据库文件
└── other/ # 工具脚本

【 生产环境 】 目录结构
