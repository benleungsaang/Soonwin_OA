# RichInput 可组合输入框组件 — 设计规范

## 设计目标

各模块输入框（文本 + emoji + 图片上传 + 粘贴检测）统一为一个可组合组件，
通过 props 选配功能，各模块仅需注入上传函数和样式覆盖。

---

## 一、Props（输入参数）

```typescript
interface RichInputProps {
  // ========== v-model ==========
  modelValue: string

  // ========== 文本配置 ==========
  placeholder?: string          // 占位文字，默认 ''
  maxlength?: number            // 最大字符数，默认不限制
  rows?: number                 // textarea 行数，默认 3
  inputType?: 'input' | 'textarea'  // 输入框类型，默认 'textarea'
  readonly?: boolean            // 只读
  disabled?: boolean            // 禁用

  // ========== 功能选配 ==========
  features?: {
    emoji?: boolean     // 是否启用 emoji 按钮，默认 false
    image?: boolean     // 是否启用图片上传按钮，默认 false
    paste?: boolean     // 是否检测粘贴图片，默认 false
  }

  // ========== 图片上传配置（features.image 或 features.paste 为 true 时必填） ==========
  upload?: {
    api: UploadApi              // 上传函数（各模块注入，控制存储路径）
    maxSizeMB?: number          // 单文件大小限制，默认 5
    accept?: string             // 接受文件类型，默认 'image/*'
  }

  // ========== 样式适配 ==========
  size?: 'small' | 'default'    // 尺寸，默认 'default'
  toolbar?: 'none' | 'bottom'   // 工具栏位置，默认 'bottom'
  customClass?: string          // 附加 CSS class（业务层覆盖用）
}
```

---

## 二、标准化返回类型

```typescript
/** 上传函数签名——由各业务模块实现，控制存储路径 */
type UploadApi = (file: File) => Promise<UploadResult>

/** 上传结果——所有模块统一返回格式 */
interface UploadResult {
  url: string              // 图片访问 URL（必需）
  thumbnailUrl?: string    // 缩略图 URL（可选，用于列表预览）
  path?: string            // 文件存储相对路径（可选，调试用）
}
```

### ⚠️ 重要：uploadApi 必须返回完整可访问 URL

RichInput 的图片预览直接使用 `url` 作为 `<img src>`，因此 **必须返回浏览器可直接访问的完整路径**，而非后端内部相对路径。

```typescript
// ❌ 错误：相对路径，浏览器无法加载
const badApi: UploadApi = async (file) => {
  const res = await uploadImage(file)
  return { url: res.path }  // "todo/2026/07/xxx.webp"
}

// ✅ 正确：拼接完整 URL 前缀
const goodApi: UploadApi = async (file) => {
  const res = await uploadImage(file)
  const raw = res.image_url || res.data?.image_url
  return {
    url: '/assets/MyModule/' + raw,          // 完整可访问路径
    thumbnailUrl: raw.includes('_display')
      ? '/assets/MyModule/' + raw.replace('_display', '_thumbnail')
      : '/assets/MyModule/' + raw,
  }
}
```

### 各模块上传路径约定

不同模块的上传路径由 `UploadApi` 的实现控制：

