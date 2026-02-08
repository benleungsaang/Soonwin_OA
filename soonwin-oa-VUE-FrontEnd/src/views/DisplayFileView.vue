<template>
  <div class="display-container" @contextmenu="handleContextMenu" @selectstart="handleSelectStart">
    <CommonHeader title="展示文件" />

    <el-card class="display-card">
      <template #header>
        <div class="card-header">
          <span style="font-size: 25px;">展示文件</span>
          <el-icon
            v-if="isCurrentUserAdmin && !isMobile"
            class="upload-icon"
            @click.stop="goToDisplayFileUpload"
          ><FolderOpened /></el-icon>
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
            <h3 class="file-title">文件标题：{{ file.title }}</h3>
            <div class="file-meta">
              <span class="file-type">{{ file.file_type === 'image_group' ? '图片' : 'PDF' }}</span>
              <span class="created-time">{{ file.created_at }}</span>
              <span class="created-time">{{ file.page_count }}p</span>
            </div>
          </div>
          <span
            class="file-type-icon"
            :class="{
              'img-bg': file.file_type === 'image_group',
              'pdf-bg': file.file_type !== 'image_group'
            }"
          >{{ file.file_type === 'image_group' ? 'IMG' : 'PDF' }}</span>
          <el-icon
            v-if="isCurrentUserAdmin"
            @click.stop="editFile(file, $event)"
            class="edit-btn"
            style="font-size: 28px;margin-right: 10px;"
          ><Edit /></el-icon>
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

    <!-- 编辑文件对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑文件" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" placeholder="请输入文件标题"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveEdit">保存</el-button>
        </span>
      </template>
    </el-dialog>

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
      <template #header>
        <div class="preview-header">
          <span>{{ currentFile?.title }}</span>
          <!-- 展示模式切换switch -->
          <div class="display-mode-controls" v-if="currentFile && (currentFile.file_type === 'image_group' || currentFile.file_type === 'pdf')">
            <el-switch
              v-model="displayMode"
              class="ml-2"
              width="80"
              size="large"
              style="--el-switch-on-color: #2c62b7; --el-switch-off-color: #056500;"
              inline-prompt
              :active-value="'pagination'"
              :inactive-value="'waterfall'"
              active-text="分页"
              inactive-text="瀑布流"
            />
          </div>
        </div>
      </template>
      <div class="preview-content" v-if="currentFile">
        <!-- 瀑布流展示 -->
        <div v-if="displayMode === 'waterfall'" class="waterfall-container">
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
              :data-page-index="index + 1"
              @contextmenu="handleContextMenu"
              @selectstart="handleSelectStart"
            >
              <img
                v-if="img"
                :src="normalizeImagePath(img)"
                :alt="`Image ${index + 1}`"
                @load="onImageLoad"
                @contextmenu="handleContextMenu"
                @selectstart="handleSelectStart"
                draggable="false"
              />
              <div
                v-else-if="loadingPages.has(index + 1)"
                class="placeholder-item loading"
                @contextmenu="handleContextMenu"
                @selectstart="handleSelectStart"
              >
                <div class="placeholder-content">
                  <el-icon class="loading-icon">
                    <Loading />
                  </el-icon>
                  <p v-if="currentFile.file_type === 'pdf'">正在加载第 {{ index + 1 }} 页...</p>
                  <p v-else>正在加载第 {{ index + 1 }} 张图片...</p>
                </div>
              </div>
              <div
                v-else
                class="placeholder-item pending"
                @contextmenu="handleContextMenu"
                @selectstart="handleSelectStart"
              >
                <div class="placeholder-content">
                  <el-icon class="pending-icon">
                    <Document />
                  </el-icon>
                  <p v-if="currentFile.file_type === 'pdf'">第 {{ index + 1 }} 页 (待加载)</p>
                  <p v-else>第 {{ index + 1 }} 张图片 (待加载)</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页展示 -->
        <div v-else-if="displayMode === 'pagination'" class="pagination-container">
          <div class="pagination-controls">
            <el-button
              @click="goToPrevPage"
              :disabled="currentPage <= 1 || totalPages === 0"
              :icon="ArrowLeft"
            >上一张</el-button>
            <div class="page-info">
              {{ currentPage }} / {{ totalPages }}
            </div>
            <el-button
              @click="goToNextPage"
              :disabled="currentPage >= totalPages || totalPages === 0"
              :icon="ArrowRight"
              icon-position="right"
            >下一张</el-button>
          </div>

          <div class="pdf-page-container" ref="pdfPageContainerRef" @click="handlePaginationClick" @mousemove="updateMouseCursor" @mouseenter="showNavArrows = true" @mouseleave="showNavArrows = false">
            <!-- 左箭头 -->
            <div class="nav-arrow left-arrow" v-show="showNavArrows && currentPage > 1" @click.stop="goToPrevPage">
              <el-icon :size="32"><ArrowLeft /></el-icon>
            </div>

            <div class="pdf-page" :class="{ 'with-nav-arrows': showNavArrows }">
              <img
                v-if="imageList[currentPage - 1]"
                :src="normalizeImagePath(imageList[currentPage - 1])"
                :alt="`Page ${currentPage}`"
                style="max-width: 100%; max-height: 70vh; object-fit: contain;"
                @contextmenu="handleContextMenu"
                @selectstart="handleSelectStart"
                draggable="false"
              />
              <div v-else-if="currentPage > 0 && totalPages > 0" class="placeholder-item pending" style="width: 100%; height: 70vh; display: flex; align-items: center; justify-content: center;">
                <div class="placeholder-content">
                  <el-icon class="pending-icon">
                    <Document />
                  </el-icon>
                  <p>正在加载第 {{ currentPage }} 张图片...</p>
                </div>
              </div>
            </div>

            <!-- 右箭头 -->
            <div class="nav-arrow right-arrow" v-show="showNavArrows && currentPage < totalPages" @click.stop="goToNextPage">
              <el-icon :size="32"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, Loading, Document, ArrowLeft, ArrowRight, FolderOpened, Edit } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { useRouter } from 'vue-router';
