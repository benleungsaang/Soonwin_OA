<template>
  <div class="rich-documents-page">
    <CommonHeader title="图文文档" />

    <el-card shadow="hover" class="main-card">
      <div class="toolbar">
        <el-input v-model="search" placeholder="搜索文档标题" clearable style="width: 260px" @keyup.enter="load" @clear="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-radio-group v-if="isAdmin && !trash" v-model="scope" @change="page = 1">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="mine">我的</el-radio-button>
        </el-radio-group>
        <el-button v-if="!trash" type="primary" :icon="Plus" @click="create">新建文档</el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button v-if="isAdmin" :icon="trash ? Back : Delete" @click="toggleTrash">{{ trash ? '返回文档' : '回收站' }}</el-button>
      </div>

      <el-table :data="pageRows" v-loading="loading" border stripe
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', 'text-align': 'center' }"
        :cell-style="{ 'text-align': 'center', 'vertical-align': 'middle' }"
        :empty-text="trash ? '回收站为空' : '暂无图文文档，点击“新建文档”开始'">
        <el-table-column prop="title" label="文档名" min-width="200" align="left">
          <template #default="{ row }">
            <span class="document-name">{{ row.title }}</span>
            <el-tooltip v-if="row.is_shared" content="共享可见"><el-icon style="margin-left: 8px; vertical-align: middle"><View /></el-icon></el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="所有者" min-width="110" />
        <el-table-column label="创建时间" min-width="160"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
        <el-table-column :label="trash ? '删除时间' : '更新时间'" min-width="160"><template #default="{ row }">{{ formatTime(trash ? row.deleted_at : row.updated_at) }}</template></el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="(command: string) => handleCommand(command, row)">
              <el-button size="small" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu v-if="!trash">
                  <el-dropdown-item command="open" :icon="Edit" style="color: #409eff">编辑文档</el-dropdown-item>
                  <el-dropdown-item v-if="row.can_edit" command="rename" :icon="EditPen" style="color: #e6a23c">修改文档名</el-dropdown-item>
                  <el-dropdown-item v-if="row.owner === currentOwner" command="sharing" :icon="View">{{ row.is_shared ? '设为仅自己可见' : '设为共享可见' }}</el-dropdown-item>
                  <el-dropdown-item command="copy" :icon="DocumentCopy">复制一份</el-dropdown-item>
                  <el-dropdown-item v-if="row.can_edit" command="delete" :icon="Delete" divided style="color: #f56c6c">删除</el-dropdown-item>
                </el-dropdown-menu>
                <el-dropdown-menu v-else>
                  <el-dropdown-item command="restore" :icon="RefreshLeft">恢复</el-dropdown-item>
                  <el-dropdown-item command="permanent" :icon="Delete" divided style="color: #f56c6c">永久删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" v-model:page-size="perPage" :total="filteredRows.length"
        :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next, jumper" class="pagination" />
    </el-card>

    <el-dialog v-model="copyDialogVisible" title="复制文档" width="440px" :close-on-click-modal="false">
      <el-form label-width="80px" @submit.prevent>
        <el-form-item label="原文档"><span>{{ copyForm.sourceTitle }}（所有者：{{ copyForm.sourceOwner }}）</span></el-form-item>
        <el-form-item label="新文档名" required><el-input v-model="copyForm.title" maxlength="200" show-word-limit @keyup.enter="copyDocument" /></el-form-item>
        <el-form-item label="说明"><div class="form-tip">复制当前已保存的内容和媒体，新文档归属您本人。</div></el-form-item>
      </el-form>
      <template #footer><el-button @click="copyDialogVisible = false">取消</el-button><el-button type="primary" :loading="copying" @click="copyDocument">复制</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Back, Delete, DocumentCopy, Edit, EditPen, MoreFilled, Plus, Refresh, RefreshLeft, Search, View } from '@element-plus/icons-vue';
import CommonHeader from '@/components/CommonHeader.vue';

interface RichDocumentRow { id: number; title: string; owner: string; is_shared: boolean; can_edit: boolean; version: number; created_at: string; updated_at: string; deleted_at: string | null }
const rows = ref<RichDocumentRow[]>([]), search = ref(''), trash = ref(false), loading = ref(false), isAdmin = ref(false);
const currentOwner = ref(''), scope = ref<'all' | 'mine'>('all'), page = ref(1), perPage = ref(20);
const copyDialogVisible = ref(false), copying = ref(false);
const copyForm = ref({ sourceId: 0, sourceTitle: '', sourceOwner: '', title: '' });
const filteredRows = computed(() => scope.value === 'mine' && !trash.value ? rows.value.filter(row => row.owner === currentOwner.value) : rows.value);
const pageRows = computed(() => filteredRows.value.slice((page.value - 1) * perPage.value, page.value * perPage.value));

