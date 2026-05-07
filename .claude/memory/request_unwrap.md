---
name: request_auto_unwrap
description: 前端request.ts自动解包response.data
type: reference
---

# 前端请求响应自动解包

`request.ts` 的响应拦截器会自动解包 `response.data`：

1. **success/data 格式**：成功时直接返回 `res.data`（第143-144行）
2. **code/msg/data 格式**（code=200）：返回 `res.data`（第158-159行）

因此 `request.get/post/put/delete` 返回的已经是解包后的数据，调用时直接使用：
```ts
const data = await request.get('/api/xxx')  // data 就是 res.data
```

**Why:** 统一封装避免每个调用处都需要 response.data.data 访问
**How to apply:** 使用这些方法时直接取返回值作为数据，不需要再 `.data` 访问
