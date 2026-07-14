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
           添加任务方案投票
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge" style="background:#d97706">+</span>
          添加任务方案投票
          <span class="section-sub">—— 在已定稿页面上补充新建任务的方式</span>
        </h2>
        <p class="supplement-intro">搜索栏保持现有样式不变，以下三种方案仅影响「添加任务」区域的交互布局。</p>

        <div class="detail-preview-row">
          <button class="preview-card" @click="addDemoVisible='a'; showAddDemo=true">
            <span class="preview-badge" style="background:#6366f1">A</span>
            <span class="preview-label">顶栏精简添加</span>
            <span class="preview-desc">输入框+颜色点+添加按钮，一行搞定</span>
          </button>
          <button class="preview-card" @click="addDemoVisible='b'; showAddDemo=true">
            <span class="preview-badge" style="background:#0891b2">B</span>
            <span class="preview-label">展开式面板</span>
            <span class="preview-desc">点击"新建"展开表单，用完收起</span>
          </button>
          <button class="preview-card" @click="addDemoVisible='c'; showAddDemo=true">
            <span class="preview-badge" style="background:#7c3aed">C</span>
            <span class="preview-label">浮动 FAB + 弹窗</span>
            <span class="preview-desc">右下角悬浮按钮→弹窗完整录入</span>
          </button>
        </div>

        <!-- 方案 A 演示 -->
        <div v-if="showAddDemo && addDemoVisible==='a'" class="demo-card add-demo-card">
          <div class="add-demo-header">方案 A · 顶栏精简添加</div>
          <div class="add-bar-demo">
            <input v-model="addDemoInput" type="text" class="add-bar-input" placeholder="添加新的待办事项..." maxlength="500" @keypress.enter="addDemoInput=''; ElMessage.success('已添加（模拟）')" />
            <div class="add-bar-colors">
              <button v-for="c in colorOptions" :key="c.value" class="color-dot-btn" :class="['bg-'+c.value, { active: addDemoColor===c.value }]" :title="c.label" @click="addDemoColor=c.value" />
            </div>
            <button class="add-bar-btn" @click="addDemoInput=''; ElMessage.success('已添加（模拟）')">添加</button>
          </div>
          <div class="add-demo-note">快捷添加，默认今天/白色，颜色点速选</div>
        </div>

        <!-- 方案 B 演示 -->
        <div v-if="showAddDemo && addDemoVisible==='b'" class="demo-card add-demo-card">
          <div class="add-demo-header">方案 B · 展开式面板</div>
          <div class="add-expand-demo">
            <button class="add-expand-trigger" @click="addExpanded=!addExpanded">
              <span>＋ 新建任务</span>
              <svg :class="{ rotated: addExpanded }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
            </button>
            <div v-if="addExpanded" class="add-expand-body">
              <input v-model="addDemoInput2" type="text" class="add-bar-input" placeholder="输入任务内容..." maxlength="500" style="width:100%;margin-bottom:10px" />
              <div class="add-expand-row">
                <span class="add-expand-label">日期</span>
                <input type="date" class="add-expand-date" v-model="addDemoDate" />
              </div>
              <div class="add-expand-row">
                <span class="add-expand-label">颜色</span>
                <div class="add-bar-colors">
                  <button v-for="c in colorOptions" :key="c.value" class="color-dot-btn" :class="['bg-'+c.value,{active:addDemoColor2===c.value}]" :title="c.label" @click="addDemoColor2=c.value" />
                </div>
              </div>
              <button class="add-bar-btn" style="width:100%;justify-content:center;margin-top:8px" @click="addExpanded=false;ElMessage.success('已添加（模拟）')">确认添加</button>
            </div>
          </div>
          <div class="add-demo-note">点击"＋ 新建任务"展开表单，用完自动收起</div>
        </div>

        <!-- 方案 C 演示 -->
        <div v-if="showAddDemo && addDemoVisible==='c'" class="demo-card add-demo-card" style="position:relative;min-height:140px">
          <div class="add-demo-header">方案 C · 浮动 FAB + 弹窗</div>
          <p style="font-size:14px;color:#6b7280;padding:20px 0;text-align:center">工具栏无添加区域，右下角悬浮按钮</p>
          <button class="add-fab-demo" @click="addFabOpen=true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
          <div class="add-demo-note">FAB 悬浮在右下角，不占用工具栏空间</div>
        </div>
      </section>

      <!-- 添加任务弹窗（方案 C） -->
      <el-dialog v-model="addFabOpen" title="新建任务" width="480px" top="20vh">
        <div class="add-fab-form">
          <label class="add-fab-label">任务内容</label>
          <input v-model="addDemoInput3" type="text" class="add-bar-input" placeholder="输入任务内容..." maxlength="500" style="width:100%;margin-bottom:14px" />
          <label class="add-fab-label">所属日期</label>
          <input type="date" class="add-expand-date" v-model="addDemoDate2" style="width:100%;margin-bottom:14px" />
          <label class="add-fab-label">卡片颜色</label>
          <div class="add-bar-colors" style="margin-bottom:4px">
            <button v-for="c in colorOptions" :key="c.value" class="color-dot-btn" :class="['bg-'+c.value,{active:addDemoColor3===c.value}]" :title="c.label" @click="addDemoColor3=c.value" />
          </div>
        </div>
        <template #footer>
          <el-button @click="addFabOpen=false">取消</el-button>
          <el-button type="primary" @click="addFabOpen=false;ElMessage.success('已添加（模拟）')">确认添加</el-button>
        </template>
      </el-dialog>

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
           详情弹窗样式（已选用 A 左轨时间线）
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge selected-badge">★</span>
          详情弹窗样式 <span class="selected-label">已选用 A</span>
          <span class="section-sub">—— 左轨时间线，内容卡片浅灰背景+边框</span>
        </h2>

        <div class="detail-preview-row">
          <button class="preview-card preview-chosen" @click="openDialog('a')">
            <span class="preview-badge" style="background:#6366f1">A</span>
            <span class="preview-label">左轨时间线 <span class="chosen-tag">已选用</span></span>
            <span class="preview-desc">点击查看当前的完整效果</span>
          </button>
        </div>
      </section>

      <!-- ============================================================
           补充功能方案：管理员的留言 + 用户完成后的补充信息
           ============================================================ -->
      <section class="demo-section">
        <h2 class="section-title">
          <span class="section-badge">▼</span>
          补充功能 — 三块分隔样式投票
          <span class="section-sub">—— 已选用 A1 对话流式，三种区块分隔方案</span>
        </h2>
        <p class="supplement-intro">
          同一套「基础信息·留言·补充」三段内容，三种区块分隔方式呈现。<strong>模拟数据</strong>：
          <span class="demo-tag">💬 管理员留言 2 条</span>
          <span class="demo-tag">📎 用户补充信息 1 条</span>
        </p>

        <div class="detail-preview-row">
          <button class="preview-card" @click="openDialog('a1a')">
            <span class="preview-badge" style="background:#6366f1">V1</span>
            <span class="preview-label">间隔底色</span>
            <span class="preview-desc">三块不同底色过渡，自然分区</span>
          </button>
          <button class="preview-card" @click="openDialog('a1b')">
            <span class="preview-badge" style="background:#0891b2">V2</span>
            <span class="preview-label">边框块</span>
            <span class="preview-desc">三个独立边框块，层次分明</span>
          </button>
          <button class="preview-card" @click="openDialog('a1c')">
            <span class="preview-badge" style="background:#7c3aed">V3</span>
            <span class="preview-label">图标标题分隔</span>
            <span class="preview-desc">图标标题+装饰分隔线，干净轻盈</span>
          </button>
          <button class="preview-card" @click="openDialog('a1d')">
            <span class="preview-badge" style="background:#d97706">V4</span>
            <span class="preview-label">边框块+行内输入</span>
            <span class="preview-desc">V2 边框块 + 留言区行内输入框</span>
          </button>
        </div>
      </section>

      <!-- ============================================================
           功能说明卡（已确认 + 待定）
           ============================================================ -->
      <section class="feature-card">
        <div class="fc-row">
          <span class="fc-row-badge">✅ 已确认</span>
          <div class="feature-grid">
            <span class="feat-item">🏷️ 药丸式 Tab</span>
            <span class="feat-item">🔵 彩色圆点条目</span>
            <span class="feat-item">🖼️ 缩略图占位</span>
            <span class="feat-item">🎨 三点菜单→选色</span>
            <span class="feat-item">✏️ 三点菜单→改内容</span>
            <span class="feat-item">🗑️ 三点菜单→删除</span>
            <span class="feat-item">👁️ 点击条目→查看详情</span>
            <span class="feat-item">📋 左轨时间线详情布局</span>
          </div>
        </div>
        <div class="fc-row fc-row-new">
          <span class="fc-row-badge fc-badge-new">🆕 待定</span>
          <div class="feature-grid">
            <span class="feat-item feat-new">💬 管理员留言</span>
            <span class="feat-item feat-new">📎 用户完成后的补充信息</span>
          </div>
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
         V1 · 间隔底色 — 三块不同底色过渡
         ============================================================ -->
    <el-dialog v-model="dialogA1a.visible" title="任务详情" width="520px" top="8vh">
      <div class="da-outer">
        <div class="da-rail">
          <div class="da-rail-line"></div>
          <div class="da-rail-dot"></div>
        </div>
        <div class="da-card a1a-card">
          <!-- ===== 块 1：基础信息（白底） ===== -->
          <div class="a1a-section">
            <div class="da-top">
              <span class="da-status" :class="demoItem.status==='completed'?'da-done':'da-pending'">
                {{ demoItem.status==='completed'?'✓ 已完成':'● 待完成' }}
              </span>
              <span class="da-date">{{ demoItem.date }}</span>
              <span class="da-author">{{ demoItem.author }}</span>
            </div>
            <div class="da-subject">{{ demoItem.content }}</div>
            <div v-if="demoItem.note" class="da-note-text">{{ demoItem.note }}</div>
            <div v-if="demoItem.image_url" class="da-img-wrap">
              <div class="d-thumb da-thumb" :style="{ background: thumbBg(demoItem) }">
                <span class="d-thumb-icon">🖼️</span>
              </div>
            </div>
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

          <!-- ===== 块 2：留言（浅蓝底） ===== -->
          <div class="a1a-section a1a-section-msg">
            <div class="a1a-section-title">💬 管理员留言</div>
            <div class="a1a-messages">
              <div v-for="msg in demoAdminMessages" :key="msg.id" class="a1-bubble" :class="msg.author==='你'?'a1-self':'a1-other'">
                <div class="a1-bubble-author">{{ msg.author }}</div>
                <div class="a1-bubble-text">{{ msg.content }}</div>
                <div class="a1-bubble-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>

          <!-- ===== 块 3：补充（浅黄底） ===== -->
          <div class="a1a-section a1a-section-supp">
            <div class="a1a-section-title">📎 用户补充信息</div>
            <div class="a1b-supp-text">{{ demoUserSupplement.content }}</div>
            <div v-if="demoUserSupplement.image_url" class="a1b-supp-img">
              <div class="d-thumb da-thumb" style="background:linear-gradient(135deg,#fde68a,#fbbf24)">
                <span class="d-thumb-icon">📎</span>
              </div>
            </div>
            <div class="a1b-supp-time">{{ demoUserSupplement.addedAt }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogA1a.visible=false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         V2 · 边框块 — 三个独立边框块
         ============================================================ -->
    <el-dialog v-model="dialogA1b.visible" title="任务详情" width="520px" top="8vh">
      <div class="da-outer">
        <div class="da-rail">
          <div class="da-rail-line"></div>
          <div class="da-rail-dot"></div>
        </div>
        <div class="da-card a1b-card">
          <!-- ===== 块 1：基础信息边框块 ===== -->
          <div class="a1b-block">
            <div class="da-top">
              <span class="da-status" :class="demoItem.status==='completed'?'da-done':'da-pending'">
                {{ demoItem.status==='completed'?'✓ 已完成':'● 待完成' }}
              </span>
              <span class="da-date">{{ demoItem.date }}</span>
              <span class="da-author">{{ demoItem.author }}</span>
            </div>
            <div class="da-subject">{{ demoItem.content }}</div>
            <div v-if="demoItem.note" class="da-note-text">{{ demoItem.note }}</div>
            <div v-if="demoItem.image_url" class="da-img-wrap">
              <div class="d-thumb da-thumb" :style="{ background: thumbBg(demoItem) }">
                <span class="d-thumb-icon">🖼️</span>
              </div>
            </div>
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

          <!-- ===== 块 2：留言边框块（同款气泡） ===== -->
          <div class="a1b-block a1b-block-msg">
            <div class="a1b-block-title">💬 管理员留言</div>
            <div class="a1a-messages">
              <div v-for="msg in demoAdminMessages" :key="msg.id" class="a1-bubble" :class="msg.author==='你'?'a1-self':'a1-other'">
                <div class="a1-bubble-author">{{ msg.author }}</div>
                <div class="a1-bubble-text">{{ msg.content }}</div>
                <div class="a1-bubble-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>

          <!-- ===== 块 3：补充边框块 ===== -->
          <div class="a1b-block a1b-block-supp">
            <div class="a1b-block-title">📎 用户补充信息</div>
            <div class="a1b-supp-text">{{ demoUserSupplement.content }}</div>
            <div v-if="demoUserSupplement.image_url" class="a1b-supp-img">
              <div class="d-thumb da-thumb" style="background:linear-gradient(135deg,#fde68a,#fbbf24)">
                <span class="d-thumb-icon">📎</span>
              </div>
            </div>
            <div class="a1b-supp-time">{{ demoUserSupplement.addedAt }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogA1b.visible=false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         V3 · 图标标题分隔 — 图标标题 + 装饰分隔线
         ============================================================ -->
    <el-dialog v-model="dialogA1c.visible" title="任务详情" width="520px" top="8vh">
      <div class="da-outer">
        <div class="da-rail">
          <div class="da-rail-line"></div>
          <div class="da-rail-dot"></div>
        </div>
        <div class="da-card a1c-card">
          <!-- ===== 块 1：基础信息 ===== -->
          <div class="da-top">
            <span class="da-status" :class="demoItem.status==='completed'?'da-done':'da-pending'">
              {{ demoItem.status==='completed'?'✓ 已完成':'● 待完成' }}
            </span>
            <span class="da-date">{{ demoItem.date }}</span>
            <span class="da-author">{{ demoItem.author }}</span>
          </div>
          <div class="da-subject">{{ demoItem.content }}</div>
          <div v-if="demoItem.note" class="da-note-text">{{ demoItem.note }}</div>
          <div v-if="demoItem.image_url" class="da-img-wrap">
            <div class="d-thumb da-thumb" :style="{ background: thumbBg(demoItem) }">
              <span class="d-thumb-icon">🖼️</span>
            </div>
          </div>
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

          <!-- 装饰分隔线 -->
          <div class="a1c-divider"><span class="a1c-divider-icon">✦</span></div>

          <!-- ===== 块 2：留言 ===== -->
          <div class="a1c-section-label">💬 管理员留言</div>
          <div class="a1c-messages">
            <div v-for="msg in demoAdminMessages" :key="msg.id" class="a1-bubble" :class="msg.author==='你'?'a1-self':'a1-other'">
              <div class="a1-bubble-author">{{ msg.author }}</div>
              <div class="a1-bubble-text">{{ msg.content }}</div>
              <div class="a1-bubble-time">{{ msg.time }}</div>
            </div>
          </div>

          <!-- 装饰分隔线 -->
          <div class="a1c-divider"><span class="a1c-divider-icon">✦</span></div>

          <!-- ===== 块 3：补充 ===== -->
          <div class="a1c-section-label">📎 用户补充信息</div>
          <div class="a1c-supp">
            <div class="a1c-supp-text">{{ demoUserSupplement.content }}</div>
            <div v-if="demoUserSupplement.image_url" class="a1c-supp-img">
              <div class="d-thumb da-thumb" style="background:linear-gradient(135deg,#fde68a,#fbbf24)">
                <span class="d-thumb-icon">📎</span>
              </div>
            </div>
            <div class="a1c-supp-time">{{ demoUserSupplement.addedAt }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogA1c.visible=false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============================================================
         V4 · 边框块+行内输入 — V2 边框块 + 留言区行内输入框
         ============================================================ -->
    <el-dialog v-model="dialogA1d.visible" title="任务详情" width="520px" top="8vh">
      <div class="da-outer">
        <div class="da-rail">
          <div class="da-rail-line"></div>
          <div class="da-rail-dot"></div>
        </div>
        <div class="da-card a1b-card">
          <!-- ===== 块 1：基础信息边框块 ===== -->
          <div class="a1b-block">
            <div class="da-top">
              <span class="da-status" :class="demoItem.status==='completed'?'da-done':'da-pending'">
                {{ demoItem.status==='completed'?'✓ 已完成':'● 待完成' }}
              </span>
              <span class="da-date">{{ demoItem.date }}</span>
              <span class="da-author">{{ demoItem.author }}</span>
            </div>
            <div class="da-subject">{{ demoItem.content }}</div>
            <div v-if="demoItem.note" class="da-note-text">{{ demoItem.note }}</div>
            <div v-if="demoItem.image_url" class="da-img-wrap">
              <div class="d-thumb da-thumb" :style="{ background: thumbBg(demoItem) }">
                <span class="d-thumb-icon">🖼️</span>
              </div>
            </div>
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

          <!-- ===== 块 2：留言边框块 + 行内输入 ===== -->
          <div class="a1b-block a1b-block-msg">
            <div class="a1b-block-title">💬 管理员留言</div>
            <div class="a1a-messages">
              <div v-for="msg in demoAdminMessages" :key="msg.id" class="a1-bubble" :class="msg.author==='你'?'a1-self':'a1-other'">
                <div class="a1-bubble-author">{{ msg.author }}</div>
                <div class="a1-bubble-text">{{ msg.content }}</div>
                <div class="a1-bubble-time">{{ msg.time }}</div>
              </div>
            </div>

            <!-- 行内输入框（含 emoji + 图片 + 发送） -->
            <div class="a1d-inline-input">
              <input
                v-model="a1dInput"
                type="text"
                class="a1d-input"
                placeholder="输入留言内容..."
                maxlength="300"
                @keypress.enter="a1dSend"
              />
              <div class="a1d-actions">
                <!-- emoji 按钮 -->
                <button type="button" class="a1d-action-btn" title="插入 emoji" @click.stop="a1dToggleEmoji">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                </button>
                <!-- 图片上传按钮 -->
                <button type="button" class="a1d-action-btn" title="上传图片" @click="a1dTriggerUpload">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
                </button>
                <!-- 发送按钮 -->
                <button class="a1d-send-btn" :disabled="!a1dInput.trim() && !a1dPendingImage" @click="a1dSend">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
                </button>
              </div>
              <!-- emoji picker 弹层 -->
              <div v-show="a1dEmojiVisible" class="a1d-emoji-popup" @click.stop>
                <emoji-picker class="a1d-emoji-picker" @emoji-click="a1dInsertEmoji" />
              </div>
            </div>
            <!-- 图片预览 -->
            <div v-if="a1dPendingImage" class="a1d-image-preview">
              <div class="a1d-image-thumb" :style="{ background: a1dPendingImage }"></div>
              <span class="a1d-image-label">待发送</span>
              <button class="a1d-image-remove" @click="a1dPendingImage=''">✕</button>
            </div>
          </div>

          <!-- ===== 块 3：补充边框块 ===== -->
          <div class="a1b-block a1b-block-supp">
            <div class="a1b-block-title">📎 用户补充信息</div>
            <div class="a1b-supp-text">{{ demoUserSupplement.content }}</div>
            <div v-if="demoUserSupplement.image_url" class="a1b-supp-img">
              <div class="d-thumb da-thumb" style="background:linear-gradient(135deg,#fde68a,#fbbf24)">
                <span class="d-thumb-icon">📎</span>
              </div>
            </div>
            <div class="a1b-supp-time">{{ demoUserSupplement.addedAt }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogA1d.visible=false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import 'emoji-picker-element'
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

// ===== 管理员留言 & 用户补充的模拟数据 =====
const demoAdminMessages = [
  { id:1, content:'请确认样品规格是否与客户要求一致，特别是尺寸部分', author:'张总', time:'2026-07-14 09:30' },
  { id:2, content:'已和工厂确认，规格无误，可以安排打样',             author:'你',   time:'2026-07-14 10:15' },
]
const demoUserSupplement = {
  content: '已通知物流部门安排发货，预计 7/22 到达港口，附上装箱单照片',
  image_url: 'mock',
  addedAt: '2026-07-14 11:00',
}

// ===== 弹窗状态 =====
const dialogA   = reactive({ visible:false })
const dialogA1a = reactive({ visible:false })
const dialogA1b = reactive({ visible:false })
const dialogA1c = reactive({ visible:false })
const dialogA1d = reactive({ visible:false })

// 用于弹窗显示的任务（取第 1 条有附件的待完成任务）
const demoItem = computed<MockTodo>(() => {
  const rich = mockTodos.find(t=>t.image_url && t.status==='pending' && t.note)
  return rich || mockTodos[0]
})

function openDialog(which:string) {
  if(which==='a')    dialogA.visible=true
  else if(which==='a1a') dialogA1a.visible=true
  else if(which==='a1b') dialogA1b.visible=true
  else if(which==='a1c') dialogA1c.visible=true
  else if(which==='a1d') dialogA1d.visible=true
}

// ===== V4 行内输入模拟（含 emoji + 图片） =====
const a1dInput = ref('')
const a1dEmojiVisible = ref(false)
const a1dPendingImage = ref('')

function a1dToggleEmoji() {
  a1dEmojiVisible.value = !a1dEmojiVisible.value
}

function a1dInsertEmoji(event: any) {
  const emoji = event.detail.emoji.unicode
  a1dInput.value += emoji
}

function a1dTriggerUpload() {
  // 模拟上传：生成随机渐变图占位
  const colors = ['#fca5a5,#f87171', '#fde68a,#fbbf24', '#a7f3d0,#6ee7b7', '#93c5fd,#60a5fa', '#c4b5fd,#a78bfa']
  const pair = colors[Math.floor(Math.random() * colors.length)]
  a1dPendingImage.value = `linear-gradient(135deg, ${pair})`
  ElMessage.success('图片已添加（模拟）')
}

function a1dSend() {
  if (!a1dInput.value.trim() && !a1dPendingImage.value) return
  let content = a1dInput.value.trim()
  if (a1dPendingImage.value) {
    content = content ? `${content} [图片]` : '[图片]'
  }
  demoAdminMessages.push({
    id: Date.now(),
    content,
    author: '你',
    time: new Date().toLocaleString('zh-CN', { hour12: false }),
  })
  a1dInput.value = ''
  a1dPendingImage.value = ''
  a1dEmojiVisible.value = false
}

// 点击外部关闭 emoji picker
function onDocClickEmoji(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (!t.closest('.a1d-emoji-popup') && !t.closest('.a1d-action-btn')) {
    a1dEmojiVisible.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClickEmoji))
onBeforeUnmount(() => document.removeEventListener('click', onDocClickEmoji))

// ===== 添加任务 Demo 状态 =====
const showAddDemo = ref(false)
const addDemoVisible = ref<'a'|'b'|'c'>('a')
const addDemoInput = ref('')
const addDemoColor = ref('white')
const addDemoInput2 = ref('')
const addDemoColor2 = ref('white')
const addDemoDate = ref(new Date().toISOString().split('T')[0])
const addExpanded = ref(false)
const addDemoInput3 = ref('')
const addDemoColor3 = ref('white')
const addDemoDate2 = ref(new Date().toISOString().split('T')[0])
const addFabOpen = ref(false)
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
   功能说明卡新增样式
   ============================================================ */
.fc-row {
  margin-bottom: 14px;
}
.fc-row:last-child { margin-bottom: 0; }
.fc-row-new { padding-top: 14px; border-top: 1px dashed #e5e7eb; }

.fc-row-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 6px;
  background: #d1fae5;
  color: #059669;
  margin-bottom: 8px;
}
.fc-badge-new {
  background: #fef3c7;
  color: #d97706;
}

.feat-new {
  background: #fffbeb !important;
  border: 1px solid #fde68a;
}

/* ============================================================
   补充功能方案的介绍行
   ============================================================ */
.supplement-intro {
  font-size: 14px;
  color: #6b7280;
  margin: -4px 0 14px 0;
  line-height: 1.6;
}
.demo-tag {
  display: inline-block;
  font-size: 12px;
  background: #f3f4f6;
  padding: 0 8px;
  border-radius: 4px;
  margin: 0 2px;
}

/* ============================================================
   V1 · 间隔底色 — 三块不同底色过渡
   ============================================================ */
.a1a-card {
  padding: 0 !important;       /* 去掉卡片整体 padding，由各区自己控制 */
  overflow: hidden;
  border-radius: 10px;
}

.a1a-section {
  padding: 18px 18px 14px;
}
.a1a-section:last-child { padding-bottom: 18px; }

.a1a-section-msg {
  background: #f5f9ff;
  border-top: 1px solid #e8edf5;
  border-bottom: 1px solid #e8edf5;
}
.a1a-section-supp {
  background: #fffcf0;
}

.a1a-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 10px;
}

.a1a-messages {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 气泡样式（所有变体共用） */
.a1-bubble {
  padding: 10px 14px;
  border-radius: 10px;
  max-width: 88%;
  position: relative;
}
.a1-other {
  background: #ffffff;
  border: 1px solid #dbeafe;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}
.a1-self {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}
.a1-bubble-author {
  font-size: 11px;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 3px;
}
.a1-self .a1-bubble-author { color: #6b7280; }
.a1-bubble-text {
  font-size: 14px;
  color: #1f2937;
  line-height: 1.6;
  word-break: break-word;
}
.a1-bubble-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  text-align: right;
}

.a1b-supp-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  word-break: break-word;
}
.a1b-supp-img { margin-top: 8px; }
.a1b-supp-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 6px;
  text-align: right;
}

/* ============================================================
   V2 · 边框块 — 三个独立边框块
   ============================================================ */
.a1b-card {
  padding: 0 !important;
  overflow: hidden;
}

.a1b-block {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 18px;
  margin: 12px 14px;
  background: #ffffff;
}
.a1b-block:first-child { margin-top: 14px; }
.a1b-block:last-child { margin-bottom: 14px; }

.a1b-block-msg {
  border-color: #dbeafe;
  background: #f8faff;
}
.a1b-block-supp {
  border-color: #fde68a;
  background: #fffcf5;
}

.a1b-block-title {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 10px;
}


/* ============================================================
   V3 · 图标标题分隔 — 装饰分隔线
   ============================================================ */
.a1c-card {
  /* 使用卡片默认 padding */
}

.a1c-divider {
  text-align: center;
  margin: 16px 0;
  position: relative;
}
.a1c-divider::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: linear-gradient(to right, transparent, #e5e7eb, transparent);
}
.a1c-divider-icon {
  position: relative;
  z-index: 1;
  background: #f8f9fb;
  padding: 0 12px;
  font-size: 12px;
  color: #d1d5db;
}

.a1c-section-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 10px;
}

.a1c-messages {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.a1c-supp {
  background: #fafafa;
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid #f3f4f6;
}
.a1c-supp-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  word-break: break-word;
}
.a1c-supp-img { margin-top: 8px; }
.a1c-supp-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 6px;
  text-align: right;
}

/* ============================================================
   添加任务 Demo 样式
   ============================================================ */
.add-demo-card { margin-top: 14px; padding: 0; overflow: hidden; }
.add-demo-header {
  font-size: 13px; font-weight: 600; color: #6b7280;
  padding: 10px 16px; background: #fafafa;
  border-bottom: 1px solid #f3f4f6;
}
.add-demo-note {
  font-size: 12px; color: #9ca3af;
  padding: 8px 16px 12px; border-top: 1px solid #f3f4f6;
}

/* A 顶栏精简 */
.add-bar-demo {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 16px;
}
.add-bar-input {
  flex: 1; padding: 8px 14px; border: 1px solid #d1d5db;
  border-radius: 8px; outline: none; font-size: 14px; transition: all 0.2s;
}
.add-bar-input:focus {
  border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}
.add-bar-colors { display: flex; gap: 4px; flex-shrink: 0; }
.add-bar-colors .color-dot-btn {
  width: 20px; height: 20px; border-radius: 50%;
  cursor: pointer; transition: transform 0.15s;
  border: 2px solid transparent; padding: 0;
}
.add-bar-colors .color-dot-btn:hover { transform: scale(1.15); }
.add-bar-colors .color-dot-btn.active { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.25); }
.add-bar-colors .bg-white  { background: #ffffff; border-color: #d1d5db; }
.add-bar-colors .bg-red    { background: #fee2e2; }
.add-bar-colors .bg-yellow { background: #fef3c7; }
.add-bar-colors .bg-green  { background: #d1fae5; }
.add-bar-colors .bg-blue   { background: #dbeafe; }
.add-bar-colors .bg-dark   { background: #e5e7eb; }

.add-bar-btn {
  padding: 8px 18px; border: none; border-radius: 8px;
  background: #3b82f6; color: white; font-size: 14px;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.add-bar-btn:hover { background: #2563eb; }

/* B 展开式面板 */
.add-expand-demo { padding: 10px 16px; }
.add-expand-trigger {
  width: 100%; display: flex; align-items: center; justify-content: center;
  gap: 6px; padding: 10px; border: 2px dashed #d1d5db;
  border-radius: 8px; background: transparent; color: #6b7280;
  font-size: 14px; cursor: pointer; transition: all 0.2s;
}
.add-expand-trigger:hover {
  border-color: #3b82f6; color: #3b82f6; background: #f0f7ff;
}
.add-expand-trigger svg { transition: transform 0.25s; }
.add-expand-trigger svg.rotated { transform: rotate(180deg); }
.add-expand-body { margin-top: 12px; padding: 14px; background: #f9fafb; border-radius: 8px; }
.add-expand-row {
  display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
}
.add-expand-label { font-size: 13px; color: #6b7280; white-space: nowrap; min-width: 36px; }
.add-expand-date {
  padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px;
  font-size: 13px; outline: none;
}

/* C FAB */
.add-fab-demo {
  position: absolute; right: 20px; bottom: 50px;
  width: 48px; height: 48px; border-radius: 50%;
  background: #3b82f6; color: white; border: none;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 14px rgba(59,130,246,0.35);
  transition: all 0.2s;
}
.add-fab-demo:hover { transform: scale(1.08); background: #2563eb; }

.add-fab-form { padding: 8px 0; }
.add-fab-label { display: block; font-size: 13px; color: #6b7280; margin-bottom: 6px; }

/* ============================================================
   V4 · 边框块+行内输入
   ============================================================ */
.a1d-inline-input {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  position: relative;  /* emoji picker 定位锚点 */
}
.a1d-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  font-size: 13px;
  transition: border-color 0.2s;
  background: white;
}
.a1d-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.1);
}
.a1d-input::placeholder { color: #9ca3af; }
.a1d-send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
.a1d-send-btn:hover { background: #2563eb; }
.a1d-send-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

/* 操作按钮组（emoji + 图片） */
.a1d-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.a1d-action-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
}
.a1d-action-btn:hover {
  color: #3b82f6;
  background: rgba(59,130,246,0.08);
}

/* emoji picker 弹出 */
.a1d-emoji-popup {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  z-index: 200;
}
.a1d-emoji-picker {
  height: 220px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  --num-columns: 8;
  --border-radius: 10px;
}

/* 图片预览条 */
.a1d-image-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.a1d-image-thumb {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  flex-shrink: 0;
}
.a1d-image-label {
  font-size: 12px;
  color: #6b7280;
  flex: 1;
}
.a1d-image-remove {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s;
  flex-shrink: 0;
}
.a1d-image-remove:hover {
  background: #fecaca;
  color: #dc2626;
}
</style>
