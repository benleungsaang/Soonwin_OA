<template>
  <div class="todo-page">
    <CommonHeader title="待办事项" />

    <div class="todo-container">
      <!-- ============ 搜索栏 + 管理员筛选（独立圆角容器） ============ -->
      <div class="search-row">
        <div class="search-bar">
          <div class="search-inner">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input v-model="searchKeyword" class="search-input" placeholder="按 Enter 搜索任务…" @keypress.enter="onSearchEnter" />
            <button v-if="searchKeyword" class="search-clear" @click="clearSearch">清除</button>
          </div>
        </div>
        <div v-if="isAdmin" class="search-filter-box">
          <span class="at-label">用户</span>
          <select v-model="selectedUserId" class="at-select">
            <option value="">全部用户</option>
            <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.name }}</option>
          </select>
        </div>
      </div>

      <!-- ============ 药丸式 Tab ============ -->
      <div class="tabs-bar">
        <button v-for="t in tabDefs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">
          {{ t.label }}
          <span v-if="t.key !== 'deleted' || t.count > 0" class="tab-count">{{ t.count }}</span>
        </button>
        <!-- 通知铃铛 -->
        <div v-if="totalUnread > 0" class="bell-btn" title="有新留言未读" @click="openFirstNotification">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          <span class="bell-badge">{{ totalUnread > 99 ? '99+' : totalUnread }}</span>
        </div>
      </div>

      <!-- ============ 任务列表 ============ -->
      <div class="list-card">
        <div v-if="loading && todos.length === 0" class="loading-state">
          <el-skeleton :rows="3" animated />
        </div>

        <!-- ====== 回收站列表 ====== -->
        <template v-else-if="activeTab === 'deleted'">
          <div v-if="filteredDeleted.length === 0" class="empty-state">
            <el-empty description="回收站暂无内容" />
          </div>
          <div v-for="dt in filteredDeleted" :key="dt.id" class="item-row deleted-row" :class="{'menu-open': openMenuId === dt.id}" @click="openViewDialog(dt)">
            <!-- 灰色圆点 -->
            <span class="color-dot dot-dark"></span>

            <!-- 任务内容 -->
            <div class="item-main">
              <span class="item-text">{{ dt.content }}</span>
            </div>

            <!-- 缩略图 -->
            <span class="thumb-area">
              <img v-if="dt.image_url" :src="resolveAssetUrl(dt.image_url, 'thumbnail')" class="item-thumb img-border" alt="附图" @click.stop="openImageViewer(dt.image_url)" />
              <span v-else class="thumb-placeholder"></span>
            </span>

            <!-- 右侧固定组（作者 + 三点菜单） -->
            <span class="item-right-group">
              <span class="author-pill">{{ dt.author_name || dt.author_id }}</span>
              <!-- 三点菜单 -->
              <div class="menu-wrapper" @click.stop>
                <button class="menu-trigger" :class="{ open: openMenuId === dt.id }" @click="toggleMenu(dt.id)">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="3" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="8" cy="13" r="1.5"/></svg>
                </button>
                <transition name="menu-fade">
                  <div v-show="openMenuId === dt.id" class="task-menu-dropdown" @click.stop>
                    <div class="menu-divider" style="margin:0"></div>
                    <button class="menu-btn" @click="onRestoreTodo(dt); closeMenu()">
                      <span class="mi-fixed">↶</span><span>恢复</span>
                    </button>
                    <button v-if="isAdmin" class="menu-btn danger" @click="onPermanentDelete(dt); closeMenu()">
                      <span class="mi-fixed">🗑️</span><span>彻底删除</span>
                    </button>
                  </div>
                </transition>
              </div>
            </span>
          </div>
        </template>

        <!-- ====== 常规空状态 ====== -->
        <div v-else-if="groupedDates.length === 0" class="empty-state">
          <el-empty :description="searchKeyword ? '没有找到匹配的任务' : '暂无任务，开始添加吧！'" />
        </div>

        <!-- ====== 常规列表（活跃条目） ====== -->
        <template v-else>
          <div v-for="date in groupedDates" :key="date">
            <div class="date-divider">{{ formatDateLabel(date) }}</div>

            <div
              v-for="todo in groups[date]"
              :key="todo.id"
              class="item-row"
              :class="{
                completed: todo.status === 'completed',
                'menu-open': openMenuId === todo.id,
              }"
              @click="openViewDialog(todo)"
            >
              <!-- 彩色圆点 -->
              <span class="color-dot" :class="'dot-' + todo.color"></span>

              <!-- 复选框 -->
              <div class="chk-box" :class="{ checked: todo.status === 'completed' }" @click.stop="onToggleComplete(todo)"></div>

              <!-- 任务内容 -->
              <div class="item-main">
                <span class="item-text" :class="{ done: todo.status === 'completed' }">{{ todo.content }}</span>
              </div>

              <!-- 缩略图（固定位置占位，无图时留空保持对齐） -->
              <span class="thumb-area">
                <img v-if="todo.image_url" :src="resolveAssetUrl(todo.image_url, 'thumbnail')" class="item-thumb img-border" alt="附图" @click.stop="openImageViewer(todo.image_url)" />
                <span v-else class="thumb-placeholder"></span>
              </span>

              <!-- 右侧固定组（作者 + 未读红点 + 三点菜单 → 居右） -->
              <span class="item-right-group">
                <!-- 作者 -->
                <span class="author-pill">{{ todo.author_name || todo.author_id }}</span>
                <!-- 共享徽标 -->
                <span v-if="isAdmin && todo.shared_count && todo.shared_count > 0" class="shared-badge" :title="`已设置可见性（${todo.shared_count} 人）`" @click.stop="openVisibilityDialog(todo)">👥</span>
                <!-- 未读红点 -->
                <span v-if="todo.unread_count > 0" class="unread-dot" :title="`${todo.unread_count} 条新留言`" @click.stop="openMessagesDialog(todo.id)">{{ todo.unread_count }}</span>
                <!-- 三点菜单 -->
                <div class="menu-wrapper" @click.stop>
                  <button class="menu-trigger" :class="{ open: openMenuId === todo.id }" @click="toggleMenu(todo.id)">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="3" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="8" cy="13" r="1.5"/></svg>
                  </button>
                  <transition name="menu-fade">
                    <div v-show="openMenuId === todo.id" class="task-menu-dropdown" @click.stop>
                    <div class="menu-color-row">
                      <button v-for="c in colorOptions" :key="c.value" class="color-dot-btn" :class="['bg-'+c.value,{active:todo.color===c.value}]" :title="c.label" @click="onChangeColor(todo, c.value)" />
                    </div>
                    <div class="menu-divider"></div>
                    <button class="menu-btn" @click="openEditDialog(todo); closeMenu()">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                      <span>修改内容</span>
                    </button>
                    <button v-if="isAdmin" class="menu-btn" @click="openVisibilityDialog(todo); closeMenu()">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                      <span>可见性</span>
                    </button>
                    <button v-if="canModify(todo)" class="menu-btn danger" @click="onDelete(todo); closeMenu()">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
                      <span>删除</span>
                    </button>
                  </div>
                </transition>
              </div>
            </span>
          </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ============ FAB 按钮 ============ -->
    <button class="fab-btn" @click="openCreateDialog" title="新建任务">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
    </button>

    <!-- ============================================================
         详情弹窗（左轨时间线 + V2 边框块 + V4 行内输入）
         ============================================================ -->
    <el-dialog v-model="viewDialogVisible" title="任务详情" width="640px" top="8vh" @closed="onDetailClosed">
      <div class="da-outer">
        <div class="da-rail">
          <div class="da-rail-line"></div>
          <div class="da-rail-dot"></div>
        </div>
        <div class="da-card a1b-card">
          <!-- 块 1：基础信息 -->
          <div class="a1b-block">
            <div class="da-top">
              <span class="da-status" :class="viewingTodo?.status==='completed'?'da-done':'da-pending'">{{ viewingTodo?.status==='completed'?'✓ 已完成':'● 待完成' }}</span>
              <span class="da-date">{{ viewingTodo?.date }}</span>
              <span class="da-author">{{ viewingTodo?.author_name || viewingTodo?.author_id }}</span>
            </div>
            <div class="da-subject">{{ viewingTodo?.content }}</div>
            <div v-if="viewingTodo?.note" class="da-note-text">{{ viewingTodo.note }}</div>
            <div v-if="viewingTodo?.image_url" class="da-img-wrap">
              <img :src="resolveAssetUrl(viewingTodo.image_url)" class="d-thumb da-thumb img-border" style="object-fit:cover;background:#f3f4f6" @click.stop="openImageViewer(viewingTodo!.image_url!)" />
            </div>
          </div>

          <!-- 块 2：留言 + 行内输入（已删除条目不显示） -->
          <div v-if="!viewingTodo?.is_deleted" class="a1b-block a1b-block-msg">
            <div class="a1b-block-title">💬 留言</div>
            <div v-if="detailMessages.length === 0" class="a1b-empty-msg">暂无留言</div>
            <div v-else class="a1a-messages">
              <div v-for="msg in detailMessages" :key="msg.id" class="a1-bubble" :class="msg.author_id===currentEmpId?'a1-self':'a1-other'">
                <div class="a1-bubble-author">{{ msg.author_name || msg.author_id }}</div>
                <div class="a1-bubble-text">{{ msg.content }}</div>
                <div v-if="msg.image_url" class="a1-bubble-img">
                  <img :src="resolveAssetUrl(msg.image_url)" class="d-thumb img-border" style="cursor:pointer" @click.stop="openImageViewer(msg.image_url)" />
                </div>
                <div class="a1-bubble-time">{{ msg.created_at }}</div>
              </div>
            </div>
            <!-- 行内输入（管理员或创建人可留言） -->
            <div v-if="isAdmin || viewingTodo?.author_id === currentEmpId" class="a1d-inline-input">
              <input v-model="msgInput" ref="msgInputRef" type="text" class="a1d-input" placeholder="输入留言内容…（支持 Ctrl+V 粘贴图片）" maxlength="300" @keypress.enter="sendMessage" @paste="onMsgPaste" />
              <div class="a1d-actions">
                <button type="button" class="a1d-action-btn" title="插入 emoji" @click.stop="toggleMsgEmoji"><span style="font-size:18px">😊</span></button>
                <button type="button" class="a1d-action-btn" title="上传图片" @click="handleMsgImageUpload"><span style="font-size:18px">🖼️</span></button>
                <button class="a1d-send-btn" :disabled="!msgInput.trim() && !msgImageUrl" @click="sendMessage">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
                </button>
              </div>
              <div v-if="msgImageUrl" class="a1d-msg-img">
                <img :src="msgImageUrl" class="a1d-msg-img-thumb" />
                <button class="a1d-msg-img-remove" @click="msgImageUrl=''">✕</button>
              </div>
              <div v-show="msgEmojiVisible" class="a1d-emoji-popup" @click.stop>
                <emoji-picker class="a1d-emoji-picker" @emoji-click="insertMsgEmoji" />
              </div>
            </div>
          </div>

          <!-- 块 3：完成情况（仅已完成且未删除时显示） -->
          <div v-if="viewingTodo?.status === 'completed' && !viewingTodo?.is_deleted" class="a1b-block a1b-block-supp">
            <div class="a1b-block-title">✅ 完成情况</div>
            <div class="a1b-supp-text">{{ viewingTodo.completion_note || '未填写完成说明' }}</div>
            <div v-if="viewingTodo?.completion_image_url" class="a1b-supp-img">
              <img :src="resolveAssetUrl(viewingTodo.completion_image_url)" class="d-thumb da-thumb img-border" style="object-fit:cover" @click.stop="openImageViewer(viewingTodo!.completion_image_url!)" />
            </div>
            <div v-if="viewingTodo?.completed_at" class="a1b-supp-time">{{ viewingTodo.completed_at }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button v-if="canModify(viewingTodo)" type="primary" @click="switchViewToEdit">修改</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         新建/修改弹窗（C · 聊天式）
         ============================================================ -->
    <el-dialog v-model="formVisible" :title="formMode==='edit'?'修改内容':'新建任务'" width="500px" top="10vh" @closed="onFormClosed">
      <div class="ntc-body">
        <div class="ntc-title-row">
          <input v-model="formTitle" ref="formTitleRef" class="ntc-title-input" :placeholder="formMode==='edit'?'修改任务标题…':'任务标题'" maxlength="100" />
        </div>
        <div class="ntc-sep"></div>
        <RichInput
          :key="'form-' + (formEditId || 'new') + '-' + formVisible"
          v-model="formContent"
          custom-class="todo-form-rich"
          placeholder="备注内容…支持 emoji 📝"
          :maxlength="500"
          :rows="3"
          :features="{ emoji: true, image: true, paste: true }"
          :upload="{ api: todoUploadApi, maxSizeMB: 5 }"
          size="default"
          toolbar="bottom"
          @image-uploaded="(r: any) => formImageUrl = r.url"
        >
          <template #toolbar-extra>
            <div style="position:relative;display:inline-flex">
              <div class="ntc-color-chip" :class="'bg-'+formColor" style="cursor:pointer" @click.stop="formColorVisible=!formColorVisible"></div>
              <div v-show="formColorVisible" class="ntc-color-pop" @click.stop>
                <button v-for="c in colorOptions" :key="c.value" class="color-dot-btn" :class="['bg-'+c.value,{active:formColor===c.value}]" :title="c.label" @click="formColor=c.value; formColorVisible=false" />
              </div>
            </div>
            <input v-model="formDate" type="date" class="ntc-date-input" style="margin-left:4px" />
          </template>
        </RichInput>
      </div>
      <template #footer>
        <el-button @click="formVisible=false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitTaskForm">{{ formMode==='edit'?'保存修改':'确认添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         标记完成弹窗
         ============================================================ -->
    <el-dialog v-model="completeDialogVisible" title="标记完成" width="480px" top="20vh">
      <el-alert title="完成时必须填写文字或图片（至少一项）" type="info" :closable="false" style="margin-bottom:14px" />
      <div class="complete-body">
        <RichInput
          :key="'complete-' + completeDialogVisible"
          v-model="completeForm.completion_note"
          custom-class="todo-complete-rich"
          placeholder="简单说明完成情况…"
          :maxlength="500"
          :rows="3"
          :features="{ emoji: true, image: true, paste: true }"
          :upload="{ api: completeUploadApi, maxSizeMB: 5 }"
          size="default"
          toolbar="bottom"
          @image-uploaded="(r: any) => completeForm.completion_image_url = r.url"
        />
      </div>
      <template #footer>
        <el-button @click="completeDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitComplete">确认完成</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         添加备注弹窗
         ============================================================ -->
    <el-dialog v-model="messageDialogVisible" title="添加备注" width="420px" top="20vh">
      <div class="input-with-emoji" style="position:relative">
        <el-input v-model="newMessageContent" type="textarea" :rows="4" placeholder="备注内容（仅管理员可添加）" maxlength="300" show-word-limit />
        <button type="button" class="emoji-btn" @click="toggleEmoji('message')">😊</button>
        <div v-show="emojiVisible.message" class="emoji-wrapper"><emoji-picker class="emoji-picker" @emoji-click="(e)=>newMessageContent+=e.detail.emoji.unicode" /></div>
      </div>
      <template #footer>
        <el-button @click="messageDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAddMessage">添加</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         留言列表弹窗
         ============================================================ -->
    <el-dialog v-model="messagesViewVisible" title="留言记录" width="480px" top="15vh">
      <div v-if="messages.length===0" class="empty-msg">暂无留言</div>
      <div v-else class="msg-list">
        <div v-for="msg in messages" :key="msg.id" class="msg-item">
          <div class="msg-header">
            <span class="msg-author">{{ msg.author_name || msg.author_id }}</span>
            <span class="msg-time">{{ msg.created_at }}</span>
            <el-button v-if="isAdmin" link type="danger" size="small" @click="onDeleteMessage(msg.id)">删除</el-button>
          </div>
          <div class="msg-content">{{ msg.content }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="messagesViewVisible=false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============ 可见性设置弹窗（仅管理员） ============ -->
    <el-dialog v-model="visibilityDialogVisible" title="设置可见性" width="480px" top="10vh" @closed="visibilitySelected=[]">
      <div class="visibility-dialog-inner">
        <p class="vis-hint">选择可查看此任务的员工。留空则仅<b>创建人</b>和<b>管理员</b>可见。</p>
        <el-select
          v-model="visibilitySelected"
          multiple
          filterable
          placeholder="搜索并选择员工…"
          style="width:100%"
          :loading="visibilitySaving"
        >
          <el-option
            v-for="e in allEmployees"
            :key="e.emp_id"
            :label="`${e.name}（${e.emp_id}）`"
            :value="e.emp_id"
          />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="visibilityDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="visibilitySaving" @click="confirmVisibility">保存</el-button>
      </template>
    </el-dialog>

    <!-- ============ 图片灯箱（滚轮缩放 + 拖动 + 点击空白关闭） ============ -->
    <el-image-viewer v-if="imageViewerVisible" hide-on-click-modal :url-list="[resolveAssetUrl(imageViewerUrl)]" @close="imageViewerVisible=false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import 'emoji-picker-element'
import CommonHeader from '@/components/CommonHeader.vue'
import RichInput from '@/components/RichInput.vue'
import type { RichInputUploadApi } from '@/components/RichInput.vue'
import {
  getTodos, getTodo, createTodo, updateTodo, deleteTodo,
  completeTodo, uncompleteTodo, uploadTodoImage,
  getTodoMessages, addTodoMessage, deleteTodoMessage,
  getTodoNotifications, clearTodoNotifications,
  getDeletedTodos, restoreTodo, permanentDeleteTodo,
  updateTodoVisibility, getActiveEmployees,
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
const activeSearch = ref('')  // 按 Enter 后才真正生效的搜索词
const activeTab = ref('all')
const isAdmin = ref(false)
const currentEmpId = ref('')
const openMenuId = ref<number | null>(null)
const notificationItems = ref<any[]>([])
const totalUnread = computed(() => notificationItems.value.reduce((s: number, n: any) => s + n.unread_count, 0))
const imageViewerVisible = ref(false)
const imageViewerUrl = ref('')

// 用户筛选 + 回收站
const selectedUserId = ref('')
const deletedTodos = ref<TodoItem[]>([])
const deletedCount = ref(0)

// 可见性设置弹窗（仅管理员）
const visibilityDialogVisible = ref(false)
const visibilityTodoId = ref<number | null>(null)
const visibilitySelected = ref<string[]>([])
const visibilitySaving = ref(false)
const allEmployees = ref<Array<{ emp_id: string; name: string }>>([])

// 用户筛选后的回收站条目
const filteredDeleted = computed(() => {
  if (!selectedUserId.value) return deletedTodos.value
  return deletedTodos.value.filter(t => t.author_id === selectedUserId.value)
})

// 提取所有用户（用于筛选下拉，同时从活跃条目和回收站中提取）
const allUsers = computed(() => {
  const map = new Map<string, string>()
  for (const t of todos.value) {
    if (!map.has(t.author_id)) {
      map.set(t.author_id, t.author_name || t.author_id)
    }
  }
  for (const t of deletedTodos.value) {
    if (!map.has(t.author_id)) {
      map.set(t.author_id, t.author_name || t.author_id)
    }
  }
  return Array.from(map.entries()).map(([id, name]) => ({ id, name }))
})

// emoji picker 状态
const emojiVisible = reactive<Record<string, boolean>>({ content: false, note: false, completion: false, message: false })

// RichInput 上传 API（返回完整可访问路径）
function resolveMediaUrl(rawUrl: string): { url: string; thumbnailUrl: string } {
  const prefix = '/assets/TodoMedia/'
  const url = prefix + rawUrl
  const thumbnailUrl = rawUrl.includes('_display.webp')
    ? prefix + rawUrl.replace('_display.webp', '_thumbnail.webp')
    : url
  return { url, thumbnailUrl }
}
const todoUploadApi: RichInputUploadApi = async (file) => {
  const res: any = await uploadTodoImage(file, 'todo')
  const raw = res?.image_url || res?.data?.image_url
  return raw ? resolveMediaUrl(raw) : { url: '' }
}
const completeUploadApi: RichInputUploadApi = async (file) => {
  const res: any = await uploadTodoImage(file, 'completion')
  const raw = res?.image_url || res?.data?.image_url
  return raw ? resolveMediaUrl(raw) : { url: '' }
}

// ============================================================
// Tab 定义（动态计算数量）
// ============================================================
const tabDefs = computed(() => {
  const defs = [
    { key: 'all',       label: '全部',     count: todos.value.length },
    { key: 'pending',   label: '待完成',   count: todos.value.filter(t => t.status === 'pending').length },
    { key: 'completed', label: '已完成',   count: todos.value.filter(t => t.status === 'completed').length },
    { key: 'urgent',    label: '紧急',     count: todos.value.filter(t => t.color === 'red').length },
  ]
  if (isAdmin.value) {
    defs.push({ key: 'deleted', label: '🗑️ 回收站', count: deletedCount.value })
  }
  return defs
})

// ============================================================
// 颜色
// ============================================================
const colorOptions = [
  { value: 'white',  label: '默认' },
  { value: 'red',    label: '紧急' },
  { value: 'yellow', label: '重要' },
  { value: 'green',  label: '完成' },
  { value: 'blue',   label: '进行中' },
  { value: 'dark',   label: '长期' },
]
function colorLabel(v: string) { return colorOptions.find(c => c.value === v)?.label || v }

// ============================================================
// 资源 URL 解析
// ============================================================
function resolveAssetUrl(url: string, variant?: 'display' | 'thumbnail'): string {
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('blob:') || url.startsWith('data:')) return url
  if (url.startsWith('/')) return url
  // 新上传的图片是 WebP 双尺寸：_display.webp（详情/灯箱）/_thumbnail.webp（缩略图）
  if (variant === 'thumbnail' && url.includes('_display.webp')) {
    url = url.replace('_display.webp', '_thumbnail.webp')
  }
  return '/assets/TodoMedia/' + url
}

// ============================================================
// 图片灯箱
// ============================================================
function openImageViewer(url: string) {
  imageViewerUrl.value = url
  imageViewerVisible.value = true
}

// ============================================================
// Tab 切换 + 搜索
// ============================================================
function switchTab(key: string) {
  activeTab.value = key
  if (key === 'deleted') {
    loadDeletedTodos()
  } else {
    loadTodos()
  }
}

function onSearchEnter() {
  activeSearch.value = searchKeyword.value.trim()
  loadTodos()
}

function clearSearch() {
  searchKeyword.value = ''
  activeSearch.value = ''
  loadTodos()
}

// ============================================================
// 分组与日期
// ============================================================
const groups = computed<Record<string, TodoItem[]>>(() => {
  const g: Record<string, TodoItem[]> = {}
  for (const t of todos.value) {
    if (selectedUserId.value && t.author_id !== selectedUserId.value) continue
    if (!g[t.date]) g[t.date] = []
    g[t.date].push(t)
  }
  return g
})
const groupedDates = computed(() => Object.keys(groups.value).sort((a, b) => b.localeCompare(a)))

function formatDateLabel(date: string): string {
  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
  if (date === today) return '今天'
  if (date === yesterday) return '昨天'
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' })
}

// ============================================================
// 加载数据
// ============================================================
async function loadTodos() {
  loading.value = true
  try {
    const params: any = {}
    if (activeSearch.value) params.search = activeSearch.value
    if (activeTab.value === 'pending') params.status = 'pending'
    else if (activeTab.value === 'completed') params.status = 'completed'
    const res: any = await getTodos(params)
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
// 三点菜单
// ============================================================
function toggleMenu(id: number) { openMenuId.value = openMenuId.value === id ? null : id }
function closeMenu() { openMenuId.value = null }

function onDocumentClick(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (!t.closest('.menu-wrapper')) openMenuId.value = null
  // emoji close（兼容新旧类名）
  if (!t.closest('.emoji-wrapper') && !t.closest('.emoji-btn') && !t.closest('.ntc-emoji-pop') && !t.closest('.ntc-tool-btn')) {
    for (const k of Object.keys(emojiVisible)) emojiVisible[k] = false
  }
  if (!t.closest('.a1d-emoji-popup') && !t.closest('.a1d-action-btn')) msgEmojiVisible.value = false
  if (!t.closest('.ntc-emoji-pop') && !t.closest('.ntc-tool-btn')) {}  // RichInput 自行管理 emoji
  if (!t.closest('.ntc-color-pop') && !t.closest('.ntc-color-chip')) formColorVisible.value = false
}

// ============================================================
// 颜色修改
// ============================================================
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
// 权限
// ============================================================
function canModify(todo: TodoItem | null): boolean {
  if (!todo) return false
  if (todo.is_deleted) return false
  return isAdmin.value || todo.author_id === currentEmpId.value
}

// ============================================================
// 删除
// ============================================================
async function onDelete(todo: TodoItem) {
  try {
    await ElMessageBox.confirm(`确定删除任务"${todo.content}"吗？`, '提示', { type: 'warning' })
    await deleteTodo(todo.id)
    ElMessage.success('已删除')
    await loadTodos()
  } catch { /* cancel */ }
}

// ============================================================
// 完成 / 撤销
// ============================================================
const completeDialogVisible = ref(false)
const completingTodo = ref<TodoItem | null>(null)
const completeForm = reactive({ completion_note: '', completion_image_url: '' })

function openCompleteDialog(todo: TodoItem) {
  completingTodo.value = todo
  completeForm.completion_note = todo.completion_note || ''
  completeForm.completion_image_url = todo.completion_image_url || ''
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
    await ElMessageBox.confirm(
      `确定撤销"${todo.content}"的完成状态吗？\n（已填写的完成内容会保留）`,
      '提示', { type: 'warning' }
    )
    await uncompleteTodo(todo.id)
    ElMessage.success('已撤销')
    await loadTodos()
  } catch { /* cancel */ }
}

// ============================================================
// 可见性设置（仅管理员）
// ============================================================
async function openVisibilityDialog(todo: TodoItem) {
  visibilityTodoId.value = todo.id
  // 加载已激活员工列表（首次打开时）
  if (allEmployees.value.length === 0) {
    try {
      const res: any = await getActiveEmployees()
      allEmployees.value = Array.isArray(res) ? res : []
    } catch { /* silent */ }
  }
  // 从详情接口获取当前 visible_to
  try {
    const detail: any = await getTodo(todo.id)
    visibilitySelected.value = detail?.visible_to || []
  } catch {
    visibilitySelected.value = []
  }
  visibilityDialogVisible.value = true
}

async function confirmVisibility() {
  if (!visibilityTodoId.value) return
  visibilitySaving.value = true
  try {
    await updateTodoVisibility(visibilityTodoId.value, visibilitySelected.value)
    ElMessage.success('可见性已更新')
    visibilityDialogVisible.value = false
    await loadTodos()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || '保存失败')
  } finally {
    visibilitySaving.value = false
  }
}

// ============================================================
// 图片上传
// ============================================================
function beforeImageUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) ElMessage.error('只能上传图片')
  if (!isLt5M) ElMessage.error('图片大小不能超过 5MB')
  return isImage && isLt5M
}

// ============================================================
// 详情弹窗
// ============================================================
const viewDialogVisible = ref(false)
const viewingTodo = ref<TodoItem | null>(null)
const detailMessages = ref<TodoMessage[]>([])

async function openViewDialog(todo: TodoItem) {
  viewingTodo.value = todo
  try {
    const res: any = await getTodo(todo.id)
    if (res?.messages) detailMessages.value = res.messages
    else detailMessages.value = []
    viewDialogVisible.value = true
    await clearTodoNotifications(todo.id)
    await loadNotifications()
  } catch {
    detailMessages.value = []
    viewDialogVisible.value = true
  }
}

function onDetailClosed() {
  // 关闭详情后刷新列表（更新未读计数等）
  loadTodos()
}

function switchViewToEdit() {
  if (!viewingTodo.value) return
  viewDialogVisible.value = false
  setTimeout(() => openEditDialog(viewingTodo.value!), 100)
}

// ============================================================
// 详情弹窗 - 留言输入（V4 行内）
// ============================================================
const msgInput = ref('')
const msgInputRef = ref<HTMLInputElement | null>(null)
const msgEmojiVisible = ref(false)
const msgImageUrl = ref('')
const msgFileInputRef = ref<HTMLInputElement | null>(null)

function toggleMsgEmoji() { msgEmojiVisible.value = !msgEmojiVisible.value }

function insertMsgEmoji(event: any) {
  const emoji = event.detail.emoji.unicode
  const el = msgInputRef.value
  if (el) {
    const start = el.selectionStart ?? msgInput.value.length
    const end = el.selectionEnd ?? start
    msgInput.value = msgInput.value.substring(0, start) + emoji + msgInput.value.substring(end)
    nextTick(() => { el.selectionStart = el.selectionEnd = start + emoji.length; el.focus() })
  } else {
    msgInput.value += emoji
  }
}

async function sendMessage() {
  if ((!msgInput.value.trim() && !msgImageUrl.value) || !viewingTodo.value) return
  try {
    await addTodoMessage(viewingTodo.value.id, msgInput.value.trim(), msgImageUrl.value || undefined)
    const res: any = await getTodo(viewingTodo.value.id)
    if (res?.messages) detailMessages.value = res.messages
    msgInput.value = ''
    msgImageUrl.value = ''
  } catch (e: any) {
    ElMessage.error(e?.message || '发送失败')
  }
}

function handleMsgImageUpload() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (e: any) => {
    const file = e.target?.files?.[0]
    if (!file || !beforeImageUpload(file)) return
    try {
      const res: any = await uploadTodoImage(file, 'todo')
      const url = res?.image_url || res?.data?.image_url
      if (url) { msgImageUrl.value = '/assets/TodoMedia/' + url; ElMessage.success('图片已上传') }
    } catch (err: any) { ElMessage.error(err?.message || '上传失败') }
  }
  input.click()
}

function onMsgPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (let i = 0; i < items.length; i++) {
    const f = items[i].getAsFile()
    if (f && f.type.startsWith('image/')) {
      e.preventDefault()
      if (!beforeImageUpload(f)) return
      uploadTodoImage(f, 'todo').then((res: any) => {
        const url = res?.image_url || res?.data?.image_url
        if (url) msgImageUrl.value = '/assets/TodoMedia/' + url
      }).catch((err: any) => ElMessage.error(err?.message || '图片上传失败'))
      break
    }
  }
}

