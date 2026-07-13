<template>
  <div class="todo-page">
    <div class="todo-container">
      <!-- ============ 顶部工具栏（白底圆角阴影卡片） ============ -->
      <div class="toolbar-card">
        <!-- 第一行：添加任务输入框 -->
        <div class="add-row">
          <input
            v-model="newTaskContent"
            type="text"
            placeholder="添加新的待办事项..."
            class="add-input"
            maxlength="500"
            @keypress.enter="onAddTask"
          />
          <button class="add-btn" @click="onAddTask">
            <el-icon><Plus /></el-icon>
            <span>添加</span>
          </button>
        </div>

        <!-- 第二行：搜索 + 显示已完成 + 调整位置 + 通知铃铛 -->
        <div class="filter-row">
          <div class="search-wrap">
            <el-icon class="search-icon"><Search /></el-icon>
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索任务..."
              class="search-input"
              @input="onSearchInput"
            />
          </div>

          <button
            class="toggle-btn"
            :class="{ active: showCompleted }"
            @click="toggleShowCompleted"
          >
            <el-icon v-if="showCompleted" style="color: white"><CircleCheckFilled /></el-icon>
            <el-icon v-else style="color: #3b82f6"><CircleCheck /></el-icon>
            <span>{{ showCompleted ? '隐藏已完成' : '显示已完成' }}</span>
          </button>

          <button
            class="toggle-btn drag-toggle"
            :class="{ active: dragMode }"
            @click="toggleDragMode"
          >
            <el-icon><Rank /></el-icon>
            <span>{{ dragMode ? '完成调整' : '调整位置' }}</span>
          </button>

          <!-- 通知铃铛：未读 > 0 时显示 -->
          <div
            v-if="totalUnread > 0"
            class="bell-wrap"
            title="您有新留言未读"
            @click="openFirstNotification"
          >
            <el-icon class="bell-icon"><Bell /></el-icon>
            <span class="bell-badge">{{ totalUnread }}</span>
          </div>
        </div>
      </div>

      <!-- ============ 任务列表（白底圆角阴影卡片） ============ -->
      <div class="list-card">
        <!-- 加载中 -->
        <div v-if="loading && todos.length === 0" class="loading-state">
          <el-skeleton :rows="3" animated />
        </div>

        <!-- 空状态 -->
        <div v-else-if="groupedDates.length === 0" class="empty-state">
          <el-empty :description="searchKeyword ? '没有找到匹配的任务' : '暂无任务，开始添加吧！'" />
        </div>

        <!-- 任务列表 -->
        <template v-else>
          <div v-for="date in groupedDates" :key="date">
            <!-- 日期分隔条（参考样式：bg-gray-50 + 上下边框） -->
            <div class="date-divider">{{ formatDateLabel(date) }}</div>

            <!-- 任务卡片：6 色直接应用到卡片本身 -->
            <div
              v-for="todo in groups[date]"
              :key="todo.id"
              class="task-card"
              :class="['color-' + todo.color, { 'is-completed': todo.status === 'completed' }]"
            >
              <!-- 左侧：圆形复选框 -->
              <input
                type="checkbox"
                class="task-checkbox"
                :checked="todo.status === 'completed'"
                @change="onToggleComplete(todo)"
              />

              <!-- 中间：内容 + 备注 + 图片 -->
              <div class="task-main">
                <div class="content-row">
                  <span
                    class="task-content"
                    :class="{ completed: todo.status === 'completed' }"
                  >{{ todo.content }}</span>
                  <span class="task-author">[{{ todo.author_id }}]</span>
                  <!-- 红点通知（管理员留言后） -->
                  <span
                    v-if="todo.unread_count > 0"
                    class="unread-badge"
                    :title="`${todo.unread_count} 条新留言未读`"
                    @click.stop="openMessagesDialog(todo.id)"
                  >{{ todo.unread_count }}</span>
                </div>

                <!-- 备注预览（line-clamp-1） -->
                <div v-if="todo.note" class="note-text" @click="openEditDialog(todo)">
                  <span>{{ todo.note }}</span>
                  <span class="note-expand">查看</span>
                </div>

                <!-- 任务附图 -->
                <el-image
                  v-if="todo.image_url"
                  :src="resolveAssetUrl(todo.image_url)"
                  fit="cover"
                  class="task-thumb"
                  :preview-src-list="[resolveAssetUrl(todo.image_url)]"
                  :hide-on-click-modal="true"
                  preview-teleported
                />
              </div>

              <!-- 右侧：操作按钮 + 菜单 + 拖拽手柄 -->
              <div class="task-actions">
                <!-- 已完成：查看完成情况按钮（参考"操作菜单按钮左边"） -->
                <button
                  v-if="todo.status === 'completed'"
                  class="completion-btn"
                  @click="openCompletionDialog(todo)"
                >
                  <el-icon><Finished /></el-icon>
                  <span>查看完成情况</span>
                </button>

                <!-- 菜单按钮（···） -->
                <div class="menu-wrapper">
                  <button
                    class="menu-trigger"
                    :title="'操作'"
                    @click.stop="toggleMenu(todo.id)"
                  >
                    <el-icon><MoreFilled /></el-icon>
                  </button>

                  <!-- 自定义弹出菜单 -->
                  <transition name="menu-fade">
                    <div
                      v-show="openMenuId === todo.id"
                      class="task-menu-dropdown"
                      @click.stop
                    >
                      <!-- 顶部：6 颜色圆点（一行） -->
                      <div class="color-row">
                        <button
                          v-for="c in colorOptions"
                          :key="c.value"
                          class="color-dot"
                          :class="['bg-' + c.value, { selected: todo.color === c.value }]"
                          :title="c.label"
                          @click="onChangeColor(todo, c.value)"
                        />
                      </div>

                      <!-- 操作按钮组 -->
                      <button class="menu-btn" @click="openEditDialog(todo); closeMenu()">
                        <el-icon><EditPen /></el-icon>
                        <span>修改内容</span>
                      </button>

                      <button
                        v-if="todo.status !== 'completed' && canModify(todo)"
                        class="menu-btn"
                        @click="openCompleteDialog(todo); closeMenu()"
                      >
                        <el-icon><Select /></el-icon>
                        <span>标记完成</span>
                      </button>

                      <button
                        v-if="todo.status === 'completed' && canModify(todo)"
                        class="menu-btn"
                        @click="onUncomplete(todo); closeMenu()"
                      >
                        <el-icon><RefreshLeft /></el-icon>
                        <span>撤销完成</span>
                      </button>

                      <!-- 仅管理员 -->
                      <button
                        v-if="isAdmin"
                        class="menu-btn"
                        @click="openAddMessageDialog(todo); closeMenu()"
                      >
                        <el-icon><ChatLineRound /></el-icon>
                        <span>添加备注</span>
                      </button>

                      <button class="menu-btn" @click="openMessagesDialog(todo.id); closeMenu()">
                        <el-icon><ChatDotRound /></el-icon>
                        <span>查看留言</span>
                      </button>

                      <!-- 仅创建人/管理员可删 -->
                      <button
                        v-if="canModify(todo)"
                        class="menu-btn danger"
                        @click="onDelete(todo); closeMenu()"
                      >
                        <el-icon><Delete /></el-icon>
                        <span>删除</span>
                      </button>
                    </div>
                  </transition>
                </div>

                <!-- 拖拽手柄（仅 dragMode 时显示） -->
                <button v-show="dragMode" class="drag-handle" title="拖动调整顺序">
                  <el-icon><Rank /></el-icon>
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- ============ 底部统计栏 ============ -->
      <div class="stats-bar">
        待完成: {{ pendingCount }} | 已完成: {{ completedCount }} | 总计: {{ todos.length }}
      </div>
    </div>

    <!-- ============ 添加/编辑任务弹窗 ============ -->
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
            placeholder="例如：完成哥伦比亚餐具套装的邮件回复 🚀"
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
            placeholder="备注（可选，支持 emoji 📝）"
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
        <el-button type="primary" :loading="submitting" @click="submitEditForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- ============ 标记完成弹窗 ============ -->
    <el-dialog v-model="completeDialogVisible" title="标记完成" width="500px">
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
        <el-button type="primary" :loading="submitting" @click="submitComplete">确认完成</el-button>
      </template>
    </el-dialog>

    <!-- ============ 查看完成情况弹窗 ============ -->
    <el-dialog v-model="completionViewVisible" title="完成情况" width="500px">
      <div v-if="viewingTodo" class="completion-view">
        <div class="cv-section">
          <h4>原项目</h4>
          <div class="cv-row"><label>标题：</label>{{ viewingTodo.content }}</div>
          <div class="cv-row"><label>日期：</label>{{ viewingTodo.date }}</div>
          <div v-if="viewingTodo.note" class="cv-row"><label>备注：</label>{{ viewingTodo.note }}</div>
          <div v-if="viewingTodo.image_url" class="cv-row">
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
          <div v-if="viewingTodo.completion_note" class="cv-row">
            <label>内容：</label>{{ viewingTodo.completion_note }}
          </div>
          <div v-if="viewingTodo.completion_image_url" class="cv-row">
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

    <!-- ============ 管理员添加备注弹窗 ============ -->
    <el-dialog v-model="messageDialogVisible" title="添加备注" width="420px">
      <el-input
        v-model="newMessageContent"
        type="textarea"
        :rows="4"
        placeholder="备注内容（仅管理员可添加，支持 emoji）"
        maxlength="300"
        show-word-limit
      />
      <template #footer>
        <el-button @click="messageDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAddMessage">添加</el-button>
      </template>
    </el-dialog>

    <!-- ============ 留言列表弹窗 ============ -->
    <el-dialog v-model="messagesViewVisible" title="留言记录" width="500px">
      <div v-if="messages.length === 0" class="empty-messages">暂无留言</div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Picture, Search, Rank, MoreFilled,
  CircleCheck, CircleCheckFilled, Bell,
  Finished, EditPen, Select, RefreshLeft,
  ChatLineRound, ChatDotRound, Delete,
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
const newTaskContent = ref('')
const searchKeyword = ref('')
const showCompleted = ref(true)
const dragMode = ref(false)
const isAdmin = ref(false)
const currentEmpId = ref('')
const openMenuId = ref<number | null>(null)

