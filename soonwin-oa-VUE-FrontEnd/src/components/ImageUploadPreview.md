# ImageUploadPreview 组件使用规范

---

## 一、组件概述

`ImageUploadPreview` 是一个封装好的图片/视频上传组件，支持：
- 拖拽上传
- 点击选择上传
- Ctrl+V 粘贴上传
- 上传前预览与确认
- 上传进度显示

---

## 二、工作模式

组件支持两种上传模式，通过 `uploadImmediately` 属性控制：

| 模式 | `uploadImmediately` | 触发时机 | 适用场景 |
|------|---------------------|----------|----------|
| 立即上传 | `true` | 点击"确认上传"后立即上传 | 已有关联对象（如编辑场景） |
| 延迟上传 | `false` | 点击"确定"保存对象时一起上传 | 待创建对象（如新增场景） |

---

## 三、组件 Props

```typescript
interface Props {
  taskId?: number;           // 任务ID（用于 OrderStatus 等业务）
  communicationId?: number;  // 沟通记录ID（用于询盘业务）
  orderId?: number;          // 订单ID（用于订单记录业务）
  recordType?: string;       // 记录类型（income/expense）
  remark?: string;           // 备注信息（用于生成文件名）
  uploadImmediately?: boolean;  // 是否立即上传，默认 false
  uploadPath?: string;       // 上传接口路径
}
```

**关键说明**：
- `uploadImmediately=true` 时，**必须**提供 `taskId`、`orderId`、`communicationId` 至少一个
- `uploadImmediately=false` 时，关联参数用于生成文件路径，上传时机由父组件控制
- `recordType` 和 `remark` 用于自定义上传后的文件名

---

## 四、组件 Events

```typescript
emit('upload-success', [files: File[], mediaFiles: any[]])
// files: 原始文件数组
// mediaFiles: 上传成功后后端返回的媒体文件信息数组

emit('upload-failure', [error: any])
// 上传失败时触发

emit('upload-clipboard-image', [response: any, file: File, taskId: number])
// 粘贴图片时触发（用于特殊处理）
```

---

## 五、上传响应格式规范

后端上传接口**必须**返回标准格式：

```json
{
  "code": 200,
  "msg": "文件上传成功",
  "data": {
    "path": "folder/subfolder/filename.jpg",
    "filename": "filename.jpg",
    "folder": "folder/subfolder"
  }
}
```

**关键说明**：
- 响应拦截器会自动返回 `res.data`，前端直接用 `response.path` 获取文件路径
- 不需要额外返回 `media_files` 字段

---

## 六、延迟上传模式调用规范

适用于新增对象的业务场景（如订单记录的收入/支出）：

### 6.1 模板写法

```vue
<template>
  <el-form-item label="佐证截图">
    <ImageUploadPreview
      ref="imageUploadRef"
      :upload-path="uploadPath"
      :upload-immediately="false"
      :order-id="currentRecord?.id"
      :record-type="recordForm.type"
      :remark="recordForm.remark"
      @upload-success="handleUploadSuccess"
      @upload-failure="handleUploadFailure"
    />
    <!-- 本地预览区域 -->
    <div v-if="localPreviewFile" class="local-preview">
      <el-image
        :src="localPreviewFile.url"
        :preview-src-list="[localPreviewFile.url]"
        preview-teleported
        close-on-press-esc
        hide-on-click-modal
      />
      <el-button @click="removeLocalPreview">删除</el-button>
    </div>
    <!-- 已保存的图片（编辑时） -->
    <div v-else-if="recordForm.screenshot" class="existing-screenshot">
      <el-image
        :src="getImageUrl(recordForm.screenshot)"
        :preview-src-list="[getImageUrl(recordForm.screenshot)]"
        preview-teleported
        close-on-press-esc
        hide-on-click-modal
      />
      <el-button @click="removeExistingScreenshot">删除</el-button>
    </div>
  </el-form-item>
</template>
```

### 6.2 数据定义

```typescript
const imageUploadRef = ref<any>(null)
const localPreviewFile = ref<{ file: File; url: string } | null>(null)
const uploadPath = '/api/xxx/upload-screenshot'

const recordForm = ref({
  id: 0,
  screenshot: '',
  // ... 其他字段
})
```

### 6.3 上传成功回调

```typescript
const handleUploadSuccess = (files: File[], mediaFiles: any[]) => {
  // 延迟模式：只创建本地预览，不立即上传
  if (files && files.length > 0) {
    const previewUrl = URL.createObjectURL(files[0])
    localPreviewFile.value = { file: files[0], url: previewUrl }
  }
}
```

### 6.4 保存时上传

