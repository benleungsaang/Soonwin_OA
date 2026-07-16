<!--
  RichInput 可组合输入框组件

  通过 props 选配 emoji / 图片上传 / 粘贴检测功能。
  各业务模块注入自己的 uploadApi 控制存储路径。

  使用文档见同目录 RichInput.md
-->
<template>
  <div
    class="rich-input"
    :class="[size === 'small' ? 'ri-small' : 'ri-default', customClass]"
  >
    <!-- ========== 文本输入区 ========== -->
    <div class="ri-input-wrap" :class="{ 'ri-has-toolbar': hasToolbar }">
      <textarea
        v-if="inputType === 'textarea'"
        ref="inputRef"
        v-model="text"
        class="ri-textarea"
        :placeholder="placeholder"
        :maxlength="maxlength"
        :rows="rows"
        :readonly="readonly"
        :disabled="disabled"
        @paste="onPaste"
        @keydown="onKeydown"
      ></textarea>
      <input
        v-else
        ref="inputRef"
        v-model="text"
        class="ri-input"
        :placeholder="placeholder"
        :maxlength="maxlength"
        :readonly="readonly"
        :disabled="disabled"
        @paste="onPaste"
        @keydown="onKeydown"
      />
    </div>

    <!-- ========== 工具栏 ========== -->
    <div v-if="hasToolbar" class="ri-toolbar">
      <!-- Emoji 按钮 -->
      <button
        v-if="features?.emoji"
        ref="emojiBtnRef"
        type="button"
        class="ri-tool-btn"
        title="插入 emoji"
        @click.stop="toggleEmoji"
      >
        <span style="font-size: 16px; line-height: 1;">😊</span>
      </button>

      <!-- 工具栏扩展插槽 -->
      <slot name="toolbar-extra" />

      <!-- 图片上传按钮 -->
      <button
        v-if="features?.image"
        type="button"
        class="ri-tool-btn"
        title="添加图片"
        @click="triggerImageUpload"
      >
        <span style="font-size: 16px; line-height: 1;">🖼️</span>
      </button>
    </div>

    <!-- ========== Emoji 弹出层 ========== -->
    <div v-show="emojiVisible" class="ri-emoji-popup" @click.stop>
      <emoji-picker
        class="ri-emoji-picker"
        @emoji-click="insertEmoji"
      />
    </div>

    <!-- ========== 图片预览条 ========== -->
    <div v-if="imagePreviewUrl" class="ri-preview-bar">
      <img :src="imagePreviewUrl" class="ri-preview-thumb" />
      <span class="ri-preview-label">已上传</span>
      <button type="button" class="ri-preview-remove" @click="removeImage">✕ 移除</button>

      <!-- 预览条扩展插槽 -->
      <slot name="preview-extra" />
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      style="display: none"
      @change="onFileSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import 'emoji-picker-element'

// ============================================================
// 类型
// ============================================================

export interface RichInputUploadResult {
  url: string
  thumbnailUrl?: string
}

export type RichInputUploadApi = (file: File) => Promise<RichInputUploadResult>

export interface RichInputFeatures {
  emoji?: boolean
  image?: boolean
  paste?: boolean
}

export interface RichInputUploadConfig {
  api: RichInputUploadApi
  maxSizeMB?: number
  accept?: string
}

// ============================================================
// Props
// ============================================================

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  maxlength?: number
  rows?: number
  inputType?: 'input' | 'textarea'
  readonly?: boolean
  disabled?: boolean
  features?: RichInputFeatures
  upload?: RichInputUploadConfig
  size?: 'small' | 'default'
  toolbar?: 'none' | 'bottom'
  customClass?: string
}>(), {
  placeholder: '',
  maxlength: undefined,
  rows: 3,
  inputType: 'textarea',
  readonly: false,
  disabled: false,
  features: () => ({}),
  upload: undefined,
  size: 'default',
  toolbar: 'bottom',
  customClass: '',
})

// ============================================================
// Emits
// ============================================================

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'emoji-select': [emoji: string]
  'image-uploaded': [result: RichInputUploadResult]
  'image-error': [error: Error]
  'paste-image': [file: File]
}>()

// ============================================================
// 状态
// ============================================================

const text = computed({
  get: () => props.modelValue,
  set: (val: string) => emit('update:modelValue', val),
})

const inputRef = ref<HTMLTextAreaElement | HTMLInputElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const emojiBtnRef = ref<HTMLElement | null>(null)

const emojiVisible = ref(false)
const imagePreviewUrl = ref('')

// 当前已上传的图片 URL（供 reset / 父组件查询）
const currentImageUrl = ref('')

// ============================================================
// 计算
// ============================================================

const hasToolbar = computed(() => {
  return props.toolbar !== 'none'
    && (props.features?.emoji || props.features?.image)
})

const maxUploadSize = computed(() => (props.upload?.maxSizeMB || 5) * 1024 * 1024)
const acceptType = computed(() => props.upload?.accept || 'image/*')

// ============================================================
// Emoji
// ============================================================

function toggleEmoji() {
  emojiVisible.value = !emojiVisible.value
}

