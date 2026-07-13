<template>
  <div class="todo-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索任务内容或备注..."
        clearable
        class="search-input"
        @input="onSearchInput"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-checkbox v-model="showCompleted" @change="renderGroups">
        显示已完成
      </el-checkbox>

      <el-button
        :type="dragMode ? 'warning' : 'default'"
        @click="toggleDragMode"
        :icon="Rank"
        plain
      >
        {{ dragMode ? '完成调整' : '调整位置' }}
      </el-button>

      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        添加任务
      </el-button>
    </div>

    <!-- 红点通知条（管理员有未读留言时显示） -->
    <el-alert
      v-if="notificationItems.length > 0"
      :title="`您有 ${totalUnread} 条新留言未读`"
      type="warning"
      show-icon
      :closable="false"
      class="notification-alert"
    >
      <template #default>
        <div class="notification-list">
          <span
            v-for="n in notificationItems.slice(0, 3)"
            :key="n.todo_id"
            class="notification-item"
            @click="openMessagesDialog(n.todo_id)"
          >
            <el-badge :value="n.unread_count" class="notif-badge">
              <span class="notif-preview">{{ n.todo_content_preview }}</span>
            </el-badge>
          </span>
          <el-button
            v-if="notificationItems.length > 0"
            link
            type="primary"
            @click="clearAllNotifications"
          >
            全部标记已读
          </el-button>
        </div>
      </template>
    </el-alert>

    <!-- 任务列表（按日期分组） -->
    <div class="todo-list">
      <template v-if="loading && todos.length === 0">
        <el-skeleton :rows="5" animated />
      </template>

      <template v-else-if="groupedDates.length === 0">
        <el-empty description="暂无任务，点击右上角添加" />
      </template>

      <template v-else>
        <div v-for="date in groupedDates" :key="date" class="date-group">
          <div class="date-divider">{{ formatDateLabel(date) }}</div>

          <div
            v-for="todo in groups[date]"
            :key="todo.id"
            class="todo-card"
            :class="['color-' + todo.color, { 'is-completed': todo.status === 'completed' }]"
          >
            <!-- 左侧：复选框 -->
            <el-checkbox
              :model-value="todo.status === 'completed'"
              @change="onToggleComplete(todo)"
              class="todo-checkbox"
            />

            <!-- 中间：内容 + 备注 + 图片 -->
            <div class="todo-main">
              <div class="todo-content-row">
                <span
                  class="todo-content"
                  :class="{ 'completed': todo.status === 'completed' }"
                >
                  {{ todo.content }}
                </span>
                <span class="todo-author">[{{ todo.author_id }}]</span>
                <el-badge
                  v-if="todo.unread_count > 0"
                  :value="todo.unread_count"
                  class="unread-badge"
                />
              </div>

              <div v-if="todo.note" class="todo-note">{{ todo.note }}</div>

              <el-image
                v-if="todo.image_url"
                :src="resolveAssetUrl(todo.image_url)"
                fit="cover"
                class="todo-thumb"
                :preview-src-list="[resolveAssetUrl(todo.image_url)]"
                :hide-on-click-modal="true"
                preview-teleported
              />
            </div>

            <!-- 右侧：操作按钮组 -->
            <div class="todo-actions">
              <!-- 已完成：显示"查看完成情况" -->
              <el-button
                v-if="todo.status === 'completed'"
                size="small"
                type="success"
                plain
                @click="openCompletionDialog(todo)"
              >
                查看完成情况
              </el-button>

              <el-dropdown trigger="click" @command="(cmd) => onCommand(cmd, todo)">
                <el-button size="small" :icon="MoreFilled" circle plain />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">修改内容</el-dropdown-item>
                    <el-dropdown-item
                      v-if="todo.status !== 'completed' && canModify(todo)"
                      command="complete"
                    >
                      标记完成
                    </el-dropdown-item>
                    <el-dropdown-item
                      v-if="todo.status === 'completed' && canModify(todo)"
                      command="uncomplete"
                    >
                      撤销完成
                    </el-dropdown-item>
                    <el-dropdown-item
                      v-if="isAdmin"
                      command="addMessage"
                    >
                      添加备注
                    </el-dropdown-item>
                    <el-dropdown-item command="viewMessages">
                      查看留言（{{ todo.unread_count || 0 }}）
                    </el-dropdown-item>
                    <el-dropdown-item
                      v-if="canModify(todo)"
                      command="delete"
                      divided
                    >
                      <span style="color: #f56c6c">删除</span>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>

              <!-- 拖拽手柄 -->
              <el-button
                v-show="dragMode"
                size="small"
                :icon="Rank"
                class="drag-handle"
                circle
                plain
              />
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 添加/编辑任务弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="editingTodo ? '修改任务' : '添加任务'"
      width="500px"
      @closed="resetEditForm"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="任务内容" required>
          <el-input
            v-model="editForm.content"
            type="textarea"
            :rows="3"
            placeholder="例如：完成哥伦比亚餐具套装的邮件回复"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="所属日期">
          <el-date-picker
            v-model="editForm.dateObj"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
            @change="onDateChange"
          />
        </el-form-item>

        <el-form-item label="卡片颜色">
          <div class="color-picker">
            <span
              v-for="c in colorOptions"
              :key="c.value"
              class="color-dot"
              :class="['bg-' + c.value, { active: editForm.color === c.value }]"
              :title="c.label"
              @click="editForm.color = c.value"
            />
          </div>
        </el-form-item>

        <el-form-item label="任务备注">
          <el-input
            v-model="editForm.note"
            type="textarea"
            :rows="2"
            placeholder="备注（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="任务附图">
          <el-upload
            :show-file-list="false"
            :http-request="handleUploadImage"
            :before-upload="beforeImageUpload"
            accept="image/*"
          >
            <el-button :icon="Picture" :loading="uploading">点击上传图片</el-button>
          </el-upload>
          <div v-if="editForm.image_url" class="uploaded-preview">
            <el-image
              :src="resolveAssetUrl(editForm.image_url)"
              fit="cover"
              class="preview-thumb"
              :preview-src-list="[resolveAssetUrl(editForm.image_url)]"
              :hide-on-click-modal="true"
              preview-teleported
            />
            <el-button link type="danger" @click="editForm.image_url = ''">移除</el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEditForm" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 标记完成弹窗 -->
    <el-dialog
      v-model="completeDialogVisible"
      title="标记完成"
      width="500px"
    >
      <el-alert
        title="完成时必须填写文字或图片（至少一项）"
        type="info"
        :closable="false"
        style="margin-bottom: 16px"
      />
      <el-form :model="completeForm" label-width="80px">
        <el-form-item label="完成内容">
          <el-input
            v-model="completeForm.completion_note"
            type="textarea"
            :rows="3"
            placeholder="简单说明完成情况"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="完成图片">
          <el-upload
            :show-file-list="false"
            :http-request="(opt) => handleUploadImage(opt, 'completion')"
            :before-upload="beforeImageUpload"
            accept="image/*"
          >
            <el-button :icon="Picture" :loading="uploading">点击上传图片</el-button>
          </el-upload>
          <div v-if="completeForm.completion_image_url" class="uploaded-preview">
            <el-image
              :src="resolveAssetUrl(completeForm.completion_image_url)"
              fit="cover"
              class="preview-thumb"
              :preview-src-list="[resolveAssetUrl(completeForm.completion_image_url)]"
              :hide-on-click-modal="true"
              preview-teleported
            />
            <el-button link type="danger" @click="completeForm.completion_image_url = ''">移除</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitComplete" :loading="submitting">
          确认完成
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看完成情况弹窗 -->
    <el-dialog
      v-model="completionViewVisible"
      title="完成情况"
      width="500px"
    >
      <div v-if="viewingTodo" class="completion-view">
        <div class="cv-section">
          <h4>原项目</h4>
          <div class="cv-row"><label>标题：</label>{{ viewingTodo.content }}</div>
          <div class="cv-row"><label>日期：</label>{{ viewingTodo.date }}</div>
          <div class="cv-row" v-if="viewingTodo.note"><label>备注：</label>{{ viewingTodo.note }}</div>
          <div class="cv-row" v-if="viewingTodo.image_url">
            <label>图片：</label>
            <el-image
              :src="resolveAssetUrl(viewingTodo.image_url)"
              fit="cover"
              class="preview-thumb"
              :preview-src-list="[resolveAssetUrl(viewingTodo.image_url)]"
              :hide-on-click-modal="true"
              preview-teleported
            />
          </div>
        </div>

        <el-divider />

        <div class="cv-section">
          <h4>完成记录</h4>
          <div class="cv-row" v-if="viewingTodo.completion_note">
            <label>内容：</label>{{ viewingTodo.completion_note }}
          </div>
          <div class="cv-row" v-if="viewingTodo.completion_image_url">
            <label>图片：</label>
            <el-image
              :src="resolveAssetUrl(viewingTodo.completion_image_url)"
              fit="cover"
              class="preview-thumb"
              :preview-src-list="[resolveAssetUrl(viewingTodo.completion_image_url)]"
              :hide-on-click-modal="true"
              preview-teleported
            />
          </div>
          <div class="cv-row">
            <label>完成时间：</label>{{ viewingTodo.completed_at || '—' }}
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="completionViewVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 管理员添加备注弹窗 -->
    <el-dialog
      v-model="messageDialogVisible"
      title="添加备注"
      width="420px"
    >
      <el-input
        v-model="newMessageContent"
        type="textarea"
        :rows="4"
        placeholder="备注内容（仅管理员可添加）"
        maxlength="300"
        show-word-limit
      />
      <template #footer>
        <el-button @click="messageDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddMessage" :loading="submitting">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 留言列表弹窗 -->
    <el-dialog
      v-model="messagesViewVisible"
      title="留言记录"
      width="500px"
    >
      <div v-if="messages.length === 0" class="empty-messages">
        暂无留言
      </div>
      <div v-else class="message-list">
        <div v-for="msg in messages" :key="msg.id" class="message-item">
          <div class="message-header">
            <span class="message-author">{{ msg.author_name }}</span>
            <span class="message-time">{{ msg.created_at }}</span>
            <el-button
              v-if="isAdmin"
              link
              type="danger"
              size="small"
              @click="onDeleteMessage(msg.id)"
            >删除</el-button>
          </div>
          <div class="message-content">{{ msg.content }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="messagesViewVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 统计信息 -->
    <div class="stats-bar">
      待完成: {{ pendingCount }} | 已完成: {{ completedCount }} | 总计: {{ todos.length }}
      <span v-if="totalUnread > 0" class="stats-unread">
        · 红点: {{ totalUnread }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Picture, Search, Rank, MoreFilled,
} from '@element-plus/icons-vue'
import Sortable from 'sortablejs'
import {
  getTodos, getTodo, createTodo, updateTodo, deleteTodo,
  completeTodo, uncompleteTodo, uploadTodoImage,
  getTodoMessages, addTodoMessage, deleteTodoMessage,
  getTodoNotifications, clearTodoNotifications,
  type TodoItem, type TodoMessage,
} from '@/api/todo'
import { getCurrentUserInfo, getCurrentUserEmpId } from '@/utils/authUtils'

// ============================================================
// 状态
// ============================================================
const todos = ref<TodoItem[]>([])
const loading = ref(false)
const submitting = ref(false)
const uploading = ref(false)
const searchKeyword = ref('')
const showCompleted = ref(true)
const dragMode = ref(false)
const isAdmin = ref(false)
const currentEmpId = ref('')

const notificationItems = ref<any[]>([])
const totalUnread = computed(() => notificationItems.value.reduce((s, n) => s + n.unread_count, 0))

// ============================================================
// 颜色映射（hex 值与 todo 模板一致）
// ============================================================
const colorOptions = [
  { value: 'white',  label: '默认',   hex: '#ffffff' },
  { value: 'red',    label: '紧急',   hex: '#fee2e2' },
  { value: 'yellow', label: '重要',   hex: '#fef3c7' },
  { value: 'green',  label: '完成',   hex: '#d1fae5' },
  { value: 'blue',   label: '进行中', hex: '#dbeafe' },
  { value: 'purple', label: '长期',   hex: '#ede9fe' },
]
const COLOR_HEX: Record<string, string> = Object.fromEntries(colorOptions.map(c => [c.value, c.hex]))

// ============================================================
// 编辑/创建弹窗
// ============================================================
const editDialogVisible = ref(false)
const editingTodo = ref<TodoItem | null>(null)
const editForm = reactive({
  content: '',
  dateObj: null as string | null,
  color: 'white',
  note: '',
  image_url: '',
})

function resetEditForm() {
  editForm.content = ''
  editForm.dateObj = new Date().toISOString().split('T')[0]
  editForm.color = 'white'
  editForm.note = ''
  editForm.image_url = ''
  editingTodo.value = null
}

function openCreateDialog() {
  resetEditForm()
  editDialogVisible.value = true
}

function openEditDialog(todo: TodoItem) {
  editingTodo.value = todo
  editForm.content = todo.content
  editForm.dateObj = todo.date
  editForm.color = todo.color
  editForm.note = todo.note
  editForm.image_url = todo.image_url
  editDialogVisible.value = true
}

function onDateChange(val: string | null) {
  // value-format 已自动格式化为 YYYY-MM-DD
}

async function submitEditForm() {
  if (!editForm.content.trim()) {
    ElMessage.warning('任务内容不能为空')
    return
  }
  submitting.value = true
  try {
    const payload = {
      content: editForm.content.trim(),
      date: editForm.dateObj || new Date().toISOString().split('T')[0],
      color: editForm.color,
      note: editForm.note,
      image_url: editForm.image_url,
    }
    if (editingTodo.value) {
      await updateTodo(editingTodo.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await createTodo(payload)
      ElMessage.success('已添加')
    }
    editDialogVisible.value = false
    await loadTodos()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

// ============================================================
// 图片上传（独立接口）
// ============================================================
function beforeImageUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) ElMessage.error('只能上传图片')
  if (!isLt5M) ElMessage.error('图片大小不能超过 5MB')
  return isImage && isLt5M
}

async function handleUploadImage(option: any, subDir: 'todo' | 'completion' = 'todo') {
  uploading.value = true
  try {
    const res: any = await uploadTodoImage(option.file, subDir)
    const url = res?.image_url || res?.data?.image_url
    if (url) {
      if (subDir === 'completion') {
        completeForm.completion_image_url = url
      } else {
        editForm.image_url = url
      }
      ElMessage.success('上传成功')
      option.onSuccess?.(res)
    } else {
      throw new Error('未拿到图片 URL')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '上传失败')
    option.onError?.(e)
  } finally {
    uploading.value = false
  }
}

// ============================================================
// 完成弹窗
// ============================================================
const completeDialogVisible = ref(false)
const completingTodo = ref<TodoItem | null>(null)
const completeForm = reactive({
  completion_note: '',
  completion_image_url: '',
})

function openCompleteDialog(todo: TodoItem) {
  completingTodo.value = todo
  completeForm.completion_note = ''
  completeForm.completion_image_url = ''
  completeDialogVisible.value = true
}

async function submitComplete() {
  if (!completingTodo.value) return
  if (!completeForm.completion_note.trim() && !completeForm.completion_image_url) {
    ElMessage.warning('完成时必须填写文字或图片')
    return
  }
  submitting.value = true
  try {
    await completeTodo(completingTodo.value.id, {
      completion_note: completeForm.completion_note.trim(),
      completion_image_url: completeForm.completion_image_url,
    })
    ElMessage.success('已完成')
    completeDialogVisible.value = false
    await loadTodos()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function onToggleComplete(todo: TodoItem) {
  if (todo.status === 'completed') {
    // 撤销完成
    try {
      await ElMessageBox.confirm('确定要撤销完成状态吗？', '提示', { type: 'warning' })
      await uncompleteTodo(todo.id)
      ElMessage.success('已撤销')
      await loadTodos()
    } catch {
      // 用户取消
    }
  } else {
    // 标记完成（弹窗填文字/图片）
    openCompleteDialog(todo)
  }
}

// ============================================================
// 查看完成情况
// ============================================================
const completionViewVisible = ref(false)
const viewingTodo = ref<TodoItem | null>(null)
function openCompletionDialog(todo: TodoItem) {
  viewingTodo.value = todo
  completionViewVisible.value = true
}

// ============================================================
// 留言（管理员添加 / 所有人查看 / 管理员删除）
// ============================================================
const messageDialogVisible = ref(false)
const newMessageContent = ref('')
const messagingTodo = ref<TodoItem | null>(null)

const messagesViewVisible = ref(false)
const messages = ref<TodoMessage[]>([])
const viewingMessagesTodo = ref<TodoItem | null>(null)

function openAddMessageDialog(todo: TodoItem) {
  messagingTodo.value = todo
  newMessageContent.value = ''
  messageDialogVisible.value = true
}

async function submitAddMessage() {
  if (!messagingTodo.value) return
  if (!newMessageContent.value.trim()) {
    ElMessage.warning('备注内容不能为空')
    return
  }
  submitting.value = true
  try {
    await addTodoMessage(messagingTodo.value.id, newMessageContent.value.trim())
    ElMessage.success('已添加')
    messageDialogVisible.value = false
    await loadNotifications()
  } catch (e: any) {
    ElMessage.error(e?.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

async function openMessagesDialog(todoId: number) {
  try {
    const res: any = await getTodoMessages(todoId)
    messages.value = res || []
    viewingMessagesTodo.value = todos.value.find(t => t.id === todoId) || null
    messagesViewVisible.value = true
    // 自动标记已读
    await clearTodoNotifications(todoId)
    await loadNotifications()
    await loadTodos()
  } catch (e: any) {
    ElMessage.error(e?.message || '加载留言失败')
  }
}

async function onDeleteMessage(msgId: number) {
  if (!viewingMessagesTodo.value) return
  try {
    await ElMessageBox.confirm('确定删除该留言吗？', '提示', { type: 'warning' })
    await deleteTodoMessage(viewingMessagesTodo.value.id, msgId)
    ElMessage.success('已删除')
    messages.value = messages.value.filter(m => m.id !== msgId)
  } catch {
    // 取消
  }
}

async function clearAllNotifications() {
  await clearTodoNotifications()
  await loadNotifications()
  await loadTodos()
  ElMessage.success('已全部标记已读')
}

// ============================================================
// 删除 todo
// ============================================================
async function onDelete(todo: TodoItem) {
  try {
    await ElMessageBox.confirm(`确定删除任务"${todo.content}"吗？`, '提示', { type: 'warning' })
    await deleteTodo(todo.id)
    ElMessage.success('已删除')
    await loadTodos()
  } catch {
    // 取消
  }
}

// ============================================================
// 操作菜单分发
// ============================================================
function onCommand(cmd: string, todo: TodoItem) {
  switch (cmd) {
    case 'edit':         openEditDialog(todo); break
    case 'complete':     openCompleteDialog(todo); break
    case 'uncomplete':   onToggleComplete(todo); break
    case 'addMessage':   openAddMessageDialog(todo); break
    case 'viewMessages': openMessagesDialog(todo.id); break
    case 'delete':       onDelete(todo); break
  }
}

// ============================================================
// 权限判断
// ============================================================
function canModify(todo: TodoItem): boolean {
  return isAdmin.value || todo.author_id === currentEmpId.value
}

// ============================================================
// 分组与日期
// ============================================================
const groups = computed<Record<string, TodoItem[]>>(() => {
  const filtered = todos.value.filter(t => {
    if (!showCompleted.value && t.status === 'completed') return false
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      return t.content.toLowerCase().includes(kw) ||
             (t.note && t.note.toLowerCase().includes(kw))
    }
    return true
  })
  const g: Record<string, TodoItem[]> = {}
  for (const t of filtered) {
    if (!g[t.date]) g[t.date] = []
    g[t.date].push(t)
  }
  return g
})

const groupedDates = computed(() => Object.keys(groups.value).sort((a, b) => b.localeCompare(a)))

const pendingCount = computed(() => todos.value.filter(t => t.status !== 'completed').length)
const completedCount = computed(() => todos.value.filter(t => t.status === 'completed').length)

function formatDateLabel(date: string): string {
  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
  if (date === today) return '今天'
  if (date === yesterday) return '昨天'
  const d = new Date(date)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

// ============================================================
// 拖拽
// ============================================================
let sortableInstance: Sortable | null = null
async function toggleDragMode() {
  dragMode.value = !dragMode.value
  await nextTick()
  setupSortable()
}

function setupSortable() {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
  if (!dragMode.value) return
  const lists = document.querySelectorAll('.date-group')
  lists.forEach(list => {
    sortableInstance = new Sortable(list as HTMLElement, {
      animation: 150,
      handle: '.drag-handle',
      onEnd: () => {
        // 简单实现：拖拽后只刷新排序，不持久化跨组排序
        ElMessage.info('拖拽仅在本日内调整顺序，保存请刷新后端排序')
      },
    })
  })
}

function renderGroups() {
  // 触发 groups 重算（响应式自动）
}

// ============================================================
// 资源 URL 解析（后端存相对路径如 /assets/TodoMedia/xxx.jpg）
// ============================================================
function resolveAssetUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('blob:') || url.startsWith('data:')) return url
  if (url.startsWith('/')) return url
  return '/' + url
}

// ============================================================
// 搜索防抖
// ============================================================
let searchTimer: any = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    renderGroups()
  }, 300)
}

// ============================================================
// 加载数据
// ============================================================
async function loadTodos() {
  loading.value = true
  try {
    const res: any = await getTodos()
    todos.value = res || []
    renderGroups()
  } catch (e: any) {
    ElMessage.error(e?.message || '加载任务失败')
  } finally {
    loading.value = false
  }
}

async function loadNotifications() {
  try {
    const res: any = await getTodoNotifications()
    notificationItems.value = res?.items || []
  } catch {
    notificationItems.value = []
  }
}

// ============================================================
// 初始化
// ============================================================
onMounted(async () => {
  const userInfo = getCurrentUserInfo()
  isAdmin.value = userInfo?.user_role === 'admin'
  currentEmpId.value = getCurrentUserEmpId() || ''
  resetEditForm()
  await loadTodos()
  await loadNotifications()
})
</script>

<style scoped>
.todo-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.search-input {
  width: 280px;
}

.notification-alert {
  margin-bottom: 16px;
}

.notification-list {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.notification-item {
  cursor: pointer;
}

.notif-badge {
  margin-right: 4px;
}

.notif-preview {
  font-size: 13px;
  color: #606266;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.date-group {
  margin-bottom: 16px;
}

.date-divider {
  background: #f5f7fa;
  color: #606266;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 14px;
}

.todo-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  transition: all 0.2s;
}

.todo-card.is-completed {
  opacity: 0.75;
}

.todo-card.color-white  { background: #ffffff; }
.todo-card.color-red    { background: #fee2e2; }
.todo-card.color-yellow { background: #fef3c7; }
.todo-card.color-green  { background: #d1fae5; }
.todo-card.color-blue   { background: #dbeafe; }
.todo-card.color-purple { background: #ede9fe; }

.todo-checkbox {
  margin-top: 2px;
  flex-shrink: 0;
}

.todo-main {
  flex: 1;
  min-width: 0;
}

.todo-content-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.todo-content {
  font-size: 15px;
  color: #1f2937;
  word-break: break-word;
}

.todo-content.completed {
  text-decoration: line-through;
  color: #9ca3af;
}

.todo-author {
  font-size: 12px;
  color: #6b7280;
  background: rgba(0,0,0,0.05);
  padding: 1px 6px;
  border-radius: 4px;
}

.unread-badge {
  margin-left: 4px;
}

.todo-note {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
  line-height: 1.5;
}

.todo-thumb {
  width: 80px;
  height: 80px;
  border-radius: 6px;
  margin-top: 6px;
  cursor: pointer;
}

.todo-actions {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  flex-shrink: 0;
}

.drag-handle {
  cursor: grab;
}

.color-picker {
  display: flex;
  gap: 8px;
}

.color-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.color-dot.active {
  border-color: #409eff;
  transform: scale(1.15);
}

.color-dot.bg-white  { background: #ffffff; border-color: #d1d5db; }
.color-dot.bg-red    { background: #fee2e2; }
.color-dot.bg-yellow { background: #fef3c7; }
.color-dot.bg-green  { background: #d1fae5; }
.color-dot.bg-blue   { background: #dbeafe; }
.color-dot.bg-purple { background: #ede9fe; }

.uploaded-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.preview-thumb {
  width: 60px;
  height: 60px;
  border-radius: 4px;
}

.completion-view .cv-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #374151;
}

.completion-view .cv-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 14px;
  color: #4b5563;
}

.completion-view .cv-row label {
  flex-shrink: 0;
  width: 60px;
  color: #6b7280;
}

.empty-messages {
  text-align: center;
  color: #9ca3af;
  padding: 24px;
}

.message-list {
  max-height: 400px;
  overflow-y: auto;
}

.message-item {
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}

.message-item:last-child {
  border-bottom: none;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.message-author {
  font-weight: 500;
  color: #374151;
}

.message-time {
  color: #9ca3af;
}

.message-content {
  font-size: 14px;
  color: #1f2937;
  word-break: break-word;
}

.stats-bar {
  text-align: center;
  padding: 16px;
  color: #6b7280;
  font-size: 14px;
}

.stats-unread {
  color: #f56c6c;
  font-weight: 500;
}
</style>