import { initializePdfDocument, getPdfPage, renderPdfPage } from '@/utils/pdfUtils';
import { DisplayFile } from '@/types';
import CommonHeader from '@/components/CommonHeader.vue';
import { getCurrentUserRole } from '@/utils/authUtils';

// 路由相关
const router = useRouter();

// 文件列表相关
const displayFiles = ref<DisplayFile[]>([]);
const loading = ref(false);
const page = ref(1);
const perPage = ref(10);
const hasMore = ref(true);
const isCurrentUserAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'admin';
});

// 预览相关
const previewVisible = ref(false);
const currentFile = ref<any>(null);
const imageList = ref<string[]>([]);
const loadingImages = ref(false);
let pdfDoc: any = null;
const currentPage = ref(1);
const totalPages = ref(0);
const renderedPages = ref<Set<number>>(new Set());
const maxRenderedPage = ref(1);
const loadingPages = ref<Set<number>>(new Set());
const renderQueue = ref<number[]>([]);
const isRendering = ref(false);
const showNavArrows = ref(false);
const displayMode = ref<'waterfall' | 'pagination'>('waterfall');

// 编辑文件相关
const editDialogVisible = ref(false);
const editingFile = ref<any>(null);
const editForm = ref({ title: '' });

// 布局相关
const waterfallRef = ref<HTMLElement | null>(null);
const pdfPageContainerRef = ref<HTMLElement | null>(null);
const isMobile = ref(false);

const checkDevice = () => {
  isMobile.value = window.innerWidth <= 768;
};

// 检查管理员权限
const checkAdminRole = () => {
  const token = localStorage.getItem('oa_token');
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
  
    } catch (error) {
      console.error('解析用户信息失败:', error);
    }
  }
};

