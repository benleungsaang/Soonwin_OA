<template>
  <el-dialog v-model="visible" title="手机文件上传" width="min(620px, 94vw)" align-center @opened="loadSettings">
    <div class="intro">通过临时二维码，将手机照片、视频或其他文件上传至 NAS 临时中转目录。</div>
    <div class="qr-wrap">
      <div class="qr-stage">
        <canvas ref="canvasRef" aria-label="手机上传二维码"></canvas>
        <div v-if="qrState === 'valid' && scanned" class="qr-state-overlay state-success" role="status" aria-live="polite">
          <div class="qr-state-content">
            <div class="qr-state-symbol" aria-hidden="true">✓</div>
            <div class="qr-state-title">扫码成功</div>
            <div class="qr-state-sub">请在手机上继续上传</div>
          </div>
        </div>
        <div v-else-if="qrState === 'failed' || qrState === 'expired'" class="qr-state-overlay" :class="qrState === 'expired' ? 'state-expired' : 'state-error'" role="status">
          <div class="qr-state-content">
            <div class="qr-state-symbol" aria-hidden="true">{{ qrState === 'expired' ? '!' : '×' }}</div>
            <div class="qr-state-title">{{ qrState === 'expired' ? '二维码已过期' : '连接失败' }}</div>
            <div class="qr-state-sub">{{ qrState === 'expired' ? '请重新生成二维码' : '请联系管理员' }}</div>
          </div>
        </div>
        <div v-else-if="qrState === 'empty'" class="qr-overlay empty" role="status">
          <div class="notice-title">尚未生成二维码</div>
          <div class="notice-help">点击下方按钮先检测 NAS</div>
        </div>
      </div>
      <strong>{{ qrState === 'valid' ? '上传二维码' : qrState === 'expired' ? '上传二维码已失效' : qrState === 'failed' ? '无法生成上传二维码' : '尚未生成二维码' }}</strong>
      <span v-if="qrState === 'valid'" class="muted">剩余有效时间 {{ countdown }}</span>
    </div>
    <div class="actions">
      <el-button type="primary" :loading="generating" @click="generate">生成上传二维码</el-button>
    </div>
    <el-alert v-if="message" :title="message" :type="messageType" show-icon :closable="false" class="message" />

    <template v-if="isAdmin">
      <el-divider />
      <div v-if="settingsExpanded" class="admin-settings">
        <div class="admin-heading">NAS 上传目录设置 <el-tag type="warning">仅管理员</el-tag></div>
        <el-input v-model="pathValue" :readonly="!editing" placeholder="共享根目录下的相对路径" @keyup.enter="editing && checkAndSave()" @keyup.esc="cancelEdit" />
        <div class="hint">授权上传根目录：\\192.168.110.229\美工资料\2026美工专用。这里只能修改根目录下子目录。</div>
        <div class="actions admin-actions">
          <el-button :loading="checking" @click="manualCheck">检查连接</el-button>
          <el-button v-if="!editing" type="primary" @click="beginEdit">修改地址</el-button>
          <template v-else>
            <el-button type="primary" :loading="checking" @click="checkAndSave">检查并修改</el-button>
            <el-button @click="cancelEdit">取消修改</el-button>
          </template>
        </div>
        <el-alert v-if="adminMessage" :title="adminMessage" :type="adminMessageType" show-icon :closable="false" />
        <div class="hint">已生成的二维码继续使用生成时绑定的目录；修改只影响新二维码。</div>
      </div>
      <div class="admin-tools">
        <el-button circle text aria-label="展开或收起 NAS 上传目录设置" title="NAS 上传目录设置" @click="settingsExpanded = !settingsExpanded">
          <el-icon><Setting /></el-icon>
        </el-button>
        <el-button circle text aria-label="查看上传日志" title="上传日志" @click="openLogs">
          <el-icon><Document /></el-icon>
        </el-button>
      </div>
    </template>
  </el-dialog>

  <el-dialog v-model="logsVisible" title="手机文件上传日志" width="min(900px, 96vw)" align-center>
    <div class="log-search">
      <el-input v-model="logKeyword" clearable placeholder="按文件名搜索" @keyup.enter="searchLogs" @clear="searchLogs" />
      <el-button type="primary" :loading="logsLoading" @click="searchLogs"><el-icon><Search /></el-icon>查询</el-button>
    </div>
    <el-table :data="logRows" v-loading="logsLoading" border stripe empty-text="暂无上传记录">
      <el-table-column prop="uploaded_at" label="上传时间" width="165" />
      <el-table-column label="OA 用户" width="130">
        <template #default="scope">{{ scope.row.operator_name }}<span v-if="scope.row.operator_id" class="log-emp-id">{{ scope.row.operator_id }}</span></template>
      </el-table-column>
      <el-table-column prop="filename" label="文件名" min-width="190" show-overflow-tooltip />
      <el-table-column label="大小" width="100">
        <template #default="scope">{{ formatFileSize(scope.row.file_size) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="scope"><el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">{{ scope.row.status === 'success' ? '成功' : '失败' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="target_dir" label="NAS 目标目录" min-width="160" show-overflow-tooltip />
    </el-table>
    <div class="log-pagination">
      <el-pagination v-model:current-page="logPage" v-model:page-size="logPageSize" :page-sizes="[10, 20, 50]" :total="logTotal" layout="total, sizes, prev, pager, next" @current-change="loadLogs" @size-change="onLogPageSizeChange" />
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import QRCode from 'qrcode';
import { Document, Search, Setting } from '@element-plus/icons-vue';
import { checkNasUploadDirectory, createNasUploadToken, getNasUploadLogs, getNasUploadQrStatus, getNasUploadSettings, saveNasUploadDirectory } from '@/api/nasUpload';

