<template>
  <div class="demo-page">
    <CommonHeader title="选项卡样式投票" />

    <div class="demo-container">
      <p class="demo-intro">
        同一数据，三种选项卡风格。请选择你最喜欢的一款 👇
      </p>

      <!-- ============================================================
           样式 A：下划线式
           ============================================================ -->
      <section class="demo-section">
        <h2 class="demo-title">
          <span class="demo-badge">A</span>
          下划线式
          <span class="demo-sub">—— 经典 Material 风格，下划线指标准确</span>
        </h2>
        <div class="demo-card">
          <div class="tabs-a">
            <button
              v-for="t in tabDefs"
              :key="t.key"
              class="tab-a"
              :class="{ active: activeTabA === t.key }"
              @click="activeTabA = t.key"
            >
              {{ t.label }}
              <span v-if="t.count !== undefined" class="tab-count-a">{{ t.count }}</span>
              <span v-if="activeTabA === t.key" class="tab-ink-a"></span>
            </button>
          </div>

          <div class="tab-content-a">
            <TodoDemoList :items="filteredA" />
          </div>
        </div>
      </section>

      <!-- ============================================================
           样式 B：药丸式（分段控件）
           ============================================================ -->
      <section class="demo-section">
        <h2 class="demo-title">
          <span class="demo-badge">B</span>
          药丸式
          <span class="demo-sub">—— 类似 iOS 分段控件，高亮色块清晰醒目</span>
        </h2>
        <div class="demo-card">
          <div class="tabs-b">
            <button
              v-for="t in tabDefs"
              :key="t.key"
              class="tab-b"
              :class="{ active: activeTabB === t.key }"
              @click="activeTabB = t.key"
            >
              <el-icon v-if="t.icon" class="tab-b-icon"><component :is="t.icon" /></el-icon>
              {{ t.label }}
              <span v-if="t.count !== undefined" class="tab-count-b">{{ t.count }}</span>
            </button>
          </div>

          <div class="tab-content-b">
            <TodoDemoList :items="filteredB" />
          </div>
        </div>
      </section>

      <!-- ============================================================
           样式 C：卡片式
           ============================================================ -->
      <section class="demo-section">
        <h2 class="demo-title">
          <span class="demo-badge">C</span>
          卡片式
          <span class="demo-sub">—— 每项独立卡片，图标+数量一目了然</span>
        </h2>
        <div class="demo-card">
          <div class="tabs-c">
            <button
              v-for="t in tabDefs"
              :key="t.key"
              class="tab-c"
              :class="{ active: activeTabC === t.key }"
              @click="activeTabC = t.key"
            >
              <el-icon v-if="t.icon" class="tab-c-icon"><component :is="t.icon" /></el-icon>
              <span class="tab-c-label">{{ t.label }}</span>
              <span v-if="t.count !== undefined" class="tab-c-count">{{ t.count }}</span>
            </button>
          </div>

          <div class="tab-content-c">
            <TodoDemoList :items="filteredC" />
          </div>
        </div>
      </section>

      <!-- 底部对比总结 -->
      <section class="demo-summary">
        <h2>风格对比</h2>
        <table class="cmp-table">
          <tr>
            <th></th>
            <th>A · 下划线式</th>
            <th>B · 药丸式</th>
            <th>C · 卡片式</th>
          </tr>
          <tr>
            <td>视觉重量</td>
            <td>轻</td>
            <td>中</td>
            <td>重</td>
          </tr>
          <tr>
            <td>占用高度</td>
            <td>低（≈36px）</td>
            <td>中（≈44px）</td>
            <td>高（≈56px）</td>
          </tr>
          <tr>
            <td>适合触屏</td>
            <td>✓</td>
            <td>✓✓</td>
            <td>✓✓✓</td>
          </tr>
          <tr>
            <td>与现有 UI 融合度</td>
            <td>高（简洁百搭）</td>
            <td>高（醒目）</td>
            <td>中（偏重）</td>
          </tr>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { List, CircleCheck, Clock, Flag } from '@element-plus/icons-vue'