// 登出
const logout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    localStorage.removeItem('oa_token');
    ElMessage.success('已退出登录');
    router.push('/login');
  } catch (error) {
    // 用户取消登出
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
    const token = localStorage.getItem('oa_token');
    if (!token) {
      console.error('缺少认证令牌，请先登录');
      ElMessage.error('请先登录系统');
      return;
    }

    const response = await request.get('/api/display-file/list', {
      params: { page: page.value, per_page: perPage.value }
    });

    if (response && response.files && Array.isArray(response.files)) {
      displayFiles.value = reset ? [...response.files] : [...displayFiles.value, ...response.files];

      if (response.pagination) {
        hasMore.value = response.pagination.page < response.pagination.pages;
        if (hasMore.value) page.value += 1;
      } else {
        hasMore.value = false;
      }
    } else {
      hasMore.value = false;
    }
  } catch (error) {
    console.error('获取展示文件列表失败:', error);
    if (error && typeof error === 'object' && error.message && error.message.includes('401')) {
      ElMessage.error('未认证，请重新登录');
    } else {
      ElMessage.error('获取展示文件列表失败');
    }
  } finally {
    loading.value = false;
  }
};

// 加载更多
const loadMore = () => fetchDisplayFiles();

// 查看文件
const viewFile = async (file: any) => {
  currentFile.value = file;
  previewVisible.value = true;

  if (file.file_type === 'image_group') {
    await loadImageGroup(file.uuid);
    if (displayMode.value === 'pagination') {
      currentPage.value = 1;
      if (imageList.value.length > 0 && !imageList.value[0] && !loadingPages.value.has(1)) {
        addToLoadImageQueue(1);
      }
    }
  } else if (file.file_type === 'pdf') {
    await loadPdfFile(file);
    currentPage.value = 1;
  }
};

// 加载图片组
const loadImageGroup = async (uuid: string) => {
  loadingImages.value = true;

  try {
    const response = await request.get(`/api/display-file/${uuid}/images`);
    if (response && response.images && Array.isArray(response.images)) {
      const originalImageUrls = response.images;
      imageList.value = Array(originalImageUrls.length).fill(null);
      (window as any).__originalImageUrls = originalImageUrls;
      totalPages.value = originalImageUrls.length;

      if (currentFile.value && currentFile.value.page_count === null) {
        await updateFilePageCount(currentFile.value.id, totalPages.value);
      }

      startScrollListener();
      nextTick(() => {
        applyWaterfallLayout();
        setTimeout(() => checkAndLoadVisibleImages(), 100);
      });
    } else {
      ElMessage.error('获取的图片数据格式不正确');
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
    await initializePdf(file.file_path);
  } catch (error) {
    console.error('加载PDF文件失败:', error);
    ElMessage.error('加载PDF文件失败');
  } finally {
    loadingImages.value = false;
  }
};

// 初始化PDF文档
const initializePdf = async (pdfPath: string) => {
  const fileName = pdfPath.split('/').pop();
  const pdfUrl = `/api/display-file/file/${fileName}`;

  try {
    const doc = await initializePdfDocument(pdfUrl, {
      cMapPacked: true,
      maxCanvasPixels: 10000 * 10000,
    });

    pdfDoc = doc;
    totalPages.value = doc.numPages;
    renderQueue.value = [];

    if (totalPages.value > 0) {
      renderQueue.value = [1];
      renderPdfPageDirectly(1);
    }
  } catch (error) {
    console.error('初始化PDF失败:', error);
    ElMessage.error('初始化PDF失败');
  }
};

// 更新页面加载状态
const updatePageLoadStatus = (pageNumber: number, loaded: boolean) => {
  if (loaded) {
    renderedPages.value.add(pageNumber);
    if (pageNumber > maxRenderedPage.value) maxRenderedPage.value = pageNumber;
  } else {
    renderedPages.value.delete(pageNumber);
    loadingPages.value.add(pageNumber);
  }
};

// 直接渲染PDF页面
const renderPdfPageDirectly = async (pageNumber: number) => {
  if (!pdfDoc || !totalPages.value || pageNumber < 1 || pageNumber > totalPages.value) {
    console.error('PDF文档未正确初始化或页面号超出范围');
    return;
  }

  try {
    const page = await getPdfPage(pdfDoc, pageNumber);
    if (!page) {
      console.error(`无法获取PDF第${pageNumber}页`);
      return;
    }

    const container = pdfPageContainerRef.value;
    if (!container) {
      console.error('未找到PDF页面容器');
      return;
    }

    let canvas = container.querySelector(`#pdf-canvas-${pageNumber}`) as HTMLCanvasElement;
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = `pdf-canvas-${pageNumber}`;
      canvas.className = 'pdf-canvas';
      container.appendChild(canvas);
    }

    await renderPdfPage(page, canvas, window.devicePixelRatio || 1);

    if (displayMode.value === 'waterfall') {
      canvas.style.maxWidth = '100%';
      canvas.style.height = 'auto';
    }

    updatePageLoadStatus(pageNumber, true);
    console.log(`PDF第${pageNumber}页渲染完成`);
  } catch (error) {
    console.error(`渲染PDF第${pageNumber}页失败:`, error);
    ElMessage.error(`渲染PDF第${pageNumber}页失败`);
  }
};