const props = defineProps<{ modelValue: boolean; isAdmin: boolean }>();
const emit = defineEmits<{ (event: 'update:modelValue', value: boolean): void }>();
const visible = computed({ get: () => props.modelValue, set: (value) => emit('update:modelValue', value) });
const canvasRef = ref<HTMLCanvasElement | null>(null);
const qrState = ref<'empty' | 'valid' | 'failed' | 'expired'>('empty');
const generating = ref(false);
const checking = ref(false);
const message = ref('');
const messageType = ref<'success' | 'warning' | 'error' | 'info'>('info');
const adminMessage = ref('');
const adminMessageType = ref<'success' | 'warning' | 'error' | 'info'>('info');
const pathValue = ref('');
const originalPath = ref('');
const mobileUrl = ref('');
const qrToken = ref('');
const scanned = ref(false);
const editing = ref(false);
const settingsExpanded = ref(false);
const logsVisible = ref(false);
const logsLoading = ref(false);
const logKeyword = ref('');
const logRows = ref<any[]>([]);
const logPage = ref(1);
const logPageSize = ref(10);
const logTotal = ref(0);
const expiresAt = ref(0);
const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | undefined;
let scanTimer: ReturnType<typeof setInterval> | undefined;
let scanPollInFlight = false;
const countdown = computed(() => {
  const seconds = Math.max(0, Math.ceil((expiresAt.value - now.value) / 1000));
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
});

watch(() => props.modelValue, (open) => {
  if (!open) {
    clearInterval(timer); timer = undefined;
    clearInterval(scanTimer); scanTimer = undefined;
    return;
  }
  if (qrState.value === 'valid' && qrToken.value) startQrTimers(qrToken.value);
});
watch(now, () => {
  if (qrState.value === 'valid' && now.value >= expiresAt.value) {
    qrState.value = 'expired';
    clearInterval(timer); timer = undefined;
    clearInterval(scanTimer); scanTimer = undefined;
  }
});
onBeforeUnmount(() => {
  clearInterval(timer);
  clearInterval(scanTimer);
});