```typescript
// Todo 模块 — 存储到 assets/TodoMedia/{sub_dir}/
const todoUploadApi: UploadApi = async (file) => {
  const res = await uploadTodoImage(file, 'todo')
  return {
    url: res.image_url,                      // todo/2026/07/xxx_display.webp
    thumbnailUrl: res.image_url?.replace(     // todo/2026/07/xxx_thumbnail.webp
      '_display.webp', '_thumbnail.webp'
    ),
  }
}

// 标记完成
const completeUploadApi: UploadApi = async (file) => {
  const res = await uploadTodoImage(file, 'completion')
  return { url: res.image_url }
}

// Blog 模块 — 存储到 assets/PostsMedia/{date}/
const blogUploadApi: UploadApi = async (file) => {
  const res = await uploadSingleFile(file)
  return {
    url: res.display_path,      // PostsMedia/2026/07/xxx_display.webp
    thumbnailUrl: res.thumbnail_path,
  }
}

// 订单模块 — 存储到 assets/OrderFiles/{order_id}/
const orderUploadApi: UploadApi = async (file) => {
  const res = await uploadOrderFile(file, orderId)
  return { url: res.path }
}

// 存储路径映射表（仅参考，实际由 UploadApi 决定）：
// ─────────────────────────────────
// Todo       → assets/TodoMedia/{sub_dir}/
// Blog       → assets/PostsMedia/{date}/
// Order      → assets/OrderFiles/{order_id}/
// Machine    → assets/MachinePhoto/{date}/
// Inquiry    → assets/InquiryFiles/{communication_id}/
```

---

## 三、Events（输出参数）

```typescript
// v-model
@update:modelValue(value: string)

// Emoji
@emoji-select(emoji: string)     // emoji 被选中时的 unicode

// Image
@image-uploaded(result: {        // 图片上传成功（url 已拿到）
  url: string
  thumbnailUrl?: string
})
@image-error(error: Error)       // 图片上传失败

// Paste
@paste-image(file: File)         // 检测到粘贴图片（父组件可接管处理）
```

---

## 四、Slots

```vue
<!-- 工具栏扩展区：在 emoji/image 图标之间插入自定义按钮 -->
<slot name="toolbar-extra" />

<!-- 图片预览条下方扩展 -->
<slot name="preview-extra" />
```

### toolbar-extra 插槽使用示例

各模块可在工具栏中插入自定义控件（与 RichInput 的 emoji/image 按钮并列）。

**Todo 创建任务 — 插入日期选择和颜色指示：**

```vue
<RichInput v-model="note" :features="{ emoji: true, image: true }"
  :upload="{ api: todoUploadApi }">
  <template #toolbar-extra>
    <input v-model="date" type="date" class="my-date-input" />
    <div class="my-color-chip"></div>
  </template>
</RichInput>
```

**渲染结果：**
```
[😊] [🖼️] [自定义按钮A]    ← toolbar-extra 插在 image 之后
           ↑ toolbar-extra 插槽
```

> **设计原则**：RichInput 只管理"文本输入 + emoji + 图片上传"核心功能。  
> 各模块的自定义工具栏项（日期选择、颜色选择、标签等）通过 `toolbar-extra` 插槽注入，  
> 两者互不干扰。

---

## 五、Expose（父组件可调用的方法）

```typescript
interface RichInputExpose {
  focus(): void
  blur(): void
  reset(): void                          // 清空文本和图片
  triggerImageUpload(): void             // 手动触发文件选择
}
```

---

## 六、内部架构

```
RichInput
├── template
│   ├── input / textarea  ← v-model
│   ├── toolbar（可选）
│   │   ├── emoji button（可选）
│   │   ├── image button（可选）
│   │   ├── <slot name="toolbar-extra" />  ️// 自定义控件插在 image 之后
│   │   └── emoji-picker 弹出层
│   └── image preview bar（可选）
│       ├── 图片缩略图
│       ├── "已上传" 标签
│       ├── 移除按钮
│       └── <slot name="preview-extra" />
│
├── script
│   ├── emoji: emoji-picker-element + 光标插入 + 外部点击关闭
│   ├── image: file input → uploadApi → preview bar
│   ├── paste: @paste → clipboardData.items → getAsFile → uploadApi
│   └── expose: focus, blur, reset, triggerImageUpload
│
└── style（scoped + 可覆盖）
    ├── 基础样式（尺寸、间距、颜色中性）
    └── customClass 支持业务覆盖
```

---

## 七、使用示例

### 示例 1：Todo 创建任务（全配）