const notificationItems = ref<any[]>([])
const totalUnread = computed(() => notificationItems.value.reduce((s, n) => s + n.unread_count, 0))

// ============================================================
// 颜色映射（方案 ①：purple → dark；hex 对齐参考 bg-XXX/10）
// ============================================================
const colorOptions = [
  { value: 'white',  label: '默认',   hex: '#ffffff' },
  { value: 'red',    label: '紧急',   hex: '#fee2e2' },
  { value: 'yellow', label: '重要',   hex: '#fef3c7' },
  { value: 'green',  label: '完成',   hex: '#d1fae5' },
  { value: 'blue',   label: '进行中', hex: '#dbeafe' },
  { value: 'dark',   label: '长期',   hex: '#e5e7eb' },  // 参考 bg-dark/10 ≈ 浅灰
]

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

// 顶部添加输入框快捷提交
async function onAddTask() {
  const content = newTaskContent.value.trim()
  if (!content) {
    ElMessage.warning('请输入任务内容')
    return
  }
  submitting.value = true
  try {
    await createTodo({
      content,
      date: new Date().toISOString().split('T')[0],
      color: 'white',
    })
    newTaskContent.value = ''
    ElMessage.success('已添加')
    await loadTodos()
  } catch (e: any) {
    ElMessage.error(e?.message || '添加失败')
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
    await onUncomplete(todo)
  } else {
    openCompleteDialog(todo)
  }
}