function startQrTimers(token: string) {
  clearInterval(timer);
  clearInterval(scanTimer);
  timer = setInterval(() => { now.value = Date.now(); }, 1000);
  const poll = async () => {
    if (scanPollInFlight || qrToken.value !== token || qrState.value !== 'valid') return;
    scanPollInFlight = true;
    try {
      const state = await getNasUploadQrStatus(token);
      if (qrToken.value !== token || qrState.value !== 'valid') return;
      if (state.scanned) scanned.value = true;
    } catch (error: any) {
      if (qrToken.value !== token) return;
      if (error.response?.status === 410) {
        qrState.value = 'expired';
        message.value = '二维码已失效，请重新生成。';
        messageType.value = 'warning';
        clearInterval(scanTimer); scanTimer = undefined;
      }
    } finally {
      scanPollInFlight = false;
    }
  };
  void poll();
  scanTimer = setInterval(() => { void poll(); }, 1500);
}

async function loadSettings() {
  if (!props.isAdmin) return;
  try {
    const response: any = await getNasUploadSettings();
    pathValue.value = response.relative_dir || '';
    originalPath.value = pathValue.value;
  } catch { adminMessage.value = '读取 NAS 目录配置失败'; adminMessageType.value = 'error'; }
}

async function openLogs() {
  logsVisible.value = true;
  logPage.value = 1;
  await loadLogs();
}

async function loadLogs() {
  if (!props.isAdmin) return;
  logsLoading.value = true;
  try {
    const response: any = await getNasUploadLogs({
      page: logPage.value, page_size: logPageSize.value, keyword: logKeyword.value.trim(),
    });
    logRows.value = response.items || [];
    logTotal.value = response.total || 0;
  } catch (error: any) {
    ElMessageBox.alert(error.response?.data?.msg || '读取上传日志失败', '查询失败', { type: 'error' });
  } finally {
    logsLoading.value = false;
  }
}

function searchLogs() {
  logPage.value = 1;
  void loadLogs();
}

function onLogPageSizeChange() {
  logPage.value = 1;
  void loadLogs();
}