// 将页面添加到渲染队列
const addToRenderQueue = (pageNumber: number) => {
  if (!renderQueue.value.includes(pageNumber) &&
      pageNumber >= 1 &&
      pageNumber <= totalPages.value &&
      !imageList.value[pageNumber - 1] &&
      !loadingPages.value.has(pageNumber)) {
    renderQueue.value.push(pageNumber);
    loadingPages.value.add(pageNumber);
    processRenderQueue();
  }
};

// 处理渲染队列
const processRenderQueue = async () => {
  if (isRendering.value || renderQueue.value.length === 0 || !pdfDoc) return;

  isRendering.value = true;

  while (renderQueue.value.length > 0) {
    const pageNumber = renderQueue.value.shift();
    if (pageNumber && !imageList.value[pageNumber - 1]) {
      await renderPdfPageDirectly(pageNumber);
    }
  }

  isRendering.value = false;
};

// 启动滚动监听器
const startScrollListener = () => {
  stopScrollListener();

  nextTick(() => {
    const previewContent = document.querySelector('.preview-content');
    if (previewContent) previewContent.addEventListener('scroll', handleScroll);
  });
};

// 停止滚动监听器
const stopScrollListener = () => {
  const previewContent = document.querySelector('.preview-content');
  if (previewContent) previewContent.removeEventListener('scroll', handleScroll);
};

// 滚动处理函数
const handleScroll = async () => {
  if (!previewVisible.value) return;

  const previewContent = document.querySelector('.preview-content') as HTMLElement;
  if (!previewContent) return;

  if (currentFile.value?.file_type === 'pdf' && pdfDoc) {
    const scrollTop = previewContent.scrollTop;
    const clientHeight = previewContent.clientHeight;
    const scrollHeight = previewContent.scrollHeight;
    const scrollBottom = scrollTop + clientHeight;
    const threshold = 100;

    const loadedImageElements = document.querySelectorAll('.waterfall-item img');
    let maxPageIndex = 0;

    loadedImageElements.forEach(item => {
      const parentItem = item.closest('.waterfall-item');
      if (parentItem) {
        const pageIndex = parseInt(parentItem.getAttribute('data-page-index') || '0');
        const rect = parentItem.getBoundingClientRect();
        const containerRect = previewContent.getBoundingClientRect();
        const elementTop = rect.top - containerRect.top + scrollTop;
        const elementBottom = rect.bottom - containerRect.top + scrollTop;

        if (elementTop <= scrollBottom && elementBottom >= scrollTop && pageIndex > maxPageIndex) {
          maxPageIndex = pageIndex;
        }
      }
    });

    if (maxPageIndex > 0) {
      const nextPageIndex = maxPageIndex + 1;
      if (nextPageIndex <= totalPages.value && !imageList.value[nextPageIndex - 1] && !loadingPages.value.has(nextPageIndex)) {
        addToRenderQueue(nextPageIndex);
      }
    }

    if (scrollTop + clientHeight >= scrollHeight - threshold) {
      let nextPage = -1;
      for (let i = maxRenderedPage.value + 1; i <= totalPages.value; i++) {
        if (!renderedPages.value.has(i)) {
          nextPage = i;
          break;
        }
      }

      if (nextPage !== -1) {
        addToRenderQueue(nextPage);
        preloadNextPage();
      }
    }
  } else if (currentFile.value?.file_type === 'image_group') {
    checkAndLoadVisibleImages();
  }
};

