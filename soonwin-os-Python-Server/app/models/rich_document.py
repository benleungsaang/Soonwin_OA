from extensions import db

class RichDocument(db.Model):
    __tablename__ = 'rich_document'
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    html = db.Column(db.Text, nullable=False, default='')
    watermark = db.Column(db.Text, nullable=False, default='{}')
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

class RichMedia(db.Model):
    __tablename__ = 'rich_media'
    id = db.Column(db.String(32), primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('rich_document.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    mime = db.Column(db.String(80), nullable=False)
    size = db.Column(db.Integer, nullable=False)