async function onUncomplete(todo: TodoItem) {
  try {
    await ElMessageBox.confirm('确定要撤销完成状态吗？', '提示', { type: 'warning' })
    await uncompleteTodo(todo.id)
    ElMessage.success('已撤销')
    await loadTodos()
  } catch {
    // 取消
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
// 菜单弹出（自定义绝对定位）
// ============================================================
function toggleMenu(id: number) {
  openMenuId.value = openMenuId.value === id ? null : id
}
function closeMenu() {
  openMenuId.value = null
}

// 点击空白处关闭菜单
function onDocumentClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.menu-wrapper')) {
    openMenuId.value = null
  }
}

// 菜单内切换颜色
async function onChangeColor(todo: TodoItem, color: string) {
  if (todo.color === color) return
  try {
    await updateTodo(todo.id, { color })
    todo.color = color
    closeMenu()
  } catch (e: any) {
    ElMessage.error(e?.message || '修改颜色失败')
  }
}

// ============================================================
// 留言
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

// 点击顶部铃铛：跳到第一个未读 todo
function openFirstNotification() {
  const first = notificationItems.value[0]
  if (first) {
    openMessagesDialog(first.todo_id)
  }
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
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' })
}

// ============================================================
// 显示/隐藏已完成 切换
// ============================================================
function toggleShowCompleted() {
  showCompleted.value = !showCompleted.value
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
  const lists = document.querySelectorAll('.date-group-wrapper')
  lists.forEach(list => {
    sortableInstance = new Sortable(list as HTMLElement, {
      animation: 150,
      handle: '.drag-handle',
      filter: '.date-divider',
      onEnd: () => {
        ElMessage.info('顺序已调整（刷新后保留）')
      },
    })
  })
}

