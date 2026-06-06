/**
 * 图片懒加载并发控制队列
 *
 * 核心逻辑：
 * - 限制同时加载的图片数（默认 4 张），防止并发拥塞
 * - 超出并发上限的请求排队，前一张完成后自动出队
 * - 使用浏览器原生 Image 预加载，失败也释放槽位
 */

const MAX_CONCURRENT = 4

interface QueueItem {
  url: string
  resolve: (url: string) => void
}

let activeCount = 0
const pending: QueueItem[] = []

function processQueue() {
  while (activeCount < MAX_CONCURRENT && pending.length > 0) {
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
      // 加载失败也释放槽位并返回 url（组件自行决定是否回退展示）
      item.resolve(item.url)
      processQueue()
    }
    img.src = item.url
  }
}

/**
 * 将图片 URL 加入加载队列，返回 Promise 在图片加载完成（或失败）后 resolve。
 * 调用方在 resolve 后设置 img.src 即可从浏览器缓存即时展示。
 */
export function enqueueImageLoad(url: string): Promise<string> {
  return new Promise((resolve) => {
    pending.push({ url, resolve })
    processQueue()
  })
}

/**
 * 获取当前正在加载的图片数（调试用）
 */
export function getActiveCount(): number {
  return activeCount
}

/**
 * 获取当前排队的图片数（调试用）
 */
export function getPendingCount(): number {
  return pending.length
}
