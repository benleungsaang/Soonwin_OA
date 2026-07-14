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
          <span class="section-badge">▼</span>
          详情弹窗样式投票
          <span class="section-sub">—— 同一数据，三种布局，请选择你最喜欢的一款</span>
        </h2>

        <!-- 三列预览按钮 -->
        <div class="detail-preview-row">
          <button class="preview-card" @click="openDialog('a')">
            <span class="preview-badge" style="background:#3b82f6">A</span>
            <span class="preview-label">清爽两栏式</span>
            <span class="preview-desc">左标签·右数值·横线分隔</span>
          </button>
          <button class="preview-card" @click="openDialog('b')">
            <span class="preview-badge" style="background:#059669">B</span>
            <span class="preview-label">卡片分层式</span>
            <span class="preview-desc">分区面板·左色条·现代感</span>
          </button>
          <button class="preview-card" @click="openDialog('c')">
            <span class="preview-badge" style="background:#d97706">C</span>
            <span class="preview-label">信息时间线式</span>
            <span class="preview-desc">纵向时间线·圆点标记·流畅</span>
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
         样式 A：清爽两栏式
         ============================================================ -->
    <el-dialog v-model="dialogA.visible" title="任务详情" width="520px" top="8vh">
      <div class="da-body">
        <!-- 顶栏：状态标签 -->
        <div class="da-topbar">
          <span
            class="da-status"
            :class="demoItem.status === 'completed' ? 'da-done' : 'da-pending'"
          >
            {{ demoItem.status === 'completed' ? '✓ 已完成' : '● 待完成' }}
          </span>
          <span class="da-color-tag">
            <span class="da-dot" :class="'dot-' + demoItem.color"></span>
            {{ colorLabel(demoItem.color) }}
          </span>
          <span class="da-author-label">{{ demoItem.author }}</span>
        </div>

        <div class="da-fields">
          <div class="da-row">
            <span class="da-label">任务内容</span>
            <span class="da-val da-content">{{ demoItem.content }}</span>
          </div>
          <div class="da-row">
            <span class="da-label">所属日期</span>
            <span class="da-val">{{ demoItem.date }}</span>
          </div>
          <div class="da-row">
            <span class="da-label">任务备注</span>
            <span class="da-val da-note">{{ demoItem.note }}</span>
          </div>
          <div v-if="demoItem.image_url" class="da-row da-row-img">
            <span class="da-label">任务附图</span>
            <div class="d-thumb" :style="{ background: thumbBg(demoItem) }">
              <span class="d-thumb-icon">🖼️</span>
            </div>
          </div>

          <template v-if="demoItem.status === 'completed'">
            <div class="da-sep"></div>
            <div class="da-subtitle">完成信息</div>
            <div v-if="demoItem.completion_note" class="da-row">
              <span class="da-label">完成内容</span>
              <span class="da-val da-note">{{ demoItem.completion_note }}</span>
            </div>
            <div v-if="demoItem.completion_image_url" class="da-row da-row-img">
              <span class="da-label">完成图片</span>
              <div class="d-thumb" style="background:linear-gradient(135deg,#d1fae5,#a7f3d0)">
                <span class="d-thumb-icon">✅</span>
              </div>
            </div>
            <div v-if="demoItem.completed_at" class="da-row">
              <span class="da-label">完成时间</span>
              <span class="da-val">{{ demoItem.completed_at }}</span>
            </div>
          </template>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogA.visible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         样式 B：卡片分层式
         ============================================================ -->
    <el-dialog v-model="dialogB.visible" title="任务详情" width="520px" top="6vh">
      <div class="db-body">
        <!-- 头部卡 -->
        <div class="db-head-card" :class="'hc-' + demoItem.color">
          <div class="db-head-top">
            <span
              class="db-status"
              :class="demoItem.status === 'completed' ? 'db-done' : 'db-pending'"
            >{{ demoItem.status === 'completed' ? '已完成' : '待完成' }}</span>
            <span class="db-author">👤 {{ demoItem.author }}</span>
          </div>
          <div class="db-head-content">{{ demoItem.content }}</div>
          <div class="db-head-date">{{ demoItem.date }}</div>
        </div>

        <!-- 备注卡 -->
        <div v-if="demoItem.note" class="db-section-card">
          <div class="db-sc-label">📝 任务备注</div>
          <div class="db-sc-body">{{ demoItem.note }}</div>
        </div>

        <!-- 附图卡 -->
        <div v-if="demoItem.image_url" class="db-section-card">
          <div class="db-sc-label">🖼️ 任务附图</div>
          <div class="d-thumb db-thumb" :style="{ background: thumbBg(demoItem) }">
            <span class="d-thumb-icon">🖼️</span>
          </div>
        </div>

        <!-- 完成卡 -->
        <template v-if="demoItem.status === 'completed'">
          <div class="db-section-card db-complete-card">
            <div class="db-sc-label">✅ 完成情况</div>
            <div v-if="demoItem.completion_note" class="db-sc-body">{{ demoItem.completion_note }}</div>
            <div v-if="demoItem.completion_image_url" class="db-sc-body" style="margin-top:8px">
              <div class="d-thumb" style="background:linear-gradient(135deg,#d1fae5,#a7f3d0)">
                <span class="d-thumb-icon">✅</span>
              </div>
            </div>
            <div v-if="demoItem.completed_at" class="db-sc-meta">{{ demoItem.completed_at }}</div>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button @click="dialogB.visible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         样式 C：信息时间线式
         ============================================================ -->
    <el-dialog v-model="dialogC.visible" title="任务详情" width="520px" top="8vh">
      <div class="dc-body">
        <!-- 顶栏状态 -->
        <div class="dc-top">
          <span
            class="dc-pill"
            :class="demoItem.status === 'completed' ? 'dc-pill-done' : 'dc-pill-pending'"
          >{{ demoItem.status === 'completed' ? '已完成' : '待完成' }}</span>
          <span class="dc-color"><span class="dc-dot" :class="'dot-' + demoItem.color"></span>{{ colorLabel(demoItem.color) }}</span>
        </div>

        <!-- 时间线区域 -->
        <div class="dc-timeline">
          <!-- 01 内容 -->
          <div class="dc-node">
            <div class="dc-node-dot dc-node-main"></div>
            <div class="dc-node-body">
              <div class="dc-node-label">任务内容</div>
              <div class="dc-node-val dc-content">{{ demoItem.content }}</div>
            </div>
          </div>

          <!-- 02 日期 + 作者 -->
          <div class="dc-node">
            <div class="dc-node-dot dc-node-sub"></div>
            <div class="dc-node-body">
              <div class="dc-node-label">所属日期</div>
              <div class="dc-node-val">{{ demoItem.date }}</div>
            </div>
          </div>
          <div class="dc-node">
            <div class="dc-node-dot dc-node-sub"></div>
            <div class="dc-node-body">
              <div class="dc-node-label">发布人</div>
              <div class="dc-node-val"><span class="dc-author-pill">{{ demoItem.author }}</span></div>
            </div>
          </div>

          <!-- 03 备注 -->
          <div v-if="demoItem.note" class="dc-node">
            <div class="dc-node-dot dc-node-sub"></div>
            <div class="dc-node-body">
              <div class="dc-node-label">任务备注</div>
              <div class="dc-node-val dc-note-text">{{ demoItem.note }}</div>
            </div>
          </div>

          <!-- 04 附图 -->
          <div v-if="demoItem.image_url" class="dc-node">
            <div class="dc-node-dot dc-node-sub"></div>
            <div class="dc-node-body">
              <div class="dc-node-label">任务附图</div>
              <div class="d-thumb dc-thumb" :style="{ background: thumbBg(demoItem) }">
                <span class="d-thumb-icon">🖼️</span>
              </div>
            </div>
          </div>

          <!-- 完成信息 -->
          <template v-if="demoItem.status === 'completed'">
            <div class="dc-node">
              <div class="dc-node-dot dc-node-done"></div>
              <div class="dc-node-body">
                <div class="dc-node-label dc-done-label">✅ 完成情况</div>
              </div>
            </div>
            <div v-if="demoItem.completion_note" class="dc-node">
              <div class="dc-node-dot dc-node-sub"></div>
              <div class="dc-node-body">
                <div class="dc-node-label">完成内容</div>
                <div class="dc-node-val dc-note-text">{{ demoItem.completion_note }}</div>
              </div>
            </div>
            <div v-if="demoItem.completion_image_url" class="dc-node">
              <div class="dc-node-dot dc-node-sub"></div>
              <div class="dc-node-body">
                <div class="dc-node-label">完成图片</div>
                <div class="d-thumb dc-thumb" style="background:linear-gradient(135deg,#d1fae5,#a7f3d0)">
                  <span class="d-thumb-icon">✅</span>
                </div>
              </div>
            </div>
            <div v-if="demoItem.completed_at" class="dc-node" style="padding-bottom:0">
              <div class="dc-node-dot dc-node-sub"></div>
              <div class="dc-node-body">
                <div class="dc-node-label">完成时间</div>
                <div class="dc-node-val">{{ demoItem.completed_at }}</div>
              </div>
            </div>
          </template>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogC.visible = false">关闭</el-button>
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
   样式 A：清爽两栏式
   ============================================================ */
