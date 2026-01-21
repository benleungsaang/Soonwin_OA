<template>
  <div class="display-container" @contextmenu="handleContextMenu" @selectstart="handleSelectStart">
    <el-page-header content="展示文件" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
    <el-divider></el-divider>

    <el-card class="display-card">
      <template #header>
        <div class="card-header">
          <span>展示文件</span>
        </div>
      </template>

      <!-- 文件列表 -->
      <div class="file-list">
        <div
          v-for="file in displayFiles"
          :key="file.id"
          class="file-item"
          @click="viewFile(file)"
        >
          <div class="file-info">
            <h3 class="file-title">{{ file.title }}</h3>
            <div class="file-meta">
              <span class="file-type">{{ file.file_type === 'image_group' ? '图片组' : 'PDF文件' }}</span>
              <span class="display-mode">{{ file.display_mode === 'waterfall' ? '瀑布流' : '分页' }}</span>
              <span class="created-time">{{ file.created_at }}</span>
            </div>
          </div>
          <!-- 删除按钮，只对管理员显示 -->
          <el-icon
            v-if="isCurrentUserAdmin"
            @click.stop="deleteFile(file, $event)"
            class="delete-btn"
            style="font-size: 25px;margin-right: 15px;"
          ><Delete /></el-icon>
        </div>
      </div>

      <!-- 加载更多按钮 -->
      <div class="load-more" v-if="hasMore">
        <el-button @click="loadMore" :loading="loading" type="primary">加载更多</el-button>
      </div>

      <!-- 无数据提示 -->
      <div class="no-data" v-if="displayFiles.length === 0 && !loading">
        <p>暂无展示文件</p>
      </div>
    </el-card>

    <!-- 文件预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="currentFile?.title"
      width="90%"
      top="5vh"
      class="preview-dialog"
      @contextmenu="handleContextMenu"
      @selectstart="handleSelectStart"
      :before-close="closePreview"
    >
      <div class="preview-content" v-if="currentFile">
        <!-- 瀑布流展示 -->
        <div v-if="currentFile.file_type === 'pdf' || currentFile.display_mode === 'waterfall'" class="waterfall-container">
          <div v-if="loadingImages" class="loading-images">
            <el-icon class="is-loading">
              <Loading />
            </el-icon>
          </div>
          <div v-else class="waterfall-grid" ref="waterfallRef">
            <div
              v-for="(img, index) in imageList"
              :key="index"
              class="waterfall-item"
              @contextmenu="handleContextMenu"
              @selectstart="handleSelectStart"
            >
              <img
                :src="img"
                :alt="`Image ${index + 1}`"
                @load="onImageLoad"
                @contextmenu="handleContextMenu"
                @selectstart="handleSelectStart"
                draggable="false"
              />
            </div>
          </div>
        </div>

        <!-- 分页展示PDF -->
        <div v-else-if="currentFile.file_type === 'pdf' && currentFile.display_mode === 'pagination'" class="pagination-container">
          <div class="pagination-controls">
            <el-button @click="prevPage" :disabled="currentPage <= 1" icon="ArrowLeft">上一页</el-button>
            <span class="page-info">第 {{ currentPage }} 页，共 {{ totalPages }} 页</span>
            <el-button @click="nextPage" :disabled="currentPage >= totalPages" icon="ArrowRight">下一页</el-button>
          </div>
          <div class="pdf-page">
            <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { ElMessage, ElButton, ElPageHeader, ElDivider, ElMessageBox } from 'element-plus';
import { Delete, Loading } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { useRouter } from 'vue-router';
import * as pdfjsLib from 'pdfjs-dist';
import 'pdfjs-dist/build/pdf.worker.mjs';

// 设置PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url).toString();

// 显示文件列表
const displayFiles = ref<any[]>([]);
const loading = ref(false);
const page = ref(1);
const perPage = ref(10);
const hasMore = ref(true);
const isCurrentUserAdmin = ref(false);

// 预览相关
const previewVisible = ref(false);
const currentFile = ref<any>(null);
const imageList = ref<string[]>([]);
const loadingImages = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const pdfDoc = ref<any>(null);

// 瀑布流相关
const waterfallRef = ref<HTMLElement | null>(null);
const pdfCanvas = ref<HTMLCanvasElement | null>(null);

// 路由
const router = useRouter();

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 检查用户是否为管理员
const checkAdminRole = () => {
  const token = localStorage.getItem('oa_token');
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      isCurrentUserAdmin.value = payload.user_role === 'admin';
    } catch (error) {
      console.error('解析用户信息失败:', error);
      isCurrentUserAdmin.value = false;
    }
  } else {
    isCurrentUserAdmin.value = false;
  }
};