import CommonHeader from '@/components/CommonHeader.vue'
import TodoDemoList from './TodoDemoList.vue'

// ============================================================
// 模拟数据
// ============================================================
interface MockTodo {
  id: number
  content: string
  status: 'pending' | 'completed'
  date: string
  color: string
  author: string
}

const mockTodos: MockTodo[] = [
  { id: 1,  content: '完成哥伦比亚餐具套装的邮件回复 📧',                 status: 'pending',   date: '2026-07-14', color: 'white',  author: '你' },
  { id: 2,  content: '审核李经理提交的差旅报销单据',                       status: 'pending',   date: '2026-07-14', color: 'yellow', author: '你' },
  { id: 3,  content: '确认下周客户来访行程安排 ✈️',                       status: 'completed', date: '2026-07-14', color: 'white',  author: '你' },
  { id: 4,  content: '准备季度销售数据汇总 PPT',                           status: 'pending',   date: '2026-07-13', color: 'red',    author: '你' },
  { id: 5,  content: '跟进墨西哥客户的新样品需求',                         status: 'completed', date: '2026-07-13', color: 'white',  author: '小王' },
  { id: 6,  content: '更新产品目录第三章节内容',                           status: 'pending',   date: '2026-07-13', color: 'blue',   author: '你' },
  { id: 7,  content: '检查仓库库存并补充热销品',                           status: 'pending',   date: '2026-07-12', color: 'green',  author: '小李' },
  { id: 8,  content: '回复美国客户的验厂问题清单',                         status: 'completed', date: '2026-07-11', color: 'white',  author: '你' },
  { id: 9,  content: '安排下月广交会展位设计方案比选',                     status: 'pending',   date: '2026-07-11', color: 'yellow', author: '你' },
  { id: 10, content: '整理上周会议纪要并分发各部门',                       status: 'completed', date: '2026-07-10', color: 'white',  author: '小王' },
]

// ============================================================
// Tab 定义（3 套共享同一数据源）
// ============================================================
const tabDefs = [
  { key: 'all',       label: '全部',   icon: List,        count: mockTodos.length },
  { key: 'pending',   label: '待完成', icon: Clock,       count: mockTodos.filter(t => t.status === 'pending').length },
  { key: 'completed', label: '已完成', icon: CircleCheck, count: mockTodos.filter(t => t.status === 'completed').length },
  { key: 'urgent',    label: '紧急',   icon: Flag,        count: mockTodos.filter(t => t.color === 'red').length },
]

// ============================================================
// 当前激活 tab（每套独立）
// ============================================================
const activeTabA = ref('all')
const activeTabB = ref('all')
const activeTabC = ref('all')

// ============================================================
// 过滤函数（三套共用）
// ============================================================
function filterByTab(items: MockTodo[], tab: string): MockTodo[] {
  if (tab === 'all') return items
  if (tab === 'pending') return items.filter(t => t.status === 'pending')
  if (tab === 'completed') return items.filter(t => t.status === 'completed')
  if (tab === 'urgent') return items.filter(t => t.color === 'red')
  return items
}

const filteredA = computed(() => filterByTab(mockTodos, activeTabA.value))
const filteredB = computed(() => filterByTab(mockTodos, activeTabB.value))
const filteredC = computed(() => filterByTab(mockTodos, activeTabC.value))
</script>

<style scoped>
/* ============================================================
   页面通用
   ============================================================ */
.demo-page {
  background: #f9fafb;
  min-height: calc(100vh - 60px);
  padding: 32px 16px;
}

.demo-container {
  max-width: 800px;
  margin: 0 auto;
}

.demo-intro {
  text-align: center;
  color: #6b7280;
  font-size: 15px;
  margin-bottom: 32px;
}

