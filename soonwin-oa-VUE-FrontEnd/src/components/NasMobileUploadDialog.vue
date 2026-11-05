<template>
  <el-dialog v-model="visible" title="手机文件上传" width="min(620px, 94vw)" align-center @opened="loadSettings">
    <div class="intro">通过临时二维码，将手机照片、视频或其他文件上传至 NAS 临时中转目录。</div>
    <div class="qr-wrap">
      <div class="qr-stage">
        <canvas ref="canvasRef" aria-label="手机上传二维码"></canvas>
        <div v-if="qrState !== 'valid'" class="qr-overlay" :class="qrState" role="status">
          <div class="notice-icon">{{ qrState === 'expired' ? '!' : '×' }}</div>
          <div class="notice-title">{{ qrState === 'expired' ? '二维码过期' : qrState === 'failed' ? '连接失败' : '尚未生成二维码' }}</div>
          <div class="notice-help">{{ qrState === 'expired' ? '请重新生成二维码' : qrState === 'failed' ? '请联系管理员' : '点击下方按钮先检测 NAS' }}</div>
        </div>
      </div>
      <strong>{{ qrState === 'valid' ? '上传二维码' : qrState === 'expired' ? '上传二维码已失效' : qrState === 'failed' ? '无法生成上传二维码' : '尚未生成二维码' }}</strong>
      <span v-if="qrState === 'valid'" class="muted">剩余有效时间 {{ countdown }}</span>
      <div v-if="qrState === 'valid' && mobileUrl" class="mobile-link">
        <span class="muted">上传链接（可在电脑端直接打开）</span>
        <a :href="mobileUrl" target="_blank" rel="noopener">{{ mobileUrl }}</a>
      </div>
    </div>
    <div class="actions">
      <el-button type="primary" :loading="generating" @click="generate">生成上传二维码</el-button>
    </div>
    <el-alert v-if="message" :title="message" :type="messageType" show-icon :closable="false" class="message" />

    <template v-if="isAdmin">
      <el-divider />
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
    </template>
    <div class="note">二维码有效期 30 分钟。过期后不能开始新上传；有效期内开始的上传可继续完成。此入口仅允许上传，不提供文件浏览、下载或删除。</div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import QRCode from 'qrcode';
import { checkNasUploadDirectory, createNasUploadToken, getNasUploadSettings, saveNasUploadDirectory } from '@/api/nasUpload';

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
const editing = ref(false);
const expiresAt = ref(0);
const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | undefined;
const countdown = computed(() => {
  const seconds = Math.max(0, Math.ceil((expiresAt.value - now.value) / 1000));
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
});

watch(() => props.modelValue, (open) => { if (!open) clearInterval(timer); });
watch(now, () => { if (qrState.value === 'valid' && now.value >= expiresAt.value) qrState.value = 'expired'; });
onBeforeUnmount(() => clearInterval(timer));

async function loadSettings() {
  if (!props.isAdmin) return;
  try {
    const response: any = await getNasUploadSettings();
    pathValue.value = response.relative_dir || '';
    originalPath.value = pathValue.value;
  } catch { adminMessage.value = '读取 NAS 目录配置失败'; adminMessageType.value = 'error'; }
}

async function generate() {
  generating.value = true;
  message.value = '正在检查 NAS 目录并生成二维码…'; messageType.value = 'info';
  qrState.value = 'empty';
  mobileUrl.value = '';
  canvasRef.value?.getContext('2d')?.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
  try {
    const origin = window.location.origin;
    const host = window.location.hostname.toLowerCase().replace(/^\[|\]$/g, '');
    if (host === 'localhost' || host === '::1' || /^127\./.test(host) || host === '0.0.0.0') {
      throw new Error('请使用手机可访问的局域网 OA 地址打开本页');
    }
    const data: any = await createNasUploadToken();
    // Put the bearer token in the fragment so access logs and HTTP Referer never receive it.
    const url = `${origin}/mobile-upload#${encodeURIComponent(data.token)}`;
    mobileUrl.value = url;
    await nextTick();
    if (!canvasRef.value) throw new Error('二维码区域未就绪');
    await QRCode.toCanvas(canvasRef.value, url, { width: 190, margin: 2 });
    expiresAt.value = Number(data.expires_at) * 1000;
    qrState.value = 'valid'; message.value = 'NAS 连接与真实写入检查通过，上传二维码已生成。'; messageType.value = 'success';
    clearInterval(timer); timer = setInterval(() => { now.value = Date.now(); }, 1000);
  } catch (error: any) {
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
.intro,.hint,.note,.muted{color:#909399;font-size:12px;line-height:1.65}.qr-wrap{min-height:258px;border:1px dashed #dcdfe6;background:#fafcff;border-radius:9px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:18px;margin:18px auto;max-width:390px}.qr-stage{position:relative;width:190px;height:190px}.qr-stage canvas{width:190px!important;height:190px!important}.qr-overlay{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;border-radius:14px;background:#ffffffb8;text-align:center}.notice-icon{width:34px;height:34px;display:grid;place-items:center;border-radius:50%;background:#e75a5a;color:white;font-size:23px;font-weight:bold}.notice-title{font-size:14px;font-weight:700;color:#b83d3d}.notice-help{font-size:11px;color:#ad5555}.qr-overlay.expired .notice-icon{background:#e6a23c}.qr-overlay.expired .notice-title{color:#9d681a}.qr-overlay.empty .notice-icon{display:none}.qr-overlay.empty .notice-title{color:#606266}.mobile-link{max-width:100%;display:flex;flex-direction:column;align-items:center;gap:4px;text-align:center}.mobile-link a{max-width:100%;color:#409eff;font-size:12px;line-height:1.5;overflow-wrap:anywhere;user-select:all}.actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}.message{margin-top:14px}.admin-heading{font-size:16px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:10px}.admin-actions{justify-content:flex-start;margin:14px 0}.hint{margin-top:8px}.note{padding:12px 14px;border-left:3px solid #409eff;background:#ecf5ff;margin-top:20px;color:#606266}
</style>
