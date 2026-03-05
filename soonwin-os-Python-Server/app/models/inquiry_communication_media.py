from extensions import db
from datetime import datetime
import os


class InquiryCommunicationMedia(db.Model):
    __tablename__ = "InquiryCommunicationMedia"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="自增主键")
    communication_id = db.Column(db.Integer, db.ForeignKey('InquiryCommunication.id'), nullable=False, comment="关联沟通记录ID")
    file_name = db.Column(db.String(255), nullable=False, comment="文件原始名称")
    file_path = db.Column(db.String(500), nullable=False, comment="文件保存路径")
    thumb_path = db.Column(db.String(500), comment="缩略图路径")
    file_size = db.Column(db.Integer, comment="文件大小（字节）")
    file_type = db.Column(db.String(50), nullable=False, comment="文件类型：image/video")
    upload_time = db.Column(db.DateTime, default=datetime.now, comment="上传时间")
    
    # 定义与沟通记录的关系
    communication = db.relationship('InquiryCommunication', backref=db.backref('media_files', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            "id": self.id,
            "communication_id": self.communication_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "thumb_path": self.thumb_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "upload_time": self.upload_time.strftime('%Y-%m-%d %H:%M:%S') if self.upload_time else None
        }
    
    def delete_file(self):
        """删除文件和缩略图"""
        try:
            # 删除主文件
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            
            # 删除缩略图（如果存在）
            if self.thumb_path and os.path.exists(self.thumb_path):
                os.remove(self.thumb_path)
                
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False