async function call(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('oa_token');
  const headers = new Headers(options.headers);
  headers.set('Authorization', 'Bearer ' + token);
  let response = await fetch('/api' + path, { ...options, headers });
  if (response.status === 401 && token) {
    const refresh = await fetch('/api/auth/refresh', { method: 'POST', headers: { Authorization: 'Bearer ' + token } });
    if (refresh.ok) {
      const body = await refresh.json();
      if (body.data?.token) {
        localStorage.setItem('oa_token', body.data.token);
        headers.set('Authorization', 'Bearer ' + body.data.token);
        response = await fetch('/api' + path, { ...options, headers });
      }
    }
  }
  if (!response.ok) throw new Error('请求失败 ' + response.status);
  return response.json();
}
async function load() {
  loading.value = true;
  try {
    rows.value = await call('/rich-documents?trash=' + (trash.value ? '1' : '0') + '&q=' + encodeURIComponent(search.value));
    page.value = Math.min(page.value, Math.max(1, Math.ceil(filteredRows.value.length / perPage.value)));
  } catch (e) { console.error('加载图文文档失败', e); ElMessage.error('加载失败'); }
  finally { loading.value = false; }
}
function toggleTrash() { trash.value = !trash.value; page.value = 1; void load(); }
function create() { window.open('/rich-editor.html', '_blank', 'noopener'); }
function open(id: number) { window.open('/rich-editor.html?id=' + id, '_blank', 'noopener'); }
function formatTime(value: string | null) { if (!value) return '—'; const date = new Date(value.endsWith('Z') ? value : value + 'Z'); return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false }); }
async function rename(row: RichDocumentRow) {
  try {
    const { value } = await ElMessageBox.prompt('请输入文档标题', '重命名', { inputValue: row.title, inputValidator: (v: string) => !!v.trim() || '标题不能为空' });
    const d = await call('/rich-documents/' + row.id);
    await call('/rich-documents/' + row.id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...d, title: value }) });
    await load();
  } catch (e) { if (e !== 'cancel' && e !== 'close') { console.error('重命名图文文档失败', e); ElMessage.error('重命名失败'); } }
}
function prepareCopy(row: RichDocumentRow) {
  copyForm.value = { sourceId: row.id, sourceTitle: row.title, sourceOwner: row.owner, title: (row.title.slice(0, 195) + ' - 副本') };
  copyDialogVisible.value = true;
}
async function copyDocument() {
  const title = copyForm.value.title.trim();
  if (!title) { ElMessage.warning('请输入新文档名'); return; }
  if (copying.value) return;
  copying.value = true;
  try {
    await call('/rich-documents/' + copyForm.value.sourceId + '/copy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title }) });
    copyDialogVisible.value = false; scope.value = 'all'; page.value = 1; search.value = '';
    await load(); ElMessage.success('已复制文档');
  } catch (e) { console.error('复制图文文档失败', e); ElMessage.error('复制失败，请检查原文档媒体是否完整'); }
  finally { copying.value = false; }
}
async function remove(row: RichDocumentRow) { try { await ElMessageBox.confirm('确定删除该文档？', '删除'); await call('/rich-documents/' + row.id, { method: 'DELETE' }); await load(); } catch (e) { if (e !== 'cancel' && e !== 'close') { console.error('删除图文文档失败', e); ElMessage.error('删除失败'); } } }
async function restore(row: RichDocumentRow) { try { await call('/rich-documents/' + row.id + '/restore', { method: 'POST' }); await load(); } catch (e) { console.error('恢复图文文档失败', e); ElMessage.error('恢复失败'); } }
async function permanent(row: RichDocumentRow) { try { await ElMessageBox.confirm('永久删除后无法恢复，确定继续？', '永久删除', { type: 'warning' }); await call('/rich-documents/' + row.id + '/permanent', { method: 'DELETE' }); await load(); } catch (e) { if (e !== 'cancel' && e !== 'close') { console.error('永久删除图文文档失败', e); ElMessage.error('删除失败'); } } }
async function setSharing(row: RichDocumentRow) {
  try { await call('/rich-documents/' + row.id + '/sharing', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_shared: !row.is_shared }) }); await load(); ElMessage.success(row.is_shared ? '已设为仅自己可见' : '已设为共享可见'); }
  catch (e) { console.error('设置共享状态失败', e); ElMessage.error('设置共享状态失败'); }
}
function handleCommand(command: string, row: RichDocumentRow) {
  if (command === 'open') open(row.id);
  else if (command === 'sharing') void setSharing(row);
  else if (command === 'rename') void rename(row);
  else if (command === 'copy') prepareCopy(row);
  else if (command === 'delete') void remove(row);
  else if (command === 'restore') void restore(row);
  else if (command === 'permanent') void permanent(row);
}
onMounted(async () => { try { const info = await call('/rich-documents/me'); isAdmin.value = info.admin; currentOwner.value = info.owner; } catch (e) { console.error('获取当前用户失败', e); ElMessage.error('认证失败'); } await load(); });
</script>

<style scoped>
.rich-documents-page { padding: 20px; background: #f5f7fa; min-height: 100vh; }
.main-card { margin-top: 16px; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.document-name { font-weight: 500; color: #303133; }
.pagination { margin-top: 16px; justify-content: flex-end; }
.form-tip { font-size: 12px; color: #909399; line-height: 1.5; }
</style>
