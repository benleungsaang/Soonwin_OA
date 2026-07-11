<template>
  <div class="task-track-page">
    <CommonHeader title="任务跟踪" />

    <div class="task-container">
      <!-- 顶部标签栏 -->
      <div class="task-tabs">
        <button v-for="tab in tabs" :key="tab.key" @click="switchTab(tab.key)"
          class="task-tab" :class="{ active: activeTab === tab.key }">
          {{ tab.label }}
          <span v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</span>
        </button>
      </div>

      <!-- 发布区（"全部/进行中"标签时显示） -->
      <div v-if="activeTab === 'pending' || activeTab === 'all'" class="publish-box" :style="publishBoxStyle">
        <div class="flex gap-3">
          <div class="flex-1">
            <textarea ref="publishTextareaRef" v-model="publishContent" placeholder="记录待办事项..." rows="2"
              class="publish-textarea" @paste="onPublishPaste" />
            <!-- 待办附图预览 -->
            <div v-if="publishImage.file" class="publish-preview-wrap">
              <div class="publish-preview-item">
                <img :src="publishImage.preview" class="w-full h-full object-cover" />
                <button class="publish-preview-remove" @click="removePublishImage">&times;</button>
              </div>
            </div>
            <!-- 底部工具栏一行：日期 + 颜色 + 附图 + emoji + 发布 -->
            <div class="publish-toolbar">
              <!-- 预计完成日期 -->
              <el-date-picker
                v-model="publishExpectedDate"
                type="date"
                placeholder="预计完成日期"
                value-format="YYYY-MM-DD"
                class="publish-date-picker"
              />
              <!-- 底色选择器：默认只显示一个色标，点击展开 10 色浮层 -->
              <div class="bg-color-wrap" @click.stop>
                <button
                  class="bg-color-trigger"
                  :style="bgColorTriggerStyle"
                  :class="{ 'bg-color-trigger-active': publishBgColor }"
                  title="底色"
                  @click="toggleBgColorPanel"
                ></button>
                <div v-if="showBgColorPanel" class="bg-color-popover">
                  <button v-for="c in presetColors" :key="c"
                    class="color-dot"
                    :class="{ 'color-dot-active': publishBgColor === c }"
                    :style="{ background: c }"
                    @click="selectPresetColor(c)"
                    :title="c"></button>
                </div>
              </div>
              <label class="publish-upload-btn" title="附图">
                <el-icon :size="16"><Picture /></el-icon>
                <input type="file" accept="image/*" hidden @change="onPublishImageSelect" />
              </label>
              <button class="publish-emoji-btn" @click="publishEmojiVisible = !publishEmojiVisible" title="emoji">
                🙂
              </button>
              <div ref="publishEmojiWrapperRef" class="emoji-wrapper">
                <emoji-picker
                  v-if="publishEmojiVisible"
                  class="emoji-picker"
                  @emoji-click="handlePublishEmoji"
                />
              </div>
              <div class="publish-toolbar-spacer"></div>
              <button class="publish-submit-btn" :disabled="publishing" @click="handlePublish">
                {{ publishing ? '发布中...' : '发布' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 搜索栏 -->
      <div class="search-box">
        <el-icon :size="16" color="#9ca3af" class="search-icon"><Search /></el-icon>
        <input v-model="searchKeyword" placeholder="搜索任务..." @keyup.enter="onSearchEnter"
          class="search-input" />
        <button v-if="searchKeyword" class="search-clear-btn" @click="clearSearch">清除</button>
      </div>

      <!-- 任务列表 -->
      <div v-loading="loading" class="task-feed">
        <template v-if="tasks.length > 0">
          <template v-for="group in groupedTasks" :key="group.date">
            <!-- 日期分隔 -->
            <div class="date-divider">
              <span class="date-divider-line"></span>
              <span class="date-divider-text">{{ group.date }}</span>
              <span class="date-divider-line"></span>
            </div>
            <!-- 任务卡片 -->
            <TaskCard
              v-for="task in group.tasks"
              :key="task.id"
              :task="task"
              :current-user-id="currentUserId"
              :is-admin="isAdmin"
              @toggle-complete="handleToggleComplete"
              @edit="openEditDialog"
              @delete="handleDelete"
              @like="handleToggleLike"
              @add-comment="handleAddComment"
              @visibility="openVisibilityDialog"
              @background="openBackgroundDialog"
              @history="openHistoryDialog"
            />
          </template>
        </template>
        <el-empty v-else-if="!loading" :description="emptyText" />
      </div>
    </div>

    <!-- 完成/回退对话框 -->
    <el-dialog v-model="completeDialogVisible" :title="completeDialogTitle" width="480px" align-center>
      <div v-if="completeTask">
        <p class="text-sm text-gray-600 mb-2">原任务：{{ completeTask.content }}</p>
        <el-input v-model="completeNote" type="textarea" :rows="3" placeholder="完成事项简述（支持 emoji）" />
        <div class="mt-3">
          <label class="text-xs text-gray-500 block mb-1">完成附图（可选）</label>
          <div class="flex items-center gap-2">
            <div v-if="completeImagePreview" class="publish-preview-item">
              <img :src="completeImagePreview" class="w-full h-full object-cover" />
              <button class="publish-preview-remove" @click="removeCompleteImage">&times;</button>
            </div>
            <label v-else class="publish-upload-btn">
              <el-icon :size="16"><Picture /></el-icon><span class="text-sm ml-1">选择图片</span>
              <input type="file" accept="image/*" hidden @change="onCompleteImageSelect" />
            </label>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="completeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="completing" @click="confirmComplete">{{ completeDialogTitle }}</el-button>
      </template>
    </el-dialog>

    <!-- 编辑任务对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑任务" width="480px" align-center>
      <div v-if="editingTask">
        <el-form label-width="80px" size="default">
          <el-form-item label="任务内容">
            <el-input v-model="editingTaskDraft.content" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="预计完成">
            <el-date-picker
              v-model="editingTaskDraft.expected_date"
              type="date"
              placeholder="选择预计完成日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="底色">
            <div class="color-palette">
              <button v-for="c in presetColors" :key="c"
                class="color-dot"
                :class="{ 'color-dot-active': editingTaskDraft.background_color === c && !editCustomColor }"
                :style="{ background: c }"
                @click="selectEditColor(c)"></button>
              <input type="color" v-model="editingTaskDraft.background_color" class="color-picker-hidden" />
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="confirmEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 可见性设置对话框 -->
    <el-dialog v-model="visibilityDialogVisible" title="设置可见性（仅管理员）" width="520px" align-center>
      <div v-if="visibilityTask">
        <p class="text-sm text-gray-500 mb-3">默认仅创建人 + 管理员可见。下方列表项为额外可见的人员/角色。</p>
        <div v-for="(v, i) in visibilityDraft" :key="i" class="flex items-center gap-2 mb-2">
          <el-select v-model="v.visibility_type" style="width:120px">
            <el-option label="角色" value="role" />
            <el-option label="员工" value="employee" />
          </el-select>
          <el-input v-model="v.visibility_value" :placeholder="v.visibility_type === 'role' ? '角色名 (如 sales)' : '员工 ID (如 E001)'" />
          <el-button type="danger" :icon="Delete" circle @click="visibilityDraft.splice(i, 1)" />
        </div>
        <el-button class="mt-2" :icon="Plus" @click="addVisibilityRow">添加</el-button>
      </div>
      <template #footer>
        <el-button @click="visibilityDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="visibilitySaving" @click="confirmVisibility">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改历史对话框 -->
    <el-dialog v-model="historyDialogVisible" title="修改历史（仅管理员）" width="680px" align-center top="2vh">
      <div v-if="historyTask" v-loading="historyLoading">
        <div class="text-sm text-gray-500 mb-2">当前版本</div>
        <div class="history-card history-card-current">
          <p class="text-sm">{{ historyTask.content }}</p>
          <p class="text-xs text-gray-400 mt-1">状态：{{ historyTask.status }} · 更新时间：{{ historyTask.updated_at }}</p>
        </div>
        <div class="text-sm text-gray-500 mt-4 mb-2">历史版本（{{ historyList.length }}）</div>
        <div v-for="h in historyList" :key="h.id" class="history-card">
          <div class="history-card-bar">
            <span class="history-badge">{{ formatTime(h.modified_at) }}</span>
            <span class="history-card-editor">by {{ h.modified_by || '系统' }}</span>
          </div>
          <pre class="history-snapshot">{{ h.snapshot }}</pre>
        </div>
      </div>
    </el-dialog>

    <!-- 通知栏 -->
    <TaskNotificationBar :visible="hasToken" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Picture, Delete, Plus } from '@element-plus/icons-vue'
import 'emoji-picker-element'
import CommonHeader from '@/components/CommonHeader.vue'
import TaskCard from '@/components/TaskCard.vue'
import TaskNotificationBar from '@/components/TaskNotificationBar.vue'
import {
  getTasks, createTask, updateTask, deleteTask, createTaskWithImage,
  toggleTaskLike, getTaskComments, createTaskComment,
  updateTaskVisibility, getTaskHistory,
} from '@/api/task'
import { getCurrentUserRole, getCurrentUserEmpId, hasToken as checkHasToken } from '@/utils/authUtils'

const loading = ref(false)
const tasks = ref<any[]>([])
const currentPage = ref(1)
const perPage = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const hasCommittedSearch = ref(false)

type TabKey = 'pending' | 'completed' | 'all' | 'deleted'
const activeTab = ref<TabKey>('pending')

const currentUserId = computed(() => getCurrentUserEmpId() || '')
const isAdmin = computed(() => getCurrentUserRole() === 'admin')
const hasToken = ref(false)

// 预设颜色（10 色）
const presetColors = [
  '#ffffff', // 白
  '#ef4444', // 红
  '#f97316', // 橙
  '#eab308', // 黄
  '#22c55e', // 绿
  '#3b82f6', // 蓝
  '#a855f7', // 紫
  '#1f2937', // 黑
  '#f3f4f6', // 白灰
  '#ec4899', // 粉
  '#92400e', // 棕
]
const publishBgColor = ref('')
const showBgColorPanel = ref(false)
const editCustomColor = ref(false)

function selectPresetColor(c: string) {
  publishBgColor.value = c
  showBgColorPanel.value = false
}
function toggleBgColorPanel() {
  showBgColorPanel.value = !showBgColorPanel.value
}
// 底色按钮（当前选中色）的样式：白色不透明，其他色 0.1 透明
const bgColorTriggerStyle = computed(() => {
  const c = publishBgColor.value
  if (!c) return { background: '#ffffff' }
  const isWhite = c.toLowerCase() === '#ffffff'
  return { background: c, opacity: isWhite ? 1 : 0.1 }
})
// 发布框背景：选中底色后用 0.1 透明度；未选保持白色
const publishBoxStyle = computed(() => {
  const c = publishBgColor.value
  if (!c) return { background: '#ffffff' }
  const hex = c.replace('#', '')
  if (hex.length !== 6) return { background: '#ffffff' }
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  return { background: `rgba(${r}, ${g}, ${b}, 0.1)` }
})
function onBgColorOutsideClick(e: MouseEvent) {
  if (!showBgColorPanel.value) return
  const target = e.target as HTMLElement
  if (target.closest('.bg-color-wrap')) return
  showBgColorPanel.value = false
}
function selectEditColor(c: string) {
  editingTaskDraft.value.background_color = c
  editCustomColor.value = false
}

// 发布区
const publishContent = ref('')
const publishExpectedDate = ref('')
const publishImage = ref<{ file: File | null; preview: string }>({ file: null, preview: '' })
const publishing = ref(false)
const publishEmojiVisible = ref(false)
const publishEmojiWrapperRef = ref<HTMLElement | null>(null)
const publishTextareaRef = ref<HTMLTextAreaElement | null>(null)

function onPublishEmojiOutsideClick(e: MouseEvent) {
  if (!publishEmojiVisible.value) return
  const target = e.target as HTMLElement
  if (publishEmojiWrapperRef.value?.contains(target)) return
  if (target.closest('.publish-emoji-btn')) return
  publishEmojiVisible.value = false
}
onMounted(() => document.addEventListener('mousedown', onPublishEmojiOutsideClick))
onMounted(() => document.addEventListener('mousedown', onBgColorOutsideClick))
onUnmounted(() => document.removeEventListener('mousedown', onPublishEmojiOutsideClick))
onUnmounted(() => document.removeEventListener('mousedown', onBgColorOutsideClick))

function onPublishImageSelect(e: Event) {
  const inp = e.target as HTMLInputElement
  const f = inp.files?.[0]
  if (f) {
    if (publishImage.value.preview) URL.revokeObjectURL(publishImage.value.preview)
    publishImage.value = { file: f, preview: URL.createObjectURL(f) }
  }
  inp.value = ''
}
function removePublishImage() {
  if (publishImage.value.preview) URL.revokeObjectURL(publishImage.value.preview)
  publishImage.value = { file: null, preview: '' }
}
function onPublishPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (let i = 0; i < items.length; i++) {
    const f = items[i].getAsFile()
    if (f && f.type.startsWith('image/')) {
      if (publishImage.value.preview) URL.revokeObjectURL(publishImage.value.preview)
      publishImage.value = { file: f, preview: URL.createObjectURL(f) }
      e.preventDefault()
      break
    }
  }
}

