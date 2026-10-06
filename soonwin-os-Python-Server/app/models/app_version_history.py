from datetime import datetime

from extensions import db


class AppVersionHistory(db.Model):
    """OA 展示版本与版本历史记录。"""

    __tablename__ = 'app_version_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version = db.Column(db.String(20), nullable=False, unique=True, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    git_hash = db.Column(db.String(40), nullable=True)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text('CURRENT_TIMESTAMP'),
    )
    created_by = db.Column(db.String(20), nullable=True)

    def to_api_dict(self):
        return {
            'version': self.version,
            'date': self.date.isoformat() if self.date else None,
            'git': self.git_hash,
            'summary': self.description,
        }