// 预加载下一页
const preloadNextPage = async () => {
  if (maxRenderedPage.value < totalPages.value) {
    const nextPage = maxRenderedPage.value + 1;
    if (!renderedPages.value.has(nextPage)) addToRenderQueue(nextPage);
  }
};

// 检查并加载视口中的图片
const checkAndLoadVisibleImages = () => {
  if (!previewVisible.value || currentFile.value?.file_type !== 'image_group') return;

  const previewContent = document.querySelector('.preview-content') as HTMLElement;
  if (!previewContent) return;

  const scrollTop = previewContent.scrollTop;
  const clientHeight = previewContent.clientHeight;
  const scrollBottom = scrollTop + clientHeight;

  const waterfallItems = document.querySelectorAll('.waterfall-item');
  waterfallItems.forEach(item => {
    const imgIndexStr = item.getAttribute('data-page-index');
    if (!imgIndexStr) return;

    const imgIndex = parseInt(imgIndexStr);
    if (imageList.value[imgIndex - 1] || loadingPages.value.has(imgIndex)) return;

    const rect = item.getBoundingClientRect();
    const containerRect = previewContent.getBoundingClientRect();
    const elementTop = rect.top - containerRect.top + scrollTop;
    const elementBottom = rect.bottom - containerRect.top + scrollTop;

    if (elementTop <= scrollBottom && elementBottom >= scrollTop) {
      addToLoadImageQueue(imgIndex);
    }
  });
};

// 将图片添加到加载队列
const addToLoadImageQueue = (imgIndex: number) => {
  if (!loadingPages.value.has(imgIndex) &&
      imgIndex >= 1 &&
      imgIndex <= imageList.value.length &&
      !imageList.value[imgIndex - 1]) {
    loadingPages.value.add(imgIndex);
    loadImageAtIndex(imgIndex);
  }
};

// 加载指定索引的图片
const loadImageAtIndex = async (imgIndex: number) => {
  try {
    const originalImageUrls = (window as any).__originalImageUrls;
    if (!originalImageUrls || imgIndex > originalImageUrls.length) {
      console.error(`图片索引 ${imgIndex} 超出范围`);
      return;
    }

    const imgSrc = originalImageUrls[imgIndex - 1];
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    if (context) {
      const img = new Image();
      img.crossOrigin = "anonymous";

      const loadImagePromise = new Promise((resolve, reject) => {
        img.onload = () => resolve(null);
        img.onerror = () => reject(null);
      });

      img.src = imgSrc;
      await loadImagePromise;

      canvas.width = img.width;
      canvas.height = img.height;
      context.drawImage(img, 0, 0);

      // 添加页码水印
      context.fillStyle = 'rgba(0, 0, 0, 0.7)';
      context.font = '16px Arial';
      context.textAlign = 'right';

      const pageNumText = `${imgIndex} / ${totalPages.value}`;
      const textMetrics = context.measureText(pageNumText);
      const padding = 8;
      const x = canvas.width - padding;
      const y = canvas.height - padding;

      context.fillRect(
        x - textMetrics.width - padding,
        y - 16 - padding/2,
        textMetrics.width + padding * 2,
        16 + padding
      );

      context.fillStyle = 'white';
      context.fillText(pageNumText, x, y);

      const imgWithPageNum = canvas.toDataURL('image/png');
      const updatedImageList = [...imageList.value];
      updatedImageList[imgIndex - 1] = imgWithPageNum;
      imageList.value = updatedImageList;
    } else {
      const updatedImageList = [...imageList.value];
      updatedImageList[imgIndex - 1] = imgSrc;
      imageList.value = updatedImageList;
    }
  } catch (error) {
    console.error(`加载第${imgIndex}张图片失败:`, error);
    loadingPages.value.delete(imgIndex);

    try {
      const originalImageUrls = (window as any).__originalImageUrls;
      if (originalImageUrls && imgIndex <= originalImageUrls.length) {
        const imgSrc = originalImageUrls[imgIndex - 1];
        const updatedImageList = [...imageList.value];
        updatedImageList[imgIndex - 1] = imgSrc;
        imageList.value = updatedImageList;
      }
    } catch (e) {
      console.error(`加载原始图片失败:`, e);
    }
  } finally {
    loadingPages.value.delete(imgIndex);
  }
};

