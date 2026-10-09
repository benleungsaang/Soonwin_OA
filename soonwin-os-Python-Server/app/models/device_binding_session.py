from datetime import datetime
from extensions import db


class DeviceBindingSession(db.Model):
    __tablename__ = 'device_binding_session'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    emp_id = db.Column(db.String(20), nullable=False, index=True)
    created_by = db.Column(db.String(20), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='waiting_scan', index=True)
    device_id = db.Column(db.String(100), nullable=True)
    device_info = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    scanned_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decided_by = db.Column(db.String(20), nullable=True)
