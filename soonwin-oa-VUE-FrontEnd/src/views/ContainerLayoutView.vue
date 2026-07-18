<template>
  <div class="container-layout-page">
    <CommonHeader title="货柜排布" />

    <el-card shadow="hover" class="main-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <el-input
          v-model="search"
          placeholder="搜索方案名 / 作者"
          clearable
          style="width: 260px"
          @keyup.enter="fetchList"
          @clear="fetchList"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-radio-group v-model="scope" @change="fetchList">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="mine">我的</el-radio-button>
        </el-radio-group>

        <el-button type="primary" :icon="Plus" @click="openCreateDialog">
          新建方案
        </el-button>

        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>

      <!-- 列表 -->
      <el-table
        :data="list"
        v-loading="loading"
        border
        stripe
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', 'text-align': 'center' }"
        :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
        empty-text="暂无货柜排布方案，点击右上角“新建方案”开始"
      >
        <el-table-column prop="name" label="方案名" min-width="200" align="left">
          <template #default="{ row }">
            <span class="layout-name">{{ row.name }}</span>
            <el-tag v-if="row.is_owner" type="success" size="small" effect="plain" style="margin-left: 8px">我的</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="container_name" label="货柜类型" min-width="120" />
        <el-table-column prop="cargo_count" label="货物数" width="90" />
        <el-table-column prop="author_name" label="作者" min-width="100" />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column prop="updated_at" label="更新时间" min-width="160" />
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="(cmd) => handleTableCommand(cmd, row)">
              <el-button size="small" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit" :icon="Edit" style="color: #409eff">
                    编辑排布
                  </el-dropdown-item>
                  <el-dropdown-item command="rename" :icon="EditPen" style="color: #e6a23c">
                    修改方案名
                  </el-dropdown-item>
                  <el-dropdown-item command="copy" :icon="DocumentCopy">
                    复制一份
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="row.is_owner || isAdmin"
                    command="delete"
                    :icon="Delete"
                    divided
                    style="color: #f56c6c"
                  >
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="fetchList"
        @size-change="fetchList"
        class="pagination"
      />
    </el-card>

    <!-- 新建方案弹窗 -->
    <el-dialog v-model="createDialogVisible" title="新建货柜排布方案" width="440px" :close-on-click-modal="false">
      <el-form :model="createForm" label-width="80px" @submit.prevent>
        <el-form-item label="方案名" required>
          <el-input
            v-model="createForm.name"
            placeholder="例如：40HQ-客户A"
            maxlength="100"
            show-word-limit
            @keyup.enter="handleCreate"
          />
        </el-form-item>
        <el-form-item label="说明">
          <div class="form-tip">
            创建后将打开独立的 3D 编辑标签页；同一作者下方案名不可重复。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建并打开</el-button>
      </template>
    </el-dialog>

    <!-- 另存为弹窗 -->
    <el-dialog v-model="saveAsDialogVisible" title="另存为新方案" width="440px" :close-on-click-modal="false">
      <el-form :model="saveAsForm" label-width="80px" @submit.prevent>
        <el-form-item label="原方案">
          <span>{{ saveAsForm.sourceName }}（作者：{{ saveAsForm.sourceAuthor }}）</span>
        </el-form-item>
        <el-form-item label="新名字" required>
          <el-input
            v-model="saveAsForm.newName"
            maxlength="100"
            show-word-limit
            @keyup.enter="handleSaveAs"
          />
        </el-form-item>
        <el-form-item label="说明">
          <div class="form-tip">将原方案的当前布局数据复制为新方案，归属您本人。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveAsDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingAs" @click="handleSaveAs">创建并打开</el-button>
      </template>
    </el-dialog>

    <!-- 修改方案名弹窗 -->
    <el-dialog v-model="renameDialogVisible" title="修改方案名" width="440px" :close-on-click-modal="false">
      <el-form :model="renameForm" label-width="80px" @submit.prevent>
        <el-form-item label="原方案名">
          <span>{{ renameForm.oldName }}</span>
        </el-form-item>
        <el-form-item label="新方案名" required>
          <el-input
            v-model="renameForm.newName"
            maxlength="100"
            show-word-limit
            @keyup.enter="handleRename"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="renaming" @click="handleRename">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, Edit, Delete, DocumentCopy, Search, MoreFilled, EditPen
} from '@element-plus/icons-vue'
import CommonHeader from '@/components/CommonHeader.vue'
import {
  listContainerLayouts,
  getContainerLayout,
  createContainerLayout,
  updateContainerLayout,
  deleteContainerLayout,
  type ContainerLayout,
} from '@/api/container'
import { getCurrentUserInfo } from '@/utils/authUtils'

// ========== 列表状态 ==========
const list = ref<ContainerLayout[]>([])
const loading = ref(false)
const search = ref('')
const scope = ref<'all' | 'mine'>('all')
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

const userInfo = getCurrentUserInfo()
const isAdmin = computed(() => userInfo?.user_role === 'admin')

