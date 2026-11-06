<template>
  <main class="mobile-page">
    <header class="mobile-head"><div class="upload-mark">⇧</div><h1>上传文件</h1><div>文件将保存至 NAS 临时中转目录</div></header>
    <section class="mobile-body">
      <el-alert v-if="pageError" :title="pageError" type="error" show-icon :closable="false" />
      <el-tag v-else type="success" effect="light" round>上传链接有效 · 剩余 {{ countdown }}</el-tag>

      <label class="upload-zone" :class="{ disabled: !valid }">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <strong>选择照片、视频或文件</strong>
        <span>支持一次选择多个文件</span>
        <span class="choose-button">选择文件</span>
        <input type="file" multiple :disabled="!valid" @change="selectFiles">
      </label>

      <div v-if="files.length" class="file-list">
        <article v-for="item in files" :key="item.key" class="file-row">
          <div class="file-name">{{ item.file.name }}</div>
          <div class="file-meta">{{ formatSize(item.file.size) }}</div>
          <el-progress :percentage="item.progress" :status="item.status === 'success' ? 'success' : item.status === 'failed' ? 'exception' : undefined" :stroke-width="7" />
          <div class="file-state" :class="item.status">{{ item.message }}</div>
          <el-button v-if="item.status === 'failed' && item.task" link type="primary" @click="retryItem(item)">重试当前文件</el-button>
        </article>
      </div>
      <el-button class="start-button" type="primary" size="large" :loading="busy" :disabled="busy || !valid || !files.some(f => f.status === 'queued')" @click="startUploads">{{ busy ? '上传队列运行中' : '开始上传' }}</el-button>
      <div class="foot">单文件最大 2048 MB。仅提供文件上传，不支持浏览、下载或删除。上传完成后，请通过 NAS 原有方式管理文件。</div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { UploadFilled } from '@element-plus/icons-vue';
import { acknowledgeNasUploadTask, createNasUploadTask, getNasUploadTaskStatus, getNasUploadTasksStatus, uploadNasFile, validateNasUploadToken, type NasUploadTask } from '@/api/nasUpload';
import { createNasUploadDeadline, nasUploadRemainingMs } from '@/utils/nasUploadExpiry';

type UploadItem = { key: string; file: File; progress: number; status: 'queued' | 'uploading' | 'waiting' | 'success' | 'failed'; message: string; task?: NasUploadTask; pollErrors?: number; restartOnRetry?: boolean };
const route = useRoute();
const token = ref('');
let fileKeySequence = 0;
let validationRun = 0;
let lastValidatedFragment: string | null = null;
const valid = ref(false);
const pageError = ref('');
const files = ref<UploadItem[]>([]);
const busy = ref(false);
const expiresAt = ref(0);
const now = ref(performance.now());
let clock: ReturnType<typeof setInterval> | undefined;
let pollClock: ReturnType<typeof setInterval> | undefined;
let polling = false;
const countdown = computed(() => {
  const seconds = Math.ceil(nasUploadRemainingMs(expiresAt.value, now.value) / 1000);
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
});

function refreshTokenFromUrl() {
  const fragment = window.location.hash;
  if (fragment === lastValidatedFragment) return;
  lastValidatedFragment = fragment;
  const run = ++validationRun;
  token.value = '';
  valid.value = false;
  pageError.value = '';
  files.value = [];
  expiresAt.value = 0;
  now.value = performance.now();

  try {
    token.value = decodeURIComponent(fragment.slice(1));
  } catch {
    pageError.value = '上传链接格式无效，请联系 OA 用户重新生成。';
    return;
  }
  if (!token.value) {
    pageError.value = '上传链接缺少令牌，请联系 OA 用户重新生成。';
    return;
  }
  void validateCurrentToken(token.value, run);
}

watch(() => route.hash, refreshTokenFromUrl, { immediate: true });
function handleHashChange() { refreshTokenFromUrl(); }

