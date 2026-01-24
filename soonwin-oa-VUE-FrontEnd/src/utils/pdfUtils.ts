/**
 * PDF工具类 - 实现PDF worker的按需加载
 * 用于在需要使用PDF功能时才加载pdf.worker.mjs，避免影响首屏加载速度
 */

import * as pdfjsLib from 'pdfjs-dist';

// 用于跟踪worker是否已加载
let workerLoaded = false;

/**
 * 按需加载PDF worker
 * 只有在首次调用PDF功能时才会加载worker
 */
export async function loadPdfWorker() {
  if (!workerLoaded) {
    // 使用动态导入确保worker只在需要时加载
    const workerSrc = new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url).href;
    pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;
    workerLoaded = true;
  }
}

/**
 * 初始化PDF文档
 * @param pdfUrl PDF文件的URL
 * @param options 额外的配置选项
 * @returns PDF文档对象
 */
export async function initializePdfDocument(pdfUrl: string, options: any = {}) {
  await loadPdfWorker(); // 确保worker已加载
  
  try {
    const getDocumentParams = {
      url: pdfUrl,
      cMapUrl: 'https://unpkg.com/pdfjs-dist@5.4.530/cmaps/',
      cMapPacked: true,
      ...options
    };
    
    const loadingTask = pdfjsLib.getDocument(getDocumentParams);
    const pdfDoc = await loadingTask.promise;
    
    return pdfDoc;
  } catch (error) {
    console.error('初始化PDF失败:', error);
    throw error;
  }
}

/**
 * 获取PDF页面
 * @param pdfDoc PDF文档对象
 * @param pageNumber 页码
 * @returns PDF页面对象
 */
export async function getPdfPage(pdfDoc: any, pageNumber: number) {
  if (!pdfDoc || pageNumber < 1 || pageNumber > pdfDoc.numPages) {
    throw new Error(`PDF文档未正确初始化或页面号超出范围: ${pageNumber}`);
  }
  
  try {
    const page = await pdfDoc.getPage(pageNumber);
    return page;
  } catch (error) {
    console.error(`无法获取PDF第${pageNumber}页:`, error);
    throw error;
  }
}

/**
 * 渲染PDF页面到canvas
 * @param page PDF页面对象
 * @param canvas canvas元素
 * @param scale 缩放比例
 * @returns 渲染任务Promise
 */
export async function renderPdfPage(page: any, canvas: HTMLCanvasElement, scale: number = 1.5) {
  try {
    const viewport = page.getViewport({ scale });
    
    // 设置canvas尺寸
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    const renderContext = {
      canvasContext: context,
      viewport: viewport,
    };
    
    const renderTask = page.render(renderContext);
    await renderTask.promise;
    
    return canvas;
  } catch (error) {
    console.error('渲染PDF页面失败:', error);
    throw error;
  }
}

/**
 * 获取PDF文档信息
 * @param pdfUrl PDF文件的URL
 * @returns 包含PDF信息的对象
 */
export async function getPdfInfo(pdfUrl: string) {
  const pdfDoc = await initializePdfDocument(pdfUrl);
  
  return {
    numPages: pdfDoc.numPages,
    metadata: await pdfDoc.getMetadata(),
    fingerprints: pdfDoc.fingerprints
  };
}