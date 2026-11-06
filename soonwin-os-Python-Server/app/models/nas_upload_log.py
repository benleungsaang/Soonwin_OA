from datetime import datetime

from extensions import db


class NasUploadLog(db.Model):
    """Server-confirmed outcome of a QR-authorized NAS whole-file upload."""
    __tablename__ = 'nas_upload_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    upload_id = db.Column(db.String(32), nullable=False, unique=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    operator_id = db.Column(db.String(20), nullable=True)
    operator_name = db.Column(db.String(50), nullable=False, default='未知账号')
    filename = db.Column(db.String(255), nullable=False, index=True)
    file_size = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(16), nullable=False)
    target_dir = db.Column(db.String(255), nullable=False)
