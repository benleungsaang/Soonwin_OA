<template>
  <div class="final-page">
    <CommonHeader title="待办事项 · 最终方案" />

    <div class="final-container">
      <!-- ============ 搜索栏（C · 卡片内嵌式） ============ -->
      <div class="search-bar">
        <div class="search-inner">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="searchText" class="search-input" placeholder="按 Enter 搜索任务…" @keypress.enter="onSearch" />
          <button v-if="searchText" class="search-clear" @click="searchText=''">清除</button>
        </div>
      </div>

      <!-- ============ 药丸式 Tab ============ -->
      <div class="tabs-bar">
        <button v-for="t in tabDefs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
          {{ t.label }}
          <span class="tab-count">{{ t.count }}</span>
        </button>
      </div>

      <!-- ============ 任务列表 ============ -->
      <div class="list-card">
        <ListStyle02 :items="filteredItems" :no-dialogs="true" @view-detail="onViewDetail" @edit-item="onEditItem" />

        <!-- 空状态 -->
        <div v-if="filteredItems.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <p class="empty-text">没有符合条件的任务</p>
        </div>
      </div>
    </div>

    <!-- ============ FAB 按钮 ============ -->
    <button class="fab-btn" @click="openNewTask">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
    </button>

    <!-- ============ 底部设计说明 ============ -->
    <div class="notes-section">
      <h2 class="notes-title">📐 设计决策说明</h2>

      <div class="notes-grid">
        <div class="note-card">
          <div class="note-card-header">🔍 搜索栏</div>
          <ul class="note-list">
            <li><strong>样式</strong>：卡片内嵌式（C 方案）</li>
            <li><strong>触发</strong>：仅 Enter 键触发搜索，不实时过滤</li>
            <li><strong>清除</strong>：输入内容后右侧显示「清除」按钮</li>
            <li><strong>聚焦</strong>：灰色背景 → 白底 + 蓝色边框 + 光晕</li>
            <li><strong>空状态</strong>：placeholder 浅灰文字"按 Enter 搜索任务…"</li>
          </ul>
        </div>

        <div class="note-card">
          <div class="note-card-header">📌 顶部 Tab</div>
          <ul class="note-list">
            <li><strong>样式</strong>：药丸式（圆角胶囊）</li>
            <li><strong>选中态</strong>：蓝色实心 + 白色文字 + 阴影</li>
            <li><strong>未选中</strong>：透明背景 + 灰色文字</li>
            <li><strong>数量徽标</strong>：选中时白底蓝字，未选中时灰底</li>
            <li><strong>分类</strong>：全部 · 待完成 · 已完成 · 紧急</li>
          </ul>
        </div>

        <div class="note-card">
          <div class="note-card-header">📝 条目列表</div>
          <ul class="note-list">
            <li><strong>布局</strong>：彩色圆点 → 复选框 → 内容 → 缩略图 → 作者 → 三点菜单</li>
            <li><strong>圆点</strong>：固定 12px，白条用浅灰点保持对齐</li>
            <li><strong>复选框</strong>：圆形 div 模拟，完成态蓝色勾</li>
            <li><strong>缩略图</strong>：48×36px 渐变色块占位</li>
            <li><strong>作者</strong>：圆角灰色标签`#f3f4f6`</li>
            <li><strong>已完成</strong>：opacity 0.6 + 删除线</li>
            <li><strong>悬停</strong>：背景变 `#f5f7fa`</li>
          </ul>
        </div>

        <div class="note-card">
          <div class="note-card-header">⋮ 三点菜单</div>
          <ul class="note-list">
            <li><strong>颜色选择</strong>：6 色圆点面板（默认/紧急/重要/完成/进行中/长期）</li>
            <li><strong>修改内容</strong>：弹窗 textarea</li>
            <li><strong>删除</strong>：确认后移除</li>
            <li><strong>点击外部</strong>：自动关闭菜单</li>
          </ul>
        </div>

        <div class="note-card">
          <div class="note-card-header">🖼️ 详情弹窗</div>
          <ul class="note-list">
            <li><strong>框架</strong>：左轨时间线（方案 A）</li>
            <li><strong>内容卡片</strong>：浅灰背景 `#f8f9fb` + 边框 `#e8eaee`</li>
            <li><strong>三块分隔</strong>：边框块（V2）</li>
            <li><strong>留言区</strong>：对话气泡 + 行内输入框（V4）</li>
            <li><strong>输入框</strong>：文字 + 😊 emoji + 🖼️ 图片 + 发送</li>
            <li><strong>备注/附图</strong>：无标题，直接跟在主题下</li>
          </ul>
        </div>

        <div class="note-card">
          <div class="note-card-header">➕ 新建任务</div>
          <ul class="note-list">
            <li><strong>入口</strong>：右下角 FAB 蓝色浮动按钮</li>
            <li><strong>弹窗</strong>：聊天式（C 方案）</li>
            <li><strong>标题</strong>：大字号无边框，下划线分隔</li>
            <li><strong>内容</strong>：无边框 textarea，自由书写</li>
            <li><strong>工具栏</strong>：😊（光标插入）· 🖼️（模拟上传）· 日期 · 颜色</li>
            <li><strong>必填</strong>：标题不为空才能提交</li>
          </ul>
        </div>

        <div class="note-card">
          <div class="note-card-header">🎨 设计令牌</div>
          <ul class="note-list">
            <li><strong>主色</strong>：`#3b82f6`（按钮/选中态/链接）</li>
            <li><strong>背景</strong>：`#f9fafb`（页面）/ `#f8f9fb`（卡片浴）</li>
            <li><strong>文字</strong>：`#1f2937`（主要）/ `#6b7280`（次要）/ `#9ca3af`（辅助）</li>
            <li><strong>边框</strong>：`#e5e7eb` / `#e8eaee`</li>
            <li><strong>圆角</strong>：8px（常规）/ 10px（卡片）/ 20px（药丸 tab）</li>
            <li><strong>阴影</strong>：`0 1px 3px rgba(0,0,0,0.08)`（卡片）</li>
          </ul>
        </div>

        <div class="note-card">
          <div class="note-card-header">🔮 状态与异常</div>
          <ul class="note-list">
            <li><strong>加载态</strong>：骨架屏（Skeleton）3 行</li>
            <li><strong>空列表</strong>：el-empty 组件 + 说明文字</li>
            <li><strong>空搜索</strong>："没有符合条件的任务"</li>
            <li><strong>空留言</strong>："暂无留言"</li>
            <li><strong>操作反馈</strong>：ElMessage 轻提示（成功/警告/错误）</li>
            <li><strong>确认删除</strong>：ElMessageBox.confirm</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ============================================================
         详情弹窗（左轨时间线 + V2 边框块 + V4 行内输入）
         ============================================================ -->
    <el-dialog v-model="detailVisible" title="任务详情" width="520px" top="8vh">
      <div class="da-outer">
        <div class="da-rail">
          <div class="da-rail-line"></div>
          <div class="da-rail-dot"></div>
        </div>
        <div class="da-card a1b-card">
          <!-- 块 1：基础信息 -->
          <div class="a1b-block">
            <div class="da-top">
              <span class="da-status" :class="detailItem?.status==='completed'?'da-done':'da-pending'">
                {{ detailItem?.status==='completed'?'✓ 已完成':'● 待完成' }}
              </span>
              <span class="da-date">{{ detailItem?.date }}</span>
              <span class="da-author">{{ detailItem?.author }}</span>
            </div>
            <div class="da-subject">{{ detailItem?.content }}</div>
            <div v-if="detailItem?.note" class="da-note-text">{{ detailItem?.note }}</div>
            <div v-if="detailItem?.image_url" class="da-img-wrap">
              <div class="d-thumb da-thumb" :style="{ background: thumbBg(detailItem!) }">
                <span class="d-thumb-icon">🖼️</span>
              </div>
            </div>
            <template v-if="detailItem?.status === 'completed'">
              <div class="da-sep"></div>
              <div class="da-complete-header">✅ 完成情况</div>
              <div v-if="detailItem?.completion_note" class="da-comp-note">{{ detailItem?.completion_note }}</div>
              <div v-if="detailItem?.completion_image_url" class="da-img-wrap">
                <div class="d-thumb da-thumb" style="background:linear-gradient(135deg,#d1fae5,#a7f3d0)"><span class="d-thumb-icon">✅</span></div>
              </div>
              <div v-if="detailItem?.completed_at" class="da-comp-time">{{ detailItem?.completed_at }}</div>
            </template>
          </div>

          <!-- 块 2：留言 + 行内输入 -->
          <div class="a1b-block a1b-block-msg">
            <div class="a1b-block-title">💬 管理员留言</div>
            <div class="a1a-messages">
              <div v-for="msg in detailMessages" :key="msg.id" class="a1-bubble" :class="msg.author==='你'?'a1-self':'a1-other'">
                <div class="a1-bubble-author">{{ msg.author }}</div>
                <div class="a1-bubble-text">{{ msg.content }}</div>
                <div class="a1-bubble-time">{{ msg.time }}</div>
              </div>
            </div>
            <div class="a1d-inline-input">
              <input v-model="msgInput" type="text" class="a1d-input" placeholder="输入留言内容…" maxlength="300" @keypress.enter="sendMessage" />
              <div class="a1d-actions">
                <button type="button" class="a1d-action-btn" title="插入 emoji" @click.stop="toggleMsgEmoji"><span style="font-size:18px">😊</span></button>
                <button type="button" class="a1d-action-btn" title="上传图片" @click="mockMsgImage"><span style="font-size:18px">🖼️</span></button>
                <button class="a1d-send-btn" :disabled="!msgInput.trim()" @click="sendMessage">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
                </button>
              </div>
              <div v-show="msgEmojiVisible" class="a1d-emoji-popup" @click.stop>
                <emoji-picker class="a1d-emoji-picker" @emoji-click="e=>msgInput+=e.detail.emoji.unicode" />
              </div>
            </div>
          </div>

          <!-- 块 3：补充信息 -->
          <div class="a1b-block a1b-block-supp">
            <div class="a1b-block-title">📎 用户补充信息</div>
            <div class="a1b-supp-text">{{ detailSupplement?.content }}</div>
            <div v-if="detailSupplement?.image_url" class="a1b-supp-img">
              <div class="d-thumb da-thumb" style="background:linear-gradient(135deg,#fde68a,#fbbf24)"><span class="d-thumb-icon">📎</span></div>
            </div>
            <div class="a1b-supp-time">{{ detailSupplement?.addedAt }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible=false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         修改内容弹窗（聊天式 C 风格）
         ============================================================ -->
    <el-dialog v-model="editVisible" title="修改内容" width="500px" top="10vh">
      <div class="ntc-body">
        <div class="ntc-content-area">
          <textarea v-model="editContent" ref="editContentRef" class="ntc-textarea" placeholder="修改任务内容…" rows="5" maxlength="500" @focus="editLastFocus='content'"></textarea>
        </div>
        <div class="ntc-toolbar">
          <button type="button" class="ntc-tool-btn" @click="onEditEmojiClick" title="插入 emoji"><span style="font-size:18px">😊</span></button>
        </div>
        <div v-show="editEmojiVisible" class="ntc-emoji-pop" @click.stop>
          <emoji-picker class="ntc-ep" @emoji-click="insertEditEmoji" />
        </div>
      </div>
      <template #footer>
        <el-button @click="editVisible=false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         新建任务弹窗（聊天式 C）
         ============================================================ -->
    <el-dialog v-model="newTaskVisible" title="新建任务" width="500px" top="10vh">
      <div class="ntc-body">
        <div class="ntc-title-row">
          <input v-model="newTitle" ref="newTitleRef" class="ntc-title-input" placeholder="任务标题" maxlength="100" @focus="newLastFocus='title'" />
        </div>
        <div class="ntc-sep"></div>
        <div class="ntc-content-area">
          <textarea v-model="newContent" ref="newContentRef" class="ntc-textarea" placeholder="写点什么…支持 emoji 📝" rows="4" maxlength="500" @focus="newLastFocus='content'"></textarea>
        </div>
        <div class="ntc-toolbar">
          <button type="button" class="ntc-tool-btn" @click="onNewEmojiClick" title="插入 emoji"><span style="font-size:18px">😊</span></button>
          <button type="button" class="ntc-tool-btn" @click="mockNewImage" title="添加图片"><span style="font-size:18px">🖼️</span></button>
          <input v-model="newDate" type="date" class="ntc-date-input" />
          <div class="ntc-color-chip" :class="'bg-'+newColor"></div>
        </div>
        <div v-show="newEmojiVisible" class="ntc-emoji-pop" @click.stop>
          <emoji-picker class="ntc-ep" @emoji-click="insertNewEmoji" />
        </div>
        <div class="ntc-color-bar">
          <span class="ntc-color-label">颜色</span>
          <button v-for="c in colorOpts" :key="c.value" class="color-dot-btn" :class="['bg-'+c.value,{active:newColor===c.value}]" :title="c.label" @click="newColor=c.value" />
        </div>
      </div>
      <template #footer>
        <el-button @click="newTaskVisible=false">取消</el-button>
        <el-button type="primary" @click="submitNewTask">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import 'emoji-picker-element'
import CommonHeader from '@/components/CommonHeader.vue'
import ListStyle02 from './ListStyle02.vue'

// ============================================================
// 模拟数据
// ============================================================
interface TodoItem {
  id: number; content: string; status: 'pending' | 'completed'
  date: string; color: string; author: string; note: string; image_url: string
  completion_note?: string; completion_image_url?: string; completed_at?: string
}
const mockTodos: TodoItem[] = [
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

// 管理员留言 & 补充数据
const demoAdminMessages = ref([
  { id:1, content:'请确认样品规格是否与客户要求一致，特别是尺寸部分', author:'张总', time:'2026-07-14 09:30' },
  { id:2, content:'已和工厂确认，规格无误，可以安排打样',             author:'你',   time:'2026-07-14 10:15' },
])
const demoUserSupplement = {
  content: '已通知物流部门安排发货，预计 7/22 到达港口，附上装箱单照片',
  image_url: 'mock',
  addedAt: '2026-07-14 11:00',
}

// ============================================================
// Tab 定义
// ============================================================
const tabDefs = [
  { key:'all', label:'全部', count:mockTodos.length },
  { key:'pending', label:'待完成', count:mockTodos.filter(t=>t.status==='pending').length },
  { key:'completed', label:'已完成', count:mockTodos.filter(t=>t.status==='completed').length },
  { key:'urgent', label:'紧急', count:mockTodos.filter(t=>t.color==='red').length },
]
const activeTab = ref('all')

const filteredItems = computed(() => {
  const items = mockTodos
  const tab = activeTab.value
  if (tab==='pending') return items.filter(t=>t.status==='pending')
  if (tab==='completed') return items.filter(t=>t.status==='completed')
  if (tab==='urgent') return items.filter(t=>t.color==='red')
  return items
})

// ============================================================
// 搜索
// ============================================================
const searchText = ref('')
function onSearch() {
  if (searchText.value.trim()) ElMessage.success(`搜索「${searchText.value.trim()}」（模拟）`)
}

// ============================================================
// 颜色
// ============================================================
const colorOpts = [
  { value:'white',label:'默认' }, { value:'red',label:'紧急' },
  { value:'yellow',label:'重要' }, { value:'green',label:'完成' },
  { value:'blue',label:'进行中' }, { value:'dark',label:'长期' },
]
function thumbBg(item: TodoItem): string {
  const m:Record<string,string>={
    white:'linear-gradient(135deg,#e5e7eb,#d1d5db)', red:'linear-gradient(135deg,#fca5a5,#f87171)',
    yellow:'linear-gradient(135deg,#fde68a,#fbbf24)', green:'linear-gradient(135deg,#a7f3d0,#6ee7b7)',
    blue:'linear-gradient(135deg,#93c5fd,#60a5fa)', dark:'linear-gradient(135deg,#d1d5db,#9ca3af)',
  }
  return m[item.color]||m.white
}

// ============================================================
// 详情弹窗
// ============================================================
const detailVisible = ref(false)
const detailItem = ref<TodoItem | null>(null)
const detailMessages = ref<any[]>([])
const detailSupplement = ref(demoUserSupplement)

function onViewDetail(item: TodoItem) {
  detailItem.value = item
  detailMessages.value = demoAdminMessages.value
  detailSupplement.value = demoUserSupplement
  detailVisible.value = true
}

// ===== 编辑弹窗（C · 聊天式风格） =====
const editVisible = ref(false)
const editItem = ref<TodoItem | null>(null)
const editContent = ref('')
const editEmojiVisible = ref(false)
const editLastFocus = ref<'title'|'content'>('content')
const editTitleRef = ref<HTMLInputElement|null>(null)
const editContentRef = ref<HTMLTextAreaElement|null>(null)

function onEditItem(item: TodoItem) {
  editItem.value = item
  editContent.value = item.content
  editEmojiVisible.value = false
  editVisible.value = true
}
function onEditEmojiClick() { editEmojiVisible.value = !editEmojiVisible.value }
function insertEditEmoji(event: any) {
  const emoji = event.detail.emoji.unicode
  const el = editContentRef.value
  if (el) {
    const start = el.selectionStart ?? 0
    const end = el.selectionEnd ?? start
    editContent.value = editContent.value.substring(0, start) + emoji + editContent.value.substring(end)
    nextTick(() => { el.selectionStart = el.selectionEnd = start + emoji.length; el.focus() })
  } else {
    editContent.value += emoji
  }
}
function submitEdit() {
  if (!editContent.value.trim()) { ElMessage.warning('内容不能为空'); return }
  if (editItem.value) editItem.value.content = editContent.value.trim()
  editVisible.value = false
  ElMessage.success('内容已更新（模拟）')
}

// 留言输入
const msgInput = ref('')
const msgEmojiVisible = ref(false)
function toggleMsgEmoji() { msgEmojiVisible.value = !msgEmojiVisible.value }
function sendMessage() {
  if (!msgInput.value.trim()) return
  demoAdminMessages.value.push({
    id: Date.now(), content: msgInput.value.trim(), author: '你',
    time: new Date().toLocaleString('zh-CN', { hour12: false }),
  })
  msgInput.value = ''
}
function mockMsgImage() { ElMessage.success('图片已添加（模拟）') }

// ============================================================
// 新建任务弹窗（C · 聊天式）
// ============================================================
const newTaskVisible = ref(false)
const newTitle = ref('')
const newContent = ref('')
const newDate = ref(new Date().toISOString().split('T')[0])
const newColor = ref('white')
const newEmojiVisible = ref(false)
const newLastFocus = ref<'title'|'content'>('content')
const newTitleRef = ref<HTMLInputElement|null>(null)
const newContentRef = ref<HTMLTextAreaElement|null>(null)

function openNewTask() {
  newTitle.value = ''; newContent.value = ''; newColor.value = 'white'
  newDate.value = new Date().toISOString().split('T')[0]
  newEmojiVisible.value = false
  newTaskVisible.value = true
}
function onNewEmojiClick() { newEmojiVisible.value = !newEmojiVisible.value }
function insertNewEmoji(event: any) {
  const emoji = event.detail.emoji.unicode
  const target = newLastFocus.value
  const el = target === 'title' ? newTitleRef.value : newContentRef.value
  if (el) {
    const start = el.selectionStart ?? 0
    const end = el.selectionEnd ?? start
    const text = target === 'title' ? newTitle.value : newContent.value
    const newText = text.substring(0, start) + emoji + text.substring(end)
    if (target === 'title') newTitle.value = newText
    else newContent.value = newText
    nextTick(() => { el.selectionStart = el.selectionEnd = start + emoji.length; el.focus() })
  }
}
function mockNewImage() { ElMessage.success('图片已添加（模拟）') }
function submitNewTask() {
  if (!newTitle.value.trim()) { ElMessage.warning('请输入任务标题'); return }
  newTaskVisible.value = false
  ElMessage.success('任务已创建（模拟）')
}

// ============================================================
// emoji 外部关闭
// ============================================================
function onDocClick(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (!t.closest('.a1d-emoji-popup') && !t.closest('.a1d-action-btn')) msgEmojiVisible.value = false
  if (!t.closest('.ntc-emoji-pop') && !t.closest('.ntc-tool-btn')) { newEmojiVisible.value = false; editEmojiVisible.value = false }
}
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<style scoped>
/* ============================================================
   页面
   ============================================================ */
.final-page {
  background: #f9fafb;
  min-height: calc(100vh - 60px);
  padding: 32px 16px 96px;
  position: relative;
}
.final-container {
  max-width: 768px;
  margin: 0 auto;
}

/* ============================================================
   搜索栏（C · 卡片内嵌式）
   ============================================================ */
.search-bar {
  margin-bottom: 14px;
}
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
  transition: all 0.15s;
}
.search-clear:hover { background: #d1d5db; }

/* ============================================================
   药丸式 Tab
   ============================================================ */
.tabs-bar {
  display: flex; gap: 4px; padding: 10px 14px;
  background: white; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  margin-bottom: 16px;
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

/* ============================================================
   任务列表
   ============================================================ */
.list-card {
  background: white; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.empty-state { text-align: center; padding: 48px 16px; }
.empty-icon { font-size: 40px; margin-bottom: 8px; }
.empty-text { color: #9ca3af; font-size: 14px; }

/* ============================================================
   FAB
   ============================================================ */
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
   底部设计说明
   ============================================================ */
.notes-section {
  max-width: 768px; margin: 48px auto 0;
  padding-top: 32px; border-top: 2px dashed #d1d5db;
}
.notes-title {
  font-size: 20px; font-weight: 700; color: #1f2937;
  margin-bottom: 20px;
}
.notes-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
}
.note-card {
  background: white; border-radius: 10px; padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid #e5e7eb;
}
.note-card-header {
  font-size: 14px; font-weight: 600; color: #374151;
  margin-bottom: 8px; padding-bottom: 6px;
  border-bottom: 1px solid #f3f4f6;
}
.note-list { margin: 0; padding: 0; list-style: none; }
.note-list li {
  font-size: 12px; color: #6b7280; line-height: 1.7;
  padding: 2px 0; position: relative; padding-left: 12px;
}
.note-list li::before { content: '·'; position: absolute; left: 0; color: #d1d5db; }

/* ============================================================
   以下为从 TabStylesDemo 复用的样式
   ============================================================ */

/* 左轨时间线 */
.da-outer { display: flex; gap: 16px; padding: 4px 0; min-height: 120px; }
.da-rail { display: flex; flex-direction: column; align-items: center; width: 20px; flex-shrink: 0; padding-top: 6px; }
.da-rail-dot { width: 12px; height: 12px; border-radius: 50%; background: #3b82f6; border: 2px solid white; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); flex-shrink: 0; z-index: 1; }
.da-rail-line { width: 2px; flex: 1; background: linear-gradient(to bottom, #e5e7eb, #f3f4f6); margin-top: -2px; margin-bottom: -2px; }

/* 卡片（覆盖 a1b-card 的 padding） */
.a1b-card { padding: 0 !important; overflow: hidden; }
.a1b-block { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px 18px; margin: 12px 14px; background: #ffffff; }
.a1b-block:first-child { margin-top: 14px; }
.a1b-block:last-child { margin-bottom: 14px; }
.a1b-block-msg { border-color: #dbeafe; background: #f8faff; }
.a1b-block-supp { border-color: #fde68a; background: #fffcf5; }
.a1b-block-title { font-size: 13px; font-weight: 600; color: #6b7280; margin-bottom: 10px; }

/* 顶栏 */
.da-top { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.da-status { font-size:11px; font-weight:600; padding:2px 10px; border-radius:6px; }
.da-pending { background:#dbeafe; color:#2563eb; }
.da-done { background:#d1fae5; color:#059669; }
.da-date { font-size:12px; color:#9ca3af; margin-left:auto; }
.da-author { font-size:12px; color:#6b7280; background:#f3f4f6; padding:1px 10px; border-radius:10px; }
.da-subject { font-size: 16px; font-weight: 600; color: #1f2937; line-height: 1.6; margin-bottom: 10px; word-break: break-word; }
.da-note-text { font-size: 14px; color: #4b5563; background: #ffffff; border: 1px solid #e8eaee; padding: 10px 14px; border-radius: 8px; line-height: 1.7; margin-bottom: 10px; word-break: break-word; white-space: pre-wrap; }
.da-img-wrap { margin-bottom: 10px; }
.da-thumb { width: 120px; height: 72px; }
.da-sep { height:1px; background:#e5e7eb; margin:14px 0; }
.da-complete-header { font-size: 13px; font-weight: 600; color: #059669; margin-bottom: 8px; }
.da-comp-note { font-size: 14px; color: #374151; background: #ffffff; border: 1px solid #d1fae5; padding: 8px 12px; border-radius: 8px; line-height: 1.6; margin-bottom: 8px; word-break: break-word; }
.da-comp-time { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.d-thumb { width: 100px; height: 64px; border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(0,0,0,0.06); flex-shrink: 0; }
.d-thumb-icon { font-size: 22px; opacity: 0.7; }

/* 消息气泡 */
.a1a-messages { display: flex; flex-direction: column; gap: 10px; }
.a1-bubble { padding: 10px 14px; border-radius: 10px; max-width: 88%; position: relative; }
.a1-other { background: #ffffff; border: 1px solid #dbeafe; align-self: flex-start; border-bottom-left-radius: 4px; }
.a1-self { background: #f3f4f6; border: 1px solid #e5e7eb; align-self: flex-end; border-bottom-right-radius: 4px; }
.a1-bubble-author { font-size: 11px; font-weight: 600; color: #3b82f6; margin-bottom: 3px; }
.a1-self .a1-bubble-author { color: #6b7280; }
.a1-bubble-text { font-size: 14px; color: #1f2937; line-height: 1.6; word-break: break-word; }
.a1-bubble-time { font-size: 11px; color: #9ca3af; margin-top: 4px; text-align: right; }

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

/* 补充块 */
.a1b-supp-text { font-size: 14px; color: #374151; line-height: 1.6; word-break: break-word; }
.a1b-supp-img { margin-top: 8px; }
.a1b-supp-time { font-size: 12px; color: #9ca3af; margin-top: 6px; text-align: right; }

/* C 弹窗通用 */
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
.ntc-color-chip { width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 0 1px #e5e7eb; }
.ntc-color-chip.bg-white { background:#e5e7eb; }
.ntc-color-chip.bg-red { background:#f87171; }
.ntc-color-chip.bg-yellow { background:#fbbf24; }
.ntc-color-chip.bg-green { background:#34d399; }
.ntc-color-chip.bg-blue { background:#60a5fa; }
.ntc-color-chip.bg-dark { background:#9ca3af; }
.ntc-emoji-pop { position: absolute; bottom: 100%; left: 0; z-index: 200; margin-bottom: 4px; }
.ntc-ep { height: 220px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); --num-columns:8; }
.ntc-color-bar { display: flex; align-items: center; gap: 6px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f3f4f6; }
.ntc-color-label { font-size: 12px; color: #9ca3af; margin-right: 4px; }

.color-dot-btn { width: 22px; height: 22px; border-radius: 50%; cursor: pointer; transition: transform 0.15s; border: 2px solid transparent; padding: 0; }
.color-dot-btn:hover { transform: scale(1.15); }
.color-dot-btn.active { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.25); }
.color-dot-btn.bg-white { background:#ffffff; border-color:#d1d5db; }
.color-dot-btn.bg-red { background:#fee2e2; }
.color-dot-btn.bg-yellow { background:#fef3c7; }
.color-dot-btn.bg-green { background:#d1fae5; }
.color-dot-btn.bg-blue { background:#dbeafe; }
.color-dot-btn.bg-dark { background:#e5e7eb; }
</style>