.da-body { padding: 4px 0; }

.da-topbar {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid #f3f4f6;
}
.da-status { font-size:12px; font-weight:600; padding:3px 10px; border-radius:6px; }
.da-pending { background:#dbeafe; color:#2563eb; }
.da-done { background:#d1fae5; color:#059669; }
.da-color-tag { display:flex; align-items:center; gap:5px; font-size:12px; color:#6b7280; }
.da-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.da-author-label { margin-left:auto; font-size:12px; color:#9ca3af; }

.da-fields { }
.da-row { display:flex; align-items:flex-start; gap:14px; margin-bottom:14px; font-size:14px; color:#374151; }
.da-label { flex-shrink:0; width:70px; color:#6b7280; font-size:13px; padding-top:2px; }
.da-val { flex:1; word-break:break-word; line-height:1.6; }
.da-content { font-size:15px; color:#1f2937; font-weight:500; }
.da-note { background:#f9fafb; padding:8px 12px; border-radius:6px; font-size:13px; color:#4b5563; }
.da-row-img { align-items:center; }
.da-sep { height:1px; background:#e5e7eb; margin:16px 0; }
.da-subtitle { font-size:13px; font-weight:600; color:#374151; margin-bottom:14px; }

/* ============================================================
   样式 B：卡片分层式
   ============================================================ */
.db-body { display:flex; flex-direction:column; gap:14px; }

.db-head-card {
  border-radius: 10px; padding: 18px 20px;
  border-left: 4px solid #d1d5db;
}
.hc-white  { background:#fafafa; border-left-color:#d1d5db; }
.hc-red    { background:#fef2f2; border-left-color:#f87171; }
.hc-yellow { background:#fffbeb; border-left-color:#fbbf24; }
.hc-blue   { background:#eff6ff; border-left-color:#60a5fa; }
.hc-green  { background:#ecfdf5; border-left-color:#34d399; }

.db-head-top { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.db-status { font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; }
.db-pending { background:#dbeafe; color:#2563eb; }
.db-done { background:#d1fae5; color:#059669; }
.db-author { font-size:12px; color:#9ca3af; margin-left:auto; }
.db-head-content { font-size:15px; font-weight:600; color:#1f2937; line-height:1.5; margin-bottom:4px; }
.db-head-date { font-size:12px; color:#9ca3af; }

.db-section-card {
  background: #fafafa; border-radius: 10px; padding: 16px 18px;
  border: 1px solid #f3f4f6;
}
.db-sc-label { font-size:13px; font-weight:600; color:#6b7280; margin-bottom:8px; }
.db-sc-body { font-size:14px; color:#374151; line-height:1.6; word-break:break-word; white-space:pre-wrap; }
.db-sc-meta { margin-top:8px; font-size:12px; color:#9ca3af; }

.db-complete-card { background:#f0fdf4; border-color:#d1fae5; }
.db-complete-card .db-sc-label { color:#059669; }

.db-thumb { margin-top:4px; }

/* ============================================================
   样式 C：信息时间线式
   ============================================================ */
.dc-body { padding: 4px 0; }

.dc-top {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid #f3f4f6;
}
.dc-pill { font-size:12px; font-weight:600; padding:3px 12px; border-radius:20px; }
.dc-pill-pending { background:#dbeafe; color:#2563eb; }
.dc-pill-done { background:#d1fae5; color:#059669; }
.dc-color { display:flex; align-items:center; gap:5px; font-size:13px; color:#6b7280; }
.dc-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }

.dc-timeline { position:relative; }
/* 竖线 */
.dc-timeline::before {
  content:''; position:absolute; left:11px; top:8px; bottom:8px;
  width:2px; background:#e5e7eb; border-radius:1px;
}

.dc-node { display:flex; gap:16px; padding-bottom:18px; position:relative; }
.dc-node-dot {
  width: 24px; height: 24px; border-radius: 50%;
  flex-shrink: 0; position: relative; z-index: 1;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid white;
}
.dc-node-main {
  background: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}
.dc-node-main::after {
  content: ''; width: 8px; height: 8px; border-radius: 50%; background: white;
}
.dc-node-sub {
  width: 10px; height: 10px; margin: 7px 7px;
  background: #d1d5db; border: none;
}
.dc-node-body { flex:1; min-width:0; padding-top:2px; }
.dc-node-label { font-size:12px; color:#9ca3af; margin-bottom:4px; }
.dc-node-val { font-size:14px; color:#374151; line-height:1.5; }
.dc-content { font-size:15px; color:#1f2937; font-weight:500; }
.dc-note-text { background:#f9fafb; padding:8px 12px; border-radius:6px; font-size:13px; color:#4b5563; }
.dc-author-pill { font-size:12px; color:#6b7280; background:#f3f4f6; padding:2px 12px; border-radius:12px; }
.dc-thumb { margin-top:4px; }
.dc-done-label { color:#059669; font-weight:600; }
</style>
