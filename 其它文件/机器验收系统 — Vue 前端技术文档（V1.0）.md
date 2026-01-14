# 📄 机器验收系统 — Vue 前端技术文档（V1.0）

## 一、系统概述

本系统为公司内部 OA 子模块，用于对设备/机器进行结构化验收。验收人员通过选择预设或自定义的验收模板，逐项填写状态（正常 / 不正常 / 没此项），并上传图片及文字说明，最终生成可存档的验收报告。

- **部署环境**：公司内网
- **后端技术栈**：Python + Flask + SQLite3
- **前端技术栈**：Vue 3 + Vite + TypeScript（可选）+ Element Plus
- **认证方式**：身份证号 + TOTP（时间一次性密码）登录，JWT 令牌鉴权

---

## 二、核心功能模块

### 1. 用户认证模块
- 身份证号 + TOTP 登录
- JWT 自动续期（Axios 拦截器处理）
- 登出清除本地 Token

### 2. 验收模板管理（仅管理员）
- 创建/编辑/删除验收模板
- 每个模板包含多个“验收项”
- 验收项字段：
  - `title`（字符串，必填）：如“急停按钮功能是否正常”

> ⚠️ 注意：不按“区域”分组（简化 MVP），所有验收项平铺；后续可扩展分组。

### 3. 验收任务执行（普通用户）
- 选择一台机器（可手动输入编号或下拉选择）
- 选择一个验收模板
- 逐项操作：
  - 状态三选一：✅ 正常 / ❌ 不正常 / ⚪ 没此项
  - 若选“正常”：可上传 1~N 张图片（留档）
  - 若选“不正常”：必须上传 ≥1 张图片 + 必填文字说明
  - 若选“没此项”：无需操作
- 实时保存草稿（防刷新丢失）
- 提交后锁定，不可再编辑

### 4. 报告生成与查看
- 提交后自动生成 HTML 预览页
- 支持导出 PDF（使用 `html2canvas` + `jsPDF`）
- 报告内容包括：
  - 机器编号、验收人、时间
  - 每项状态、图片、说明
  - 整体结论（自动判断：若无“不正常”则通过）

### 5. 历史记录查询
- 按机器编号、日期范围、验收人筛选
- 点击可查看/下载历史报告

---

## 三、关键数据模型（前端视角）

### 验收项定义（CheckItem）
```ts
interface CheckItem {
  id: string;           // 唯一ID（UUID）
  title: string;        // 验收项标题
}
```

### 验收结果（InspectionResult）
```ts
interface InspectionResult {
  itemId: string;
  status: 'normal' | 'abnormal' | 'not_applicable'; // 正常/不正常/没此项
  photos: string[];     // 图片URL数组（相对路径或base64）
  comment: string;      // 仅当 status === 'abnormal' 时必填
}
```

### 验收记录（InspectionRecord）
```ts
interface InspectionRecord {
  id: string;
  machineId: string;    // 机器编号
  templateId: string;
  inspectorName: string;
  timestamp: string;    // ISO8601
  results: Record<string, InspectionResult>; // key: itemId
  status: 'draft' | 'submitted';
}
```

---

## 四、前端技术架构

### 项目初始化
```bash
npm create vue@3
# 选择：TypeScript (推荐), JSX, ESLint, Prettier
npm install element-plus axios html2canvas jspdf
```

### 目录结构建议
```
src/
├── api/               # API 封装（axios）
├── assets/            # 静态资源
├── components/        # 通用组件
│   └── InspectionItem.vue  # 单个验收项组件（含状态选择+图片上传）
├── views/
│   ├── Login.vue
│   ├── TemplateList.vue
│   ├── InspectionForm.vue   # 核心：验收表单页
│   └── ReportView.vue       # 报告预览+导出
├── router/
├── store/             # 可用 Pinia 管理草稿状态
├── utils/
│   └── auth.ts        # JWT 存储与拦截器
└── App.vue
```

### 关键组件说明

#### `InspectionItem.vue`
- Props: `item: CheckItem`, `value: InspectionResult`
- Emits: `update:value`
- 内部：
  - 使用 `el-radio-group` 三选项
  - 动态显示：
    - “正常” → 图片上传区（非必填）
    - “不正常” → 图片上传（必填）+ `el-input` 文字说明（必填）
    - “没此项” → 隐藏其他控件
  - 图片上传使用 `el-upload`，支持拍照（`capture="environment"`）

#### `InspectionForm.vue`
- 加载模板 → 渲染所有 `InspectionItem`
- 使用 `Pinia` 或 `reactive` 保存草稿（`localStorage` 同步）
- 提交前校验：所有“不正常”项必须有图+说明
- 提交后跳转到 `ReportView`

---

## 五、UI 原型草图（文字版）

### 页面1：登录页（Login.vue）
```
[ 公司Logo ]
机器验收系统

身份证号： [_____________] （数字键盘）
TOTP验证码： [______] （6位数字）

[ 登录按钮 ]
```

### 页面2：验收表单页（InspectionForm.vue）
```
顶部栏：
  机器编号：[ M-CNC-2025 ]（只读）
  验收人：张工 | 时间：2026-01-12 11:00

验收项列表（滚动区域）：
----------------------------------------
✅ 急停按钮功能是否正常？
  ○ 正常   ● 不正常   ○ 没此项
  [上传图片]（最多5张）
  问题描述：[_________________________]
----------------------------------------
✅ 液压管路有无泄漏？
  ● 正常   ○ 不正常   ○ 没此项
  [已上传 2 张图片] 👁️
----------------------------------------

底部操作栏：
[ 保存草稿 ]       [ 提交验收 ]
（提交前校验完整性）
```

### 页面3：报告预览页（ReportView.vue）
```
【机器验收报告】

机器编号：M-CNC-2025
验收人：张工
时间：2026-01-12 11:05

验收结果：
- 急停按钮功能是否正常？ → 不正常
  问题：按钮卡滞
  [图片缩略图 x2]

- 液压管路有无泄漏？ → 正常
  [图片缩略图 x2]

结论：❌ 未通过（存在异常项）

[ 下载PDF ]   [ 返回列表 ]
```

---

## 六、MVP 最小可行版本功能清单 ✅

| 模块 | 功能 | 是否包含 |
|------|------|--------|
| 认证 | 身份证 + TOTP 登录，JWT 存储 | ✅ |
| 模板 | 管理员可创建简单模板（仅标题列表） | ✅ |
| 表单 | 用户选择模板后逐项填写三态 + 图片/文字 | ✅ |
| 图片 | 支持上传 JPG/PNG，前端压缩（ MVP 开发周期建议：2~3 周（1名前端 + 1名后端）

---

## 七、API 接口约定（简版，供前后端联调）

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/auth/login` | POST | {id_card, totp} → {token, user} |
| `/api/templates` | GET | 获取模板列表 |
| `/api/templates` | POST | 创建新模板 |
| `/api/inspections/draft` | GET | 获取当前用户草稿 |
| `/api/inspections` | POST | 提交新验收记录 |
| `/api/inspections/{id}` | GET | 获取验收详情（用于报告） |
| `/api/upload` | POST (multipart) | 上传图片 → 返回 URL |