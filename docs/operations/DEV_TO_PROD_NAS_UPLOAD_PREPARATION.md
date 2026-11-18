# OA DEV 手机上传发布准备

> 历史记录（2026-11-06）：下文的提交号、数据库版本、镜像和部署状态仅反映当时的调查，不代表当前环境，也不是本次整合或发布的验收依据。当前状态须以实际代码、配置和运行环境为准。

本文件是待审查方案，不表示已授权或已执行生产部署。

## 当前阻碍

- 生产 Nginx 的 `/api/nas-upload/` 限制为 9 MiB；Waitress 默认请求体限制为 1 GiB。业务限制为单文件 2,147,483,648 字节，当前上传 PUT 的请求体是原始文件字节，不是 multipart。
- 如果仅为请求体预留 16 MiB 余量，可将 Nginx 对该 location 的 `client_max_body_size` 改为 `2064m`，并将 Waitress 启动参数设为 `--max-request-body-size=2164260864`。Flask 此上传端点的原始请求体限制仍为 2 GiB，普通接口的 200 MiB 限制无需放宽。现有 Nginx `client_body_timeout`、`proxy_send_timeout`、`proxy_read_timeout` 是 300 秒的空闲超时，不是总传输时长；Waitress `channel_timeout` 默认 120 秒，建议评估调整为 300 秒以避免长时间空闲连接提前终止。
- 上述数值调整本身不足以发布。Waitress 在将请求交给 Flask 前接收并缓冲完整请求体，Flask 因而无法在接收文件前检查二维码，上传过程中换码或二维码到期会影响尚未进入 Flask 的请求。需单独设计并验证在请求头到达后即可将请求交给应用的生产服务方案，保持现有单次 PUT 协议，并核对并发、超时、流控、断线、授权和回滚；这属于运行架构调整，当前未实施。
- 已创建任务但尚未进入 Flask 授权检查时，二维码过期或被替换会被拒绝；已在 Flask 授权通过并开始读取的请求继续完成。部署时须验证实际生产服务器同样满足这一边界。

## 空间与缓冲

2026-11-06 检查：backend 容器 Waitress 临时目录 `/tmp` 位于 Docker overlay，宿主机可用约 783 GiB；NAS 可用约 962 GiB。Nginx 的 `client_body_temp_path` 是 `/var/cache/nginx/client_temp`，`proxy_temp_path` 是 `/var/cache/nginx/proxy_temp`，均在前端容器 overlay；现有上传 location 为 `proxy_request_buffering off`。Waitress 会将大请求体缓冲到本地临时文件，随后应用写 NAS 临时文件；单次 2 GiB 上传可能同时占用约 2 GiB 本地临时空间和 2 GiB NAS 空间，并发时按数量叠加。代理临时文件、重试、文件系统预分配和其他业务还需额外余量。NAS 最终文件由现有 hard link 发布，不应简单把目标和临时链接当作两份文件。

## 代码整理与提交范围

- 正式功能：前端 `src/api/nasUpload.ts`、`src/components/NasMobileUploadDialog.vue`、`src/views/HomeView.vue`、`src/views/NasMobileUploadView.vue`、所需组件类型；后端 `app/routes/nas_upload_routes.py`、`app/models/nas_upload_log.py`、`app/__init__.py` 的模型注册、迁移文件；数据库结构快照、迁移冒烟检查和本准备说明。
- `app/__init__.py`、`config.py`、前端 API 中同时含 DEV 诊断或环境隔离，逐段复核后再确定提交内容。浏览器诊断仅在 Vite DEV 模式运行；后端诊断必须同时满足 DEV 端口和显式标志。后端 `.dockerignore` 排除 DEV 诊断路由，防止进入生产镜像。`vite.config.ts` 的长请求设置和 `src/types/env.d.ts` 的直连变量属于 DEV 运行用途；如保留相关 DEV 代码，应一并保留匹配的类型声明。
- 不提交 `.oa-dev/`、`.venv/`、数据库、日志、运行密钥及 `node_modules/`；`app/routes/dev_diagnostics_routes.py` 保留在 DEV，默认不作为正式功能提交。若保留其条件注册代码，应确保 DEV 需要该工具时仍可找到它。

## Git 和生产备份

两个仓库 HEAD 和只读查询到的 GitHub `dev` / `main` 均为 `708c866`。DEV `dev` 配置跟踪 `origin/dev`，但本地没有该远程跟踪引用。经后续授权后，先在 DEV 整理提交并推送到远端 `dev`，通过审查的 PR 将其合入远端 `main`；保持线性历史后再处理 PROD 的快进更新。此轮不提交、推送、合并或拉取。

PROD 有三个本地修改：`docs/ARCHITECTURE_INDEX.md`、手机上传前端视图及后端路由。原文件、`git diff --binary` 和 SHA-256 已保存至 `.oa-dev/predeploy-prod-backups/20261106-122339-133121/`。此备份被 DEV 本地 Git 忽略；正式更新前需独立保管并重新校验，协商保留或迁移重叠的本地修改。`oa-pull` 会因这些修改停止，不能用 reset 或覆盖绕过。

生产当前镜像 ID：frontend `sha256:798836b3fbdff14f72bf9bd1ca861af0be4787b3eeec9fa83efdd3d1429c91b8`；backend `sha256:fd35e5b2663cac8817bb1b023e8d233cf8a46a26c7bb90bb443455b0a9d3d1b4`。正式构建前需给运行中的两个镜像各加独立回滚标签并确认存在；这些镜像包含生产本地源码修改，不能只靠 Git HEAD 重建。执行迁移前，用 SQLite backup API 对实际挂载库 `/data/backup/oa/soonwin_oa.db` 做一致性备份、完整性校验并保存；回滚先停止写入并按审核方案恢复备份、切回对应镜像，验证数据库及业务。降级会删除新增日志表及其中记录，恢复备份也会丢弃备份后的数据库写入，须在部署窗口安排和确认。

## 数据库

当前 PROD 为 `device_binding_qr_sessions_20261009`，与对应结构快照一致。DEV 增加 `nas_upload_log_20261106`，其 `down_revision` 为上述版本；`schema_baseline_20261106.json` 描述新 head。隔离数据库冒烟检查覆盖旧版本、升级、降级和再次升级的结构比较。新表的业务日志不会倒填历史上传。