// ============================================================
// 新建 / 修改弹窗（C · 聊天式）
// ============================================================
const formMode = ref<'create' | 'edit'>('create')
const formVisible = ref(false)
const formEditId = ref<number | null>(null)
const formTitle = ref('')
const formContent = ref('')
const formDate = ref('')
const formColor = ref('white')
const formImageUrl = ref('')
const formTitleRef = ref<HTMLInputElement | null>(null)
const formColorVisible = ref(false)

function resetForm() {
  formTitle.value = ''
  formContent.value = ''
  formDate.value = new Date().toISOString().split('T')[0]
  formColor.value = 'white'
  formImageUrl.value = ''
  formEditId.value = null
}

function openCreateDialog() {
  formMode.value = 'create'
  resetForm()
  formVisible.value = true
}

function openEditDialog(todo: TodoItem) {
  formMode.value = 'edit'
  formTitle.value = todo.content
  formContent.value = todo.note || ''
  formDate.value = todo.date
  formColor.value = todo.color
  formImageUrl.value = todo.image_url || ''
  formEditId.value = todo.id
  formVisible.value = true
}

function onFormClosed() {
  // nothing needed
}

async function submitTaskForm() {
  if (!formTitle.value.trim()) { ElMessage.warning('请输入任务标题'); return }
  submitting.value = true
  try {
    const payload = {
      content: formTitle.value.trim(),
      date: formDate.value || new Date().toISOString().split('T')[0],
      color: formColor.value,
      note: formContent.value.trim(),
      image_url: formImageUrl.value || undefined,
    }
    if (formMode.value === 'edit' && formEditId.value) {
      await updateTodo(formEditId.value, payload)
      ElMessage.success('已更新')
    } else {
      await createTodo(payload)
      ElMessage.success('已添加')
    }
    formVisible.value = false
    await loadTodos()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

// ============================================================
// 留言（管理员添加/查看）
// ============================================================
const messageDialogVisible = ref(false)
const newMessageContent = ref('')
const messagingTodo = ref<TodoItem | null>(null)

const messagesViewVisible = ref(false)
const messages = ref<TodoMessage[]>([])

function openAddMessageDialog(todo: TodoItem) {
  messagingTodo.value = todo
  newMessageContent.value = ''
  messageDialogVisible.value = true
}

async function submitAddMessage() {
  if (!messagingTodo.value) return
  if (!newMessageContent.value.trim()) { ElMessage.warning('备注内容不能为空'); return }
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
    messagesViewVisible.value = true
    await clearTodoNotifications(todoId)
    await loadNotifications()
    await loadTodos()
  } catch (e: any) {
    ElMessage.error(e?.message || '加载留言失败')
  }
}

async function onDeleteMessage(msgId: number) {
  try {
    await ElMessageBox.confirm('确定删除该留言吗？', '提示', { type: 'warning' })
    await deleteTodoMessage(messages.value[0]?.todo_id || 0, msgId)
    ElMessage.success('已删除')
    messages.value = messages.value.filter(m => m.id !== msgId)
  } catch { /* cancel */ }
}

function openFirstNotification() {
  const first = notificationItems.value[0]
  if (first) openMessagesDialog(first.todo_id)
}

// ============================================================
// 回收站
// ============================================================
async function loadDeletedTodos() {
  loading.value = true
  try {
    const res: any = await getDeletedTodos()
    deletedTodos.value = res || []
    deletedCount.value = deletedTodos.value.length
  } catch (e: any) {
    ElMessage.error(e?.message || '加载回收站失败')
  } finally {
    loading.value = false
  }
}

async function onRestoreTodo(todo: TodoItem) {
  try {
    await restoreTodo(todo.id)
    ElMessage.success('已恢复')
    deletedTodos.value = deletedTodos.value.filter(t => t.id !== todo.id)
    deletedCount.value = deletedTodos.value.length
  } catch (e: any) {
    ElMessage.error(e?.message || '恢复失败')
  }
}

async function onPermanentDelete(todo: TodoItem) {
  try {
    await ElMessageBox.confirm(`确定永久删除"${todo.content}"吗？此操作不可撤销！`, '警告', { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' })
    await permanentDeleteTodo(todo.id)
    ElMessage.success('已永久删除')
    deletedTodos.value = deletedTodos.value.filter(t => t.id !== todo.id)
    deletedCount.value = deletedTodos.value.length
  } catch { /* cancel */ }
}

// ============================================================
// emoji（旧弹窗用）
// ============================================================
function toggleEmoji(target: string) {
  for (const k of Object.keys(emojiVisible)) {
    emojiVisible[k] = k === target ? !emojiVisible[target] : false
  }
}

// ============================================================
// 初始化
// ============================================================
onMounted(async () => {
  const userInfo = getCurrentUserInfo()
  isAdmin.value = userInfo?.user_role === 'admin'
  currentEmpId.value = getCurrentUserEmpId() || ''
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
   页面
   ============================================================ */
.todo-page {
  background: #f9fafb;
  min-height: calc(100vh - 60px);
  padding: 32px 16px 96px;
  position: relative;
}
.todo-container { max-width: 768px; margin: 0 auto; }

/* ============================================================
   管理员工具栏
   ============================================================ */
/* ============================================================
   搜索栏行 + 独立筛选容器
   ============================================================ */
.search-row { display: flex; align-items: stretch; gap: 10px; margin-bottom: 14px; }
.search-bar { flex: 1; min-width: 0; margin-bottom: 0; }
.search-filter-box {
  display: flex; align-items: center; gap: 6px; flex-shrink: 0;
  background: #f3f4f6; border-radius: 10px; padding: 8px 14px;
  border: 2px solid transparent;
}
.at-label { font-size: 12px; color: #6b7280; white-space: nowrap; }
.at-select {
  font-size: 13px; padding: 4px 8px; border: 1px solid #d1d5db;
  border-radius: 6px; outline: none; color: #374151; background: white;
  cursor: pointer; max-width: 130px;
}
.at-select:focus { border-color: #3b82f6; }

/* ============================================================
   回收站条目样式
   ============================================================ */
.deleted-row { opacity: 0.75; }
.deleted-row:hover { opacity: 1; }

/* ============================================================
   搜索栏
   ============================================================ */
.search-inner {
  display: flex; align-items: center; gap: 8px;
  background: #f3f4f6; border-radius: 10px; padding: 8px 14px;
  border: 2px solid transparent; transition: all 0.2s;
}
.search-inner:focus-within {
  background: white; border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.08);
}
.search-icon { flex-shrink: 0; color: #9ca3af; }
.search-input {
  flex: 1; padding: 4px 0; border: none; outline: none;
  font-size: 14px; color: #1f2937; background: transparent;
}
.search-input::placeholder { color: #9ca3af; }
.search-clear {
  flex-shrink: 0; padding: 3px 10px; border: none; border-radius: 6px;
  background: #e5e7eb; color: #6b7280; font-size: 12px; cursor: pointer;
}
.search-clear:hover { background: #d1d5db; }

/* ============================================================
   药丸式 Tab
   ============================================================ */
.tabs-bar {
  display: flex; gap: 4px; padding: 10px 14px;
  background: white; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  margin-bottom: 16px; align-items: center;
}
.tab-btn {
  flex: 1; padding: 7px 10px; font-size: 13px; font-weight: 500;
  color: #6b7280; background: transparent; border: none; border-radius: 20px;
  cursor: pointer; transition: all 0.25s;
  display: flex; align-items: center; justify-content: center; gap: 5px;
}
.tab-btn:hover { color: #374151; background: rgba(0,0,0,0.03); }
.tab-btn.active {
  color: white; background: #3b82f6;
  box-shadow: 0 2px 8px rgba(59,130,246,0.3);
}
.tab-count {
  font-size: 11px; background: rgba(0,0,0,0.08); color: inherit;
  padding: 0 7px; border-radius: 10px; line-height: 18px;
}
.tab-btn.active .tab-count { background: rgba(255,255,255,0.25); color: white; }

/* 通知铃铛 */
.bell-btn {
  position: relative; display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: 50%;
  color: #92400e; background: #fef3c7; cursor: pointer; flex-shrink: 0;
  transition: all 0.2s;
}
.bell-btn:hover { background: #fde68a; }
.bell-badge {
  position: absolute; top: -2px; right: -2px;
  min-width: 18px; height: 16px; padding: 0 5px;
  background: #ef4444; color: white; font-size: 10px; font-weight: 600;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
}

/* ============================================================
   任务列表
   ============================================================ */
.list-card {
  background: white; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.loading-state, .empty-state { padding: 48px 16px; }

.date-divider {
  background: #f9fafb; color: #374151; font-weight: 600;
  padding: 10px 16px; border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb; font-size: 15px;
}

/* ============================================================
   条目行
   ============================================================ */
.item-row {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-bottom: 1px solid #f3f4f6;
  transition: background 0.12s; cursor: pointer;
}
.item-row:last-child { border-bottom: none; }
.item-row:hover { background: #f5f7fa; }
.item-row.completed .item-text,
.item-row.completed .color-dot,
.item-row.completed .author-pill,
.item-row.completed .thumb-area { opacity: 0.6; }
.item-row.completed .chk-box { opacity: 0.8; }
.item-row.menu-open { z-index: 50; position: relative; }

/* 彩色圆点 */
.color-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; transition: transform 0.2s; }
.item-row:hover .color-dot { transform: scale(1.2); }
.dot-white  { background: #e5e7eb; }
.dot-red    { background: #f87171; }
.dot-yellow { background: #fbbf24; }
.dot-green  { background: #34d399; }
.dot-blue   { background: #60a5fa; }
.dot-dark   { background: #9ca3af; }

/* 复选框 */
.chk-box {
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid #d1d5db; flex-shrink: 0; background: white;
  position: relative; transition: all 0.2s;
}
.chk-box.checked { background: #3b82f6; border-color: #3b82f6; }
.chk-box.checked::after {
  content: ''; position: absolute; left: 5px; top: 2px;
  width: 5px; height: 9px; border: solid white;
  border-width: 0 2px 2px 0; transform: rotate(45deg);
}
.chk-box:hover { border-color: #60a5fa; }

/* 任务内容 */
.item-main { flex: 0 0 60%; min-width: 0; }
.item-text { font-size: 15px; color: #1f2937; line-height: 1.5; word-break: break-word; }
.item-text.done { text-decoration: line-through; color: #9ca3af; }

/* 右侧固定组（作者/红点/菜单 → 居右） */
.item-right-group {
  display: flex; align-items: center; gap: 10px;
  margin-left: auto; flex-shrink: 0;
}

/* 缩略图 */
.item-thumb { width: 48px; height: 36px; object-fit: cover; border-radius: 6px; flex-shrink: 0; cursor: pointer; background: #f3f4f6; }

/* 作者 */
.author-pill {
  font-size: 12px; color: #6b7280; background: #f3f4f6;
  padding: 2px 10px; border-radius: 12px; white-space: nowrap; line-height: 20px; flex-shrink: 0;
}

/* 未读红点 */
.unread-dot {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: #ef4444; color: white; border-radius: 9px;
  font-size: 11px; font-weight: 500; cursor: pointer; flex-shrink: 0;
}

/* 三点菜单 */
.menu-wrapper { position: relative; flex-shrink: 0; }
.menu-trigger {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border-radius: 6px; background: transparent; border: none;
  color: #9ca3af; cursor: pointer; transition: all 0.15s;
}
.menu-trigger:hover, .menu-trigger.open { color: #4b5563; background: rgba(0,0,0,0.05); }

.task-menu-dropdown {
  position: absolute; right: 0; top: calc(100% + 4px);
  background: white; border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.04);
  z-index: 200; min-width: 170px; padding: 6px 0;
}
.menu-color-row {
  display: flex; justify-content: center; gap: 6px; padding: 8px 14px;
}
.menu-divider { height: 1px; background: #f3f4f6; margin: 4px 8px; }
.menu-btn {
  width: 100%; text-align: left; padding: 8px 14px; font-size: 13px;
  color: #374151; background: transparent; border: none; cursor: pointer;
  display: flex; align-items: center; gap: 8px; transition: background 0.1s;
}
.menu-btn:hover { background: #f9fafb; }
.menu-btn.danger { color: #ef4444; }
.menu-btn.danger:hover { background: #fef2f2; }
.mi-fixed { display: inline-block; width: 18px; text-align: center; flex-shrink: 0; }
.menu-fade-enter-active, .menu-fade-leave-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.menu-fade-enter-from, .menu-fade-leave-to { opacity: 0; transform: translateY(-4px); }

/* FAB */
.fab-btn {
  position: fixed; right: 28px; bottom: 32px;
  width: 52px; height: 52px; border-radius: 50%;
  background: #3b82f6; color: white; border: none;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 16px rgba(59,130,246,0.4);
  transition: all 0.2s; z-index: 100;
}
.fab-btn:hover { transform: scale(1.08); background: #2563eb; }

/* ============================================================
   左轨时间线（详情弹窗复用）
   ============================================================ */
.da-outer { display: flex; gap: 10px; padding: 4px 0; min-height: 120px; }
.da-rail { display: flex; flex-direction: column; align-items: center; width: 16px; flex-shrink: 0; padding-top: 6px; }
.da-rail-dot { width: 10px; height: 10px; border-radius: 50%; background: #3b82f6; border: 2px solid white; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); flex-shrink: 0; z-index: 1; }
.da-rail-line { width: 2px; flex: 1; background: linear-gradient(to bottom, #e5e7eb, #f3f4f6); margin-top: -2px; margin-bottom: -2px; }
.a1b-card { padding: 0 !important; overflow: hidden; flex: 1; min-width: 0; }
.a1b-block { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px 18px; margin: 10px 4px; background: #ffffff; }
.a1b-block:first-child { margin-top: 12px; }
.a1b-block:last-child { margin-bottom: 12px; }
.a1b-block-msg { border-color: #dbeafe; background: #f8faff; }
.a1b-block-supp { border-color: #fde68a; background: #fffcf5; }
.a1b-block-title { font-size: 13px; font-weight: 600; color: #6b7280; margin-bottom: 10px; }
.a1b-empty-msg { font-size: 13px; color: #9ca3af; text-align: center; padding: 12px 0; }

.da-top { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.da-status { font-size:11px; font-weight:600; padding:2px 10px; border-radius:6px; }
.da-pending { background:#dbeafe; color:#2563eb; }
.da-done { background:#d1fae5; color:#059669; }
.da-date { font-size:12px; color:#9ca3af; margin-left:auto; }
.da-author { font-size:12px; color:#6b7280; background:#f3f4f6; padding:1px 10px; border-radius:10px; }
.da-subject { font-size: 16px; font-weight: 600; color: #1f2937; line-height: 1.6; margin-bottom: 10px; word-break: break-word; }
.da-note-text { font-size: 14px; color: #4b5563; background: #ffffff; border: 1px solid #e8eaee; padding: 10px 14px; border-radius: 8px; line-height: 1.7; margin-bottom: 10px; }
.da-img-wrap { margin-bottom: 10px; }
.da-thumb { width: 120px; height: 72px; border-radius:8px; }
.da-sep { height:1px; background:#e5e7eb; margin:14px 0; }
.da-complete-header { font-size: 13px; font-weight: 600; color: #059669; margin-bottom: 8px; }
.da-comp-note { font-size: 14px; color: #374151; background: #ffffff; border: 1px solid #d1fae5; padding: 8px 12px; border-radius: 8px; line-height: 1.6; margin-bottom: 8px; }
.da-comp-time { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.d-thumb { width: 100px; height: 64px; border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(0,0,0,0.06); flex-shrink: 0; }

/* 消息气泡 */
.a1a-messages { display: flex; flex-direction: column; gap: 10px; margin-bottom:4px; }
.a1-bubble { padding: 10px 14px; border-radius: 10px; max-width: 88%; position: relative; }
.a1-other { background: #ffffff; border: 1px solid #dbeafe; align-self: flex-start; border-bottom-left-radius: 4px; }
.a1-self { background: #f3f4f6; border: 1px solid #e5e7eb; align-self: flex-end; border-bottom-right-radius: 4px; }
.a1-bubble-author { font-size: 11px; font-weight: 600; color: #3b82f6; margin-bottom: 3px; }
.a1-self .a1-bubble-author { color: #6b7280; }
.a1-bubble-text { font-size: 14px; color: #1f2937; line-height: 1.6; word-break: break-word; }
.a1-bubble-time { font-size: 11px; color: #9ca3af; margin-top: 4px; text-align: right; }
.a1-bubble-img { margin-top: 6px; }
.a1-bubble-img img { width: 120px; height: 80px; object-fit: cover; border-radius: 6px; cursor: pointer; }

/* 行内输入 */
.a1d-inline-input { display: flex; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb; position: relative; }
.a1d-input { flex: 1; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 8px; outline: none; font-size: 13px; transition: border-color 0.2s; background: white; }
.a1d-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.1); }
.a1d-input::placeholder { color: #9ca3af; }
.a1d-actions { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.a1d-action-btn { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 6px; background: transparent; color: #9ca3af; cursor: pointer; transition: all 0.15s; }
.a1d-action-btn:hover { color: #3b82f6; background: rgba(59,130,246,0.08); }
.a1d-send-btn { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 8px; background: #3b82f6; color: white; cursor: pointer; transition: all 0.15s; flex-shrink: 0; }
.a1d-send-btn:hover { background: #2563eb; }
.a1d-send-btn:disabled { background: #d1d5db; cursor: not-allowed; }
.a1d-emoji-popup { position: absolute; bottom: calc(100% + 4px); left: 0; z-index: 200; }
.a1d-emoji-picker { height: 220px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); --num-columns:8; --border-radius:10px; }
.a1d-msg-img { display: flex; align-items: center; gap: 6px; margin-top: 6px; padding: 4px 8px; background: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb; }
.a1d-msg-img-thumb { width: 36px; height: 27px; border-radius: 4px; object-fit: cover; }
.a1d-msg-img-remove { font-size: 12px; color: #ef4444; background: none; border: none; cursor: pointer; padding: 2px 4px; }

/* 补充块 */
.a1b-supp-text { font-size: 14px; color: #374151; line-height: 1.6; word-break: break-word; }
.a1b-supp-empty { color: #9ca3af; font-style: italic; }
.a1b-supp-img { margin-top: 8px; }
.a1b-supp-time { font-size: 12px; color: #9ca3af; margin-top: 6px; text-align: right; }

/* ============================================================
   C 聊天式弹窗（新建/修改共用）
   ============================================================ */
.ntc-body { padding: 4px 0; position: relative; }
.ntc-title-row { display: flex; align-items: center; gap: 6px; border-bottom: 2px solid #e5e7eb; transition: border-color 0.2s; }
.ntc-title-row:focus-within { border-color: #3b82f6; }
.ntc-title-input { flex: 1; padding: 4px 0 10px; border: none; outline: none; font-size: 18px; font-weight: 600; color: #1f2937; }
.ntc-title-input::placeholder { color: #d1d5db; font-weight: 400; }
.ntc-sep { height: 12px; }
.ntc-textarea { width: 100%; padding: 0; border: none; outline: none; font-size: 15px; color: #374151; line-height: 1.7; resize: vertical; font-family: inherit; }
.ntc-textarea::placeholder { color: #d1d5db; }
.ntc-toolbar { display: flex; align-items: center; gap: 4px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f3f4f6; }
.ntc-tool-btn { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 6px; background: transparent; color: #9ca3af; cursor: pointer; font-size: 18px; transition: all 0.15s; }
.ntc-tool-btn:hover { color: #3b82f6; background: rgba(59,130,246,0.08); }
.ntc-date-input { border: none; outline: none; font-size: 12px; color: #6b7280; background: #f3f4f6; padding: 3px 10px; border-radius: 10px; margin-left: 4px; cursor: pointer; }
.ntc-date-input::-webkit-calendar-picker-indicator { cursor: pointer; opacity: 0.5; }
.ntc-color-chip { width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 0 1px #e5e7eb; flex-shrink:0; }
.ntc-color-chip.bg-white { background:#e5e7eb; }
.ntc-color-chip.bg-red { background:#f87171; }
.ntc-color-chip.bg-yellow { background:#fbbf24; }
.ntc-color-chip.bg-green { background:#34d399; }
.ntc-color-chip.bg-blue { background:#60a5fa; }
.ntc-color-chip.bg-dark { background:#9ca3af; }
.ntc-emoji-pop { position: absolute; bottom: 100%; left: 0; z-index: 200; margin-bottom: 4px; }
.ntc-ep { height: 220px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); --num-columns:8; }
.ntc-img-bar { display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 6px 10px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb; }
.ntc-img-thumb-real { width: 40px; height: 30px; border-radius: 4px; object-fit: cover; }
.ntc-img-label { font-size: 12px; color: #6b7280; flex:1; }
.ntc-img-remove { font-size: 12px; color: #ef4444; background: none; border: none; cursor: pointer; padding: 2px 6px; white-space:nowrap; }
.ntc-color-bar { display: flex; align-items: center; gap: 6px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f3f4f6; }
.ntc-color-label { font-size: 12px; color: #9ca3af; margin-right: 4px; }

/* 颜色弹窗 */
.ntc-color-pop {
  position: absolute; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%);
  display: flex; gap: 4px; padding: 8px 10px;
  background: white; border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.04);
  z-index: 200; white-space: nowrap;
}

/* color-dot-btn 通用 */
.color-dot-btn { width: 22px; height: 22px; border-radius: 50%; cursor: pointer; transition: transform 0.15s; border: 2px solid transparent; padding: 0; display:inline-block; }
.color-dot-btn:hover { transform: scale(1.15); }
.color-dot-btn.active { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.25); }
.color-dot-btn.bg-white { background:#ffffff; border-color:#d1d5db; }
.color-dot-btn.bg-red { background:#fee2e2; }
.color-dot-btn.bg-yellow { background:#fef3c7; }
.color-dot-btn.bg-green { background:#d1fae5; }
.color-dot-btn.bg-blue { background:#dbeafe; }
.color-dot-btn.bg-dark { background:#e5e7eb; }

/* ============================================================
   旧弹窗遗留样式（完成/备注/留言列表）
   ============================================================ */
.complete-body { padding: 4px 0; }
.input-with-emoji { position: relative; width: 100%; }
.emoji-btn { position: absolute; right: 4px; bottom: 4px; background: none; border: none; cursor: pointer; padding: 6px 10px; border-radius: 8px; font-size: 18px; line-height: 1; z-index: 5; }
.emoji-btn:hover { background: #f3f4f6; }
.emoji-wrapper { position: relative; }
.emoji-picker { position: absolute; bottom: calc(100% + 4px); right: 0; z-index: 200; height: 260px; border-radius: 12px; --num-columns: 8; --border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); }
.uploaded-preview { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.preview-thumb { width: 60px; height: 60px; border-radius: 4px; object-fit: cover; cursor: pointer; }
.empty-msg { text-align: center; color: #9ca3af; padding: 24px; }
.msg-list { max-height: 400px; overflow-y: auto; }
.msg-item { padding: 10px 0; border-bottom: 1px solid #f3f4f6; }
.msg-item:last-child { border-bottom: none; }
.msg-header { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.msg-author { font-weight: 500; color: #374151; }
.msg-time { color: #9ca3af; }
.msg-content { font-size: 14px; color: #1f2937; word-break: break-word; white-space: pre-wrap; }

/* ============================================================
   RichInput 样式覆盖——保持与原有 todo 输入框一致
   ============================================================ */
/* 创建/修改弹窗的 RichInput */
:deep(.todo-form-rich .ri-textarea),
:deep(.todo-complete-rich .ri-textarea) {
  padding: 0; border: none; border-radius: 0;
  font-size: 15px; color: #374151; line-height: 1.7;
}
:deep(.todo-form-rich .ri-textarea:focus),
:deep(.todo-complete-rich .ri-textarea:focus) {
  box-shadow: none;
}
:deep(.todo-form-rich .ri-toolbar) {
  margin-top: 10px; padding: 10px 0 0; border: none;
  border-top: 1px solid #f3f4f6; background: transparent; border-radius: 0;
}
:deep(.todo-complete-rich .ri-toolbar) {
  margin-top: 8px; padding: 10px 0 0; border: none;
  border-top: 1px solid #f3f4f6; background: transparent; border-radius: 0;
}
:deep(.todo-form-rich .ri-tool-btn),
:deep(.todo-complete-rich .ri-tool-btn) {
  width: 34px; height: 34px;
}
:deep(.todo-form-rich .ri-emoji-popup) {
  position: absolute; bottom: 100%; left: 0; z-index: 200; margin-bottom: 4px;
}
:deep(.todo-form-rich .ri-preview-bar) {
  display: flex; align-items: center; gap: 8px; margin-top: 8px;
  padding: 6px 10px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;
}
:deep(.todo-complete-rich .ri-preview-bar) {
  margin-top: 8px;
}
:deep(.todo-form-rich .ri-preview-thumb),
:deep(.todo-complete-rich .ri-preview-thumb) {
  width: 40px; height: 30px; border-radius: 4px; object-fit: cover;
  border: 4px solid #e5e7eb; border-radius: 6px;
}
:deep(.todo-form-rich .ri-preview-label),
:deep(.todo-complete-rich .ri-preview-label) {
  font-size: 12px; color: #6b7280; flex: 1;
}
:deep(.todo-form-rich .ri-preview-remove),
:deep(.todo-complete-rich .ri-preview-remove) {
  font-size: 12px; color: #ef4444; background: none; border: none; cursor: pointer; padding: 2px 6px;
}

/* ============================================================
   图片边框 & 灯箱
   ============================================================ */
.img-border { border: 4px solid #e5e7eb; border-radius: 6px; }

.item-thumb:hover { cursor: pointer; }
.da-thumb:hover { cursor: pointer; }

/* 缩略图固定占位（无论有无图片，对齐不受作者名影响） */
.thumb-area { flex-shrink: 0; width: 56px; display: flex; align-items: center; justify-content: center; }
.thumb-placeholder { width: 56px; height: 44px; display: block; }
.item-thumb { display: block; }

/* 共享徽标（管理员可见） */
.shared-badge {
  margin-left: 4px; font-size: 14px; cursor: help;
  opacity: 0.65; transition: opacity .15s; flex-shrink: 0;
}
.shared-badge:hover { opacity: 1; }

/* 可见性设置弹窗 */
.visibility-dialog-inner { padding: 4px 0; }
.vis-hint { font-size: 13px; color: #6b7280; margin: 0 0 12px; line-height: 1.6; }
.vis-hint b { color: #374151; font-weight: 600; }

</style>

<style>
/* 图片灯箱内 grab 光标（非 scoped 穿透 el-image-viewer） */
.el-image-viewer__img { cursor: grab !important; }
.el-image-viewer__img:active { cursor: grabbing !important; }
</style>
