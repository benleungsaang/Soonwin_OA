# Soonwin OA Architecture Index

Last verified: 2026-09-28
Git commit: `9aff4088d30e1d1b572742b14c147372d01aabf7`

This index is navigation guidance, not the source of truth. Before modifying a module, verify the referenced paths and behavior against the current source.

## Overview

- Soonwin OA is an internal office system covering attendance, employees and permissions, expenses, inquiries, orders, files/media, tasks and related operations.
- Frontend: Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router (`soonwin-oa-VUE-FrontEnd/`).
- Backend: Python 3.12 + Flask + SQLAlchemy + Flask-Migrate/Alembic; SQLite (`soonwin-os-Python-Server/`).
- Production topology: Compose project `soonwin-oa` runs `frontend` (Nginx, host port 80) and `backend` (Waitress, container port 5000, internal only). Nginx serves the SPA and proxies `/api/` to `backend:5000`; `/assets/` falls back to backend.

## Repository Map

| Path | Purpose |
|---|---|
| `soonwin-oa-VUE-FrontEnd/` | Vue application, route views, API callers and production build. |
| `soonwin-os-Python-Server/app/routes/` | Flask API blueprints. |
| `soonwin-os-Python-Server/app/models/` | SQLAlchemy models. |
| `soonwin-os-Python-Server/app/utils/` | Auth, uploads, video processing and shared helpers. |
| `soonwin-os-Python-Server/migrations/` | Alembic environment and versioned schema changes. |
| `soonwin-os-Python-Server/assets/` | Backend media tree; production bind-mounted. |
| `windows-tools/` | Windows-side backup and tray/startup utilities. |
| `辅助脚本/` | Historical/operational helper scripts; inspect before use. |
| `/data/services/oa/` | Active production Compose, Dockerfiles and Nginx configuration (outside source repo). |

## Frontend Index

| Feature | Path | Main responsibility |
|---|---|---|
| App bootstrap and route guards | `soonwin-oa-VUE-FrontEnd/src/main.ts`; `src/router/index.ts` | Vue/Pinia setup, lazy-loaded pages, login/admin route metadata. |
| Login and home navigation | `src/views/LoginView.vue`; `src/views/HomeView.vue`; `src/utils/userInfo.ts` | Login UI, module entry points and client-side user state. |
| HTTP/auth/upload helpers | `src/utils/request.ts`; `src/utils/authUtils.ts`; `src/utils/upload.ts` | Axios defaults/interceptors, token handling and shared file/chunk upload. |
| Attendance | `src/views/AttendanceSystemView.vue`; `src/views/AttendanceApplyView.vue`; `src/api/attendance.ts` | Attendance list, apply/approve flow and attendance API calls. |
| Display files | `src/views/DisplayFileView.vue`; `src/views/DisplayFileUploadView.vue` | Browse image groups/PDFs and upload display files. |
| Video | `src/views/VideoManagementView.vue`; `src/components/BatchVideoUpload.vue` | Video library, upload and compression actions. |
| Orders and order status | `src/views/OrderView.vue`; `src/views/OrderStatusView.vue`; `src/views/OrderStatusReportView.vue` | Order management and status/report pages. |
| Order records | `src/views/OrderRecordView.vue` | Order record, item, income/expense and attachment UI. |
| Inquiry and expenses | `src/views/InquiryView.vue`; `src/views/ExpenseManagementView.vue` | Inquiry communications and expense workflows. |
| Employee and access administration | `src/views/EmployeeManagementView.vue`; `src/views/LogManagement.vue` | Employee, role/permission and operation-log UI. |
| Other main modules | `src/views/MachineManagementNewView.vue`; `src/views/QuotationManagementView.vue`; `src/views/PhotoManagementView.vue`; `src/views/BlogManagementView.vue`; `src/views/TaskTrackView.vue`; `src/views/todo/TodoListView.vue`; `src/views/ContainerLayoutView.vue` | Machines/quotations, photos, work posts, tasks/todos and container layouts. |

Production build is `yarn build:prod` (`package.json`: typecheck then Vite production build). The production frontend image additionally installs via frozen Yarn lockfile and copies `dist/` into Nginx.

## Backend Index