function handlePublishEmoji(event: any) {
  const emoji: string = event.detail.emoji.unicode
  const ta = publishTextareaRef.value
  if (ta) {
    const s = ta.selectionStart; const e = ta.selectionEnd
    publishContent.value = publishContent.value.substring(0, s) + emoji + publishContent.value.substring(e)
    nextTick(() => { const p = s + emoji.length; ta.setSelectionRange(p, p); ta.focus() })
  } else {
    publishContent.value += emoji
  }
  publishEmojiVisible.value = false
}

async function handlePublish() {
  if (!publishContent.value.trim() && !publishImage.value.file) {
    ElMessage.warning('请输入任务内容或附图')
    return
  }
  if (!publishExpectedDate.value) {
    ElMessage.warning('请选择预计完成日期')
    return
  }
  publishing.value = true
  try {
    const content = publishContent.value.trim()
    const expected = publishExpectedDate.value || undefined
    const color = publishBgColor.value || undefined
    if (publishImage.value.file) {
      await createTaskWithImage(content, publishImage.value.file, {
        expected_date: expected,
        background_color: color,
      })
    } else {
      await createTask({ content, expected_date: expected, background_color: color })
    }
    ElMessage.success('发布成功')
    publishContent.value = ''
    publishExpectedDate.value = ''
    publishBgColor.value = ''
    showBgColorPanel.value = false
    removePublishImage()
    currentPage.value = 1
    await loadTasks()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || '发布失败')
  } finally {
    publishing.value = false
  }
}