async function validateCurrentToken(currentToken: string, run: number) {
  try {
    const info = await validateNasUploadToken(currentToken);
    if (run !== validationRun) return;
    expiresAt.value = createNasUploadDeadline(info.remaining_seconds);
    // Only a successful server response marks this link as validated. The
    // countdown below is informational; session creation rechecks JWT expiry.
    valid.value = true;
  } catch (error: any) {
    if (run !== validationRun) return;
    pageError.value = error.response?.status === 410 ? '上传二维码已过期或无效，请联系 OA 用户重新生成。' : '无法验证上传链接，请检查局域网连接后重试。';
  }
}

onMounted(() => {
  window.addEventListener('hashchange', handleHashChange);
  refreshTokenFromUrl();
  clock = setInterval(() => { now.value = performance.now(); }, 1000);
  pollClock = setInterval(pollPendingTasks, 1000);
});
onBeforeUnmount(() => {
  clearInterval(clock); clearInterval(pollClock);
  window.removeEventListener('hashchange', handleHashChange);
});

function setQrExpiredFromServer() {
  valid.value = false;
  pageError.value = '上传二维码已过期或无效，请联系 OA 用户重新生成。';
}

function selectFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  const incoming = Array.from(input.files || []);
  const max = 2048 * 1024 * 1024;
  for (const file of incoming) {
    const item: UploadItem = { key: `${Date.now()}-${fileKeySequence++}`, file, progress: 0, status: 'queued', message: '等待上传' };
    if (file.size > max) { item.status = 'failed'; item.message = '超过单文件 2048 MB 限制'; }
    files.value.push(item);
  }
  input.value = '';
}

async function startUploads() {
  if (!valid.value || busy.value) return;
  busy.value = true;
  try {
    while (true) {
      // Find the next queued row each time so files added during upload join the tail.
      const item = files.value.find(row => row.status === 'queued');
      if (!item || !valid.value) break;
      await uploadItem(item);
    }
  } finally {
    busy.value = false;
  }
}

async function retryItem(item: UploadItem) {
  if (busy.value || !item.task) return;
  if (item.restartOnRetry) {
    item.task = undefined; item.progress = 0; item.restartOnRetry = false;
  }
  busy.value = true;
  try {
    await uploadItem(item);
  } finally {
    busy.value = false;
  }
}

function markUploadSuccess(item: UploadItem) {
  item.progress = 100; item.status = 'success'; item.message = '上传完成';
  if (item.task) {
    // Cleanup is best-effort; failed acknowledgements retain the normal expiry fallback.
    void acknowledgeNasUploadTask(item.task).catch(() => console.warn('上传状态清理失败，将在过期后处理'));
  }
}

async function uploadItem(item: UploadItem) {
  item.status = 'uploading'; item.message = '正在上传文件';
  try {
    if (!item.task) {
      item.task = await createNasUploadTask(token.value, item.file);
    }
    const state = await getNasUploadTaskStatus(item.task);
    if (state.status === 'completed') {
      markUploadSuccess(item); return;
    }
    if (state.status === 'failed') {
      item.restartOnRetry = true;
      throw new Error(state.error || '文件处理失败，请重新上传');
    }
    if (state.status === 'pending' || state.status === 'processing') {
      item.progress = 100; item.status = 'waiting'; item.message = state.status === 'processing' ? '等待文件处理完成' : '数据已传完，等待文件处理';
      void pollPendingTasks(); return;
    }
    try {
      await uploadNasFile(item.task, item.file, loaded => {
        item.progress = item.file.size ? Math.min(99, Math.round(loaded * 100 / item.file.size)) : 0;
      });
    } catch (error: any) {
      // If the response was lost after the NAS write, reconcile before retrying
      // the complete file body.
      const serverState = await getNasUploadTaskStatus(item.task).catch(() => undefined);
      if (serverState?.file_size === item.file.size && ['pending', 'processing', 'completed'].includes(serverState.status)) {
        if (serverState.status === 'completed') {
          markUploadSuccess(item); return;
        }
        item.progress = 100; item.status = 'waiting'; item.message = '数据已传完，等待文件处理';
        void pollPendingTasks(); return;
      }
      if (serverState?.status === 'failed') throw new Error(serverState.error || '文件处理失败，请重新上传');
      throw error;
    }
    item.progress = 100; item.status = 'waiting'; item.message = '数据已传完，等待文件处理';
    void pollPendingTasks();
  } catch (error: any) {
    if (!item.task && error.response?.status === 410) setQrExpiredFromServer();
    item.status = 'failed';
    item.message = error.code === 'ECONNABORTED'
      ? '整体上传超时，可在本页面重试当前文件'
      : error.response?.data?.msg || error.message || (item.task ? '上传失败，可在本页面重试当前文件' : '任务未能创建，请稍后重新选择文件');
  }
}

