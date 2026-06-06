"""博客功能数据模型"""
from .. import db
from datetime import datetime


class BlogPost(db.Model):
    """博客文章表"""
    __tablename__ = 'blog_post'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False, default='')
    author = db.Column(db.String(100), nullable=False, default='')
    author_id = db.Column(db.String(100), nullable=False, default='')
    is_draft = db.Column(db.Integer, nullable=False, default=0)  # 0=已发布, 1=草稿
    is_deleted = db.Column(db.Integer, nullable=False, default=0)  # 0=正常, 1=已删除
    repost_from = db.Column(db.Integer, nullable=True)  # 转发来源的博文ID
    edit_version = db.Column(db.Integer, nullable=False, default=1)  # 当前版本号
    search_field = db.Column(db.Text, nullable=False, default='')  # 搜索用冗余字段
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(100), nullable=True)

    # 关系
    media_list = db.relationship('BlogMedia', backref='post', lazy='dynamic',
                                  cascade='all, delete-orphan')
    comments = db.relationship('BlogComment', backref='post', lazy='dynamic',
                                cascade='all, delete-orphan')
    likes = db.relationship('BlogLike', backref='post', lazy='dynamic',
                             cascade='all, delete-orphan')
    favorites = db.relationship('BlogFavorite', backref='post', lazy='dynamic',
                                 cascade='all, delete-orphan')
    edit_histories = db.relationship('BlogEditHistory', backref='post', lazy='dynamic',
                                      cascade='all, delete-orphan',
                                      order_by='BlogEditHistory.version.desc()')

    def to_dict(self, include_media=True, include_repost=False):
        data = {
            'id': self.id,
            'content': self.content,
            'author': self.author,
            'author_id': self.author_id,
            'is_draft': bool(self.is_draft),
            'is_deleted': bool(self.is_deleted),
            'repost_from': self.repost_from,
            'edit_version': self.edit_version,
            'comment_count': self.comments.filter_by(is_deleted=0).count(),
            'like_count': self.likes.count(),
            'favorite_count': self.favorites.count(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }

        if include_media:
            data['media'] = [m.to_dict() for m in self.media_list.all()]

        if include_repost and self.repost_from:
            repost = BlogPost.query.get(self.repost_from)
            if repost and not repost.is_deleted:
                data['repost'] = repost.to_dict(include_media=True, include_repost=False)

        return data


class BlogMedia(db.Model):
    """博客媒体文件表"""
    __tablename__ = 'blog_media'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    media_type = db.Column(db.String(10), nullable=False, default='image')  # 'image' 或 'video'
    file_path = db.Column(db.String(500), nullable=False)  # 相对于 assets/PostsMedia 的路径（原图，灯箱查看原图时用）
    thumbnail_path = db.Column(db.String(500), nullable=True, default='')  # 缩略图 WebP（800px，列表网格用）
    display_path = db.Column(db.String(500), nullable=True, default='')  # 展示图 WebP（1600px，展开轮播用）
    original_filename = db.Column(db.String(255), nullable=True, default='')
    file_size = db.Column(db.BigInteger, nullable=True, default=0)
    width = db.Column(db.Integer, nullable=True, default=0)
    height = db.Column(db.Integer, nullable=True, default=0)
    duration = db.Column(db.Float, nullable=True, default=0.0)  # 视频时长（秒）
    compress_status = db.Column(db.String(20), nullable=False, default='pending')
    # compress_status: 'pending'(等待处理), 'processing'(处理中), 'success'(成功), 'failed'(失败)
    # 图片直接设为 'success'，视频进入队列处理
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'media_type': self.media_type,
            'file_path': self.file_path,
            'thumbnail_path': self.thumbnail_path or '',
            'display_path': self.display_path or '',
            'original_filename': self.original_filename or '',
            'file_size': self.file_size or 0,
            'width': self.width or 0,
            'height': self.height or 0,
            'duration': self.duration or 0.0,
            'compress_status': self.compress_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            # 计算字段：是否已生成 v2 WebP 缩略图（零 DB 开销）
            # 旧图片 display_path 为空 → False；新图片两路径均非空 → True
            'has_v2_thumbnails': bool(self.display_path and self.thumbnail_path),
        }


class BlogEditHistory(db.Model):
    """博客编辑历史表（旧版本记录）"""
    __tablename__ = 'blog_edit_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)  # 版本号
    content = db.Column(db.Text, nullable=False, default='')
    media_snapshot = db.Column(db.Text, nullable=True, default='')  # JSON: 当时的媒体文件快照
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    edited_by = db.Column(db.String(100), nullable=True, default='')

    def to_dict(self, include_full_content=False):
        data = {
            'id': self.id,
            'post_id': self.post_id,
            'version': self.version,
            'edited_by': self.edited_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
        if include_full_content:
            data['content'] = self.content
            data['media_snapshot'] = self.media_snapshot
        return data


class BlogComment(db.Model):
    """博客评论/留言表"""
    __tablename__ = 'blog_comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    author = db.Column(db.String(100), nullable=False, default='匿名')
    author_id = db.Column(db.String(100), nullable=True, default='')
    content = db.Column(db.Text, nullable=False, default='')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    is_deleted = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'author': self.author,
            'author_id': self.author_id or '',
            'content': self.content,
            'is_deleted': bool(self.is_deleted),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class BlogLike(db.Model):
    """博客点赞表"""
    __tablename__ = 'blog_like'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='uq_post_user_like'),
    )


class BlogFavorite(db.Model):
    """博客收藏表"""
    __tablename__ = 'blog_favorite'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='uq_post_user_fav'),
    )
