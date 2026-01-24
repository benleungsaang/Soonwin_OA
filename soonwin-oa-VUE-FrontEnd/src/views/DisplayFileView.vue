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
          <span style="font-size: 25px;">展示文件</span>
          <el-icon
          v-if="isCurrentUserAdmin"
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
          <!-- 编辑按钮，只对管理员显示 -->
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
                        </template>                  <div class="preview-content" v-if="currentFile">
                            <!-- 瀑布流展示 -->
                            <div v-if="displayMode === 'waterfall'" class="waterfall-container">                  <div v-if="loadingImages" class="loading-images">
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

                                        <div v-else-if="displayMode === 'pagination'" class="pagination-container">                          <div class="pagination-controls">
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

                          <div class="pdf-page-container" @click="handlePaginationClick" @mousemove="updateMouseCursor" @mouseenter="showNavArrows = true" @mouseleave="showNavArrows = false">
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
                        </div>              </div>
            </el-dialog>  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { ElMessage, ElButton, ElPageHeader, ElDivider, ElMessageBox, ElSwitch, ElDialog, ElForm, ElFormItem, ElInput, ElSelect, ElOption } from 'element-plus';
import { Delete, Loading, Document, ArrowLeft, ArrowRight, FolderOpened, Edit } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { useRouter } from 'vue-router';
import { initializePdfDocument, getPdfPage, renderPdfPage } from '@/utils/pdfUtils';
import { DisplayFile, DisplayFileListResponse } from '@/types';

// ==================== 路由相关 ====================
const router = useRouter();

// ==================== 文件列表相关 ====================
const displayFiles = ref<DisplayFile[]>([]);
const loading = ref(false);
const page = ref(1);
const perPage = ref(10);
const hasMore = ref(true);
const isCurrentUserAdmin = ref(false);

// ==================== 预览相关 ====================
const previewVisible = ref(false);
const currentFile = ref<any>(null);
const imageList = ref<string[]>([]); // 已渲染的页面
const loadingImages = ref(false);
let pdfDoc: any = null; // PDF文档对象（使用普通变量以避免响应式代理问题）
const currentPage = ref(1); // 当前渲染到的页面
const totalPages = ref(0); // PDF总页数
const renderedPages = ref<Set<number>>(new Set()); // 已渲染的页面集合
const maxRenderedPage = ref(1); // 已渲染的最大页码
const loadingPages = ref<Set<number>>(new Set()); // 正在加载的页面集合

// PDF页面渲染队列
const renderQueue = ref<number[]>([]);
const isRendering = ref(false);

// 导航箭头显示
const showNavArrows = ref(false);

// 展示模式 - 在不同文件间保持一致
const displayMode = ref<'waterfall' | 'pagination'>('waterfall');

// 编辑文件相关
const editDialogVisible = ref(false);
const editingFile = ref<any>(null);
const editForm = ref({
  title: ''
});

// ==================== 布局相关 ====================
const waterfallRef = ref<HTMLElement | null>(null);
const pdfPageContainerRef = ref<HTMLElement | null>(null);

