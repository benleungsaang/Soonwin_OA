<template>
  <div class="demo-page">
    <CommonHeader title="条目样式票选" />

    <div class="demo-container">
      <p class="demo-intro">
        上部 tab 已确定为药丸式。下部展示了<strong>三种条目样式</strong>，数据联动联动（点 tab 三个区域同步过滤）。
      </p>

      <!-- ============================================================
           上部：药丸式 Tab（仅一套）
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge">✓</span>
          上部 Tab：药丸式（已定稿）
        </h2>
        <div class="demo-card">
          <div class="tabs-b">
            <button
              v-for="t in tabDefs"
              :key="t.key"
              class="tab-b"
              :class="{ active: activeTab === t.key }"
              @click="activeTab = t.key"
            >
              <el-icon v-if="t.icon" class="tab-b-icon"><component :is="t.icon" /></el-icon>
              {{ t.label }}
              <span v-if="t.count !== undefined" class="tab-b-count">{{ t.count }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- ============================================================
           下部样式 ①：左侧彩色竖线 + 绝对定位（完美对齐）
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge">①</span>
          彩色竖线式
          <span class="section-sub">—— 左侧色条 | 绝对定位不占位 | 日期大标题 | 作者圆角灰底</span>
        </h2>
        <div class="demo-card">
          <ListStyle01 :items="filteredItems" :active-tab="activeTab" />
        </div>
      </section>

      <!-- ============================================================
           下部样式 ②：左侧彩色圆点 + 统一间距
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge">②</span>
          彩色圆点式
          <span class="section-sub">—— 圆点标记紧急度 | 所有条目统一缩进 | 作者圆角灰底</span>
        </h2>
        <div class="demo-card">
          <ListStyle02 :items="filteredItems" :active-tab="activeTab" />
        </div>
      </section>

      <!-- ============================================================
           下部样式 ③：右侧彩色标签
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge">③</span>
          彩色标签式
          <span class="section-sub">—— 颜色标签放右侧 | 内容区无偏移 | 作者圆角灰底</span>
        </h2>
        <div class="demo-card">
          <ListStyle03 :items="filteredItems" :active-tab="activeTab" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { List, CircleCheck, Clock, Flag } from '@element-plus/icons-vue'
import CommonHeader from '@/components/CommonHeader.vue'
import ListStyle01 from './ListStyle01.vue'
import ListStyle02 from './ListStyle02.vue'
import ListStyle03 from './ListStyle03.vue'

interface MockTodo {
  id: number
  content: string
  status: 'pending' | 'completed'
  date: string
  color: string
  author: string
}

const mockTodos: MockTodo[] = [
  { id: 1,  content: '完成哥伦比亚餐具套装的邮件回复 📧',              date: '2026-07-14', status: 'pending',   color: 'white',  author: '你' },
  { id: 2,  content: '审核李经理提交的差旅报销单据',                    date: '2026-07-14', status: 'pending',   color: 'yellow', author: '你' },
  { id: 3,  content: '确认下周客户来访行程安排 ✈️',                    date: '2026-07-14', status: 'completed', color: 'white',  author: '你' },
  { id: 4,  content: '准备季度销售数据汇总 PPT',                        date: '2026-07-13', status: 'pending',   color: 'red',    author: '你' },
  { id: 5,  content: '跟进墨西哥客户的新样品需求',                      date: '2026-07-13', status: 'completed', color: 'white',  author: '小王' },
  { id: 6,  content: '更新产品目录第三章节内容',                        date: '2026-07-13', status: 'pending',   color: 'blue',   author: '你' },
  { id: 7,  content: '检查仓库库存并补充热销品',                        date: '2026-07-12', status: 'pending',   color: 'green',  author: '小李' },
  { id: 8,  content: '回复美国客户的验厂问题清单',                      date: '2026-07-11', status: 'completed', color: 'white',  author: '你' },
  { id: 9,  content: '安排下月广交会展位设计方案比选',                  date: '2026-07-11', status: 'pending',   color: 'yellow', author: '你' },
  { id: 10, content: '整理上周会议纪要并分发各部门',                    date: '2026-07-10', status: 'completed', color: 'white',  author: '小王' },
]

const tabDefs = [
  { key: 'all',       label: '全部',   icon: List,        count: mockTodos.length },
  { key: 'pending',   label: '待完成', icon: Clock,       count: mockTodos.filter(t => t.status === 'pending').length },
  { key: 'completed', label: '已完成', icon: CircleCheck, count: mockTodos.filter(t => t.status === 'completed').length },
  { key: 'urgent',    label: '紧急',   icon: Flag,        count: mockTodos.filter(t => t.color === 'red').length },
]

const activeTab = ref('all')

function filterByTab(items: MockTodo[], tab: string): MockTodo[] {
  if (tab === 'all') return items
  if (tab === 'pending') return items.filter(t => t.status === 'pending')
  if (tab === 'completed') return items.filter(t => t.status === 'completed')
  if (tab === 'urgent') return items.filter(t => t.color === 'red')
  return items
}

const filteredItems = computed(() => filterByTab(mockTodos, activeTab.value))
</script>

<style scoped>
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

.demo-section { margin-bottom: 40px; }

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  font-size: 14px;
  font-weight: 700;
  padding: 0 6px;
}

.section-sub {
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
   药丸式 Tab
   ============================================================ */
.tabs-b {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f3f4f6;
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

.tab-b-count {
  font-size: 11px;
  background: rgba(0,0,0,0.08);
  color: inherit;
  padding: 0 7px;
  border-radius: 10px;
  line-height: 18px;
  transition: all 0.2s;
}

.tab-b.active .tab-b-count {
  background: rgba(255,255,255,0.25);
  color: white;
}
</style>