// 应用瀑布流布局
const applyWaterfallLayout = () => {
  if (!waterfallRef.value) return;

  const container = waterfallRef.value;
  const items = container.querySelectorAll('.waterfall-item');

  items.forEach((item: Element) => {
    (item as HTMLElement).style.position = 'static';
    (item as HTMLElement).style.top = 'auto';
    (item as HTMLElement).style.left = 'auto';
    (item as HTMLElement).style.width = '100%';
    (item as HTMLElement).style.marginBottom = '10px';
  });

  container.style.height = 'auto';
};

// 确保图片路径正确
const normalizeImagePath = (path: string): string => {
  if (!path) return '';

  if (path.startsWith('data:image/')) {
    return path;
  }

  if (currentFile.value && currentFile.value.file_type === 'pdf') {
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    if (path.startsWith('/api/display-file/file/')) return path;
    if (path.startsWith('/display-file/file/')) return `/api${path}`;
    return `/api/display-file/file/${path}`;
  } else {
    if (!path.startsWith('/api/')) {
      return path.startsWith('/') ? `/api${path}` : `/api/${path}`;
    }
  }

  return path;
};

// 图片加载完成
const onImageLoad = () => {
  nextTick(() => {
    if (currentFile.value && (currentFile.value.file_type === 'image_group' || currentFile.value.file_type === 'pdf')) {
      applyWaterfallLayout();
    }
  });
};

// 删除文件
const deleteFile = async (file: any, event: Event) => {
  event.stopPropagation();

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

    await request.delete(`/api/display-file/${file.id}`);

    const index = displayFiles.value.findIndex(f => f.id === file.id);
    if (index !== -1) displayFiles.value.splice(index, 1);

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
  pdfDoc = null;
  currentPage.value = 1;
  totalPages.value = 0;
  renderedPages.value.clear();
  maxRenderedPage.value = 1;
  renderQueue.value = [];
  isRendering.value = false;
  stopScrollListener();
  (window as any).__originalImageUrls = null;

  done();
};

// 禁用右键菜单和选择
const handleContextMenu = (e: Event) => e.preventDefault();
const handleSelectStart = (e: Event) => e.preventDefault();

// 编辑文件
const editFile = async (file: any, event: Event) => {
  event.stopPropagation();
  editingFile.value = { ...file };
  editForm.value = { title: file.title };
  editDialogVisible.value = true;
};

// 保存编辑
const saveEdit = async () => {
  try {
    await request.put(`/api/display-file/${editingFile.value.id}`, {
      title: editForm.value.title
    });

    const index = displayFiles.value.findIndex(f => f.id === editingFile.value.id);
    if (index !== -1) displayFiles.value[index].title = editForm.value.title;

    ElMessage.success('文件信息更新成功');
    editDialogVisible.value = false;
  } catch (error) {
    console.error('更新文件信息失败:', error);
    ElMessage.error('文件信息更新失败');
  }
};

// 更新文件页数
const updateFilePageCount = async (fileId: number, pageCount: number) => {
  try {
    await request.put(`/api/display-file/${fileId}/page-count`, {
      page_count: pageCount
    });

    console.log(`文件 ${fileId} 的页数已更新为 ${pageCount}`);
    if (currentFile.value && currentFile.value.id === fileId) {
      currentFile.value.page_count = pageCount;
    }
  } catch (error) {
    console.error('更新页数失败:', error);
  }
};

