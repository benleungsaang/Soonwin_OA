<template>
  <div class="demo-page">
    <CommonHeader title="条目样式 Demo（已定稿）" />

    <div class="demo-container">
      <p class="demo-intro">
        上部药丸式 tab <strong>✓ 已定稿</strong> · 下部样式② <strong>已选用</strong>
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
           下部：样式② 彩色圆点式（已选用）
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge selected-badge">★</span>
          下部条目：彩色圆点式 <span class="selected-label">已选用</span>
          <span class="section-sub">—— 含缩略图 · 三点菜单 · 点击查看明细</span>
        </h2>
        <div class="demo-card">
          <ListStyle02 :items="filteredItems" />
        </div>
      </section>

      <!-- ============================================================
           详情弹窗样式对比
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge selected-badge">★</span>
          详情弹窗样式 <span class="selected-label">已选用 A</span>
          <span class="section-sub">—— 左轨时间线，内容卡片浅灰背景+边框</span>
        </h2>

        <!-- 三列预览按钮 -->
        <div class="detail-preview-row">
          <button class="preview-card preview-chosen" @click="openDialog('a')">
            <span class="preview-badge" style="background:#6366f1">A</span>
            <span class="preview-label">左轨时间线 <span class="chosen-tag">已选用</span></span>
            <span class="preview-desc">卡片左侧时间线导轨·内容自由流淌</span>
          </button>
          <button class="preview-card" @click="openDialog('b')">
            <span class="preview-badge" style="background:#0891b2">B</span>
            <span class="preview-label">流式时间线</span>
            <span class="preview-desc">节点贯穿内容·分段但不分卡·圆点标记</span>
          </button>
          <button class="preview-card" @click="openDialog('c')">
            <span class="preview-badge" style="background:#7c3aed">C</span>
            <span class="preview-label">卡片融合式</span>
            <span class="preview-desc">彩色侧边栏·信息流式垂直排列</span>
          </button>
        </div>
      </section>

      <!-- ============================================================
           功能说明卡
           ============================================================ -->
      <section class="feature-card">
        <h3>当前条目功能列表（模拟）</h3>
        <div class="feature-grid">
          <div class="feat-item"><span class="feat-icon">🖼️</span><span>缩略图占位</span></div>
          <div class="feat-item"><span class="feat-icon">🎨</span><span>三点菜单 → 选择颜色</span></div>
          <div class="feat-item"><span class="feat-icon">✏️</span><span>三点菜单 → 修改内容</span></div>
          <div class="feat-item"><span class="feat-icon">🗑️</span><span>三点菜单 → 删除</span></div>
          <div class="feat-item"><span class="feat-icon">👁️</span><span>点击条目 → 查看详情</span></div>
          <div class="feat-item"><span class="feat-icon">📋</span><span>A/B/C 三种详情弹窗样式</span></div>
        </div>
      </section>
    </div>

    <!-- ============================================================
         样式 A：左轨时间线 — 卡片左侧时间线导轨，内容自由流淌
         ============================================================ -->
    <el-dialog v-model="dialogA.visible" title="任务详情" width="520px" top="8vh">
      <div class="da-outer">
        <!-- 时间线导轨（固定左侧） -->
        <div class="da-rail">
          <div class="da-rail-line"></div>
          <div class="da-rail-dot"></div>
        </div>

        <!-- 卡片内容 -->
        <div class="da-card">
          <!-- 顶栏 -->
          <div class="da-top">
            <span class="da-status" :class="demoItem.status==='completed'?'da-done':'da-pending'">
              {{ demoItem.status==='completed'?'✓ 已完成':'● 待完成' }}
            </span>
            <span class="da-date">{{ demoItem.date }}</span>
            <span class="da-author">{{ demoItem.author }}</span>
          </div>

          <!-- 主题（无标签） -->
          <div class="da-subject">{{ demoItem.content }}</div>

          <!-- 备注（直接跟在主题下，无标题） -->
          <div v-if="demoItem.note" class="da-note-text">{{ demoItem.note }}</div>

          <!-- 附图（无标题） -->
          <div v-if="demoItem.image_url" class="da-img-wrap">
            <div class="d-thumb da-thumb" :style="{ background: thumbBg(demoItem) }">
              <span class="d-thumb-icon">🖼️</span>
            </div>
          </div>

          <!-- 完成信息 -->
          <template v-if="demoItem.status === 'completed'">
            <div class="da-sep"></div>
            <div class="da-complete-header">✅ 完成情况</div>
            <div v-if="demoItem.completion_note" class="da-comp-note">{{ demoItem.completion_note }}</div>
            <div v-if="demoItem.completion_image_url" class="da-img-wrap">
              <div class="d-thumb da-thumb" style="background:linear-gradient(135deg,#d1fae5,#a7f3d0)">
                <span class="d-thumb-icon">✅</span>
              </div>
            </div>
            <div v-if="demoItem.completed_at" class="da-comp-time">{{ demoItem.completed_at }}</div>
          </template>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogA.visible=false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         样式 B：流式时间线 — 节点贯穿内容，分段但不分卡
         ============================================================ -->
    <el-dialog v-model="dialogB.visible" title="任务详情" width="520px" top="6vh">
      <div class="db-outer">
        <div class="db-timeline">
          <!-- 节点 1：主题 + 备注（合并，无备注标题） -->
          <div class="db-node">
            <div class="db-dot db-dot-main"></div>
            <div class="db-node-body">
              <div class="db-subject">{{ demoItem.content }}</div>
              <div v-if="demoItem.note" class="db-note-text">{{ demoItem.note }}</div>
            </div>
          </div>

          <!-- 节点 2：附图（无标题） -->
          <div v-if="demoItem.image_url" class="db-node">
            <div class="db-dot db-dot-sub"></div>
            <div class="db-node-body">
              <div class="d-thumb db-thumb" :style="{ background: thumbBg(demoItem) }">
                <span class="d-thumb-icon">🖼️</span>
              </div>
            </div>
          </div>

          <!-- 节点 3：完成信息 -->
          <template v-if="demoItem.status === 'completed'">
            <div class="db-node">
              <div class="db-dot db-dot-done"></div>
              <div class="db-node-body">
                <div class="db-section-label">✅ 完成情况</div>
                <div v-if="demoItem.completion_note" class="db-note-text" style="margin-top:6px">{{ demoItem.completion_note }}</div>
                <div v-if="demoItem.completion_image_url" class="d-thumb db-thumb" style="margin-top:8px;background:linear-gradient(135deg,#d1fae5,#a7f3d0)">
                  <span class="d-thumb-icon">✅</span>
                </div>
                <div v-if="demoItem.completed_at" class="db-meta" style="margin-top:6px">{{ demoItem.completed_at }}</div>
              </div>
            </div>
          </template>
        </div>

        <!-- 浮动状态角标 -->
        <div class="db-corner-badge" :class="demoItem.status==='completed'?'db-c-done':'db-c-pending'">
          <span class="db-corner-status">{{ demoItem.status==='completed'?'已完成':'待完成' }}</span>
          <span class="db-corner-date">{{ demoItem.date }}</span>
          <span class="db-corner-author">{{ demoItem.author }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogB.visible=false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         样式 C：卡片融合式 — 彩色侧边栏 + 信息流式垂直排列
         ============================================================ -->
    <el-dialog v-model="dialogC.visible" title="任务详情" width="520px" top="8vh">
      <div class="dc-outer" :class="'dc-accent-' + demoItem.color">
        <!-- 左侧彩色侧边栏 -->
        <div class="dc-accent"></div>

        <!-- 主卡片 -->
        <div class="dc-card">
          <!-- 元信息行 -->
          <div class="dc-meta-row">
            <span class="dc-pill" :class="demoItem.status==='completed'?'dc-pill-done':'dc-pill-pending'">
              {{ demoItem.status==='completed'?'已完成':'待完成' }}
            </span>
            <span class="dc-date">{{ demoItem.date }}</span>
            <span class="dc-author">{{ demoItem.author }}</span>
          </div>

          <!-- 主题 -->
          <div class="dc-subject">{{ demoItem.content }}</div>

          <!-- 备注（无标题，灰色底框） -->
          <div v-if="demoItem.note" class="dc-note-block">{{ demoItem.note }}</div>

          <!-- 附图（无标题） -->
          <div v-if="demoItem.image_url" class="dc-img-block">
            <div class="d-thumb dc-thumb" :style="{ background: thumbBg(demoItem) }">
              <span class="d-thumb-icon">🖼️</span>
            </div>
          </div>

          <!-- 完成信息 -->
          <template v-if="demoItem.status === 'completed'">
            <div class="dc-divider"></div>
            <div class="dc-section-tag">✅ 完成情况</div>
            <div v-if="demoItem.completion_note" class="dc-note-block">{{ demoItem.completion_note }}</div>
            <div v-if="demoItem.completion_image_url" class="dc-img-block">
              <div class="d-thumb dc-thumb" style="background:linear-gradient(135deg,#d1fae5,#a7f3d0)">
                <span class="d-thumb-icon">✅</span>
              </div>
            </div>
            <div v-if="demoItem.completed_at" class="dc-meta-time">{{ demoItem.completed_at }}</div>
          </template>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogC.visible=false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { List, CircleCheck, Clock, Flag } from '@element-plus/icons-vue'
import CommonHeader from '@/components/CommonHeader.vue'
import ListStyle02 from './ListStyle02.vue'

// ===== 模拟数据 =====
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
  { id:1, content:'完成哥伦比亚餐具套装的邮件回复 📧',           date:'2026-07-14', status:'pending', color:'white', author:'你',
    note:'客户要求提供 FOB 价格和最小起订量，需先跟工厂确认',     image_url:'mock' },
  { id:2, content:'审核李经理提交的差旅报销单据',                 date:'2026-07-14', status:'pending', color:'yellow', author:'你',
    note:'包括机票、酒店、交通共 3 笔，总金额 ¥8,632',            image_url:'' },
  { id:3, content:'确认下周客户来访行程安排 ✈️',                 date:'2026-07-14', status:'completed', color:'white', author:'你',
    note:'7/20 广州白云机场接机，已预订希尔顿',                    image_url:'mock',
    completion_note:'已跟客户最终确认 arrival time 为 14:30',     completed_at:'2026-07-14 10:23' },
  { id:4, content:'准备季度销售数据汇总 PPT',                     date:'2026-07-13', status:'pending', color:'red', author:'你',
    note:'需包含北美、欧洲、东南亚三个区域数据，截止周五',         image_url:'' },
  { id:5, content:'跟进墨西哥客户的新样品需求',                   date:'2026-07-13', status:'completed', color:'white', author:'小王',
    note:'客户要求 3 款新样品，已安排打样',                        image_url:'mock',
    completion_note:'样品已寄出，DHL 单号 1234-5678-90',          completion_image_url:'mock', completed_at:'2026-07-13 16:45' },
  { id:6, content:'更新产品目录第三章节内容',                     date:'2026-07-13', status:'pending', color:'blue', author:'你',
    note:'新增陶瓷系列 12 页，需等美工出图',                       image_url:'' },
  { id:7, content:'检查仓库库存并补充热销品',                     date:'2026-07-12', status:'pending', color:'green', author:'小李',
    note:'重点检查 KA32 系列库存',                                 image_url:'' },
  { id:8, content:'回复美国客户的验厂问题清单',                   date:'2026-07-11', status:'completed', color:'white', author:'你',
    note:'客户发来 45 项问题列表，已逐条回复',                     image_url:'mock',
    completion_note:'客户表示满意，安排下周视频验厂',              completed_at:'2026-07-11 09:30' },
  { id:9, content:'安排下月广交会展位设计方案比选',               date:'2026-07-11', status:'pending', color:'yellow', author:'你',
    note:'3 家设计公司提交了方案，周三开会讨论',                   image_url:'' },
  { id:10,content:'整理上周会议纪要并分发各部门',                 date:'2026-07-10', status:'completed', color:'white', author:'小王',
    note:'上周会议讨论了 Q3 销售目标和人员调整',                   image_url:'',
    completion_note:'已邮件发送给全体部门经理',                     completed_at:'2026-07-10 17:00' },
]

