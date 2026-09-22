# Warehouse V1 DEV Schema

本记录对应当前 DEV 数据库中新增的 Warehouse V1 关系表。它不是旧 Alembic 历史的 reconciliation，也不修改旧表。

## Tables

### `warehouse_maps`

| Column | Type | Constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | VARCHAR(100) | NOT NULL |
| `width_mm` | INTEGER | NOT NULL |
| `length_mm` | INTEGER | NOT NULL |
| `grid_columns` | INTEGER | NOT NULL |
| `grid_rows` | INTEGER | NOT NULL |
| `revision` | INTEGER | NOT NULL, starts at 1 |
| `active` | INTEGER | NOT NULL, 0/1 |
| `created_at` | DATETIME | NOT NULL |
| `updated_at` | DATETIME | NOT NULL |

### `warehouse_items`

| Column | Type | Constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `map_id` | INTEGER | NOT NULL, FK `warehouse_maps.id` ON DELETE CASCADE |
| `name` | VARCHAR(200) | NOT NULL |
| `x_mm`, `y_mm` | INTEGER | NOT NULL |
| `length_mm`, `width_mm`, `height_mm` | INTEGER | NOT NULL |
| `rotation` | INTEGER | NOT NULL, 0/90/180/270 |
| `owner_group` | VARCHAR(20) | NOT NULL, OVERSEAS/OTHER |
| `color` | VARCHAR(20) | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, ACTIVE/SHIPPED |
| `stocked_date` | DATE | nullable |
| `stocked_by` | VARCHAR(20) | FK `Employee.emp_id`, nullable |
| `remark` | TEXT | nullable |
| `shipped_date` | DATE | nullable |
| `shipped_at` | DATETIME | nullable |
| `shipped_by` | VARCHAR(20) | FK `Employee.emp_id`, nullable |
| `shipped_remark` | TEXT | nullable |
| `is_deleted` | INTEGER | NOT NULL, 0/1 |
| `deleted_at` | DATETIME | nullable |
| `created_at`, `updated_at` | DATETIME | NOT NULL |

Indexes:

- `ix_warehouse_items_map_deleted (map_id, is_deleted)`
- `ix_warehouse_items_map_status (map_id, status)`
- `ix_warehouse_items_map_owner (map_id, owner_group)`

### `warehouse_objects`

| Column | Type | Constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `map_id` | INTEGER | NOT NULL, FK `warehouse_maps.id` ON DELETE CASCADE |
| `name` | VARCHAR(200) | NOT NULL |
| `type` | VARCHAR(30) | NOT NULL |
| `x_mm`, `y_mm` | INTEGER | NOT NULL |
| `length_mm`, `width_mm` | INTEGER | NOT NULL |
| `rotation` | INTEGER | NOT NULL, 0/90/180/270 |
| `show_text` | INTEGER | NOT NULL, 0/1 |
| `pattern` | VARCHAR(20) | NOT NULL |
| `blocks_cargo` | INTEGER | NOT NULL, 0/1 |
| `color` | VARCHAR(20) | NOT NULL |
| `is_deleted` | INTEGER | NOT NULL, 0/1 |
| `deleted_at` | DATETIME | nullable |
| `created_at`, `updated_at` | DATETIME | NOT NULL |

Indexes:

- `ix_warehouse_objects_map_deleted (map_id, is_deleted)`
- `ix_warehouse_objects_map_type (map_id, type)`

## Existing tables changed

None. The DEV schema was extended only with the three tables above. The old Alembic revision value remains unchanged.

## Deployment note

Production must be backed up and inspected before applying the equivalent three-table DDL. Do not replay old `034`-`044` migrations as part of Warehouse deployment.