```vue
<RichInput
  :key="'form-' + dialogVisible"  ️// ⚠️ 弹窗内必须用 :key 保证关闭后状态重置
  v-model="note"
  placeholder="备注内容…"
  :features="{ emoji: true, image: true, paste: true }"
  :upload="{ api: todoUploadApi }"
  size="default"
  toolbar="bottom"
  @image-uploaded="r => formImageUrl = r.url"  ️// r 是 { url, thumbnailUrl? }
/>
```

### 示例 2：评论区（仅 emoji）

```vue
<RichInput
  v-model="comment"
  placeholder="写评论…"
  input-type="input"
  :features="{ emoji: true }"
  size="small"
/>
```

### 示例 3：订单备注（仅粘贴图片）

```vue
<RichInput
  v-model="remark"
  placeholder="备注（支持 Ctrl+V 粘贴图片）"
  input-type="textarea"
  :features="{ paste: true }"
  :upload="{ api: orderUploadApi }"
  size="default"
/>
```

### 示例 4：Blog 发布（两阶段上传）

```vue
<RichInput
  v-model="content"
  placeholder="分享你的想法…"
  :features="{ emoji: true, image: true, paste: true }"
  :upload="{ api: blogUploadApi }"
  @image-uploaded="cacheUploadResult"
/>
```

---

## 九、落地注意事项（从 Todo 模块替换中总结）

### 1. 弹窗内必须加 :key

RichInput 内部维护 `imagePreviewUrl` 状态。弹窗关闭再打开时，若不加 `:key` 强制重建实例，上一次的图片预览会残留。

```vue
<!-- ✅ 弹窗内用法 -->
<RichInput :key="'form-' + dialogVisible" ... />
```

### 2. @image-uploaded 接收对象而非字符串

```vue
<!-- ✅ 正确 -->
@image-uploaded="r => formImageUrl = r.url"
<!-- r = { url: string, thumbnailUrl?: string } -->
```

### 3. 样式覆盖必须用 :deep()

RichInput 的样式是 `<style scoped>`，父组件不能直接写 `.ri-textarea`，必须：

```css
:deep(.custom-class .ri-textarea) { ... }
```

### 4. 上传 API 必须返回完整 URL

RichInput 预览直接用 `url` 作为 `<img src>`。相对路径会导致裂图。

```typescript
// ✅ 返回完整路径
return { url: '/assets/Module/' + raw }
```

### 5. 水平布局不适用

RichInput 的工具栏是垂直排列在输入框下方（`toolbar="bottom"`）。  
如果业务需要**水平排列**的输入框（如：`[输入框] [发送按钮]`），RichInput 不适合，应保留独立实现。

### 6. 工具栏固定顺序

工具栏按钮顺序不可配置，固定为：
```
[😊] [🖼️] [toolbar-extra 插槽]
```
各模块的自定义控件通过 `toolbar-extra` 插槽注入，排在图片按钮之后。

---

## 十、样式覆盖指南

组件提供中性基础样式，各模块通过两种方式做视觉适配。

### 方式 1：customClass + :deep()

RichInput 的样式是 scoped 的，父组件的 scoped CSS **无法直接穿透**。必须用 `:deep()`：

```vue
<RichInput custom-class="todo-input" :upload="{ api: todoUploadApi }" />
```

```css
/* ✅ 正确：使用 :deep() 穿透 scoped 边界 */
:deep(.todo-input .ri-textarea) {
  padding: 0; border: none; font-size: 15px;
}
:deep(.todo-input .ri-toolbar) {
  margin-top: 10px; border-top: 1px solid #eee;
  background: transparent; border: none;
}
:deep(.todo-input .ri-tool-btn) { width: 34px; height: 34px; }
:deep(.todo-input .ri-emoji-popup) { bottom: 100%; left: 0; }
:deep(.todo-input .ri-preview-bar) { margin-top: 8px; }
```

### 方式 2：CSS 变量（后续扩展）

预留 CSS 变量体系，未来可按需引入：
```
--ri-bg: #f3f4f6
--ri-border-color: #d1d5db
--ri-border-radius: 10px
--ri-toolbar-bg: transparent
```
