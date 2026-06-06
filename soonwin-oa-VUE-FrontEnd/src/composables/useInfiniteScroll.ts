/**
 * 无限滚动 composable
 *
 * 用法：
 *   const { sentinelRef, isLoadingMore, reset } = useInfiniteScroll(loadMore, {
 *     threshold: 600,           // 距底部多少 px 触发（默认 600）
 *     enabled: () => hasMore,   // 条件：还有更多数据才触发
 *   })
 *
 *   模板中放一个哨兵元素：
 *   <div ref="sentinelRef" style="height:1px"></div>
 */

import { ref, onMounted, onBeforeUnmount } from 'vue'

export interface InfiniteScrollOptions {
  /** 底部边距（px），哨兵进入此范围时触发加载 */
  threshold?: number
  /** 是否允许触发加载（如 hasMore && !loading） */
  enabled?: () => boolean
}

export function useInfiniteScroll(
  loadMore: () => Promise<void>,
  options: InfiniteScrollOptions = {}
) {
  const { threshold = 600, enabled } = options

  const sentinelRef = ref<HTMLElement | null>(null)
  const isLoadingMore = ref(false)
  let observer: IntersectionObserver | null = null

  function setup() {
    if (!sentinelRef.value) return
    teardown()

    observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (!entry) return
        if (entry.isIntersecting && !isLoadingMore.value && (enabled?.() ?? true)) {
          isLoadingMore.value = true
          loadMore().finally(() => {
            isLoadingMore.value = false
          })
        }
      },
      {
        rootMargin: `0px 0px ${threshold}px 0px`,
        threshold: 0,
      }
    )
    observer.observe(sentinelRef.value)
  }

  function teardown() {
    observer?.disconnect()
    observer = null
  }

  onMounted(() => {
    // 延迟一帧确保 DOM 已渲染
    requestAnimationFrame(() => setup())
  })

  onBeforeUnmount(() => teardown())

  return {
    sentinelRef,
    isLoadingMore,
    /** 哨兵 DOM 变化后（如数据追加导致哨兵被推下去）重新观察 */
    refresh: setup,
  }
}