async function fetchList() {
  loading.value = true
  try {
    // request 拦截器已自动解包后端 data 字段
    // resp 直接是 {items, total, page, per_page, total_pages}
    const resp = await listContainerLayouts({
      page: page.value,
      per_page: perPage.value,
      search: search.value || undefined,
      scope: scope.value,
    })
    list.value = resp?.items || []
    total.value = resp?.total || 0
  } catch (e: any) {
    console.error('fetchContainerLayouts error:', e)
    // request 拦截器已通过 ElMessage 提示错误，这里不重复
  } finally {
    loading.value = false
  }
}

// ========== 新建 ==========
const createDialogVisible = ref(false)
const creating = ref(false)
const createForm = ref({ name: '' })

function openCreateDialog() {
  createForm.value = { name: '' }
  createDialogVisible.value = true
}

async function handleCreate() {
  const name = createForm.value.name.trim()
  if (!name) {
    ElMessage.warning('请输入方案名')
    return
  }
  creating.value = true
  try {
    // resp 是解包后的 ContainerLayoutDetail
    const resp = await createContainerLayout({ name })
    ElMessage.success('已创建，正在打开编辑器...')
    createDialogVisible.value = false
    const newId = resp.id
    setTimeout(() => openEditorById(newId), 100)
    fetchList()
  } catch (e: any) {
    console.error('createContainerLayout error:', e)
  } finally {
    creating.value = false
  }
}

// ========== 编辑（打开新标签页） ==========
// 注意：必须带 .html 后缀，否则 Vite SPA fallback 会把请求转到 index.html，
// 进而触发 vue-router 警告 + 页面空白（vue-router 无对应路由）。
function openEditorById(id: number) {
  const url = `/container-editor.html?id=${id}`
  window.open(url, '_blank', 'noopener')
}

function openEditor(row: ContainerLayout) {
  openEditorById(row.id)
}

// ========== 另存为 ==========
const saveAsDialogVisible = ref(false)
const savingAs = ref(false)
const saveAsForm = ref({
  sourceId: 0,
  sourceName: '',
  sourceAuthor: '',
  newName: '',
})

function openSaveAsDialog(row: ContainerLayout) {
  saveAsForm.value = {
    sourceId: row.id,
    sourceName: row.name,
    sourceAuthor: row.author_name,
    newName: `${row.name} (副本)`,
  }
  saveAsDialogVisible.value = true
}

async function handleSaveAs() {
  const newName = saveAsForm.value.newName.trim()
  if (!newName) {
    ElMessage.warning('请输入新方案名')
    return
  }
  savingAs.value = true
  try {
    // 1) 拉取原方案数据（resp 是 ContainerLayoutDetail）
    const srcResp = await getContainerLayout(saveAsForm.value.sourceId)
    // 2) 用新名 + 同一份 data 创建
    const createResp = await createContainerLayout({
      name: newName,
      data: srcResp.data,
    })
    ElMessage.success('已另存为新方案，正在打开编辑器...')
    saveAsDialogVisible.value = false
    const newId = createResp.id
    setTimeout(() => openEditorById(newId), 100)
    fetchList()
  } catch (e: any) {
    console.error('saveAs error:', e)
  } finally {
    savingAs.value = false
  }
}

// ========== 下拉菜单命令分发 ==========
function handleTableCommand(cmd: string, row: ContainerLayout) {
  switch (cmd) {
    case 'edit':
      openEditor(row)
      break
    case 'rename':
      openRenameDialog(row)
      break
    case 'copy':
      openSaveAsDialog(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

// ========== 修改方案名 ==========
const renameDialogVisible = ref(false)
const renaming = ref(false)
const renameForm = ref({
  id: 0,
  oldName: '',
  newName: '',
})

function openRenameDialog(row: ContainerLayout) {
  renameForm.value = {
    id: row.id,
    oldName: row.name,
    newName: row.name,
  }
  renameDialogVisible.value = true
}

async function handleRename() {
  const newName = renameForm.value.newName.trim()
  if (!newName) {
    ElMessage.warning('请输入新方案名')
    return
  }
  if (newName === renameForm.value.oldName) {
    ElMessage.info('方案名未变更')
    renameDialogVisible.value = false
    return
  }
  renaming.value = true
  try {
    await updateContainerLayout(renameForm.value.id, { name: newName })
    ElMessage.success('方案名已修改')
    renameDialogVisible.value = false
    fetchList()
  } catch (e: any) {
    console.error('rename error:', e)
  } finally {
    renaming.value = false
  }
}

// ========== 删除 ==========
async function handleDelete(row: ContainerLayout) {
  try {
    await ElMessageBox.confirm(
      `确定删除方案「${row.name}」？此操作不可撤销。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return // 取消
  }
  try {
    await deleteContainerLayout(row.id)
    ElMessage.success('已删除')
    // 列表分页位置调整：删完最后一页最后一条时回退一页
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    fetchList()
  } catch (e: any) {
    console.error('deleteContainerLayout error:', e)
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.container-layout-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.main-card {
  margin-top: 16px;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.layout-name {
  font-weight: 500;
  color: #303133;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style>