"""Warehouse map, item and object models."""

from datetime import datetime

from extensions import db


class WarehouseMap(db.Model):
    __tablename__ = 'warehouse_maps'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    width_mm = db.Column(db.Integer, nullable=False)
    length_mm = db.Column(db.Integer, nullable=False)
    grid_columns = db.Column(db.Integer, nullable=False)
    grid_rows = db.Column(db.Integer, nullable=False)
    revision = db.Column(db.Integer, nullable=False, default=1)
    active = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    items = db.relationship('WarehouseItem', back_populates='map', cascade='all, delete-orphan')
    objects = db.relationship('WarehouseObject', back_populates='map', cascade='all, delete-orphan')


class WarehouseItem(db.Model):
    __tablename__ = 'warehouse_items'
    __table_args__ = (
        db.Index('ix_warehouse_items_map_deleted', 'map_id', 'is_deleted'),
        db.Index('ix_warehouse_items_map_status', 'map_id', 'status'),
        db.Index('ix_warehouse_items_map_owner', 'map_id', 'owner_group'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    map_id = db.Column(db.Integer, db.ForeignKey('warehouse_maps.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    x_mm = db.Column(db.Integer, nullable=False)
    y_mm = db.Column(db.Integer, nullable=False)
    length_mm = db.Column(db.Integer, nullable=False)
    width_mm = db.Column(db.Integer, nullable=False)
    height_mm = db.Column(db.Integer, nullable=False)
    rotation = db.Column(db.Integer, nullable=False, default=0)
    owner_group = db.Column(db.String(20), nullable=False, default='OVERSEAS')
    color = db.Column(db.String(20), nullable=False, default='#4d96ff')
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    stocked_date = db.Column(db.Date, nullable=True)
    stocked_by = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), nullable=True)
    remark = db.Column(db.Text, nullable=True)
    shipped_date = db.Column(db.Date, nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    shipped_by = db.Column(db.String(20), db.ForeignKey('Employee.emp_id'), nullable=True)
    shipped_remark = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Integer, nullable=False, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    map = db.relationship('WarehouseMap', back_populates='items')


class WarehouseObject(db.Model):
    __tablename__ = 'warehouse_objects'
    __table_args__ = (
        db.Index('ix_warehouse_objects_map_deleted', 'map_id', 'is_deleted'),
        db.Index('ix_warehouse_objects_map_type', 'map_id', 'type'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    map_id = db.Column(db.Integer, db.ForeignKey('warehouse_maps.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(30), nullable=False, default='OTHER')
    x_mm = db.Column(db.Integer, nullable=False)
    y_mm = db.Column(db.Integer, nullable=False)
    length_mm = db.Column(db.Integer, nullable=False)
    width_mm = db.Column(db.Integer, nullable=False)
    rotation = db.Column(db.Integer, nullable=False, default=0)
    show_text = db.Column(db.Integer, nullable=False, default=0)
    pattern = db.Column(db.String(20), nullable=False, default='solid')
    blocks_cargo = db.Column(db.Integer, nullable=False, default=1)
    color = db.Column(db.String(20), nullable=False, default='#687386')
    is_deleted = db.Column(db.Integer, nullable=False, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    map = db.relationship('WarehouseMap', back_populates='objects')
