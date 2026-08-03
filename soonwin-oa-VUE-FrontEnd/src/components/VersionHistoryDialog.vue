<template>
  <el-dialog v-model="dialogVisible" title="版本记录" width="520px" align-center
             :close-on-click-modal="true" @open="loadFirstPage">
    <div v-loading="loading" class="vh-list">
      <div v-for="(r, i) in records" :key="r.version + '-' + i" class="vh-item">
        <div class="vh-head">
          <span class="vh-version">v{{ r.version }}</span>
          <span class="vh-date">{{ r.date }}</span>
          <span class="vh-git" :title="'本地 git 提交号'">git-{{ r.git }}</span>
        </div>
        <p class="vh-summary">{{ r.summary }}</p>
      </div>
      <el-empty v-if="!loading && records.length === 0" description="暂无版本记录" :image-size="60" />
      <div class="vh-footer">
        <el-button v-if="hasMore" text type="primary" :loading="loadingMore" @click="loadMore">
          继续加载
        </el-button>
        <span v-else-if="records.length > 0" class="vh-end">没有更多了</span>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface VersionRecord {
  version: string
  date: string
  git: string
  summary: string
}

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const records = ref<VersionRecord[]>([])
const page = ref(0)
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = computed(() => records.value.length < total.value)

async function fetchPage(p: number) {
  const res = await fetch(`/api/version/history?page=${p}&per_page=10`)
  return res.json()
}

async function loadFirstPage() {
  loading.value = true
  try {
    const res = await fetchPage(1)
    records.value = res.list || []
    total.value = res.total || 0
    page.value = 1
  } catch { records.value = [] }
  finally { loading.value = false }
}

async function loadMore() {
  loadingMore.value = true
  try {
    const res = await fetchPage(page.value + 1)
    records.value.push(...(res.list || []))
    page.value++
  } catch { /* ignore */ }
  finally { loadingMore.value = false }
}
</script>

<style scoped>
.vh-list {
  max-height: 55vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.vh-item {
  background: #f8fafc;
  border: 1px solid #eef0f3;
  border-radius: 8px;
  padding: 10px 12px;
}
.vh-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.vh-version {
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
}
.vh-date {
  font-size: 12px;
  color: #9ca3af;
}
.vh-git {
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: Consolas, monospace;
  margin-left: auto;
}
.vh-summary {
  margin: 6px 0 0 0;
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.vh-footer {
  display: flex;
  justify-content: center;
  padding-top: 4px;
}
.vh-end {
  font-size: 12px;
  color: #9ca3af;
  padding: 6px 0;
}
</style>