// 更新鼠标指针效果
const updateMouseCursor = (event: MouseEvent) => {
  if (!currentFile.value || displayMode.value !== 'pagination') return;

  const container = event.currentTarget as HTMLElement;
  const rect = container.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const width = rect.width;

  const pageElement = container.querySelector('.pdf-page') as HTMLElement;
  if (!pageElement) return;

  if (x < width * 0.5) {
    pageElement.classList.add('left-half');
    pageElement.classList.remove('right-half');
  } else {
    pageElement.classList.add('right-half');
    pageElement.classList.remove('left-half');
  }
};

// 处理分页模式下的点击事件
const handlePaginationClick = (event: MouseEvent) => {
  if (!currentFile.value || displayMode.value !== 'pagination') return;

  const container = event.currentTarget as HTMLElement;
  const rect = container.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const width = rect.width;

  if (x < width * 0.5) {
    goToPrevPage();
  } else {
    goToNextPage();
  }
};

// 跳转到上一页
const goToPrevPage = () => {
  if (currentFile.value?.file_type === 'image_group' && displayMode.value === 'pagination') {
    if (currentPage.value > 1) {
      currentPage.value--;
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToLoadImageQueue(currentPage.value);
      }
      const prevPage = currentPage.value - 1;
      if (prevPage > 0 && !imageList.value[prevPage - 1] && !loadingPages.value.has(prevPage)) {
        addToLoadImageQueue(prevPage);
      }
    }
  } else if (currentFile.value?.file_type === 'pdf' && displayMode.value === 'pagination') {
    if (currentPage.value > 1) {
      currentPage.value--;
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToRenderQueue(currentPage.value);
      }
      const prevPage = currentPage.value - 1;
      if (prevPage > 0 && !imageList.value[prevPage - 1] && !loadingPages.value.has(prevPage)) {
        addToRenderQueue(prevPage);
      }
    }
  }
};

// 跳转到下一页
const goToNextPage = () => {
  if (currentFile.value?.file_type === 'image_group' && displayMode.value === 'pagination') {
    if (currentPage.value < totalPages.value) {
      currentPage.value++;
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToLoadImageQueue(currentPage.value);
      }
      const nextPage = currentPage.value + 1;
      if (nextPage <= totalPages.value && !imageList.value[nextPage - 1] && !loadingPages.value.has(nextPage)) {
        addToLoadImageQueue(nextPage);
      }
    }
  } else if (currentFile.value?.file_type === 'pdf' && displayMode.value === 'pagination') {
    if (currentPage.value < totalPages.value) {
      currentPage.value++;
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToRenderQueue(currentPage.value);
      }
      const nextPage = currentPage.value + 1;
      if (nextPage <= totalPages.value && !imageList.value[nextPage - 1] && !loadingPages.value.has(nextPage)) {
        addToRenderQueue(nextPage);
      }
    }
  }
};

// 跳转上传展示文件页面
const goToDisplayFileUpload = () => {
  if (!isCurrentUserAdmin.value) {
    ElMessage.error('您没有权限访问上传展示文件页面！');
    return;
  }
  router.push('/display-file-upload');
};

// 初始化
onMounted(() => {
  const token = localStorage.getItem('oa_token');
  if (!token) {
    console.error('缺少认证令牌，重定向到登录页');
    ElMessage.error('请先登录系统');
    router.push('/login');
    return;
  }

  checkAdminRole();
  fetchDisplayFiles(true);

  checkDevice();
  window.addEventListener('resize', checkDevice);

  window.addEventListener('resize', () => {
    if (currentFile.value && (currentFile.value.file_type === 'image_group' || currentFile.value.file_type === 'pdf')) {
      nextTick(() => applyWaterfallLayout());
    }
  });
});
</script>

<style scoped>
.upload-icon {
  font-size: 25px;
  margin-bottom: 10px;
  cursor: pointer;
}

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
  background-color: rgba(0, 0, 0, 0.1);
  padding: 10px 25px;
  border-radius: 5px;
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

.file-type-icon {
  margin-right: 20px;
  flex-shrink: 0;
  color: white;
  padding: 5px 10px;
  border-radius: 6px;
}

.img-bg {
  background-color: #143474;
}

.pdf-bg {
  background-color: #b13c30;
}

.delete-btn {
  margin-left: 10px;
  flex-shrink: 0;
}