function formatFileSize(value: number) {
  const size = Number(value) || 0;
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

async function generate() {
  generating.value = true;
  message.value = '正在检查 NAS 目录并生成二维码…'; messageType.value = 'info';
  qrState.value = 'empty';
  qrToken.value = '';
  scanned.value = false;
  clearInterval(timer); timer = undefined;
  clearInterval(scanTimer); scanTimer = undefined;
  mobileUrl.value = '';
  canvasRef.value?.getContext('2d')?.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
  try {
    const origin = window.location.origin;
    const host = window.location.hostname.toLowerCase().replace(/^\[|\]$/g, '');
    if (host === 'localhost' || host === '::1' || /^127\./.test(host) || host === '0.0.0.0') {
      throw new Error('请使用手机可访问的局域网 OA 地址打开本页');
    }
    const data: any = await createNasUploadToken();
    qrToken.value = data.token;
    // Put the bearer token in the fragment so access logs and HTTP Referer never receive it.
    const url = `${origin}/mobile-upload#${encodeURIComponent(data.token)}`;
    mobileUrl.value = url;
    await nextTick();
    if (!canvasRef.value) throw new Error('二维码区域未就绪');
    await QRCode.toCanvas(canvasRef.value, url, { width: 190, margin: 2 });
    expiresAt.value = Number(data.expires_at) * 1000;
    qrState.value = 'valid'; message.value = 'NAS 连接与真实写入检查通过，上传二维码已生成。'; messageType.value = 'success';
    startQrTimers(data.token);
  } catch (error: any) {
    qrToken.value = '';
    qrState.value = 'failed'; message.value = error.response?.data?.msg || error.message || 'NAS 暂不可用，请联系管理员'; messageType.value = 'error';
  } finally { generating.value = false; }
}

async function manualCheck() {
  checking.value = true;
  try {
    const response: any = await checkNasUploadDirectory(pathValue.value);
    adminMessage.value = `连接成功：${response.relative_dir || pathValue.value} 可写`;
    adminMessageType.value = 'success';
  } catch (error: any) { adminMessage.value = error.response?.data?.msg || 'NAS 连接失败，请检查路径或联系运维'; adminMessageType.value = 'error'; }
  finally { checking.value = false; }
}

function beginEdit() { originalPath.value = pathValue.value; editing.value = true; adminMessage.value = ''; }
function cancelEdit() { pathValue.value = originalPath.value; editing.value = false; adminMessage.value = ''; }

async function checkAndSave() {
  checking.value = true;
  try {
    await checkNasUploadDirectory(pathValue.value);
    await ElMessageBox.confirm(`新目录检查成功，确认将上传目标修改为：\n${pathValue.value}？`, '确认保存', { type: 'warning' });
    await saveNasUploadDirectory(pathValue.value);
    originalPath.value = pathValue.value; editing.value = false;
    adminMessage.value = '新目标目录已保存；已生成的二维码保持原目录。'; adminMessageType.value = 'success';
  } catch (error: any) {
    if (error === 'cancel' || error === 'close') return;
    adminMessage.value = error.response?.data?.msg || '检查失败，请重新输入目录'; adminMessageType.value = 'error';
  } finally { checking.value = false; }
}
</script>

<style scoped>
.intro,.hint,.muted{color:#909399;font-size:12px;line-height:1.65}
.qr-wrap{min-height:258px;border:1px dashed #dcdfe6;background:#fafcff;border-radius:9px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:18px;margin:18px auto;max-width:390px}
.qr-stage{position:relative;box-sizing:border-box;width:214px;height:214px;padding:12px;background:#fff;border:1px solid #ebeef5;border-radius:10px;overflow:hidden;display:grid;place-items:center}
.qr-stage canvas{display:block;width:190px!important;height:190px!important}
.qr-state-overlay{position:absolute;inset:0;z-index:2;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:inherit;background:rgba(13,27,39,.88);color:#fff;text-align:center}
.qr-state-content{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px}
.qr-state-symbol{width:47px;height:47px;display:grid;place-items:center;border-radius:50%;margin:0 auto 9px;font-size:27px;font-weight:700;line-height:1;background:var(--state-tint);color:var(--state-tone)}
.qr-state-title{font-size:17px;font-weight:750;letter-spacing:.3px;color:var(--state-tone)}
.qr-state-sub{font-size:11px;margin-top:6px;line-height:1.5;color:#c7d1d9}
.state-success{--state-tone:#35d38a;--state-tint:#e2faed}
.state-error{--state-tone:#ff6868;--state-tint:#ffe6e6}
.state-expired{--state-tone:#ffcf58;--state-tint:#fff3cf}
.qr-overlay{position:absolute;inset:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;border-radius:6px;background:#ffffffd9;text-align:center}
.notice-title{font-size:14px;font-weight:700;color:#606266}
.notice-help{font-size:11px;color:#909399}
.actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
.message{margin-top:14px}
.admin-heading{font-size:16px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:10px}
.admin-actions{justify-content:flex-start;margin:14px 0}
.admin-tools{display:flex;justify-content:flex-end;align-items:center;margin-top:8px;padding-top:4px;border-top:1px solid #ebeef5}
.admin-tools :deep(.el-button){font-size:17px;color:#606266}
.admin-tools :deep(.el-button:hover){color:#409eff}
.admin-settings{padding-bottom:4px}
.log-search{display:flex;gap:10px;margin-bottom:14px}
.log-search .el-input{max-width:360px}
.log-emp-id{display:block;margin-top:2px;color:#909399;font-size:11px}
.log-pagination{display:flex;justify-content:flex-end;margin-top:16px}
.hint{margin-top:8px}
</style>
