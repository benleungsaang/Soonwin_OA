<template>
  <div class="demo-page">
    <CommonHeader title="条目样式 Demo（已定稿）" />

    <div class="demo-container">
      <p class="demo-intro">
        上部药丸式 tab <strong>✓ 已定稿</strong> · 下部样式② <strong>已选用</strong>，含完整功能模拟
        <span class="intro-note">（所有操作为本地模拟，不涉及后端 API）</span>
      </p>

      <!-- ============================================================
           上部：药丸式 Tab
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge selected-badge">✓</span>
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
           下部：样式② 彩色圆点式（已选用 + 完整功能模拟）
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge selected-badge">★</span>
          下部条目：彩色圆点式 <span class="selected-label">已选用</span>
          <span class="section-sub">—— 含缩略图 · 三点菜单 · 点击查看明细（全部模拟）</span>
        </h2>
        <div class="demo-card">
          <ListStyle02 :items="filteredItems" />
        </div>
      </section>

      <!-- 功能说明卡 -->
      <section class="feature-card">
        <h3>当前条目功能列表（模拟）</h3>
        <div class="feature-grid">
          <div class="feat-item">
            <span class="feat-icon">🖼️</span>
            <span>缩略图占位（60×40px）</span>
          </div>
          <div class="feat-item">
            <span class="feat-icon">🎨</span>
            <span>三点菜单 → 选择颜色（6 色）</span>
          </div>
          <div class="feat-item">
            <span class="feat-icon">✏️</span>
            <span>三点菜单 → 修改内容</span>
          </div>
          <div class="feat-item">
            <span class="feat-icon">🗑️</span>
            <span>三点菜单 → 删除条目</span>
          </div>
          <div class="feat-item">
            <span class="feat-icon">👁️</span>
            <span>点击条目 → 查看详情弹窗（只读）</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { List, CircleCheck, Clock, Flag } from '@element-plus/icons-vue'
import CommonHeader from '@/components/CommonHeader.vue'
import ListStyle02 from './ListStyle02.vue'

// ===== 更丰富的模拟数据（含 note / image_url） =====
interface MockTodo {
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

const mockTodos: MockTodo[] = [
  {
    id: 1, content: '完成哥伦比亚餐具套装的邮件回复 📧',
    date: '2026-07-14', status: 'pending', color: 'white', author: '你',
    note: '客户要求提供 FOB 价格和最小起订量，需先跟工厂确认',
    image_url: 'mock',
  },
  {
    id: 2, content: '审核李经理提交的差旅报销单据',
    date: '2026-07-14', status: 'pending', color: 'yellow', author: '你',
    note: '包括机票、酒店、交通共 3 笔，总金额 ¥8,632',
    image_url: '',
  },
  {
    id: 3, content: '确认下周客户来访行程安排 ✈️',
    date: '2026-07-14', status: 'completed', color: 'white', author: '你',
    note: '7/20 广州白云机场接机，已预订希尔顿',
    image_url: 'mock',
    completion_note: '已跟客户最终确认 arrival time 为 14:30',
    completed_at: '2026-07-14 10:23',
  },
  {
    id: 4, content: '准备季度销售数据汇总 PPT',
    date: '2026-07-13', status: 'pending', color: 'red', author: '你',
    note: '需包含北美、欧洲、东南亚三个区域数据，截止周五',
    image_url: '',
  },
  {
    id: 5, content: '跟进墨西哥客户的新样品需求',
    date: '2026-07-13', status: 'completed', color: 'white', author: '小王',
    note: '客户要求 3 款新样品，已安排打样',
    image_url: 'mock',
    completion_note: '样品已寄出，DHL 单号 1234-5678-90',
    completion_image_url: 'mock',
    completed_at: '2026-07-13 16:45',
  },
  {
    id: 6, content: '更新产品目录第三章节内容',
    date: '2026-07-13', status: 'pending', color: 'blue', author: '你',
    note: '新增陶瓷系列 12 页，需等美工出图',
    image_url: '',
  },
  {
    id: 7, content: '检查仓库库存并补充热销品',
    date: '2026-07-12', status: 'pending', color: 'green', author: '小李',
    note: '重点检查 KA32 系列库存',
    image_url: '',
  },
  {
    id: 8, content: '回复美国客户的验厂问题清单',
    date: '2026-07-11', status: 'completed', color: 'white', author: '你',
    note: '客户发来 45 项问题列表，已逐条回复',
    image_url: 'mock',
    completion_note: '客户表示满意，安排下周视频验厂',
    completed_at: '2026-07-11 09:30',
  },
  {
    id: 9, content: '安排下月广交会展位设计方案比选',
    date: '2026-07-11', status: 'pending', color: 'yellow', author: '你',
    note: '3 家设计公司提交了方案，周三开会讨论',
    image_url: '',
  },
  {
    id: 10, content: '整理上周会议纪要并分发各部门',
    date: '2026-07-10', status: 'completed', color: 'white', author: '小王',
    note: '上周会议讨论了 Q3 销售目标和人员调整',
    image_url: '',
    completion_note: '已邮件发送给全体部门经理',
    completed_at: '2026-07-10 17:00',
  },
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

.intro-note {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  color: #9ca3af;
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
  flex-wrap: wrap;
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

.selected-badge { background: #059669; }

.selected-label {
  font-size: 12px;
  font-weight: 600;
  background: #d1fae5;
  color: #059669;
  padding: 2px 10px;
  border-radius: 10px;
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

/* ============================================================
   功能说明卡
   ============================================================ */
.feature-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  padding: 20px 24px;
  margin-bottom: 60px;
}

.feature-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 14px 0;
}

.feature-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.feat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
  background: #f9fafb;
  padding: 6px 14px;
  border-radius: 8px;
}

.feat-icon { font-size: 16px; }
</style>