// 分页导航函数


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
    await ElMessageBox.confirm(
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
    // 检查是否有认证令牌
    const token = localStorage.getItem('oa_token');
    if (!token) {
      console.error('缺少认证令牌，请先登录');
      ElMessage.error('请先登录系统');
      return;
    }

    // 发起API请求
    const response = await request.get('/api/display-file/list', {
      params: {
        page: page.value,
        per_page: perPage.value
      }
    });

    // 处理API响应数据
    // response应该是在request.ts解包后的数据，即 { files: [...], pagination: {...} }
    if (response && response.files && Array.isArray(response.files)) {
      if (reset) {
        displayFiles.value = [...response.files]; // 使用展开运算符确保响应式更新
      } else {
        displayFiles.value = [...displayFiles.value, ...response.files]; // 合并现有和新获取的文件
      }

      // 更新分页信息
      if (response.pagination) {
        hasMore.value = response.pagination.page < response.pagination.pages;
        // 只有在还有更多数据时才增加页数
        if (hasMore.value) {
          page.value += 1;
        }
      } else {
        // 如果没有pagination信息，假设没有更多数据
        hasMore.value = false;
      }
    } else {
      // 如果响应中没有files字段，也设置为没有更多数据
      hasMore.value = false;
    }
  } catch (error) {
    console.error('获取展示文件列表失败:', error);
    // 检查错误是否与认证相关
    if (error && typeof error === 'object' && error.message && error.message.includes('401')) {
      console.error('认证失败，请检查登录状态');
      ElMessage.error('未认证，请重新登录');
    } else {
      ElMessage.error('获取展示文件列表失败');
    }
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
    // 如果是分页模式，设置当前页为第1页并预加载
    if (displayMode.value === 'pagination') {
      currentPage.value = 1;
      // 如果第一页图片尚未加载，添加到加载队列
      if (imageList.value.length > 0 && !imageList.value[0] && !loadingPages.value.has(1)) {
        addToLoadImageQueue(1);
      }
    }
  } else if (file.file_type === 'pdf') {
    // 获取PDF文件
    await loadPdfFile(file);
    // 设置当前页为第1页
    currentPage.value = 1;
    // 对于PDF，即使在瀑布流模式下也需要设置totalPages值供页面显示
    // 在loadPdfFile函数中会设置totalPages
  }
};