// ============================================================
// 资源 URL 解析
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
    // 触发 groups 重算（响应式自动）
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
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style scoped>
/* ============================================================
   容器与背景（参考 bg-gray-50 + max-w-3xl 居中）
   ============================================================ */
.todo-page {
  background: #f9fafb;
  min-height: calc(100vh - 60px);
  padding: 32px 16px;
}

.todo-container {
  max-width: 768px;  /* max-w-3xl */
  margin: 0 auto;
}

/* ============================================================
   顶部工具栏（白底圆角阴影卡片）
   ============================================================ */
.toolbar-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  padding: 16px;
  margin-bottom: 24px;
}

.add-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.add-input {
  flex: 1;
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  font-size: 14px;
  transition: all 0.2s;
}

.add-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.add-btn {
  background: #3b82f6;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #2563eb;
  transform: scale(1.02);
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.search-wrap {
  position: relative;
  flex: 1;
  min-width: 200px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 8px 16px 8px 40px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  font-size: 14px;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.toggle-btn {
  background: #e5e7eb;
  color: #374151;
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
  white-space: nowrap;
}

.toggle-btn:hover {
  background: #d1d5db;
  transform: scale(1.02);
}

.toggle-btn.active {
  background: #3b82f6;
  color: white;
}

.toggle-btn.drag-toggle.active {
  background: #f59e0b;
  color: white;
}

.bell-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  border-radius: 8px;
  background: #fef3c7;
  color: #92400e;
  cursor: pointer;
  font-size: 13px;
}

.bell-icon {
  font-size: 16px;
}

.bell-badge {
  background: #ef4444;
  color: white;
  font-size: 11px;
  padding: 0 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  font-weight: 500;
}

/* ============================================================
   任务列表卡片
   ============================================================ */
.list-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.loading-state,
.empty-state {
  padding: 48px 16px;
}

/* ============================================================
   日期分隔（参考 bg-gray-50 + border-y）
   ============================================================ */
.date-divider {
  background: #f9fafb;
  color: #6b7280;
  font-weight: 500;
  padding: 8px 16px;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

/* ============================================================
   任务卡片（6 色直接应用到卡片本身）
   ============================================================ */
.task-card {
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border-bottom: 1px solid #f3f4f6;
  transition: all 0.3s ease;
}

.task-card:last-child {
  border-bottom: none;
}

.task-card.is-completed {
  opacity: 0.7;
}

.task-card.color-white { background: #ffffff; }
.task-card.color-red   { background: #fee2e2; }
.task-card.color-yellow{ background: #fef3c7; }
.task-card.color-green { background: #d1fae5; }
.task-card.color-blue  { background: #dbeafe; }
.task-card.color-dark  { background: #e5e7eb; }

/* 圆形复选框（参考 w-5 h-5 rounded-full） */
.task-checkbox {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  flex-shrink: 0;
  margin-top: 2px;
  position: relative;
  background: white;
  transition: all 0.2s;
}

.task-checkbox:hover {
  border-color: #9ca3af;
}

.task-checkbox:checked {
  background: #3b82f6;
  border-color: #3b82f6;
}

.task-checkbox:checked::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 1px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* ============================================================
   任务主体（内容 + 备注 + 图片）
   ============================================================ */
.task-main {
  flex: 1;
  min-width: 0;
}

.content-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-content {
  font-size: 15px;
  color: #1f2937;
  word-break: break-word;
  transition: all 0.3s;
  line-height: 1.5;
}

.task-content.completed {
  text-decoration: line-through;
  color: #6b7280;
}

.task-author {
  font-size: 11px;
  color: #6b7280;
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

/* 红点通知（标题右方的红底圆形 + 数字） */
.unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: #ef4444;
  color: white;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  animation: pulse-badge 1.5s ease-in-out infinite;
}

@keyframes pulse-badge {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50%      { box-shadow: 0 0 0 4px rgba(239, 68, 68, 0); }
}

/* 备注预览（line-clamp-1） */
.note-text {
  color: #6b7280;
  font-size: 13px;
  margin-top: 4px;
  line-height: 1.5;
  cursor: pointer;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.note-text:hover {
  color: #3b82f6;
}

.note-expand {
  color: #3b82f6;
  font-size: 12px;
  margin-left: 4px;
  cursor: pointer;
}

/* 任务附图缩略图 */
.task-thumb {
  width: 80px;
  height: 80px;
  border-radius: 6px;
  margin-top: 6px;
  cursor: pointer;
}

/* ============================================================
   任务操作区
   ============================================================ */
.task-actions {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  flex-shrink: 0;
}

/* 查看完成情况按钮（位于菜单按钮左边） */
.completion-btn {
  background: #d1fae5;
  color: #065f46;
  border: none;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
  white-space: nowrap;
}

.completion-btn:hover {
  background: #a7f3d0;
}

/* ============================================================
   自定义菜单弹出（参考绝对定位 + 6 颜色圆点 + 操作按钮）
   ============================================================ */
.menu-wrapper {
  position: relative;
}

.menu-trigger {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.menu-trigger:hover {
  color: #4b5563;
  background: rgba(0, 0, 0, 0.05);
}

.task-menu-dropdown {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 4px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1), 0 0 0 1px #e5e7eb;
  z-index: 20;
  min-width: 160px;
  padding: 4px 0;
}

.color-row {
  display: flex;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid #f3f4f6;
}

.color-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s;
  border: 2px solid transparent;
  background: white;
  padding: 0;
}

.color-dot:hover {
  transform: scale(1.15);
}

.color-dot.selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.color-dot.bg-white  { background: #ffffff; border-color: #d1d5db; }
.color-dot.bg-red    { background: #fee2e2; }
.color-dot.bg-yellow { background: #fef3c7; }
.color-dot.bg-green  { background: #d1fae5; }
.color-dot.bg-blue   { background: #dbeafe; }
.color-dot.bg-dark   { background: #e5e7eb; }

.menu-btn {
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  font-size: 13px;
  color: #374151;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.15s;
}

.menu-btn:hover {
  background: #f9fafb;
}

.menu-btn.danger {
  color: #ef4444;
}

.menu-btn.danger:hover {
  background: #fef2f2;
}

/* 菜单弹出动画 */
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ============================================================
   拖拽手柄（参考 drag-handle action-btn）
   ============================================================ */
.drag-handle {
  color: #9ca3af;
  cursor: grab;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: transparent;
  border: none;
  font-size: 16px;
  transition: all 0.2s;
}

.drag-handle:hover {
  color: #4b5563;
  background: rgba(0, 0, 0, 0.05);
}

.drag-handle:active {
  cursor: grabbing;
}

/* ============================================================
   弹窗内的颜色选择器（添加/修改任务时）
   ============================================================ */
.color-picker {
  display: flex;
  gap: 8px;
}

.color-picker .color-dot {
  width: 28px;
  height: 28px;
}

.color-picker .color-dot.active {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  transform: scale(1.1);
}

.uploaded-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.preview-thumb {
  width: 60px;
  height: 60px;
  border-radius: 4px;
}

/* ============================================================
   完成情况查看弹窗
   ============================================================ */
.completion-view .cv-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #374151;
  font-weight: 500;
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

/* ============================================================
   留言列表
   ============================================================ */
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

/* ============================================================
   底部统计栏（参考 mt-6 text-center text-gray-600 text-sm）
   ============================================================ */
.stats-bar {
  margin-top: 24px;
  text-align: center;
  color: #6b7280;
  font-size: 13px;
}
</style>