// 完成/回退对话框
const completeDialogVisible = ref(false)
const completeTask = ref<any>(null)
const completeNote = ref('')
const completeImagePreview = ref('')
const completeImageFile = ref<File | null>(null)
const completing = ref(false)
const isReverting = ref(false)
const completeDialogTitle = computed(() => isReverting.value ? '回退到待办' : '标记完成')

function handleToggleComplete(task: any) {
  completeTask.value = task
  isReverting.value = task.status === 'completed'
  if (isReverting.value) {
    // 回退：预填原内容
    completeNote.value = task.completion_note || ''
    completeImagePreview.value = task.completion_image_url ? getMediaUrl(task.completion_image_url) : ''
    completeImageFile.value = null
  } else {
    completeNote.value = ''
    completeImagePreview.value = ''
    completeImageFile.value = null
  }
  completeDialogVisible.value = true
}

function onCompleteImageSelect(e: Event) {
  const inp = e.target as HTMLInputElement
  const f = inp.files?.[0]
  if (f) {
    if (completeImagePreview.value && completeImagePreview.value.startsWith('blob:')) {
      URL.revokeObjectURL(completeImagePreview.value)
    }
    completeImageFile.value = f
    completeImagePreview.value = URL.createObjectURL(f)
  }
  inp.value = ''
}
function removeCompleteImage() {
  if (completeImagePreview.value && completeImagePreview.value.startsWith('blob:')) {
    URL.revokeObjectURL(completeImagePreview.value)
  }
  completeImagePreview.value = ''
  completeImageFile.value = null
}