```typescript
const saveRecord = async () => {
  // 1. 如果有本地预览文件，先上传
  if (localPreviewFile.value) {
    const formData = new FormData()
    formData.append('files', localPreviewFile.value.file)
    // 根据业务需要添加关联参数
    formData.append('order_id', currentRecord.value.id.toString())
    formData.append('record_type', recordForm.value.type)
    formData.append('remark', recordForm.value.remark || '')

    const response: any = await request.post(uploadPath, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    // 设置截图路径
    if (response && response.path) {
      recordForm.value.screenshot = response.path
    }
  }

  // 2. 保存记录（含截图路径）
  const { id, ...postData } = recordForm.value
  if (id) {
    await request.put(`/api/xxx/${id}`, postData)
  } else {
    await request.post('/api/xxx', postData)
  }

  // 3. 清理本地预览
  if (localPreviewFile.value) {
    URL.revokeObjectURL(localPreviewFile.value.url)
    localPreviewFile.value = null
  }
}
```

### 6.5 删除本地预览

```typescript
const removeLocalPreview = () => {
  if (localPreviewFile.value) {
    URL.revokeObjectURL(localPreviewFile.value.url)
    localPreviewFile.value = null
  }
}
```

---

## 七、立即上传模式调用规范

适用于已有关联对象的业务场景（如编辑状态下传图）：

### 7.1 模板写法

```vue
<ImageUploadPreview
  ref="imageUploadRef"
  :upload-path="uploadPath"
  :upload-immediately="true"
  :order-id="recordId"
  :record-type="recordType"
  :remark="remark"
  @upload-success="handleUploadSuccess"
  @upload-failure="handleUploadFailure"
/>
```

### 7.2 上传成功回调

```typescript
const handleUploadSuccess = (files: File[], mediaFiles: any[]) => {
  // 立即模式：从 mediaFiles 获取上传后的文件信息
  if (mediaFiles && mediaFiles.length > 0) {
    const uploadedPath = mediaFiles[0].path
    // 直接使用返回的路径更新表单
    recordForm.value.screenshot = uploadedPath
  }
}
```

---

## 八、Ctrl+V 粘贴支持

```typescript
const handleInputPaste = async (e: ClipboardEvent) => {
  const items = e.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      e.preventDefault()
      const file = item.getAsFile()
      if (file && imageUploadRef.value) {
        imageUploadRef.value.addClipboardMedia(file)
      }
      break
    }
  }
}
```

```html
<el-input @paste="handleInputPaste" placeholder="粘贴图片(Ctrl+V)" />
```

---

## 九、图片预览属性规范

所有用于预览的 `el-image` 必须设置以下属性：

```vue
<el-image
  :src="..."
  :preview-src-list="[...]"
  preview-teleported      <!-- 预览层插入 body，避免被父级遮罩遮挡 -->
  close-on-press-esc      <!-- ESC 键关闭预览 -->
  hide-on-click-modal     <!-- 点击遮罩关闭预览 -->
/>
```

---

## 十、目录结构规范

```
assets/{业务文件夹}/
└── {关联标识}_{时间戳}/
    ├── {recordType}_{remark}_{时间戳}.{ext}
    └── ...
```

**示例**：
```
assets/OrderRecords/
└── SW26-041401_20260428144454/
    ├── income_订金_20260428161429.png
    └── expense_采购支出_20260428162750.jpg
```

---

## 十一、关联删除规范

### 11.1 删除单个截图

```typescript
// 后端接口
POST /api/xxx/delete-screenshot
Body: { "path": "folder/filename.jpg" }
```

### 11.2 删除整个文件夹

```typescript
// 后端接口
POST /api/xxx/delete-order-folder
Body: { "order_id": 123 }
```

### 11.3 调用时机

| 场景 | 删除操作 |
|------|----------|
| 删除收入/支出记录 | 删除其 `screenshot` 字段对应的文件 |
| 删除订单记录 | 删除整个订单文件夹 |
| 编辑时替换图片 | 先删旧图，再上新图 |

---

## 十二、常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| "未指定任务ID" | `uploadImmediately=true` 但未传关联ID | 确保传 `taskId`/`orderId`/`communicationId` 至少一个 |
| 上传成功但路径未写入 | 响应拦截器返回 `res.data`，直接用 `response.path` | 后端返回 `data.path`，前端用 `response.path` 获取 |
| 图片预览被遮罩遮挡 | 预览层在父级模态框内 | 添加 `preview-teleported` |
| 编辑时图片不显示 | 未处理已保存图片的显示逻辑 | 模板判断 `localPreviewFile` 优先，否则显示 `screenshot` |
| 替换图片后旧图残留 | 未在替换前删除旧图 | 保存前记录旧路径，上传成功后删除 |
| 删除记录后图片残留 | 未联动删除图片 | 删除记录前先删图片/文件夹 |

---

## 十三、使用 CheckList

- [ ] 设置正确的 `uploadPath`
- [ ] 根据业务场景选择 `uploadImmediately` 模式
- [ ] 提供必要的关联参数（`orderId`/`taskId` 等）
- [ ] 实现 `handleUploadSuccess` 回调
- [ ] 维护 `localPreviewFile` 状态（延迟模式）
- [ ] 实现图片预览时添加 `preview-teleported`、`close-on-press-esc`、`hide-on-click-modal`
- [ ] 删除对象时联动删除图片/文件夹
- [ ] 编辑时正确显示已保存的图片
- [ ] 替换图片时先删旧图
- [ ] 本地预览 URL 在不需要时释放（`URL.revokeObjectURL`）