const tabDefs = [
  { key:'all', label:'全部', icon:List, count:mockTodos.length },
  { key:'pending', label:'待完成', icon:Clock, count:mockTodos.filter(t=>t.status==='pending').length },
  { key:'completed', label:'已完成', icon:CircleCheck, count:mockTodos.filter(t=>t.status==='completed').length },
  { key:'urgent', label:'紧急', icon:Flag, count:mockTodos.filter(t=>t.color==='red').length },
]

const activeTab = ref('all')
function filterByTab(items:MockTodo[], tab:string):MockTodo[] {
  if(tab==='all') return items
  if(tab==='pending') return items.filter(t=>t.status==='pending')
  if(tab==='completed') return items.filter(t=>t.status==='completed')
  if(tab==='urgent') return items.filter(t=>t.color==='red')
  return items
}
const filteredItems = computed(()=>filterByTab(mockTodos,activeTab.value))

// ===== 颜色 & 缩略图 =====
const colorOptions = [
  { value:'white',label:'默认' }, { value:'red',label:'紧急' },
  { value:'yellow',label:'重要' }, { value:'green',label:'完成' },
  { value:'blue',label:'进行中' }, { value:'dark',label:'长期' },
]
const colorLabel = (c:string)=>colorOptions.find(o=>o.value===c)?.label||c

