# Todo 模块抽取包

从 Todo_List 项目抽取出独立的 todo 模块，便于在另一个 Flask 项目中复用。

## 📦 目录结构

```
抽取文件/
├── README.md                       本文件
├── modules/
│   ├── __init__.py                 空文件，使 modules 成为 Python 包
│   ├── todo_api.py                 todo 蓝图（路由集合）
│   ├── database.py                 完整版 database（todo+cargo+posts，参考用）
│   └── database_todo_only.py       ⭐ 仅含 todo 表的精简版（推荐在新项目使用）
├── static/
│   └── index.html                  todo 前端页面（单文件，内联 CSS+JS）
├── requirements.txt                Flask >= 2.0
├── start.bat                       Windows 启动脚本（参考）
├── todo.html                       根目录旧版模板（仅作存档参考）
└── todolist_data.json              JSON 数据样本（测试导入/导出）
```

## 🚀 5 步集成到新 Flask 项目

### 步骤 1：复制文件
将 `抽取文件/` 整个文件夹（或选择性复制 `modules/` 和 `static/index.html`）复制到你的新项目。

假设新项目结构如下：

```
my_new_project/
├── server.py                       新项目入口
├── modules/                        ⬅ 复制到这里
│   ├── __init__.py
│   ├── todo_api.py
│   └── database_todo_only.py       ⬅ 重命名为 database.py
└── static/
    └── todo.html                   ⬅ 复制 index.html 并改名（避免冲突）
```

### 步骤 2：合并/重命名 database
如果你的新项目已经有 `modules/database.py`：

- 直接把 `database_todo_only.py` 里的 `todos` 和 `settings` 建表语句复制到你现有的 `init_db()` 里。
- 注意：`get_db_conn()` 上下文管理器建议保留下来，todo_api.py 依赖它。

如果新项目没有 database 模块，把 `database_todo_only.py` 重命名为 `database.py` 即可。

### 步骤 3：在 server.py 中注册蓝图

```python
from flask import Flask, send_from_directory
from modules.database import init_db          # 新项目如有 database，保持不变
from modules.todo_api import todo_bp          # 新增

app = Flask(__name__, static_folder='static')

init_db()                                       # 确保 todo 表被创建

# 注册 todo 蓝图
app.register_blueprint(todo_bp, url_prefix='/api/todos')

# 提供 todo 前端页面（路径可自定）
@app.route('/todo')
def todo_page():
    return send_from_directory('static', 'todo.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5123, debug=True)
```

### 步骤 4：安装依赖
```bash
pip install -r requirements.txt
# requirements.txt 内容：flask>=2.0
```

### 步骤 5：运行
```bash
python server.py
```
访问 `http://127.0.0.1:5123/todo` 即可使用。

---

## 🧩 API 接口清单（无需关心，已由蓝图自动挂载）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/todos` | 获取所有任务 |
| POST | `/api/todos` | 创建任务 |
| PUT | `/api/todos/<id>` | 更新任务 |
| DELETE | `/api/todos/<id>` | 删除任务 |
| POST | `/api/todos/reorder` | 重新排序 |
| GET | `/api/todos/export` | 导出 JSON |
| POST | `/api/todos/import` | 导入 JSON |
| POST | `/api/todos/save` | 整体保存（覆盖） |
| GET | `/api/todos/settings` | 读取设置 |
| PUT | `/api/todos/settings` | 写入设置 |

> 前端 `static/index.html` 内 `API_BASE = '/api/todos'`，如修改前缀需同步修改前端。

---

## ⚠️ 集成注意事项

1. **静态资源冲突**：若新项目已有 `static/index.html`，务必把抽取的 todo 前端改名（如 `todo.html`），否则会覆盖。
2. **数据库文件路径**：`database.py` 默认使用 `data/app.db`。如新项目数据库路径不同，需修改 `DATABASE` 常量。
3. **蓝图前缀**：若新项目 URL 前缀不能叫 `/api/todos`（已占用），修改 `server.py` 的 `url_prefix=` 即可；同时把 `static/index.html` 中的 `const API_BASE = '/api/todos'` 改为同一前缀。
4. **依赖**：todo 模块只依赖 Flask 自身 + SQLite（Python 标准库），无第三方依赖。
5. **静态文件目录**：Flask 实例化时必须传 `static_folder='static'`，否则 `send_from_directory` 会失败。

---

## 🧪 最小验证清单（复制完成后）

在新项目里跑通下面 4 步即视为集成成功：

```bash
# 1. 启动
python server.py

# 2. 健康检查（新项目有 /api/health 才行，没则跳过）
curl http://127.0.0.1:5123/api/health

# 3. 创建一条任务
curl -X POST http://127.0.0.1:5123/api/todos \
  -H "Content-Type: application/json" \
  -d '{"content":"测试 todo 抽取","color":"blue"}'

# 4. 列出任务
curl http://127.0.0.1:5123/api/todos

# 5. 浏览器访问 todo 页面
# http://127.0.0.1:5123/todo
```

如以上返回正常，集成完成。

---

## 📂 字段说明（todos 表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | 时间戳字符串 `str(timestamp*1000)` |
| content | TEXT | 任务正文 |
| completed | INTEGER | 0=未完成，1=完成 |
| color | TEXT | 背景色：white/red/yellow/green/blue/purple |
| date | TEXT | 所属日期 `YYYY-MM-DD` |
| note | TEXT | 备注 |
| created_at | TEXT | ISO 时间 |
| updated_at | TEXT | ISO 时间 |