// 加载图片组
const loadImageGroup = async (uuid: string) => {
  loadingImages.value = true;

  try {
    const response = await request.get(`/api/display-file/${uuid}/images`);
    if (response && response.images && Array.isArray(response.images)) {
      // 保存原始图片URL列表
      const originalImageUrls = response.images;

      // 初始化imageList，为所有图片创建null占位符
      imageList.value = Array(originalImageUrls.length).fill(null);

      // 保存原始URL以便后续懒加载使用
      // 使用普通变量存储原始URL，避免响应式代理
      (window as any).__originalImageUrls = originalImageUrls;

      // 设置总页数用于页码显示
      totalPages.value = originalImageUrls.length;

      // 如果当前文件的页数为空，则更新页数
      if (currentFile.value && currentFile.value.page_count === null) {
        await updateFilePageCount(currentFile.value.id, totalPages.value);
      }

      // 启动滚动监听器以实现懒加载
      startScrollListener();

      // 初始化后立即检查视口中的图片并加载它们
      nextTick(() => {
        applyWaterfallLayout();
        setTimeout(() => {
          checkAndLoadVisibleImages();
        }, 100); // 短暂延迟以确保DOM已更新
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
    // PDF文件通过PDF.js直接渲染，不需要获取图片组
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
  // 构建PDF URL
  const fileName = pdfPath.split('/').pop(); // 从完整路径中提取文件名
  const pdfUrl = `/api/display-file/file/${fileName}`;

  try {
    // 使用新的按需加载PDF工具初始化文档
    const doc = await initializePdfDocument(pdfUrl, {
      cMapPacked: true,
      // 增大token限制，兼容大PDF
      maxCanvasPixels: 10000 * 10000, // 默认是16794880，适当增大以支持大PDF
    });
    
    pdfDoc = doc; // 直接赋值给普通变量
    totalPages.value = doc.numPages;
    // 重置渲染队列
    renderQueue.value = [];
    // 添加所有页面到渲染队列
    for (let i = 1; i <= totalPages.value; i++) {
      renderQueue.value.push(i);
    }
    // 立即渲染第一页
    if (totalPages.value > 0) {
      renderQueue.value = [1];
      renderPdfPageDirectly(1);
    }
  } catch (error) {
    console.error('初始化PDF失败:', error);
    ElMessage.error('初始化PDF失败');
  }
};
// 将页面添加到渲染队列
const addToRenderQueue = (pageNumber: number) => {
  if (!renderQueue.value.includes(pageNumber) &&
      pageNumber >= 1 &&
      pageNumber <= totalPages.value &&
      !imageList.value[pageNumber - 1] &&
      !loadingPages.value.has(pageNumber)) {  // 确保页面不在加载中
    renderQueue.value.push(pageNumber);
    loadingPages.value.add(pageNumber);  // 添加到正在加载的页面集合
    // 启动队列处理
    processRenderQueue();
  }
};

// 处理渲染队列
const processRenderQueue = async () => {
  if (isRendering.value || renderQueue.value.length === 0 || !pdfDoc) {  // 检查普通变量
    return;
  }

  isRendering.value = true;

  while (renderQueue.value.length > 0) {
    const pageNumber = renderQueue.value.shift();
    if (pageNumber && !imageList.value[pageNumber - 1]) { // 确保页面未被渲染
      await renderPdfPageDirectly(pageNumber);
    }
  }

  isRendering.value = false;
};

// 直接渲染PDF页面（内部使用）
// 更新页面加载状态的函数
const updatePageLoadStatus = (pageNumber: number, loaded: boolean) => {
  if (loaded) {
    renderedPages.value.add(pageNumber);
    if (pageNumber > maxRenderedPage.value) {
      maxRenderedPage.value = pageNumber;
    }
  } else {
    renderedPages.value.delete(pageNumber);
    loadingPages.value.add(pageNumber);
  }
};

const renderPdfPageDirectly = async (pageNumber: number) => {
  if (!pdfDoc || !totalPages.value || pageNumber < 1 || pageNumber > totalPages.value) {
    console.error('PDF文档未正确初始化或页面号超出范围');
    return;
  }

  try {
    // 使用新的PDF工具获取页面
    const page = await getPdfPage(pdfDoc, pageNumber);
    if (!page) {
      console.error(`无法获取PDF第${pageNumber}页`);
      return;
    }

    // 获取容器元素
    const container = pdfPageContainerRef.value;
    if (!container) {
      console.error('未找到PDF页面容器');
      return;
    }

    // 为当前页面创建canvas（如果不存在）
    let canvas = container.querySelector(`#pdf-canvas-${pageNumber}`) as HTMLCanvasElement;
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = `pdf-canvas-${pageNumber}`;
      canvas.className = 'pdf-canvas';
      container.appendChild(canvas);
    }

    // 使用新的PDF工具渲染页面
    await renderPdfPage(page, canvas, window.devicePixelRatio || 1);

    // 如果是瀑布流模式，确保容器尺寸正确
    if (displayMode.value === 'waterfall') {
      // 设置canvas容器的样式
      canvas.style.maxWidth = '100%';
      canvas.style.height = 'auto';
    }

    // 更新加载状态
    updatePageLoadStatus(pageNumber, true);

    console.log(`PDF第${pageNumber}页渲染完成`);
  } catch (error) {
    console.error(`渲染PDF第${pageNumber}页失败:`, error);
    ElMessage.error(`渲染PDF第${pageNumber}页失败`);
  }
};

// 检查并加载视口中的页面（支持PDF和图片组）
const checkAndLoadVisiblePages = () => {
  if (!previewVisible.value) return;

  const previewContent = document.querySelector('.preview-content') as HTMLElement;
  if (!previewContent) return;

  // 根据文件类型决定处理逻辑
  if (currentFile.value?.file_type === 'pdf' && pdfDoc) {
    // PDF文件处理逻辑
    // 获取滚动位置信息
    const scrollTop = previewContent.scrollTop;
    const clientHeight = previewContent.clientHeight;
    const scrollBottom = scrollTop + clientHeight;

    // 遍历所有瀑布流项目，检查哪些在视口内但尚未加载
    const waterfallItems = document.querySelectorAll('.waterfall-item');

    waterfallItems.forEach(item => {
      const pageIndexStr = item.getAttribute('data-page-index');
      if (!pageIndexStr) return;

      const pageIndex = parseInt(pageIndexStr);

      // 检查页面是否已经加载或正在加载
      if (imageList.value[pageIndex - 1] || loadingPages.value.has(pageIndex)) {
        return; // 已加载或正在加载，跳过
      }

      // 获取元素的位置信息
      const rect = item.getBoundingClientRect();
      const containerRect = previewContent.getBoundingClientRect();

      // 计算元素相对于容器的位置
      const elementTop = rect.top - containerRect.top + scrollTop;
      const elementBottom = rect.bottom - containerRect.top + scrollTop;

      // 检查元素是否在可视区域内
      if (elementTop <= scrollBottom && elementBottom >= scrollTop) {
        // 如果在视口内且尚未加载，添加到渲染队列
        addToRenderQueue(pageIndex);
      }
    });
  } else if (currentFile.value?.file_type === 'image_group') {
    // 图片组处理逻辑
    checkAndLoadVisibleImages();
  }
};

// 启动滚动监听器以实现懒加载
const startScrollListener = () => {
  // 首先移除可能已存在的监听器
  stopScrollListener();

  // 添加滚动事件监听器
  nextTick(() => {
    const previewContent = document.querySelector('.preview-content');
    if (previewContent) {
      previewContent.addEventListener('scroll', handleScroll);
    }
  });
};

// 滚动处理函数 - 检测当前可见的项目，然后加载对应内容（支持PDF和图片组）
const handleScroll = async () => {
  if (!previewVisible.value) return;

  const previewContent = document.querySelector('.preview-content') as HTMLElement;
  if (!previewContent) return;

  // 根据文件类型决定处理逻辑
  if (currentFile.value?.file_type === 'pdf' && pdfDoc) {
    // PDF文件处理逻辑
    // 获取滚动位置信息
    const scrollTop = previewContent.scrollTop;
    const clientHeight = previewContent.clientHeight;
    const scrollHeight = previewContent.scrollHeight;

    // 计算可视区域底部位置
    const scrollBottom = scrollTop + clientHeight;

    // 寻找当前可视区域内的最后一个已加载的图片
    const loadedImageElements = document.querySelectorAll('.waterfall-item img');
    let lastVisibleLoadedIndex = -1;
    let maxPageIndex = 0;

    loadedImageElements.forEach(item => {
      const parentItem = item.closest('.waterfall-item');
      if (parentItem) {
        const pageIndex = parseInt(parentItem.getAttribute('data-page-index') || '0');

        // 获取元素的位置信息
        const rect = parentItem.getBoundingClientRect();
        const containerRect = previewContent.getBoundingClientRect();

        // 计算元素相对于容器的位置
        const elementTop = rect.top - containerRect.top + scrollTop;
        const elementBottom = rect.bottom - containerRect.top + scrollTop;

        // 检查元素是否在可视区域内或接近底部
        if (elementTop <= scrollBottom && elementBottom >= scrollTop) {
          // 如果这个元素的页码比之前找到的更大，更新
          if (pageIndex > maxPageIndex) {
            maxPageIndex = pageIndex;
          }
        }
      }
    });

    // 如果找到了当前可视区域内的最后一页，并且下一页未加载，则加载下一页
    if (maxPageIndex > 0) {
      const nextPageIndex = maxPageIndex + 1;
      if (nextPageIndex <= totalPages.value &&
          !imageList.value[nextPageIndex - 1] &&
          !loadingPages.value.has(nextPageIndex)) {
        // 检查是否接近最后一页的内容（提前加载）
        addToRenderQueue(nextPageIndex);
      }
    }

    // 计算接近底部的阈值（例如：还剩100px时就开始预加载）
    const threshold = 100;

    // 如果接近底部且还有未渲染的页面，则可能需要预加载更多页面
    if (scrollTop + clientHeight >= scrollHeight - threshold) {
      // 查找下一个未渲染的页面
      let nextPage = -1;
      for (let i = maxRenderedPage.value + 1; i <= totalPages.value; i++) {
        if (!renderedPages.value.has(i)) {
          nextPage = i;
          break;
        }
      }

      // 如果找到了下一个未渲染的页面，则将其添加到渲染队列
      if (nextPage !== -1) {
        addToRenderQueue(nextPage);

        // 预加载下一页（最多预加载一页）
        preloadNextPage();
      }
    }
  } else if (currentFile.value?.file_type === 'image_group') {
    // 图片组处理逻辑
    checkAndLoadVisibleImages();
  }
};

// 停止滚动监听器
const stopScrollListener = () => {
  const previewContent = document.querySelector('.preview-content');
  if (previewContent) {
    previewContent.removeEventListener('scroll', handleScroll);
  }
};



// 预加载下一页（如果当前已渲染页面小于总页数）
const preloadNextPage = async () => {
  if (maxRenderedPage.value < totalPages.value) {
    const nextPage = maxRenderedPage.value + 1;
    if (!renderedPages.value.has(nextPage)) {
      addToRenderQueue(nextPage);
    }
  }
};

// 检查并加载视口中的图片（用于图片组）
const checkAndLoadVisibleImages = () => {
  if (!previewVisible.value || currentFile.value?.file_type !== 'image_group') return;

  const previewContent = document.querySelector('.preview-content') as HTMLElement;
  if (!previewContent) return;

  // 获取滚动位置信息
  const scrollTop = previewContent.scrollTop;
  const clientHeight = previewContent.clientHeight;
  const scrollBottom = scrollTop + clientHeight;

  // 遍历所有瀑布流项目，检查哪些在视口内但尚未加载
  const waterfallItems = document.querySelectorAll('.waterfall-item');

  waterfallItems.forEach(item => {
    const imgIndexStr = item.getAttribute('data-page-index');
    if (!imgIndexStr) return;

    const imgIndex = parseInt(imgIndexStr);

    // 检查图片是否已经加载或正在加载
    if (imageList.value[imgIndex - 1] || loadingPages.value.has(imgIndex)) {
      return; // 已加载或正在加载，跳过
    }

    // 获取元素的位置信息
    const rect = item.getBoundingClientRect();
    const containerRect = previewContent.getBoundingClientRect();

    // 计算元素相对于容器的位置
    const elementTop = rect.top - containerRect.top + scrollTop;
    const elementBottom = rect.bottom - containerRect.top + scrollTop;

    // 检查元素是否在可视区域内
    if (elementTop <= scrollBottom && elementBottom >= scrollTop) {
      // 如果在视口内且尚未加载，添加到加载队列
      addToLoadImageQueue(imgIndex);
    }
  });
};

// 将图片添加到加载队列
const addToLoadImageQueue = (imgIndex: number) => {
  if (!loadingPages.value.has(imgIndex) &&
      imgIndex >= 1 &&
      imgIndex <= imageList.value.length &&
      !imageList.value[imgIndex - 1]) {  // 确保图片未被加载
    loadingPages.value.add(imgIndex);  // 添加到正在加载的集合
    // 加载图片
    loadImageAtIndex(imgIndex);
  }
};

// 加载指定索引的图片
const loadImageAtIndex = async (imgIndex: number) => {
  try {
    // 从存储的原始URL中获取对应图片URL
    const originalImageUrls = (window as any).__originalImageUrls;
    if (!originalImageUrls || imgIndex > originalImageUrls.length) {
      console.error(`图片索引 ${imgIndex} 超出范围`);
      return;
    }

    const imgSrc = originalImageUrls[imgIndex - 1]; // 转换为0基索引

    // 创建一个新的canvas用于添加页码
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    if (context) {
      // 创建图片对象用于获取尺寸
      const img = new Image();
      img.crossOrigin = "anonymous"; // 处理跨域图片

      // 设置加载完成的回调
      const loadImagePromise = new Promise((resolve, reject) => {
        img.onload = () => resolve(null);
        img.onerror = () => reject(null); // 即使加载失败也继续
      });

      // 开始加载图片
      img.src = imgSrc;

      // 等待图片加载完成
      await loadImagePromise;

      // 设置canvas尺寸
      canvas.width = img.width;
      canvas.height = img.height;

      // 绘制原始图片
      context.drawImage(img, 0, 0);

      // 在右下角绘制页码
      context.fillStyle = 'rgba(0, 0, 0, 0.7)'; // 半透明黑色背景
      context.font = '16px Arial';
      context.textAlign = 'right';

      const pageNumText = `${imgIndex} / ${totalPages.value}`;
      const textMetrics = context.measureText(pageNumText);
      const padding = 8;
      const x = canvas.width - padding;
      const y = canvas.height - padding;

      // 绘制页码背景
      context.fillStyle = 'rgba(0, 0, 0, 0.7)';
      context.fillRect(
        x - textMetrics.width - padding,
        y - 16 - padding/2,
        textMetrics.width + padding * 2,
        16 + padding
      );

      // 绘制页码文本
      context.fillStyle = 'white';
      context.fillText(pageNumText, x, y);

      // 将带页码的canvas转换为图片
      const imgWithPageNum = canvas.toDataURL('image/png');

      // 更新imageList中对应位置的图片
      const updatedImageList = [...imageList.value];
      updatedImageList[imgIndex - 1] = imgWithPageNum;
      imageList.value = updatedImageList;
    } else {
      // 如果无法创建canvas，直接使用原始图片
      const updatedImageList = [...imageList.value];
      updatedImageList[imgIndex - 1] = imgSrc;
      imageList.value = updatedImageList;
    }

  } catch (error) {
    console.error(`加载第${imgIndex}张图片失败:`, error);
    // 即使发生错误，也要从加载图片集合中移除，以便用户可以重试
    loadingPages.value.delete(imgIndex);

    // 尝试加载原始图片而不添加页码
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
    // 从加载图片集合中移除
    loadingPages.value.delete(imgIndex);
  }
};

// 应用瀑布流布局
const applyWaterfallLayout = () => {
  if (!waterfallRef.value) return;

  const container = waterfallRef.value;
  const items = container.querySelectorAll('.waterfall-item');

  // 强制使用单列展示，不再根据屏幕大小调整
  const columnCount = 1;

  // 使用普通流布局，每张图片占满容器宽度
  items.forEach((item: Element) => {
    (item as HTMLElement).style.position = 'static';
    (item as HTMLElement).style.top = 'auto';
    (item as HTMLElement).style.left = 'auto';
    (item as HTMLElement).style.width = '100%';
    (item as HTMLElement).style.marginBottom = '10px';
  });

  // 重置容器高度
  container.style.height = 'auto';
};

// 确保图片路径正确
const normalizeImagePath = (path: string): string => {
  if (!path) return '';

  // 检查是否为base64编码的图像数据
  if (path.startsWith('data:image/')) {
    // 如果是base64图像数据，直接返回，不进行URL转换
    return path;
  }

  // 只处理图片路径，不处理PDF文件路径
  if (currentFile.value && currentFile.value.file_type === 'pdf') {
    // 对于PDF文件，如果是完整的URL则直接返回，否则构造正确的路径
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    } else if (path.startsWith('/api/display-file/file/')) {
      return path;
    } else if (path.startsWith('/display-file/file/')) {
      return `/api${path}`;
    } else {
      return `/api/display-file/file/${path}`;
    }
  } else {
    // 对于图片组，确保路径以 /api 开头
    if (!path.startsWith('/api/')) {
      if (path.startsWith('/')) {
        return `/api${path}`;
      } else {
        return `/api/${path}`;
      }
    }
  }
  return path;
};

// 图片加载完成
const onImageLoad = () => {
  // 瀑布流布局调整
  nextTick(() => {
    if (currentFile.value && (currentFile.value.file_type === 'image_group' ||
        (currentFile.value.file_type === 'pdf' && currentFile.value.display_mode === 'waterfall'))) {
      applyWaterfallLayout();
    }
  });
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
  // 清理资源
  currentFile.value = null;
  imageList.value = [];
  pdfDoc = null;  // 清理普通变量
  currentPage.value = 1;
  totalPages.value = 0;
  renderedPages.value.clear();
  maxRenderedPage.value = 1;

  // 清理渲染队列
  renderQueue.value = [];
  isRendering.value = false;

  // 停止滚动监听
  stopScrollListener();

  // 清理全局变量
  (window as any).__originalImageUrls = null;

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

// 展示模式切换处理 - 由于已删除display_mode字段，此函数不再需要

// 保留全局displayMode变量用于界面展示模式控制



// 编辑文件



const editFile = async (file: any, event: Event) => {



  event.stopPropagation(); // 阻止事件冒泡，避免触发查看文件







  editingFile.value = { ...file }; // 复制文件对象



  editForm.value = {



    title: file.title



  };



  editDialogVisible.value = true;



};







// 保存编辑







const saveEdit = async () => {







  try {







    const response = await request.put(`/api/display-file/${editingFile.value.id}`, {







      title: editForm.value.title







    });















    if (response) {







      // 更新本地列表







      const index = displayFiles.value.findIndex(f => f.id === editingFile.value.id);







      if (index !== -1) {







        displayFiles.value[index].title = editForm.value.title;







      }















      ElMessage.success('文件信息更新成功');







      editDialogVisible.value = false;







    }







  } catch (error) {







    console.error('更新文件信息失败:', error);







    ElMessage.error('文件信息更新失败');







  }







};







// 更新文件页数



const updateFilePageCount = async (fileId: number, pageCount: number) => {



  try {



    const response = await request.put(`/api/display-file/${fileId}/page-count`, {



      page_count: pageCount



    });



    if (response) {



      console.log(`文件 ${fileId} 的页数已更新为 ${pageCount}`);



      // 更新当前文件的页数



      if (currentFile.value && currentFile.value.id === fileId) {



        currentFile.value.page_count = pageCount;



      }



    }



  } catch (error) {



    console.error('更新页数失败:', error);



  }



};// 更新鼠标指针效果
const updateMouseCursor = (event: MouseEvent) => {
  if (!currentFile.value || currentFile.value.display_mode !== 'pagination') return;

  const container = event.currentTarget as HTMLElement;
  const rect = container.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const width = rect.width;

  const pageElement = container.querySelector('.pdf-page') as HTMLElement;
  if (!pageElement) return;

  // 根据鼠标位置设置相应的CSS类
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

  // 如果点击左侧 50% 区域，翻到上一页
  if (x < width * 0.5) {
    goToPrevPage();
  }
  // 如果点击右侧 50% 区域，翻到下一页
  else {
    goToNextPage();
  }

  // 不再移除CSS类，以便悬停时继续显示正确光标
};
// 跳转到上一页
const goToPrevPage = () => {
  if (currentFile.value?.file_type === 'image_group' && displayMode.value === 'pagination') {
    if (currentPage.value > 1) {
      currentPage.value--;
      // 如果图片尚未加载，添加到加载队列
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToLoadImageQueue(currentPage.value);
      }
      // 预加载前一页
      const prevPage = currentPage.value - 1;
      if (prevPage > 0 && !imageList.value[prevPage - 1] && !loadingPages.value.has(prevPage)) {
        addToLoadImageQueue(prevPage);
      }
    }
  } else if (currentFile.value?.file_type === 'pdf' && displayMode.value === 'pagination') {
    if (currentPage.value > 1) {
      currentPage.value--;
      // 如果PDF页面尚未加载，添加到渲染队列
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToRenderQueue(currentPage.value);
      }
      // 预加载前一页
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
      // 如果图片尚未加载，添加到加载队列
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToLoadImageQueue(currentPage.value);
      }
      // 预加载后一页
      const nextPage = currentPage.value + 1;
      if (nextPage <= totalPages.value && !imageList.value[nextPage - 1] && !loadingPages.value.has(nextPage)) {
        addToLoadImageQueue(nextPage);
      }
    }
  } else if (currentFile.value?.file_type === 'pdf' && displayMode.value === 'pagination') {
    if (currentPage.value < totalPages.value) {
      currentPage.value++;
      // 如果PDF页面尚未加载，添加到渲染队列
      if (!imageList.value[currentPage.value - 1] && !loadingPages.value.has(currentPage.value)) {
        addToRenderQueue(currentPage.value);
      }
      // 预加载后一页
      const nextPage = currentPage.value + 1;
      if (nextPage <= totalPages.value && !imageList.value[nextPage - 1] && !loadingPages.value.has(nextPage)) {
        addToRenderQueue(nextPage);
      }
    }
  }
};