function insertEmoji(event: any) {
  const emoji: string = event.detail.emoji.unicode
  const el = inputRef.value
  if (el) {
    const start = el.selectionStart ?? text.value.length
    const end = el.selectionEnd ?? start
    text.value = text.value.substring(0, start) + emoji + text.value.substring(end)
    emit('emoji-select', emoji)
    nextTick(() => {
      el.selectionStart = el.selectionEnd = start + emoji.length
      el.focus()
    })
  } else {
    text.value += emoji
    emit('emoji-select', emoji)
  }
  emojiVisible.value = false
}

// ============================================================
// 图片上传
// ============================================================

function beforeImageUpload(file: File): boolean {
  if (!file.type.startsWith('image/')) {
    emit('image-error', new Error('只能上传图片'))
    return false
  }
  if (file.size > maxUploadSize.value) {
    emit('image-error', new Error('图片大小不能超过 ' + (props.upload?.maxSizeMB || 5) + 'MB'))
    return false
  }
  return true
}

function triggerImageUpload() {
  fileInputRef.value?.click()
}

async function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (!beforeImageUpload(file)) return
  await uploadFile(file)
  target.value = ''
}

async function uploadFile(file: File) {
  if (!props.upload?.api) {
    // 没有配置上传 API，仅通知父组件
    emit('paste-image', file)
    return
  }
  try {
    const result = await props.upload.api(file)
    if (result.url) {
      currentImageUrl.value = result.url
      imagePreviewUrl.value = result.thumbnailUrl || result.url
      emit('image-uploaded', result)
    }
  } catch (err: any) {
    emit('image-error', err instanceof Error ? err : new Error(err?.message || '上传失败'))
  }
}

function removeImage() {
  imagePreviewUrl.value = ''
  currentImageUrl.value = ''
}

// ============================================================
// 粘贴检测
// ============================================================

async function onPaste(e: ClipboardEvent) {
  if (!props.features?.paste) return

  const items = e.clipboardData?.items
  if (!items) return

  const files: File[] = []
  for (let i = 0; i < items.length; i++) {
    const f = items[i].getAsFile()
    if (f && f.type.startsWith('image/')) files.push(f)
  }
  if (files.length === 0) return

  e.preventDefault()

  for (const file of files) {
    emit('paste-image', file)
    if (!beforeImageUpload(file)) continue
    await uploadFile(file)
  }
}

// ============================================================
// 键盘事件
// ============================================================

function onKeydown(e: KeyboardEvent) {
  // Ctrl+Enter / Cmd+Enter → emit 留给父组件监听 keydown
  //（不在此处处理，父组件可通过 @keydown 自行接管）
}

// ============================================================
// 外部点击关闭 Emoji
// ============================================================

function onDocumentClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.ri-emoji-popup') && !target.closest('.ri-tool-btn')) {
    emojiVisible.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})

// ============================================================
// Expose
// ============================================================

defineExpose({
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur(),
  reset: () => {
    text.value = ''
    imagePreviewUrl.value = ''
    currentImageUrl.value = ''
  },
  triggerImageUpload,
  getImageUrl: () => currentImageUrl.value,
})
</script>

<style scoped>
/* ============================================================
   基础布局
   ============================================================ */
.rich-input {
  position: relative;
  width: 100%;
}

/* ============================================================
   文本输入区
   ============================================================ */
.ri-input-wrap {
  position: relative;
}
.ri-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  color: #1f2937;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.2s;
  background: #fff;
  box-sizing: border-box;
}
.ri-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}
.ri-textarea::placeholder {
  color: #9ca3af;
}
.ri-input {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  color: #1f2937;
  transition: border-color 0.2s;
  background: #fff;
  box-sizing: border-box;
}
.ri-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}
.ri-input::placeholder {
  color: #9ca3af;
}
.ri-has-toolbar .ri-textarea {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom: none;
}

/* ============================================================
   工具栏
   ============================================================ */
.ri-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-top: none;
  border-radius: 0 0 8px 8px;
  background: #f9fafb;
}
.ri-tool-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
  padding: 0;
}
.ri-tool-btn:hover {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
}

/* ============================================================
   Emoji 弹出层
   ============================================================ */
.ri-emoji-popup {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  z-index: 200;
  margin-bottom: 4px;
}
.ri-emoji-picker {
  height: 220px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  --num-columns: 8;
  --border-radius: 10px;
}

/* ============================================================
   图片预览条
   ============================================================ */
.ri-preview-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.ri-preview-thumb {
  width: 40px;
  height: 30px;
  border-radius: 4px;
  object-fit: cover;
  border: 1px solid #e5e7eb;
}
.ri-preview-label {
  font-size: 12px;
  color: #6b7280;
  flex: 1;
}
.ri-preview-remove {
  font-size: 12px;
  color: #ef4444;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  white-space: nowrap;
}
.ri-preview-remove:hover {
  text-decoration: underline;
}

/* ============================================================
   Small 尺寸
   ============================================================ */
.ri-small .ri-textarea {
  font-size: 13px;
  padding: 6px 10px;
}
.ri-small .ri-input {
  font-size: 13px;
  padding: 4px 10px;
}
.ri-small .ri-toolbar {
  padding: 4px 6px;
}
.ri-small .ri-tool-btn {
  width: 28px;
  height: 28px;
}
</style>