async function confirmComplete() {
  if (!completeTask.value) return
  completing.value = true
  try {
    const fd = new FormData()
    fd.append('status', isReverting.value ? 'pending' : 'completed')
    fd.append('completion_note', completeNote.value || '')
    if (completeImageFile.value) {
      fd.append('completion_image', completeImageFile.value)
    }
    // 用 multipart 接口完成（避免再写 JSON+PATCH 的二选一）
    const { multipartRequest } = await import('@/utils/request')
    await multipartRequest.put(`/api/tasks/${completeTask.value.id}`, fd)
    ElMessage.success(isReverting.value ? '已回退到待办' : '任务已完成')
    completeDialogVisible.value = false
    await loadTasks()
  } catch (e: any) {
    console.error('[submitComplete] 失败:', e)
    ElMessage.error(e?.response?.data?.message || e?.message || '操作失败')
  } finally {
    completing.value = false
  }
}

// 编辑对话框
const editDialogVisible = ref(false)
const editingTask = ref<any>(null)
const editingTaskDraft = ref<{ content: string; expected_date: string; background_color: string }>({
  content: '', expected_date: '', background_color: ''
})
const editSaving = ref(false)
function openEditDialog(task: any) {
  editingTask.value = task
  editingTaskDraft.value = {
    content: task.content,
    expected_date: task.expected_date || '',
    background_color: task.background_color || '',
  }
  editDialogVisible.value = true
}
async function confirmEdit() {
  if (!editingTask.value) return
  editSaving.value = true
  try {
    await updateTask(editingTask.value.id, {
      content: editingTaskDraft.value.content,
      expected_date: editingTaskDraft.value.expected_date || undefined,
      background_color: editingTaskDraft.value.background_color || undefined,
    })
    ElMessage.success('已保存')
    editDialogVisible.value = false
    await loadTasks()
  } catch (e: any) {
    console.error('[submitEdit] 失败:', e)
    ElMessage.error(e?.response?.data?.message || e?.message || '保存失败')
  } finally {
    editSaving.value = false
  }
}