// 返回上一页
const goBack = () => {
  router.go(-1); // 返回上一页
};


// 跳转上传展示文件页面（仅管理员可见）
const goToDisplayFileUpload = () => {
  if (!isCurrentUserAdmin.value) {
    ElMessage.error('您没有权限访问上传展示文件页面！');
    return;
  }
  router.push('/display-file-upload');
};


// 初始化
onMounted(() => {
  // 检查认证令牌
  const token = localStorage.getItem('oa_token');
  if (!token) {
    console.error('缺少认证令牌，重定向到登录页');
    ElMessage.error('请先登录系统');
    router.push('/login');
    return;
  }
  
  // 确保在获取文件列表之前检查用户权限
  checkAdminRole();
  // 重置并获取展示文件列表
  fetchDisplayFiles(true);

  // 监听窗口大小变化，重新应用瀑布流布局
  window.addEventListener('resize', () => {
    if (currentFile.value && (currentFile.value.file_type === 'image_group' ||
        (currentFile.value.file_type === 'pdf'))) {
      nextTick(() => {
        applyWaterfallLayout();
      });
    }
  });
});</script>

<style scoped>
.upload-icon{
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
  padding:10px 25px ;
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

.file-type-icon{
  margin-right: 20px;
  flex-shrink: 0;
  color: white;
  padding: 5px 10px;
  border-radius: 6px;
}

.img-bg{
  background-color: #143474;
}

.pdf-bg{
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
  position: absolute;
  padding: 5px;
  box-sizing: border-box;
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



/* 为页码添加额外样式 */
.waterfall-item {
  position: relative;
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
  /* 核心：强制不换行（flex默认值，显式声明更稳妥） */
  flex-wrap: nowrap;
  /* 可选：处理容器宽度不足时的溢出（避免元素挤压/截断） */
  overflow-x: auto; /* 横向滚动，保留所有元素可见 */
  white-space: nowrap; /* 兼容行内元素（如按钮/文字）不换行 */
  /* 可选：隐藏滚动条（美化，按需开启） */
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

/* 预览框标题样式 */
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



/* 预览框标题样式 */
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.preview-header > span {
  flex: 1;
  text-align: left;
}

.display-mode-controls {
  flex-shrink: 0;
  margin-left: 20px;
}

.display-mode-controls .el-button-group {
  display: flex;
}

/* 分页模式翻页箭头样式 */
.pdf-page-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 鼠标悬停时在左右区域显示左右箭头光标 */
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
  margin: 0 0; /* 为导航箭头留出空间 */
}

/* 移动端适配 */
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
  }

  .display-card {
    margin: 5px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .pagination-controls {
    gap: 10px;
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
    padding: 0 20px;
    /* 核心：强制不换行（flex默认值，显式声明更稳妥） */
    flex-wrap: nowrap;
    /* 可选：处理容器宽度不足时的溢出（避免元素挤压/截断） */
    overflow-x: auto; /* 横向滚动，保留所有元素可见 */
    white-space: nowrap; /* 兼容行内元素（如按钮/文字）不换行 */
    /* 可选：隐藏滚动条（美化，按需开启） */
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .display-mode-controls {
    margin-bottom: 10px;
  }

  .pagination-controls .el-button {
    width: 100%;
    margin: 2px 0;
  }

  .page-info {
    text-align: center;
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

  .display-mode-controls {
    margin-bottom: 0;
    margin-left: 10px;
  }
}
</style>