// 登出
const logout = async () => {
  try {
    await ElMessage.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    // 清除本地存储的token
    localStorage.removeItem('oa_token');
    // 提示用户
    ElMessage.success('已退出登录');

    // 跳转到登录页
    router.push('/login');
  } catch (error) {
    // 用户取消登出，什么都不做
  }
};

// 获取展示文件列表
const fetchDisplayFiles = async (reset = false) => {
  if (reset) {
    page.value = 1;
    displayFiles.value = [];
    hasMore.value = true;
  }

  if (!hasMore.value && !reset) return;

  loading.value = true;

  try {
    const response = await request.get('/api/display-file/list', {
      params: {
        page: page.value,
        per_page: perPage.value
      }
    });

    if (response && response.files) {
      if (reset) {
        displayFiles.value = response.files;
      } else {
        displayFiles.value = [...displayFiles.value, ...response.files];
      }

      // 检查是否还有更多数据
      hasMore.value = response.pagination.page < response.pagination.pages;
      page.value += 1;
    }
  } catch (error) {
    console.error('获取展示文件列表失败:', error);
    ElMessage.error('获取展示文件列表失败');
  } finally {
    loading.value = false;
  }
};
// 加载更多
const loadMore = () => {
  fetchDisplayFiles();
};

// 查看文件
const viewFile = async (file: any) => {
  currentFile.value = file;
  previewVisible.value = true;

  if (file.file_type === 'image_group') {
    // 获取图片组
    await loadImageGroup(file.uuid);
  } else if (file.file_type === 'pdf') {
    // 获取PDF文件
    await loadPdfFile(file);
  }
};

// 加载图片组
const loadImageGroup = async (uuid: string) => {
  loadingImages.value = true;

  try {
    const response = await request.get(`/api/display-file/${uuid}/images`);
    if (response && response.images) {
      imageList.value = response.images;
    }
  } catch (error) {
    console.error('获取图片组失败:', error);
    ElMessage.error('获取图片组失败');
  } finally {
    loadingImages.value = false;
  }
};

// 加载PDF文件
const loadPdfFile = async (file: any) => {
  loadingImages.value = true;

  try {
    // PDF文件通过PDF.js直接渲染，不需要获取图片组
    await renderPdf(file.file_path);
  } catch (error) {
    console.error('加载PDF文件失败:', error);
    ElMessage.error('加载PDF文件失败');
  } finally {
    loadingImages.value = false;
  }
};

// 渲染PDF
const renderPdf = async (pdfPath: string) => {
  try {
    // 构建PDF URL
    const pdfUrl = `/api/${pdfPath}`;

    // 获取PDF文档
    const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
    pdfDoc.value = pdf;
    totalPages.value = pdf.numPages;

    // 渲染第一页
    if (currentFile.value.display_mode === 'pagination') {
      await renderPdfPage(pdf, 1);
    } else {
      // 瀑布流模式：渲染所有页面为图片
      await renderAllPdfPages(pdf);
    }
  } catch (error) {
    console.error('渲染PDF失败:', error);
    ElMessage.error('渲染PDF失败');
  }
};

// 渲染所有PDF页面
const renderAllPdfPages = async (pdf: any) => {
  try {
    imageList.value = [];
    const images = [];

    // 限制渲染页面数以提高性能
    const maxPages = Math.min(pdf.numPages, 20);

    for (let i = 1; i <= maxPages; i++) {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      if (!context) continue;

      const page = await pdf.getPage(i);
      const scale = 1.5;
      const viewport = page.getViewport({ scale });

      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport
      };

      await page.render(renderContext).promise;

      // 将canvas转换为图片
      const imgSrc = canvas.toDataURL('image/png');
      images.push(imgSrc);
    }

    imageList.value = images;
  } catch (error) {
    console.error('渲染所有PDF页面失败:', error);
    ElMessage.error('渲染PDF页面失败');
  }
};

// 渲染PDF页面
const renderPdfPage = async (pdf: any, pageNumber: number) => {
  if (!pdfCanvas.value) return;

  try {
    const page = await pdf.getPage(pageNumber);
    const scale = 1.5;
    const viewport = page.getViewport({ scale });

    const canvas = pdfCanvas.value;
    const context = canvas.getContext('2d');
    if (!context) return;

    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
      canvasContext: context,
      viewport: viewport
    };

    await page.render(renderContext).promise;
  } catch (error) {
    console.error('渲染PDF页面失败:', error);
    ElMessage.error('渲染PDF页面失败');
  }
};

// 上一页
const prevPage = async () => {
  if (currentPage.value > 1 && pdfDoc.value) {
    currentPage.value--;
    await renderPdfPage(pdfDoc.value, currentPage.value);
  }
};

// 下一页
const nextPage = async () => {
  if (currentPage.value < totalPages.value && pdfDoc.value) {
    currentPage.value++;
    await renderPdfPage(pdfDoc.value, currentPage.value);
  }
};

