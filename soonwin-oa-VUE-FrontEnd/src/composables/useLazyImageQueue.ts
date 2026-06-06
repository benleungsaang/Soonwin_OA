/**
 * 图片懒加载优先级队列
 *
 * 核心逻辑：
 * - 并发上限 4：保证加载速度，不因排队而拖慢整体
 * - 优先级排序：按元素在页面的 Y 坐标，上方图片优先出队
 *   → 顶部最新博文最先加载，同时下面可见图片并发不浪费带宽
 * - 使用浏览器原生 Image 预加载，失败也释放槽位
 */

const MAX_CONCURRENT = 4

interface QueueItem {
  url: string
  priority: number   // 越小越优先（= 元素距页面顶部的 Y 坐标）
  resolve: (url: string) => void
}

let activeCount = 0
const pending: QueueItem[] = []

/** 按优先级升序排列（Y 坐标小的在上面 → 先加载） */
function sortPending() {
  pending.sort((a, b) => a.priority - b.priority)
}

function processQueue() {
  while (activeCount < MAX_CONCURRENT && pending.length > 0) {
    // 每次取之前按优先级重排（新入队的可能优先级更高）
    sortPending()
    const item = pending.shift()!
    activeCount++

    const img = new Image()
    img.onload = () => {
      activeCount--
      item.resolve(item.url)
      processQueue()
    }
    img.onerror = () => {
      activeCount--
      item.resolve(item.url)
      processQueue()
    }
    img.src = item.url
  }
}

/**
 * 将图片 URL 加入优先级队列。
 * @param url 图片地址
 * @param priority 越小越优先（默认 0 = 最高优先级）
 */
export function enqueueImageLoad(url: string, priority = 0): Promise<string> {
  return new Promise((resolve) => {
    pending.push({ url, priority, resolve })
    processQueue()
  })
}

export function getActiveCount(): number {
  return activeCount
}

export function getPendingCount(): number {
  return pending.length
}