.file-title {
  margin: 0 0 10px 15px;
  font-size: 16px;
  font-weight: 800;
  color: #303133;
}

.file-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  font-size: 12px;
  color: #909399;
  margin-left: 30px;
}

.file-type, .display-mode, .created-time {
  display: inline-block;
  background-color: rgba(0, 0, 0, 0.3);
  color: white;
  padding: 1px 8px;
  border-radius: 2px;
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
  position: relative;
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

.placeholder-item {
  width: 100%;
  min-height: 300px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
  text-align: center;
}

.placeholder-item.loading {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.placeholder-item.pending {
  background: #f8f9fa;
  border: 2px dashed #dcdfe6;
}

.placeholder-content {
  color: #909399;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.placeholder-content .loading-icon {
  font-size: 24px;
  margin-bottom: 10px;
  color: #409eff;
  animation: spin 1s linear infinite;
}

.placeholder-content .pending-icon {
  font-size: 24px;
  margin-bottom: 10px;
  color: #909399;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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
  flex-wrap: nowrap;
  overflow-x: auto;
  white-space: nowrap;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.page-info {
  color: #606266;
  font-size: 14px;
}

.pdf-page {
  display: flex;
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
}

.pdf-page img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.pdf-canvas {
  max-width: 100%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.preview-header > span {
  flex: 1;
  text-align: left;
  font-weight: 600;
  font-size: 4vh;
  background-color: #e1e2e4;
  padding: 1vh 5vh;
  border-radius: 5px;
}

.display-mode-controls {
  flex-shrink: 0;
  margin-left: 20px;
}

.pdf-page-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf-page-container .pdf-page.left-half {
  cursor: grab;
}

.pdf-page-container .pdf-page.right-half {
  cursor: grab;
}

.nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border-radius: 50%;
  padding: 10px;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.nav-arrow:hover {
  background: rgba(0, 0, 0, 0.7);
}

.left-arrow {
  left: 20px;
}

.right-arrow {
  right: 20px;
}

.pdf-page.with-nav-arrows {
  margin: 0 0;
}

/* 移动端适配优化 */
@media (max-width: 768px) {
  .display-container {
    padding: 10px;
  }

  .file-item {
    padding: 12px;
    margin-bottom: 8px;
    flex-direction: row;
    align-items: center;
    gap: 8px;
  }

  .file-info {
    width: 100%;
  }

  .file-title {
    font-size: 15px;
    margin: 0 0 8px 0;
  }

  .file-meta {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 11px;
    width: 100%;
    justify-content: flex-start;
    margin-left: 0;
  }

  .display-card {
    margin: 5px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 15px;
  }

  .pagination-controls {
    gap: 10px;
    width: 100%;
    box-sizing: border-box;
  }

  .display-mode-controls {
    margin-bottom: 0;
    margin-left: 10px;
  }

  .preview-dialog .el-dialog {
    margin-top: 5px !important;
    margin-bottom: 5px !important;
    width: 95% !important;
    max-height: 98vh;
  }

  .waterfall-item {
    padding: 3px;
  }

  .waterfall-item img {
    border-radius: 2px;
  }

  .load-more .el-button {
    width: 100%;
    padding: 10px;
  }

  .no-data {
    padding: 20px 0;
  }

  .delete-btn {
    font-size: 20px;
    margin-right: 10px;
  }

  .preview-content {
    padding: 10px;
    max-height: 85vh;
    overflow-y: auto;
  }

  .waterfall-container {
    max-height: 80vh;
  }

  .preview-header > span {
    font-size: 2vh;
    padding: 0.8vh 2vh;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  /* 移动端预览优化 */
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .display-mode-controls {
    width: 100%;
    margin-left: 0;
  }

  .pdf-page-container {
    width: 100%;
  }

  .nav-arrow {
    padding: 8px;
  }

  .nav-arrow el-icon {
    font-size: 24px !important;
  }

  .left-arrow {
    left: 10px;
  }

  .right-arrow {
    right: 10px;
  }

  .placeholder-item {
    min-height: 200px;
  }
}
</style>