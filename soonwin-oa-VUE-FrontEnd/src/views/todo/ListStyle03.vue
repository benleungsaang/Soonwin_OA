<template>
  <div>
    <div v-if="groupedDates.length === 0" class="empty-state">该分类下没有任务</div>

    <template v-else>
      <div v-for="date in groupedDates" :key="date">
        <!-- 日期大标题 -->
        <div class="date-divider">{{ formatDateLabel(date) }}</div>

        <div
          v-for="item in groups[date]"
          :key="item.id"
          class="item-row"
          :class="{ completed: item.status === 'completed' }"
        >
          <!-- 复选框（没有左侧颜色标记，最干净） -->
          <div class="chk-box" :class="{ checked: item.status === 'completed' }"></div>

          <!-- 任务内容 -->
          <div class="item-main">
            <span class="item-text" :class="{ done: item.status === 'completed' }">{{ item.content }}</span>
          </div>

          <!-- 右侧组：颜色标签 + 作者 -->
          <div class="right-group">
            <span class="color-tag" :class="'ct-' + item.color">{{ colorLabel(item.color) }}</span>
            <span class="author-pill">{{ item.author }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface MockTodo {
  id: number; content: string; status: 'pending' | 'completed'
  date: string; color: string; author: string
}

const props = defineProps<{
  items: MockTodo[]
  activeTab: string
}>()

const groups = computed(() => {
  const g: Record<string, MockTodo[]> = {}
  for (const t of props.items) {
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

const colorMap: Record<string, string> = {
  white: '默认', red: '紧急', yellow: '重要',
  green: '完成', blue: '进行中', dark: '长期',
}
function colorLabel(c: string) { return colorMap[c] || c }
</script>

<style scoped>
.empty-state {
  text-align: center; color: #9ca3af; padding: 48px 0; font-size: 14px;
}

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
   条目行 — 最干净版本，无左侧任何标记
   ============================================================ */
.item-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.15s;
}

.item-row:last-child { border-bottom: none; }
.item-row:hover { background: #fafafa; }
.item-row.completed { opacity: 0.55; }

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
   右侧组：颜色标签 + 作者
   ============================================================ */
.right-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* 颜色标签 — 小巧圆角 */
.color-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 6px;
  font-weight: 500;
  white-space: nowrap;
  line-height: 20px;
}

.ct-white  { background: #f3f4f6; color: #6b7280; }
.ct-red    { background: #fee2e2; color: #dc2626; }
.ct-yellow { background: #fef3c7; color: #d97706; }
.ct-green  { background: #d1fae5; color: #059669; }
.ct-blue   { background: #dbeafe; color: #2563eb; }
.ct-dark   { background: #e5e7eb; color: #4b5563; }

.author-pill {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 10px;
  border-radius: 12px;
  white-space: nowrap;
  line-height: 20px;
}
</style>