| Feature | Path | Main responsibility |
|---|---|---|
| Flask app and blueprint registration | `soonwin-os-Python-Server/app/__init__.py` | App factory, DB binding, model imports and route registration; startup does not mutate schema. |
| Production entry/runtime | `soonwin-os-Python-Server/wsgi.py`; `/data/services/oa/backend.Dockerfile` | WSGI app and Waitress container command. |
| Authentication/authorization | `app/routes/user_routes.py`; `app/routes/auth_routes.py`; `app/utils/auth_utils.py` | TOTP login/token refresh and JWT auth/admin/module decorators. |
| Employees and permissions | `app/routes/user_routes.py`; `app/routes/permission_routes.py`; `app/models/employee.py`; `app/models/simple_permission.py` | Employee data, roles and route/module permission policy. |
| Display files | `app/routes/display_file_routes.py`; `app/models/display_file.py` | Image-group/PDF metadata, listing, upload and file/image routes. |
| Shared upload | `app/routes/upload_routes.py`; `app/utils/upload_utils.py` | Upload/chunk handling, file placement and shared upload helpers. |
| Video and compression | `app/routes/video_routes.py`; `app/models/video.py`; `app/utils/video_compressor.py` | Video records, processing endpoints and FFmpeg compression; image includes FFmpeg. |
| Attendance | `app/routes/attendance_routes.py`; `app/models/attendance_operation.py`; `app/routes/punch_routes.py` | Attendance operations/approval plus punch/device workflows. |
| Orders and status | `app/routes/order_routes.py`; `app/routes/order_status_routes.py`; `app/models/order.py`; `app/models/order_status.py` | Order CRUD/statistics and order status/task/media workflow. |
| Order records | `app/routes/order_record_routes.py`; `app/models/order_record.py` | Record items, income/expense and screenshot endpoints. |
| Inquiry and expense | `app/routes/inquiry_routes.py`; `app/models/inquiry.py`; `app/routes/expense_routes.py`; `app/models/expense.py` | Inquiry communications/media and expense allocations/targets. |
| Supporting modules | `app/routes/machine_routes.py`; `app/routes/photo_routes.py`; `app/routes/blog_routes.py`; `app/routes/task_routes.py`; `app/routes/todo_routes.py`; matching `app/models/` modules | Machine/photo, posts, tasks and todo APIs/data. |
| Customers and layouts | `app/routes/customer_routes.py`; `app/routes/container_layout_routes.py`; `app/routes/warehouse_routes.py` | Customer records, saved container layouts and warehouse map/item APIs. |
| Schema history | `migrations/env.py`; `migrations/versions/`; `migrations/archive/legacy_versions/`; `docs/database/SCHEMA_BASELINE.md` | Standalone baseline and schema migration policy; archived revisions are historical only. |

`config.py` selects `soonwin_oa_dev.db` for port 5001 and `soonwin_oa.db` otherwise. Application creation no longer calls `db.create_all()`; schema changes belong to explicit Alembic commands. The production WSGI entry does not apply migrations during startup.

## Database Index

- Production SQLite file: `/data/backup/oa/soonwin_oa.db`, bind-mounted read/write into backend as `/app/soonwin_oa.db`.
- Development SQLite file: `soonwin-os-Python-Server/soonwin_oa_dev.db` (port 5001 configuration).
- DB access: `soonwin-os-Python-Server/extensions.py` (`db`, `migrate`); app configuration: `config.py`; model definitions: `app/models/`.
- Initialization/migrations: application startup does not mutate schema; active Alembic revisions are in `migrations/versions/`, legacy revisions are archived, and cross-platform maintenance is provided by `soonwin-os-Python-Server/migrations/tools/oa_db.py`.
- Important tables: `Employee` (staff/account identity); `role` and `role_permission_simple` (simplified roles); `Order` and `order_status` (orders and progress); `OrderRecord`, `OrderRecordItem`, `OrderRecordIncome`, `OrderRecordExpense` (commercial records); `Inquiry` and `InquiryCommunication` (inquiries/history); `Expense` and allocation/target tables (expense workflow); `AttendanceOperation` and `PunchRecord` (attendance operations/punches); `DisplayFile` (display-file metadata); `videos` and `photos` (media metadata); `container_layout` (saved layouts); `warehouse_maps`, `warehouse_items`, `warehouse_objects` (warehouse layouts/items); `task*` and `todo*` (task tracking/todos). Verify each model before changing a table.
- Backup references: SER9 scheduled Restic job is `/etc/systemd/system/ser9-restic-backup.service` + `.timer`, implemented by `/usr/local/sbin/ser9-restic-backup.sh` (backs up `/data/projects/oa`, `/data/services/oa`, `/data/backup/oa`); Windows-specific SQLite backup code is `windows-tools/oa_database_backup.py` and `windows-tools/oa_backup_scheduler.py`. Backup policy/config is outside this index's authority; verify it before relying on recovery.
- Schema baseline and adoption policy: [`docs/database/SCHEMA_BASELINE.md`](database/SCHEMA_BASELINE.md). Production was adopted to `baseline_20261006` on 2026-10-06 after exact verification.

## API Index

Most blueprints are registered under `/api` in `app/__init__.py`. Auth refresh uses `/api/auth`; `user_routes.py` is also registered under `/api`. Punch routes carry `/api` in their own route strings and are registered without another prefix.

