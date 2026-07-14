<template>
  <div>
    <div v-if="items.length === 0" class="demo-empty">
      该分类下没有任务
    </div>

    <div
      v-for="item in items"
      :key="item.id"
      class="demo-task-row"
      :class="'color-' + item.color"
    >
      <!-- 圆形复选框 -->
      <div
        class="demo-checkbox"
        :class="{ checked: item.status === 'completed' }"
      ></div>

      <!-- 任务内容 -->
      <div class="demo-task-main">
        <span
          class="demo-task-text"
          :class="{ completed: item.status === 'completed' }"
        >{{ item.content }}</span>
        <span class="demo-task-meta">
          <span class="demo-author">{{ item.author }}</span>
          <span class="demo-date">{{ item.date }}</span>
        </span>
      </div>

      <!-- 颜色标签 -->
      <span class="demo-color-tag" :class="'tag-' + item.color">
        {{ colorLabel(item.color) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  items: Array<{
    id: number
    content: string
    status: 'pending' | 'completed'
    date: string
    color: string
    author: string
  }>
}>()

const colorMap: Record<string, string> = {
  white: '默认',
  red: '紧急',
  yellow: '重要',
  green: '完成',
  blue: '进行中',
  dark: '长期',
}

function colorLabel(c: string) { return colorMap[c] || c }
</script>

<style scoped>
.demo-empty {
  text-align: center;
  color: #9ca3af;
  padding: 32px 0;
  font-size: 14px;
}

.demo-task-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.2s;
}

.demo-task-row:last-child { border-bottom: none; }
.demo-task-row:hover { background: #fafafa; margin: 0 -8px; padding: 12px 8px; border-radius: 6px; }

/* 颜色标记 */
.demo-task-row.color-white { }
.demo-task-row.color-red   { border-left: 3px solid #fca5a5; padding-left: 9px; }
.demo-task-row.color-yellow{ border-left: 3px solid #fcd34d; padding-left: 9px; }
.demo-task-row.color-green { border-left: 3px solid #6ee7b7; padding-left: 9px; }
.demo-task-row.color-blue  { border-left: 3px solid #93c5fd; padding-left: 9px; }

/* 模拟复选框 */
.demo-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  flex-shrink: 0;
  transition: all 0.2s;
  background: white;
  position: relative;
}

.demo-checkbox.checked {
  background: #3b82f6;
  border-color: #3b82f6;
}

.demo-checkbox.checked::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* 任务主体 */
.demo-task-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.demo-task-text {
  font-size: 14px;
  color: #1f2937;
  word-break: break-word;
  line-height: 1.5;
}

.demo-task-text.completed {
  text-decoration: line-through;
  color: #9ca3af;
}

.demo-task-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #9ca3af;
}

/* 颜色标签 */
.demo-color-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 4px;
  flex-shrink: 0;
  white-space: nowrap;
}

.tag-white  { background: #f9fafb; color: #6b7280; }
.tag-red    { background: #fee2e2; color: #dc2626; }
.tag-yellow { background: #fef3c7; color: #d97706; }
.tag-green  { background: #d1fae5; color: #059669; }
.tag-blue   { background: #dbeafe; color: #2563eb; }
</style>