async function pollPendingTasks() {
  if (polling) return;
  const pending = files.value.filter(item => item.status === 'waiting' && item.task).slice(0, 100);
  if (!pending.length) return;
  polling = true;
  try {
    const statuses = await getNasUploadTasksStatus(pending.map(item => item.task!));
    const byId = new Map(statuses.map(row => [row.upload_id, row]));
    for (const item of pending) {
      const state = byId.get(item.task!.upload_id);
      if (!state) continue;
      item.pollErrors = 0;
      if (state.status === 'completed') {
        markUploadSuccess(item);
      } else if (state.status === 'failed') {
        item.status = 'failed'; item.restartOnRetry = true; item.message = state.error || '文件处理失败，请重新上传';
      } else if (state.status === 'processing') {
        item.message = '数据已传完，后端正在处理文件';
      } else {
        item.message = '数据已传完，等待文件处理';
      }
    }
  } catch (error: any) {
    for (const item of pending) {
      item.pollErrors = (item.pollErrors || 0) + 1;
      if (item.pollErrors >= 3) {
        item.status = 'failed';
        item.message = error.response?.data?.msg || '无法取得文件处理结果，请重试当前文件';
      }
    }
  } finally {
    polling = false;
  }
}

function formatSize(size: number) {
  if (size >= 1024 ** 3) return `${(size / 1024 ** 3).toFixed(2)} GB`;
  return `${(size / 1024 ** 2).toFixed(2)} MB`;
}

</script>

<style scoped>
.mobile-page{min-height:100vh;background:#f4f6fa;padding:18px 12px;color:#303133}.mobile-head{max-width:430px;margin:0 auto;background:#409eff;color:white;text-align:center;border-radius:16px 16px 0 0;padding:24px 18px 18px}.mobile-head h1{font-size:20px;margin:6px 0}.mobile-head>div:last-child{font-size:12px;opacity:.9}.upload-mark{font-size:32px}.mobile-body{max-width:430px;margin:0 auto;background:white;border-radius:0 0 16px 16px;padding:18px;box-shadow:0 8px 26px #202c4412}.upload-zone{margin-top:20px;min-height:180px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;text-align:center;border:2px dashed #c6dfff;border-radius:12px;background:#f8fbff;color:#606266;font-size:13px}.upload-zone input{display:none}.upload-zone.disabled{opacity:.55}.upload-icon{font-size:38px;color:#409eff}.choose-button{background:#409eff;color:white;border-radius:6px;padding:10px 22px}.file-list{margin-top:12px}.file-row{padding:12px 0;border-bottom:1px solid #ebeef5}.file-name{word-break:break-all;font-size:14px}.file-meta,.file-state{font-size:12px;color:#909399;margin:4px 0}.file-state.waiting{color:#e6a23c}.file-state.success{color:#67c23a}.file-state.failed{color:#f56c6c}.start-button{width:100%;margin-top:18px}.foot{font-size:12px;line-height:1.7;color:#909399;margin-top:18px}
</style>