| API | Backend implementation | Frontend caller |
|---|---|---|
| `/api/totp/login`, `/api/employees` | `app/routes/user_routes.py` | `src/views/LoginView.vue`; `src/views/EmployeeManagementView.vue` |
| `/api/auth/refresh` | `app/routes/auth_routes.py` | `src/utils/request.ts` |
| `/api/display-file/*` | `app/routes/display_file_routes.py` | `src/views/DisplayFileView.vue`; `src/views/DisplayFileUploadView.vue` |
| `/api/upload*` | `app/routes/upload_routes.py` | `src/utils/upload.ts`; upload-capable views/components |
| `/api/videos*` | `app/routes/video_routes.py` | `src/views/VideoManagementView.vue`; `src/components/BatchVideoUpload.vue` |
| `/api/attendance/*` | `app/routes/attendance_routes.py` | `src/api/attendance.ts`; attendance views |
| `/api/orders*`, `/api/order-status*` | `app/routes/order_routes.py`; `app/routes/order_status_routes.py` | `src/views/OrderView.vue`; order status views |
| `/api/order-records*` | `app/routes/order_record_routes.py` | `src/views/OrderRecordView.vue` |
| `/api/inquiries*` | `app/routes/inquiry_routes.py` | `src/views/InquiryView.vue`; `src/views/OrderView.vue` |
| `/api/expenses*` | `app/routes/expense_routes.py` | `src/views/ExpenseManagementView.vue`; `src/views/OrderView.vue` |
| `/api/machines_new*`, `/api/photos*` | `app/routes/machine_routes.py`; `app/routes/photo_routes.py` | `src/views/MachineManagementNewView.vue`; `src/views/PhotoManagementView.vue` |
| `/api/tasks*`, `/api/todos*` | `app/routes/task_routes.py`; `app/routes/todo_routes.py` | `src/views/TaskTrackView.vue`; `src/views/todo/TodoListView.vue`; `src/api/todo.ts` |
| `/api/customers*`, `/api/container-layouts*`, `/api/maps*` | `app/routes/customer_routes.py`; `app/routes/container_layout_routes.py`; `app/routes/warehouse_routes.py` | `src/views/CustomerManagementView.vue`; `src/views/ContainerLayoutView.vue`; `public/warehouse-editor.html` |

## Feature → Code Map

| Feature | Frontend | Backend | Model / utility | Related API |
|---|---|---|---|---|
| Login and permissions | `src/views/LoginView.vue`; `src/router/index.ts`; `src/utils/request.ts` | `app/routes/user_routes.py`; `app/routes/permission_routes.py`; `app/utils/auth_utils.py` | `app/models/employee.py`; `app/models/simple_permission.py` | `/api/totp/login`, `/api/auth/refresh`, `/api/permissions` |
| Employees | `src/views/EmployeeManagementView.vue` | `app/routes/user_routes.py` | `app/models/employee.py`; `app/models/employee_device.py` | `/api/employees`, `/api/employee/<emp_id>` |
| Orders/status | `src/views/OrderView.vue`; `src/views/OrderStatusView.vue`; `src/views/OrderStatusReportView.vue` | `app/routes/order_routes.py`; `app/routes/order_status_routes.py` | `app/models/order.py`; `app/models/order_status.py` | `/api/orders`, `/api/order-status*` |
| Order records | `src/views/OrderRecordView.vue` | `app/routes/order_record_routes.py` | `app/models/order_record.py`; upload helpers | `/api/order-records*` |
| Inquiry | `src/views/InquiryView.vue` | `app/routes/inquiry_routes.py` | `app/models/inquiry.py`; `app/models/inquiry_communication_media.py` | `/api/inquiries*` |
| Expenses | `src/views/ExpenseManagementView.vue`; `src/views/OrderView.vue` | `app/routes/expense_routes.py` | `app/models/expense.py`; `app/models/cost_allocation.py` | `/api/expenses*`, `/api/expense-allocations` |
| Display-file upload/view | `src/views/DisplayFileUploadView.vue`; `src/views/DisplayFileView.vue` | `app/routes/display_file_routes.py` | `app/models/display_file.py`; `app/utils/upload_utils.py` | `/api/display-file/upload`, `/api/display-file/list`, `/api/display-file/<uuid>/images` |
| Generic file uploads | `src/utils/upload.ts`; `src/components/BatchVideoUpload.vue` | `app/routes/upload_routes.py` | `app/utils/upload_utils.py` | `/api/upload`, `/api/upload/chunk`, `/api/upload/move` |
| Video upload/compression | `src/views/VideoManagementView.vue`; `src/components/BatchVideoUpload.vue` | `app/routes/video_routes.py` | `app/models/video.py`; `app/utils/video_compressor.py` | `/api/videos`, `/api/videos/<id>/compress` |
| Attendance/punch | `src/views/AttendanceSystemView.vue`; `src/views/AttendanceApplyView.vue`; `src/views/PunchView.vue` | `app/routes/attendance_routes.py`; `app/routes/punch_routes.py` | `app/models/attendance_operation.py`; `app/models/punch_record.py` | `/api/attendance/*`, `/api/device-clock-in` |
| Photos/machines/quotations | `src/views/PhotoManagementView.vue`; `src/views/MachineManagementNewView.vue`; `src/views/QuotationManagementView.vue` | `app/routes/photo_routes.py`; `app/routes/machine_routes.py`; `app/routes/quotation_routes.py`; `app/routes/quotation_temp_routes.py` | `app/models/photo.py`; `app/models/machine_new.py`; `app/models/quotation_temp.py` | `/api/photos*`, `/api/machines_new*`, `/api/quotation-temp*` |
| Customers/container/warehouse layouts | `src/views/CustomerManagementView.vue`; `src/views/ContainerLayoutView.vue`; `public/warehouse-editor.html` | `app/routes/customer_routes.py`; `app/routes/container_layout_routes.py`; `app/routes/warehouse_routes.py` | `app/models/customer.py`; `app/models/container_layout.py`; `app/models/warehouse.py` | `/api/customers*`, `/api/container-layouts*`, `/api/maps*` |
| Tasks/todos | `src/views/TaskTrackView.vue`; `src/views/todo/TodoListView.vue`; `src/api/todo.ts` | `app/routes/task_routes.py`; `app/routes/todo_routes.py` | `app/models/task.py`; `app/models/todo.py`; related comment/visibility models | `/api/tasks*`, `/api/todos*` |
| Blog/work records | `src/views/BlogManagementView.vue`; `src/components/BlogCommentSection.vue` | `app/routes/blog_routes.py` | `app/models/blog.py` | `/api/posts*` |

