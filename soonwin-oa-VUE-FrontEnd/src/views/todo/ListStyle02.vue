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
          <!-- 彩色圆点（所有条目统一宽度，白色条目用浅灰点） -->
          <span class="color-dot" :class="'dot-' + item.color"></span>

          <!-- 复选框 -->
          <div class="chk-box" :class="{ checked: item.status === 'completed' }"></div>

          <!-- 任务内容 -->
          <div class="item-main">
            <span class="item-text" :class="{ done: item.status === 'completed' }">{{ item.content }}</span>
          </div>

          <!-- 作者 + 紧急度标签放在同一组 -->
          <div class="meta-group">
            <span v-if="item.color === 'red'" class="urgent-tag">紧急</span>
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
   条目行 — 所有颜色 padding 完全一致
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
.item-row.completed { opacity: 0.6; }

/* ============================================================
   彩色圆点 — 统一 12px，不占额外空间
   ============================================================ */
.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.item-row:hover .color-dot { transform: scale(1.2); }

.dot-white  { background: #e5e7eb; }  /* 默认条目用浅灰点 */
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
   右侧元信息组（标签 + 作者）
   ============================================================ */
.meta-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.urgent-tag {
  font-size: 11px;
  background: #fee2e2;
  color: #dc2626;
  padding: 1px 8px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}

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