.demo-section {
  margin-bottom: 40px;
}

.demo-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.demo-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  font-size: 14px;
  font-weight: 700;
}

.demo-sub {
  font-size: 14px;
  font-weight: 400;
  color: #9ca3af;
}

.demo-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
  overflow: hidden;
}

/* ============================================================
   样式 A：下划线式
   ============================================================ */
.tabs-a {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  background: #fafafa;
  padding: 0 8px;
}

.tab-a {
  position: relative;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.tab-a:hover { color: #374151; }
.tab-a.active { color: #3b82f6; }

.tab-count-a {
  font-size: 11px;
  background: #e5e7eb;
  color: #6b7280;
  padding: 0 7px;
  border-radius: 10px;
  line-height: 18px;
  transition: all 0.2s;
}

.tab-a.active .tab-count-a {
  background: #dbeafe;
  color: #3b82f6;
}

.tab-ink-a {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 3px;
  background: #3b82f6;
  border-radius: 3px 3px 0 0;
  animation: inkIn 0.25s ease-out;
}

@keyframes inkIn {
  from { width: 0; opacity: 0; }
  to   { width: 60%; opacity: 1; }
}

.tab-content-a {
  padding: 16px;
}

/* ============================================================
   样式 B：药丸式（分段控件）
   ============================================================ */
.tabs-b {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
}

.tab-b {
  flex: 1;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  background: transparent;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.25s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  white-space: nowrap;
}

.tab-b:hover { color: #374151; background: rgba(0,0,0,0.03); }

.tab-b.active {
  color: white;
  background: #3b82f6;
  box-shadow: 0 2px 8px rgba(59,130,246,0.3);
}

.tab-b-icon { font-size: 15px; }

.tab-count-b {
  font-size: 11px;
  background: rgba(0,0,0,0.08);
  color: inherit;
  padding: 0 7px;
  border-radius: 10px;
  line-height: 18px;
  transition: all 0.2s;
}

.tab-b.active .tab-count-b {
  background: rgba(255,255,255,0.25);
  color: white;
}

.tab-content-b {
  padding: 16px;
}

/* ============================================================
   样式 C：卡片式
   ============================================================ */
.tabs-c {
  display: flex;
  gap: 12px;
  padding: 16px 16px 12px;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
}

.tab-c {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px 10px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  line-height: 1.3;
}

.tab-c:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
  transform: translateY(-1px);
}

.tab-c.active {
  color: #1f2937;
  border-color: #3b82f6;
  box-shadow: 0 2px 12px rgba(59,130,246,0.15);
  background: linear-gradient(180deg, #eff6ff 0%, white 100%);
}

.tab-c-icon {
  font-size: 20px;
  color: #9ca3af;
  transition: color 0.2s;
}

.tab-c.active .tab-c-icon { color: #3b82f6; }

.tab-c-label { font-size: 13px; }

.tab-c-count {
  font-size: 11px;
  background: #f3f4f6;
  color: #6b7280;
  padding: 0 8px;
  border-radius: 10px;
  line-height: 18px;
  margin-top: 2px;
  transition: all 0.2s;
}

.tab-c.active .tab-c-count {
  background: #dbeafe;
  color: #3b82f6;
}

.tab-content-c {
  padding: 16px;
}

/* ============================================================
   底部对比表
   ============================================================ */
.demo-summary {
  margin-top: 48px;
  margin-bottom: 60px;
}

.demo-summary h2 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.cmp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.cmp-table th,
.cmp-table td {
  padding: 10px 16px;
  text-align: left;
  border-bottom: 1px solid #f3f4f6;
}

.cmp-table th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.cmp-table th:first-child { color: #9ca3af; font-weight: 400; }
.cmp-table td:first-child { color: #6b7280; font-weight: 500; white-space: nowrap; }

.cmp-table tr:last-child td { border-bottom: none; }
</style>
