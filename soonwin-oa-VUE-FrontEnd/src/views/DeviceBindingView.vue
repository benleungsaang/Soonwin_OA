<template>
  <main class="phone-outer"><section class="phone-card"><header><strong>OA 设备绑定</strong><span>员工手机</span></header><div class="phone-content"><div class="phone-icon" :class="status"><span>{{ icon }}</span></div><h1>{{ title }}</h1><p>{{ description }}</p><el-button v-if="status === 'scanned'" type="primary" :loading="submitting" @click="submit">提交绑定申请</el-button><el-button v-else-if="status === 'approved'" type="primary" @click="router.push('/punch')">前往打卡</el-button><el-alert v-else-if="errorMessage" :title="errorMessage" type="warning" :closable="false" /></div></section></main>
</template>
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import request from '@/utils/request';
import { getOrCreatePunchDeviceId } from '@/utils/punchDeviceId';
import { isExpiredSessionResponse, isTerminalBindingStatus } from '@/utils/deviceBindingState';
const route=useRoute(); const router=useRouter(); const token=computed(()=>String(route.params.token)); const status=ref('loading'); const submitting=ref(false); const errorMessage=ref(''); let timer:number|undefined;
const presentation=computed(()=>({ scanned:['确认绑定当前手机','请确认使用这台手机作为日常打卡设备。','▣'],pending:['申请已提交','请等待管理员现场确认。','◷'],approved:['设备绑定成功','现在可以使用这台手机正常打卡。','✓'],rejected:['申请未通过','请联系管理员重新申请。','!'],expired:['二维码已过期','请联系管理员重新生成。','!'],cancelled:['二维码已失效','请联系管理员重新生成。','!'],loading:['正在确认二维码','请稍候。','◷'] }[status.value] || ['设备绑定','请稍候。','◷']));
const title=computed(()=>presentation.value[0]); const description=computed(()=>presentation.value[1]); const icon=computed(()=>presentation.value[2]);
const stop=()=>{if(timer)window.clearInterval(timer);timer=undefined};
const apply=(data:any)=>{status.value=data.status;errorMessage.value='';if(isTerminalBindingStatus(status.value))stop()};
const load=async(scan=false)=>{try{const data:any=scan?await request.post(`/api/device-binding-sessions/${token.value}/scan`):await request.get(`/api/device-binding-sessions/${token.value}/status`);apply(data)}catch(error:any){const code=error.response?.status;if(isExpiredSessionResponse(code)){status.value='expired';stop()}else{errorMessage.value=error.response?.data?.msg||'状态同步失败，请保持页面打开后重试。'}}};
const submit=async()=>{submitting.value=true;try{const data:any=await request.post(`/api/device-binding-sessions/${token.value}/submit`,{}, {headers:{'X-Device-ID':getOrCreatePunchDeviceId()}});apply(data)}catch(error:any){errorMessage.value=error.response?.data?.msg||'提交失败，请重试。'}finally{submitting.value=false}};
onMounted(async()=>{await load(true);if(!isTerminalBindingStatus(status.value))timer=window.setInterval(()=>load(),2000)});onBeforeUnmount(stop);
</script>
<style scoped>.phone-outer{max-width:420px;margin:34px auto;padding:12px;background:#e9edf4;border-radius:28px}.phone-card{background:#fff;border-radius:21px;min-height:570px;overflow:hidden}.phone-card header{display:flex;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #eef1f5;font-size:13px;color:#6f7a8a}.phone-card header strong{color:#253044}.phone-content{padding:55px 25px 35px;text-align:center}.phone-icon{width:68px;height:68px;border-radius:22px;background:#eaf3ff;color:#347cf0;display:grid;place-items:center;margin:0 auto 24px;font-size:32px}.phone-icon.approved{background:#e7f8ef;color:#16a36b}.phone-icon.rejected,.phone-icon.expired,.phone-icon.cancelled{background:#fff1f1;color:#e05252}.phone-content h1{font-size:21px;margin:0 0 13px;color:#253044}.phone-content p{color:#7d899a;font-size:14px;line-height:1.8;margin:0 auto 29px;max-width:250px}.phone-content .el-button{width:100%;max-width:270px;height:46px}@media(max-width:460px){.phone-outer{margin:0;border-radius:0;min-height:100vh}}</style>