function thumbBg(item:MockTodo):string {
  const m:Record<string,string>={
    white:'linear-gradient(135deg,#e5e7eb,#d1d5db)', red:'linear-gradient(135deg,#fca5a5,#f87171)',
    yellow:'linear-gradient(135deg,#fde68a,#fbbf24)', green:'linear-gradient(135deg,#a7f3d0,#6ee7b7)',
    blue:'linear-gradient(135deg,#93c5fd,#60a5fa)', dark:'linear-gradient(135deg,#d1d5db,#9ca3af)',
  }
  return m[item.color]||m.white
}

// ===== 三个弹窗的状态 =====
const dialogA = reactive({ visible:false })
const dialogB = reactive({ visible:false })
const dialogC = reactive({ visible:false })

// 用于弹窗显示的任务（取第 1 条有附件的待完成任务）
// 优先用 id=1（有备注有图），tab 筛选后可能没有，所以直接引用 mockTodos[0]
const demoItem = computed<MockTodo>(() => {
  // 优先找一个有图有待完成的条目
  const rich = mockTodos.find(t=>t.image_url && t.status==='pending' && t.note)
  return rich || mockTodos[0]
})

function openDialog(which:'a'|'b'|'c') {
  if(which==='a') dialogA.visible=true
  else if(which==='b') dialogB.visible=true
  else dialogC.visible=true
}
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
.demo-container { max-width: 800px; margin: 0 auto; }
.demo-intro { text-align: center; color: #6b7280; font-size: 15px; margin-bottom: 32px; }
.intro-note { display: block; margin-top: 4px; font-size: 13px; color: #9ca3af; }
.demo-section { margin-bottom: 40px; }

.section-title {
  font-size: 18px; font-weight: 600; color: #1f2937;
  margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.section-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 28px; height: 28px; border-radius: 6px; background: #3b82f6;
  color: white; font-size: 14px; font-weight: 700; padding: 0 6px;
}
.selected-badge { background: #059669; }
.selected-label { font-size:12px; font-weight:600; background:#d1fae5; color:#059669; padding:2px 10px; border-radius:10px; }
.section-sub { font-size:14px; font-weight:400; color:#9ca3af; }

.demo-card { background:white; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08),0 1px 2px rgba(0,0,0,0.04); overflow:hidden; }

/* ============================================================
   药丸式 Tab
   ============================================================ */
.tabs-b { display:flex; gap:4px; padding:12px 16px; background:#f3f4f6; }
.tab-b {
  flex:1; padding:8px 12px; font-size:13px; font-weight:500; color:#6b7280;
  background:transparent; border:none; border-radius:20px; cursor:pointer;
  transition:all 0.25s; display:flex; align-items:center; justify-content:center; gap:5px; white-space:nowrap;
}
.tab-b:hover { color:#374151; background:rgba(0,0,0,0.03); }
.tab-b.active { color:white; background:#3b82f6; box-shadow:0 2px 8px rgba(59,130,246,0.3); }
.tab-b-icon { font-size:15px; }
.tab-b-count { font-size:11px; background:rgba(0,0,0,0.08); color:inherit; padding:0 7px; border-radius:10px; line-height:18px; transition:all 0.2s; }
.tab-b.active .tab-b-count { background:rgba(255,255,255,0.25); color:white; }

/* ============================================================
   详情弹窗预览按钮
   ============================================================ */
.detail-preview-row {
  display: flex;
  gap: 16px;
}
.preview-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 20px 12px 16px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.preview-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 16px rgba(59,130,246,0.12);
  transform: translateY(-2px);
}
.preview-badge {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border-radius: 50%; color: white;
  font-size: 16px; font-weight: 700;
}
.preview-label { font-size:14px; font-weight:600; color:#1f2937; }
.preview-desc { font-size:12px; color:#9ca3af; }

/* 已选中的预览卡 */
.preview-chosen {
  border-color: #6366f1 !important;
  background: #f5f3ff !important;
  box-shadow: 0 4px 16px rgba(99,102,241,0.12);
}
.chosen-tag {
  font-size: 10px;
  font-weight: 600;
  background: #6366f1;
  color: white;
  padding: 1px 6px;
  border-radius: 6px;
  margin-left: 4px;
  vertical-align: middle;
}

/* ============================================================
   功能说明卡
   ============================================================ */
.feature-card { background:white; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,0.08); padding:20px 24px; margin-bottom:60px; }
.feature-card h3 { font-size:15px; font-weight:600; color:#374151; margin:0 0 14px 0; }
.feature-grid { display:flex; flex-wrap:wrap; gap:10px; }
.feat-item { display:flex; align-items:center; gap:6px; font-size:13px; color:#6b7280; background:#f9fafb; padding:6px 14px; border-radius:8px; }
.feat-icon { font-size:16px; }

/* ============================================================
   共享：缩略图
   ============================================================ */
.d-thumb {
  width: 100px; height: 64px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(0,0,0,0.06); flex-shrink: 0;
}
.d-thumb-icon { font-size: 22px; opacity: 0.7; }

/* ============================================================
   样式 A：左轨时间线
   ============================================================ */
.da-outer {
  display: flex;
  gap: 16px;
  padding: 4px 0;
  min-height: 120px;
}

/* 时间线导轨 */
.da-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
  padding-top: 6px;
}
.da-rail-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #3b82f6;
  border: 2px solid white;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
  flex-shrink: 0;
  z-index: 1;
}
.da-rail-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(to bottom, #e5e7eb, #f3f4f6);
  margin-top: -2px;
  margin-bottom: -2px;
}

/* 卡片（浅灰背景 + 边框，包围内容部分，不含时间线和弹窗标题） */
.da-card {
  flex: 1;
  min-width: 0;
  background: #f8f9fb;
  border: 1px solid #e8eaee;
  border-radius: 10px;
  padding: 16px 18px;
}

.da-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.da-status { font-size:11px; font-weight:600; padding:2px 10px; border-radius:6px; }
.da-pending { background:#dbeafe; color:#2563eb; }
.da-done { background:#d1fae5; color:#059669; }
.da-date { font-size:12px; color:#9ca3af; margin-left:auto; }
.da-author { font-size:12px; color:#6b7280; background:#f3f4f6; padding:1px 10px; border-radius:10px; }

.da-subject {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.6;
  margin-bottom: 10px;
  word-break: break-word;
}

.da-note-text {
  font-size: 14px;
  color: #4b5563;
  background: #ffffff;
  border: 1px solid #e8eaee;
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.7;
  margin-bottom: 10px;
  word-break: break-word;
  white-space: pre-wrap;
}

.da-img-wrap { margin-bottom: 10px; }
.da-thumb { width: 120px; height: 72px; }

.da-sep { height:1px; background:#e5e7eb; margin:14px 0; }

.da-complete-header {
  font-size: 13px;
  font-weight: 600;
  color: #059669;
  margin-bottom: 8px;
}
.da-comp-note {
  font-size: 14px;
  color: #374151;
  background: #ffffff;
  border: 1px solid #d1fae5;
  padding: 8px 12px;
  border-radius: 8px;
  line-height: 1.6;
  margin-bottom: 8px;
  word-break: break-word;
}
.da-comp-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

/* ============================================================
   样式 B：流式时间线
   ============================================================ */
.db-outer {
  display: flex;
  gap: 0;
  padding: 4px 0;
  position: relative;
}

/* 状态角标（右上角） */
.db-corner-badge {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  padding: 6px 12px;
  border-radius: 0 10px 0 8px;
  font-size: 11px;
}
.db-c-pending { background:#eff6ff; }
.db-c-done { background:#ecfdf5; }
.db-corner-status { font-weight:600; }
.db-c-pending .db-corner-status { color:#2563eb; }
.db-c-done .db-corner-status { color:#059669; }
.db-corner-date { color:#9ca3af; }
.db-corner-author { color:#6b7280; }

/* 时间线 */
.db-timeline {
  flex: 1;
  position: relative;
  padding: 4px 0 4px 28px;
}
.db-timeline::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: #e5e7eb;
  border-radius: 1px;
}

.db-node {
  display: flex;
  gap: 16px;
  padding-bottom: 22px;
  position: relative;
}
.db-node:last-child { padding-bottom: 4px; }

.db-dot {
  position: absolute;
  left: -20px;
  border-radius: 50%;
  flex-shrink: 0;
  z-index: 1;
  border: 2px solid white;
}
.db-dot-main {
  width: 14px;
  height: 14px;
  top: 2px;
  background: #0891b2;
  box-shadow: 0 0 0 3px rgba(8,145,178,0.15);
}
.db-dot-sub {
  width: 8px;
  height: 8px;
  top: 5px;
  background: #d1d5db;
  border: none;
}
.db-dot-done {
  width: 10px;
  height: 10px;
  top: 4px;
  background: #059669;
  border: none;
}

.db-node-body {
  flex: 1;
  min-width: 0;
}

.db-subject {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.6;
  word-break: break-word;
}

.db-note-text {
  font-size: 14px;
  color: #4b5563;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 8px;
  line-height: 1.7;
  margin-top: 6px;
  word-break: break-word;
  white-space: pre-wrap;
}

.db-thumb { margin-top: 6px; }

.db-section-label {
  font-size: 13px;
  font-weight: 600;
  color: #059669;
}

.db-meta {
  font-size: 12px;
  color: #9ca3af;
}

/* ============================================================
   样式 C：卡片融合式
   ============================================================ */
.dc-outer {
  display: flex;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  min-height: 120px;
}

/* 左侧彩色侧边栏 */
.dc-accent {
  width: 5px;
  flex-shrink: 0;
}
.dc-accent-white  { background: #d1d5db; }
.dc-accent-red    { background: #f87171; }
.dc-accent-yellow { background: #fbbf24; }
.dc-accent-green  { background: #34d399; }
.dc-accent-blue   { background: #60a5fa; }
.dc-accent-dark   { background: #9ca3af; }

.dc-card {
  flex: 1;
  padding: 20px;
  min-width: 0;
}

.dc-meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.dc-pill { font-size:11px; font-weight:600; padding:2px 10px; border-radius:20px; }
.dc-pill-pending { background:#dbeafe; color:#2563eb; }
.dc-pill-done { background:#d1fae5; color:#059669; }
.dc-date { font-size:12px; color:#9ca3af; margin-left:auto; }
.dc-author { font-size:12px; color:#6b7280; background:#f3f4f6; padding:1px 10px; border-radius:10px; }

.dc-subject {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.6;
  margin-bottom: 12px;
  word-break: break-word;
}

.dc-note-block {
  font-size: 14px;
  color: #4b5563;
  background: #f9fafb;
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.7;
  margin-bottom: 10px;
  word-break: break-word;
  white-space: pre-wrap;
}

.dc-img-block { margin-bottom: 10px; }
.dc-thumb { width: 120px; height: 72px; }

.dc-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 14px 0;
}

.dc-section-tag {
  font-size: 13px;
  font-weight: 600;
  color: #059669;
  margin-bottom: 8px;
}

.dc-meta-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}
</style>
