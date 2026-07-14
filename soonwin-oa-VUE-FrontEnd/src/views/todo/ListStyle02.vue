<template>
  <div>
    <!-- ===== 空状态 ===== -->
    <div v-if="groupedDates.length === 0" class="empty-state">该分类下没有任务</div>

    <template v-else>
      <div v-for="date in groupedDates" :key="date">
        <!-- 日期大标题 -->
        <div class="date-divider">{{ formatDateLabel(date) }}</div>

        <div
          v-for="item in groups[date]"
          :key="item.id"
          class="item-row"
          :class="{ completed: item.status === 'completed', 'menu-open': openMenuId === item.id }"
          @click="openDetail(item)"
        >
          <!-- 彩色圆点 -->
          <span class="color-dot" :class="'dot-' + item.color"></span>

          <!-- 复选框 -->
          <div
            class="chk-box"
            :class="{ checked: item.status === 'completed' }"
            @click.stop="toggleComplete(item)"
          ></div>

          <!-- 任务内容 -->
          <div class="item-main">
            <span class="item-text" :class="{ done: item.status === 'completed' }">{{ item.content }}</span>
          </div>

          <!-- 缩略图占位 -->
          <div
            v-if="item.image_url"
            class="thumb-placeholder"
            :style="{ background: thumbBg(item) }"
            @click.stop
          >
            <span class="thumb-icon">🖼️</span>
          </div>

          <!-- 作者 -->
          <span class="author-pill" @click.stop>{{ item.author }}</span>

          <!-- 三点菜单 -->
          <div class="menu-wrapper" @click.stop>
            <button
              class="menu-trigger"
              :class="{ open: openMenuId === item.id }"
              @click="toggleMenu(item.id)"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="8" cy="3" r="1.5"/>
                <circle cx="8" cy="8" r="1.5"/>
                <circle cx="8" cy="13" r="1.5"/>
              </svg>
            </button>

            <transition name="menu-fade">
              <div v-show="openMenuId === item.id" class="task-menu-dropdown">
                <!-- 颜色选择 -->
                <div class="menu-color-row">
                  <button
                    v-for="c in colorOptions"
                    :key="c.value"
                    class="color-dot-btn"
                    :class="['bg-' + c.value, { active: item.color === c.value }]"
                    :title="c.label"
                    @click="onChangeColor(item, c.value)"
                  />
                </div>
                <div class="menu-divider"></div>
                <button class="menu-btn" @click="onEdit(item)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                  <span>修改内容</span>
                </button>
                <button class="menu-btn danger" @click="onDelete(item)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
                  <span>删除</span>
                </button>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </template>

    <!-- ============================================================
         详情弹窗（只读，点击条目弹出）
         ============================================================ -->
    <el-dialog
      v-model="detailVisible"
      title="任务详情"
      width="520px"
      top="8vh"
      :close-on-click-modal="true"
    >
      <template v-if="detailItem">
        <div class="detail-body">
          <!-- 第一行：颜色标记 + 状态 -->
          <div class="detail-row detail-status-row">
            <span class="color-dot" :class="'dot-' + detailItem.color"></span>
            <span class="detail-status-tag" :class="detailItem.status === 'completed' ? 'tag-done' : 'tag-pending'">
              {{ detailItem.status === 'completed' ? '已完成' : '待完成' }}
            </span>
            <span class="detail-color-label">· {{ colorLabel(detailItem.color) }}</span>
          </div>

          <!-- 任务内容 -->
          <div class="detail-row">
            <label>任务内容</label>
            <div class="detail-value content-value">{{ detailItem.content }}</div>
          </div>

          <!-- 所属日期 -->
          <div class="detail-row">
            <label>所属日期</label>
            <div class="detail-value">{{ detailItem.date }}</div>
          </div>

          <!-- 任务备注 -->
          <div v-if="detailItem.note" class="detail-row">
            <label>任务备注</label>
            <div class="detail-value note-value">{{ detailItem.note }}</div>
          </div>

          <!-- 附图 -->
          <div v-if="detailItem.image_url" class="detail-row detail-img-row">
            <label>任务附图</label>
            <div class="thumb-placeholder large-thumb" :style="{ background: thumbBg(detailItem) }">
              <span class="thumb-icon">🖼️</span>
            </div>
          </div>

          <!-- 发布人 -->
          <div class="detail-row">
            <label>发布人</label>
            <div class="detail-value">
              <span class="author-pill">{{ detailItem.author }}</span>
            </div>
          </div>

          <!-- ===== 完成信息 ===== -->
          <template v-if="detailItem.status === 'completed'">
            <el-divider style="margin: 16px 0" />
            <div class="detail-subtitle">完成情况</div>

            <div v-if="detailItem.completion_note" class="detail-row">
              <label>完成内容</label>
              <div class="detail-value note-value">{{ detailItem.completion_note }}</div>
            </div>

            <div v-if="detailItem.completion_image_url" class="detail-row detail-img-row">
              <label>完成图片</label>
              <div class="thumb-placeholder large-thumb" style="background: linear-gradient(135deg, #d1fae5, #a7f3d0);">
                <span class="thumb-icon">✅</span>
              </div>
            </div>

            <div v-if="detailItem.completed_at" class="detail-row">
              <label>完成时间</label>
              <div class="detail-value">{{ detailItem.completed_at }}</div>
            </div>
          </template>
        </div>
      </template>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         编辑弹窗（模拟，不写真实 API）
         ============================================================ -->
    <el-dialog
      v-model="editVisible"
      title="修改内容"
      width="480px"
      top="20vh"
    >
      <div class="edit-body">
        <label class="edit-label">任务内容</label>
        <el-input
          v-model="editContent"
          type="textarea"
          :rows="3"
          maxlength="500"
          show-word-limit
        />
        <p class="edit-hint">⚠️ 当前为模拟模式，修改不会持久化</p>
      </div>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEdit">保存（模拟）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'