// 软删除
async function handleDelete(task: any) {
  try {
    await ElMessageBox.confirm('确定将此任务移至回收站？', '提示', { type: 'warning' })
    await deleteTask(task.id)
    ElMessage.success('已移至回收站')
    await loadTasks()
  } catch { /* cancelled */ }
}

// 点赞
async function handleToggleLike(task: any) {
  try {
    const { toggleTaskLike: toggle } = await import('@/api/task')
    const res: any = await toggle(task.id)
    if (res) {
      task.is_liked = res.liked
      task.like_count = res.like_count
    }
  } catch (e: any) {
    // ignore
  }
}

// 留言
async function handleAddComment({ task, content }: { task: any; content: string }) {
  try {
    await createTaskComment(task.id, content)
    task.comment_count = (task.comment_count || 0) + 1
  } catch (e: any) {
    console.error('[handleAddComment] 失败:', e)
    ElMessage.error(e?.response?.data?.message || e?.message || '留言失败')
    throw e
  }
}

// 可见性
const visibilityDialogVisible = ref(false)
const visibilityTask = ref<any>(null)
const visibilityDraft = ref<Array<{ visibility_type: 'role' | 'employee'; visibility_value: string }>>([])
const visibilitySaving = ref(false)
function openVisibilityDialog(task: any) {
  visibilityTask.value = task
  visibilityDraft.value = (task.visibilities || []).map((v: any) => ({
    visibility_type: v.visibility_type,
    visibility_value: v.visibility_value,
  }))
  visibilityDialogVisible.value = true
}
function addVisibilityRow() {
  visibilityDraft.value.push({ visibility_type: 'role', visibility_value: '' })
}
async function confirmVisibility() {
  if (!visibilityTask.value) return
  visibilitySaving.value = true
  try {
    await updateTaskVisibility(visibilityTask.value.id, visibilityDraft.value.filter(v => v.visibility_value.trim()))
    ElMessage.success('已保存')
    visibilityDialogVisible.value = false
    await loadTasks()
  } catch (e: any) {
    console.error('[saveVisibility] 失败:', e)
    ElMessage.error(e?.response?.data?.message || e?.message || '保存失败')
  } finally {
    visibilitySaving.value = false
  }
}