// 图片加载完成
const onImageLoad = () => {
  // 瀑布流布局调整
  nextTick(() => {
    if (currentFile.value && currentFile.value.display_mode === 'waterfall') {
      applyWaterfallLayout();
    }
  });
};

// 应用瀑布流布局
const applyWaterfallLayout = () => {
  if (!waterfallRef.value) return;

  const container = waterfallRef.value;
  const items = container.querySelectorAll('.waterfall-item');

  // 移动端使用单列，桌面端使用多列
  const isMobile = window.innerWidth < 768;
  const columnCount = isMobile ? 1 : 2;

  // 重置高度
  const columns = Array(columnCount).fill(0).map(() => 0);

  // 清除之前的定位
  items.forEach((item: Element) => {
    (item as HTMLElement).style.position = 'static';
    (item as HTMLElement).style.top = 'auto';
    (item as HTMLElement).style.left = 'auto';
    (item as HTMLElement).style.width = `${100 / columnCount}%`;
  });

  // 重新应用瀑布流布局
  items.forEach((item: Element) => {
    const img = item.querySelector('img');
    if (img) {
      // 使用自然尺寸计算高度
      const imgHeight = img.naturalHeight && img.naturalWidth ?
        (img.naturalHeight * img.offsetWidth) / img.naturalWidth : 200;

      // 找到最短的列
      const minHeight = Math.min(...columns);
      const minIndex = columns.indexOf(minHeight);

      // 设置项目位置
      (item as HTMLElement).style.position = 'absolute';
      (item as HTMLElement).style.top = `${columns[minIndex]}px`;
      (item as HTMLElement).style.left = `${(minIndex * 100) / columnCount}%`;
      (item as HTMLElement).style.width = `${100 / columnCount}%`;

      // 更新列高度
      columns[minIndex] += imgHeight + 10; // 添加间距
    }
  });

  // 设置容器高度
  container.style.height = `${Math.max(...columns) + 20}px`;
};

// 删除文件
const deleteFile = async (file: any, event: Event) => {
  event.stopPropagation(); // 阻止事件冒泡，避免触发查看文件

  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${file.title}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 发送删除请求
    await request.delete(`/api/display-file/${file.id}`);

    // 从本地列表中移除该文件
    const index = displayFiles.value.findIndex(f => f.id === file.id);
    if (index !== -1) {
      displayFiles.value.splice(index, 1);
    }

    ElMessage.success('文件删除成功');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件失败:', error);
      ElMessage.error('删除文件失败');
    }
  }
};





// 关闭预览
const closePreview = (done: () => void) => {
  currentFile.value = null;
  imageList.value = [];
  currentPage.value = 1;
  totalPages.value = 1;
  pdfDoc.value = null;
  done();
};

// 禁用右键菜单
const handleContextMenu = (e: Event) => {
  e.preventDefault();
  return false;
};

// 禁用选择
const handleSelectStart = (e: Event) => {
  e.preventDefault();
  return false;
};

// 初始化
onMounted(() => {
  checkAdminRole(); // 检查用户是否为管理员
  fetchDisplayFiles(true);

  // 监听窗口大小变化，重新应用瀑布流布局
  window.addEventListener('resize', () => {
    if (currentFile.value && (currentFile.value.file_type === 'image_group' ||
        (currentFile.value.file_type === 'pdf' && currentFile.value.display_mode === 'waterfall'))) {
      nextTick(() => {
        applyWaterfallLayout();
      });
    }
  });
});</script>

<style scoped>
.display-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.display-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-list {
  margin-top: 20px;
}

.file-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}

.file-info {
  flex: 1;
}

.delete-btn {
  margin-left: 10px;
  flex-shrink: 0;
}

.file-title {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.file-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  font-size: 12px;
  color: #909399;
}

.file-type, .display-mode, .created-time {
  display: inline-block;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}

.no-data {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.preview-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.preview-content {
  padding: 20px;
  max-height: 80vh;
  overflow-y: auto;
}

.waterfall-container {
  position: relative;
  width: 100%;
}

.waterfall-grid {
  position: relative;
  width: 100%;
}

.waterfall-item {
  position: absolute;
  padding: 5px;
  box-sizing: border-box;
}

.waterfall-item img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.loading-images {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.pagination-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 0 20px;
}

.page-info {
  color: #606266;
  font-size: 14px;
}

.pdf-page {
  display: flex;
  justify-content: center;
  width: 100%;
}

.pdf-canvas {
  max-width: 100%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .display-container {
    padding: 10px;
  }

  .file-meta {
    flex-direction: column;
    gap: 5px;
  }

  .pagination-controls {
    flex-direction: column;
    gap: 10px;
  }
}
</style>