// ===== 类型 =====
interface TodoItem {
  id: number
  content: string
  status: 'pending' | 'completed'
  date: string
  color: string
  author: string
  note: string
  image_url: string
  completion_note?: string
  completion_image_url?: string
  completed_at?: string
}

const props = defineProps<{
  items: TodoItem[]
  noDialogs?: boolean   // true 时点击条目/编辑由父组件处理
}>()

// ===== emit =====
const emit = defineEmits<{
  (e: 'update:items', items: TodoItem[]): void
  (e: 'view-detail', item: TodoItem): void
  (e: 'edit-item', item: TodoItem): void
}>()

// ===== 本地数据（模拟，不影响父级） =====
const localItems = ref<TodoItem[]>([])

// 将 props 同步到本地
function syncItems() {
  localItems.value = props.items.map(i => ({ ...i }))
}

onMounted(syncItems)

// ===== 分组 =====
const groups = computed(() => {
  const g: Record<string, TodoItem[]> = {}
  for (const t of localItems.value) {
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

// ===== 颜色 =====
const colorOptions = [
  { value: 'white',  label: '默认' },
  { value: 'red',    label: '紧急' },
  { value: 'yellow', label: '重要' },
  { value: 'green',  label: '完成' },
  { value: 'blue',   label: '进行中' },
  { value: 'dark',   label: '长期' },
]

const colorLabel = (c: string) => colorOptions.find(o => o.value === c)?.label || c

// 缩略图背景
function thumbBg(item: TodoItem): string {
  const bgMap: Record<string, string> = {
    white:  'linear-gradient(135deg, #e5e7eb, #d1d5db)',
    red:    'linear-gradient(135deg, #fca5a5, #f87171)',
    yellow: 'linear-gradient(135deg, #fde68a, #fbbf24)',
    green:  'linear-gradient(135deg, #a7f3d0, #6ee7b7)',
    blue:   'linear-gradient(135deg, #93c5fd, #60a5fa)',
    dark:   'linear-gradient(135deg, #d1d5db, #9ca3af)',
  }
  return bgMap[item.color] || bgMap.white
}

// ===== 三点菜单 =====
const openMenuId = ref<number | null>(null)

function toggleMenu(id: number) {
  openMenuId.value = openMenuId.value === id ? null : id
}

function onDocumentClick(e: MouseEvent) {
  const el = e.target as HTMLElement
  if (!el.closest('.menu-wrapper')) openMenuId.value = null
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})

// ===== 菜单操作 =====
function onChangeColor(item: TodoItem, color: string) {
  if (item.color === color) {
    openMenuId.value = null
    return
  }
  item.color = color
  openMenuId.value = null
  ElMessage.success(`颜色已切换为「${colorLabel(color)}」`)
}

// 编辑
const editVisible = ref(false)
const editContent = ref('')
const editingItem = ref<TodoItem | null>(null)

function onEdit(item: TodoItem) {
  if (props.noDialogs) {
    openMenuId.value = null
    emit('edit-item', item)
    return
  }
  editingItem.value = item
  editContent.value = item.content
  openMenuId.value = null
  editVisible.value = true
}

function confirmEdit() {
  if (!editingItem.value || !editContent.value.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  editingItem.value.content = editContent.value.trim()
  editVisible.value = false
  editingItem.value = null
  ElMessage.success('内容已更新（模拟）')
}

// 删除
function onDelete(item: TodoItem) {
  openMenuId.value = null
  localItems.value = localItems.value.filter(i => i.id !== item.id)
  ElMessage.success(`已删除「${item.content}」（模拟）`)
}

// ===== 勾选切换 =====
function toggleComplete(item: TodoItem) {
  item.status = item.status === 'completed' ? 'pending' : 'completed'
  if (item.status === 'completed') {
    item.completed_at = new Date().toLocaleString('zh-CN', { hour12: false })
    ElMessage.success('已标记完成（模拟）')
  } else {
    ElMessage.success('已撤销完成（模拟）')
  }
}

// ===== 详情弹窗 =====
const detailVisible = ref(false)
const detailItem = ref<TodoItem | null>(null)

function openDetail(item: TodoItem) {
  if (props.noDialogs) {
    emit('view-detail', item)
    return
  }
  detailItem.value = item
  detailVisible.value = true
}
</script>

<style scoped>
/* ============================================================
   空状态
   ============================================================ */
.empty-state {
  text-align: center; color: #9ca3af; padding: 48px 0; font-size: 14px;
}

/* ============================================================
   日期大标题
   ============================================================ */
.date-divider {
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
  padding: 10px 16px;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 15px;
}

/* ============================================================
   条目行
   ============================================================ */
.item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.12s;
  cursor: pointer;
}

.item-row:last-child { border-bottom: none; }
.item-row:hover { background: #f5f7fa; }
.item-row.menu-open { z-index: 50; position: relative; }
.item-row.completed { opacity: 0.6; }

/* ============================================================
   彩色圆点
   ============================================================ */
.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.item-row:hover .color-dot { transform: scale(1.2); }

.dot-white  { background: #e5e7eb; }
.dot-red    { background: #f87171; }
.dot-yellow { background: #fbbf24; }
.dot-green  { background: #34d399; }
.dot-blue   { background: #60a5fa; }
.dot-dark   { background: #9ca3af; }

/* ============================================================
   复选框
   ============================================================ */
.chk-box {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  flex-shrink: 0;
  background: white;
  position: relative;
  transition: all 0.2s;
}

.chk-box.checked {
  background: #3b82f6;
  border-color: #3b82f6;
}

.chk-box.checked::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.chk-box:hover { border-color: #60a5fa; }

/* ============================================================
   任务内容
   ============================================================ */
.item-main {
  flex: 1;
  min-width: 0;
}

.item-text {
  font-size: 15px;
  color: #1f2937;
  line-height: 1.5;
  word-break: break-word;
}

.item-text.done {
  text-decoration: line-through;
  color: #9ca3af;
}

/* ============================================================
   缩略图占位
   ============================================================ */
.thumb-placeholder {
  width: 48px;
  height: 36px;
  border-radius: 6px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(0,0,0,0.06);
  cursor: default;
}

.thumb-icon {
  font-size: 16px;
  opacity: 0.7;
  filter: grayscale(0.3);
}

/* ============================================================
   作者
   ============================================================ */
.author-pill {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 10px;
  border-radius: 12px;
  white-space: nowrap;
  line-height: 20px;
  flex-shrink: 0;
}

/* ============================================================
   三点菜单
   ============================================================ */
.menu-wrapper {
  position: relative;
  flex-shrink: 0;
}

.menu-trigger {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
}

.menu-trigger:hover,
.menu-trigger.open {
  color: #4b5563;
  background: rgba(0,0,0,0.05);
}

.task-menu-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 4px);
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.04);
  z-index: 200;
  min-width: 170px;
  padding: 6px 0;
}

.menu-color-row {
  display: flex;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
}

.color-dot-btn {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s;
  border: 2px solid transparent;
  padding: 0;
}

.color-dot-btn:hover { transform: scale(1.2); }
.color-dot-btn.active { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.25); }

.color-dot-btn.bg-white  { background: #ffffff; border-color: #d1d5db; }
.color-dot-btn.bg-red    { background: #fee2e2; }
.color-dot-btn.bg-yellow { background: #fef3c7; }
.color-dot-btn.bg-green  { background: #d1fae5; }
.color-dot-btn.bg-blue   { background: #dbeafe; }
.color-dot-btn.bg-dark   { background: #e5e7eb; }

.menu-divider {
  height: 1px;
  background: #f3f4f6;
  margin: 4px 8px;
}

.menu-btn {
  width: 100%;
  text-align: left;
  padding: 8px 14px;
  font-size: 13px;
  color: #374151;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.1s;
}

.menu-btn:hover { background: #f9fafb; }
.menu-btn.danger { color: #ef4444; }
.menu-btn.danger:hover { background: #fef2f2; }

/* 菜单动画 */
.menu-fade-enter-active, .menu-fade-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}
.menu-fade-enter-from, .menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ============================================================
   详情弹窗
   ============================================================ */
.detail-body {
  padding: 4px 0;
}

.detail-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f3f4f6;
}

.detail-status-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 6px;
}

.tag-pending { background: #dbeafe; color: #2563eb; }
.tag-done    { background: #d1fae5; color: #059669; }

.detail-color-label {
  font-size: 13px;
  color: #6b7280;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 14px;
  font-size: 14px;
  color: #374151;
}

.detail-row label {
  flex-shrink: 0;
  width: 72px;
  color: #6b7280;
  font-size: 13px;
  padding-top: 2px;
}

.detail-value {
  flex: 1;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.6;
}

.content-value {
  font-size: 15px;
  color: #1f2937;
  font-weight: 500;
}

.note-value {
  color: #4b5563;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.detail-img-row {
  align-items: center;
}

.large-thumb {
  width: 120px;
  height: 80px;
  border-radius: 8px;
}

.detail-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 14px;
}

.detail-row .author-pill {
  font-size: 13px;
  padding: 2px 14px;
}

/* ============================================================
   编辑弹窗
   ============================================================ */
.edit-body {
  padding: 8px 0;
}

.edit-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.edit-hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: #f59e0b;
}
</style>