// 底色
async function openBackgroundDialog({ task, color }: { task: any; color: string }) {
  try {
    const { updateTaskBackground } = await import('@/api/task')
    await updateTaskBackground(task.id, color)
    task.background_color = color
    ElMessage.success('底色已更新')
  } catch (e: any) {
    console.error('[updateBackground] 失败:', e)
    ElMessage.error(e?.response?.data?.message || e?.message || '更新失败')
  }
}

// 修改历史
const historyDialogVisible = ref(false)
const historyTask = ref<any>(null)
const historyList = ref<any[]>([])
const historyLoading = ref(false)
async function openHistoryDialog(task: any) {
  historyTask.value = task
  historyList.value = []
  historyDialogVisible.value = true
  historyLoading.value = true
  try {
    const res: any = await getTaskHistory(task.id)
    historyList.value = res?.history || []
  } catch (e: any) {
    console.error('[loadHistory] 失败:', e)
    ElMessage.error(e?.response?.data?.message || e?.message || '加载历史失败')
  } finally {
    historyLoading.value = false
  }
}

// 数据加载
async function loadTasks() {
  loading.value = true
  try {
    const status = activeTab.value === 'pending' ? 'pending' :
                   activeTab.value === 'completed' ? 'completed' : 'all'
    const showDeleted = activeTab.value === 'deleted' ? '1' : '0'
    const params: any = { page: currentPage.value, per_page: perPage.value, status, show_deleted: showDeleted }
    if (searchKeyword.value) params.search = searchKeyword.value
    const res: any = await getTasks(params)
    if (res) {
      tasks.value = res.tasks || []
      total.value = res.total || 0
    }
  } catch (e: any) {
    console.error('[loadTasks] 失败:', e)
    ElMessage.error(e?.response?.data?.message || e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function switchTab(key: TabKey) {
  activeTab.value = key
  currentPage.value = 1
  searchKeyword.value = ''
  hasCommittedSearch.value = false
  loadTasks()
}

function onSearchEnter() {
  searchKeyword.value = searchKeyword.value.trim()
  hasCommittedSearch.value = true
  currentPage.value = 1
  loadTasks()
}

function clearSearch() {
  searchKeyword.value = ''
  if (hasCommittedSearch.value) {
    hasCommittedSearch.value = false
    currentPage.value = 1
    loadTasks()
  }
}

const tabs = computed(() => {
  const list: Array<{ key: TabKey; label: string; count: number }> = [
    { key: 'pending', label: '进行中', count: 0 },
    { key: 'completed', label: '已完成', count: 0 },
    { key: 'all', label: '全部', count: 0 },
  ]
  if (isAdmin.value) list.push({ key: 'deleted', label: '回收站', count: 0 })
  return list
})

const emptyText = computed(() => {
  if (activeTab.value === 'deleted') return '回收站为空'
  if (searchKeyword.value) return '未找到匹配的任务'
  if (activeTab.value === 'completed') return '暂无已完成任务'
  if (activeTab.value === 'pending') return '暂无待办，发起一个吧！'
  return '暂无任务'
})

// 按日期分组
const groupedTasks = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const t of tasks.value) {
    const date = (t.created_at || '').substring(0, 10) || '未知日期'
    if (!groups[date]) groups[date] = []
    groups[date].push(t)
  }
  const dates = Object.keys(groups).sort((a, b) => b.localeCompare(a))
  return dates.map(date => ({ date, tasks: groups[date] }))
})