## Production / Deployment Map

- Compose: `/data/services/oa/compose.yaml`; project `soonwin-oa`, services `frontend` and `backend`.
- Build contexts: frontend `/data/projects/oa/soonwin-oa-VUE-FrontEnd`; backend `/data/projects/oa/soonwin-os-Python-Server`. Production Dockerfiles are `/data/services/oa/frontend.Dockerfile` and `backend.Dockerfile`.
- Frontend image: Node 22 build stage runs frozen Yarn install and `npm run build:prod`; Nginx 1.29 Alpine serves copied `dist/` on container port 80, published on host port 80.
- Backend image: Python 3.12 slim with FFmpeg; Waitress runs `wsgi:application` on `0.0.0.0:5000`. Compose exposes 5000 only to its network, not a host port.
- Nginx: `/data/services/oa/nginx.conf`; `/api/` proxies to `backend:5000`, SPA routes fall back to `index.html`, `/assets/` can proxy to backend.
- Backend bind mounts: source `soonwin-os-Python-Server/assets/` → `/app/assets`; production DB `/data/backup/oa/soonwin_oa.db` → `/app/soonwin_oa.db`.
- Frontend bind mount: `/data/services/oa/nginx.conf` → `/etc/nginx/conf.d/default.conf` (read-only). Frontend static bundle is baked into the image at build time; updating source alone does not update the running image.
- Production container names observed from Compose: `soonwin-oa-frontend-1` and `soonwin-oa-backend-1`. Recheck `docker ps` for live state; do not restart or rebuild as part of inspection.
- SER9 Restic backup script includes source, service configuration, and `/data/backup/oa`; this is a backup reference, not a guarantee of a successful recent restore.

## Docker / Build Network

- Builder: `ser9-mihomo-buildkit`
- Driver: `docker-container`
- Runbook: `docs/operations/DOCKER_BUILD_NETWORK.md`

## Modification Guide

- Change a page or route guard → start with the relevant `src/views/*.vue`, `src/router/index.ts`, then its API caller and shared request/auth helper.
- Change an API contract → inspect frontend caller, route registration/prefix in `app/__init__.py`, route implementation, auth decorators, model, and response interceptor in `src/utils/request.ts`.
- Change schema/data → inspect model, every related route, migration history and production DB mount; prepare a reviewed migration and backup/rollback plan before any production operation.
- Change file upload/storage → inspect calling view/component, `src/utils/upload.ts`, upload/display route, `app/utils/upload_utils.py`, Compose assets mount and Nginx body-size/proxy rules.
- Change video compression → inspect video UI/upload component, `app/routes/video_routes.py`, `app/utils/video_compressor.py`, `app/models/video.py`, and backend FFmpeg image setup.
- Change production deployment → inspect `/data/services/oa/compose.yaml`, both Dockerfiles, Nginx config and the relevant `/usr/local/bin/oa-*` helper before proposing an operation.
