import { useRoute, useRouter } from 'vue-router'

/**
 * 跳转到当前路由的上一级（基于路由层级，非历史记录）
 * @param fallbackPath 无父级时的兜底路径，默认 '/'
 */
export const goToParentRoute = (fallbackPath = '/') => {
  const route = useRoute()
  const router = useRouter()
  
  const matched = route.matched
  if (matched.length >= 2) {
    const parentPath = matched[matched.length - 2].path
    router.push({ path: parentPath })
  } else {
    router.push({ path: fallbackPath })
  }
}