function formatTime(s: string) {
  if (!s) return ''
  return s.replace('T', ' ').substring(0, 19)
}

function getMediaUrl(path: string) {
  if (!path) return ''
  return `/assets/TasksMedia/${path}`
}

onMounted(async () => {
  hasToken.value = checkHasToken()
  await loadTasks()
})
</script>

<style scoped>
.task-track-page { min-height: 100vh; background: #f3f4f6; }
.task-container { max-width: 720px; margin: 0 auto; padding: 16px; }
@media (max-width: 768px) { .task-container { padding: 12px 8px; } }

/* 发布框 */
.publish-box { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 16px; margin-bottom: 16px; transition: background 0.2s; }
.publish-toolbar { display: flex; align-items: center; gap: 12px; margin-top: 10px; flex-wrap: wrap; }
.publish-toolbar > .publish-date-picker { margin-right: 4px; }
.publish-toolbar > .bg-color-wrap { margin-right: 4px; }
.publish-toolbar-spacer { flex: 1; }
.publish-date-picker { width: auto !important; }
.bg-color-wrap { position: relative; display: inline-flex; }
.bg-color-trigger { width: 24px; height: 24px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 1px rgba(0,0,0,0.1); cursor: pointer; padding: 0; transition: all 0.15s; }
.bg-color-trigger:hover { transform: scale(1.1); }
.bg-color-trigger-active { box-shadow: 0 0 0 2px #3b82f6; }
.bg-color-popover { position: absolute; top: 32px; left: 0; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; gap: 6px; z-index: 100; flex-wrap: nowrap; width: max-content; }
.publish-textarea { width: 100%; border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; resize: none; outline: none; font-size: 15px; color: #1f2937; padding: 10px; background: #fafafa; box-sizing: border-box; font-family: inherit; }
.publish-textarea:focus { border-color: #3b82f6; background: #fff; }
.publish-upload-btn { display: inline-flex; align-items: center; gap: 4px; padding: 8px 10px; color: #9ca3af; cursor: pointer; border-radius: 8px; transition: all 0.15s; }
.publish-upload-btn:hover { color: #3b82f6; background: #f3f4f6; }
.publish-emoji-btn { display: inline-flex; align-items: center; justify-content: center; padding: 6px 10px; background: none; border: none; cursor: pointer; border-radius: 8px; font-size: 18px; line-height: 1; transition: all 0.15s; color: #9ca3af; }
.publish-emoji-btn:hover { background: #f3f4f6; color: #3b82f6; }
.emoji-wrapper { position: relative; }
.emoji-picker { position: absolute; bottom: 100%; left: 0; z-index: 200; margin-bottom: 4px; height: 260px; border-radius: 12px; --num-columns: 8; --border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
.publish-submit-btn { background: #3b82f6; color: #fff; border: none; padding: 8px 24px; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.15s; }
.publish-submit-btn:hover { background: #2563eb; }
.publish-submit-btn:disabled { opacity: 0.6; cursor: default; }
.publish-preview-item { position: relative; width: 72px; height: 72px; border-radius: 8px; overflow: hidden; border: 1px solid rgba(0,0,0,0.06); }
.publish-preview-remove { position: absolute; top: 2px; right: 2px; width: 18px; height: 18px; background: #ef4444; color: #fff; border: none; border-radius: 50%; font-size: 12px; line-height: 1; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.publish-preview-wrap { margin-top: 8px; }
.publish-date-input { padding: 4px 8px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12px; outline: none; background: #fff; }
.publish-date-input:focus { border-color: #3b82f6; }

/* 调色板 */
.color-palette { display: inline-flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.color-dot { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #fff; cursor: pointer; box-shadow: 0 0 0 1px rgba(0,0,0,0.1); transition: all 0.15s; padding: 0; }
.color-dot:hover { transform: scale(1.15); }
.color-dot-active { box-shadow: 0 0 0 2px #3b82f6; transform: scale(1.15); }
.color-dot-custom { position: relative; background: linear-gradient(135deg, #ff6b6b, #4ecdc4, #45b7d1, #feca57); }
.color-picker-hidden { position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }
.custom-color-wrap { position: relative; display: inline-block; }

/* 搜索 */
.search-box { position: relative; margin-bottom: 12px; display: flex; align-items: center; }
.search-icon { position: absolute; left: 12px; z-index: 1; pointer-events: none; }
.search-input { width: 100%; padding: 10px 16px 10px 36px; border: 1px solid #e5e7eb; border-radius: 12px; font-size: 14px; outline: none; background: #fff; transition: border-color 0.15s; box-sizing: border-box; }
.search-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.1); }
.search-clear-btn { flex-shrink: 0; padding: 4px 10px; margin-left: 6px; background: #fff; color: #6b7280; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all 0.15s; }
.search-clear-btn:hover { background: #f9fafb; color: #374151; border-color: #d1d5db; }

/* 标签栏 */
.task-tabs { display: flex; gap: 4px; margin-bottom: 16px; background: #fff; border-radius: 10px; padding: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.task-tab { flex: 1; padding: 8px 0; border: none; background: transparent; border-radius: 8px; font-size: 13px; color: #6b7280; cursor: pointer; transition: all 0.15s; display: flex; align-items: center; justify-content: center; gap: 4px; }
.task-tab:hover { color: #374151; background: #f3f4f6; }
.task-tab.active { color: #3b82f6; background: #eff6ff; font-weight: 500; }
.tab-badge { font-size: 11px; background: #3b82f6; color: #fff; border-radius: 10px; padding: 1px 6px; min-width: 16px; text-align: center; }

/* 日期分隔 */
.date-divider { display: flex; align-items: center; gap: 12px; margin: 18px 0 12px; }
.date-divider-line { flex: 1; height: 1px; background: #e5e7eb; }
.date-divider-text { font-size: 12px; color: #6b7280; font-weight: 500; padding: 2px 12px; background: #f3f4f6; border-radius: 10px; }

.task-feed { min-height: 300px; }

/* 历史卡片 */
.history-card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; }
.history-card-current { background: #eff6ff; border-color: #93c5fd; }
.history-card-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.history-badge { font-size: 11px; background: #3b82f6; color: #fff; padding: 1px 8px; border-radius: 4px; }
.history-card-editor { font-size: 12px; color: #6b7280; }
.history-snapshot { font-size: 12px; color: #4b5563; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow: auto; background: #fff; padding: 8px; border-radius: 4px; border: 1px solid #e5e7eb; font-family: 'SFMono-Regular', Consolas, monospace; }
</style>