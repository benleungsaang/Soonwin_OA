import os
import uuid
from datetime import datetime
from PIL import Image, ImageOps
from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from modules.database import get_db_conn

posts_bp = Blueprint('posts', __name__)

UPLOAD_FOLDER = 'data/uploads/posts'
THUMB_SIZE = (300, 300)
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_media_file(file, post_id=''):
    """保存上传的文件并返回相对路径"""
    if not file or file.filename == '':
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}.{ext}"

    folder = os.path.join(UPLOAD_FOLDER, post_id) if post_id else UPLOAD_FOLDER
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, unique_name)
    file.save(filepath)

    relative_path = os.path.join(post_id, unique_name) if post_id else unique_name
    return relative_path.replace('\\', '/')

def generate_thumbnail(filepath):
    """为图片生成缩略图，返回缩略图文件名"""
    try:
        img = Image.open(filepath)
        # 修正 EXIF 方向（手机照片旋转问题）
        img = ImageOps.exif_transpose(img)
        img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
        # 转换 RGBA/P 为 RGB（JPEG 不支持透明）
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        dir_name = os.path.dirname(filepath)
        base_name = os.path.basename(filepath)
        thumb_name = f"thumb_{base_name.rsplit('.', 1)[0]}.jpg"
        thumb_path = os.path.join(dir_name, thumb_name)
        img.save(thumb_path, 'JPEG', quality=80)
        return thumb_name
    except Exception as e:
        print(f'缩略图生成失败: {e}')
        return None

@posts_bp.route('', methods=['GET'])
def get_posts():
    """获取所有动态（分页），支持 search 参数搜索内容和留言"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str).strip()
    offset = (page - 1) * per_page

    with get_db_conn() as conn:
        cursor = conn.cursor()

        if search:
            cursor.execute('''
                SELECT COUNT(DISTINCT p.id) as total FROM posts p
                LEFT JOIN post_comments pc ON pc.post_id = p.id
                WHERE p.content LIKE ? OR pc.content LIKE ?
            ''', (f'%{search}%', f'%{search}%'))
            total = cursor.fetchone()['total']

            cursor.execute('''
                SELECT DISTINCT p.* FROM posts p
                LEFT JOIN post_comments pc ON pc.post_id = p.id
                WHERE p.content LIKE ? OR pc.content LIKE ?
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            ''', (f'%{search}%', f'%{search}%', per_page, offset))
        else:
            cursor.execute('SELECT COUNT(*) as total FROM posts')
            total = cursor.fetchone()['total']

            cursor.execute('''
                SELECT * FROM posts
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
        posts = []
        for row in cursor.fetchall():
            post_id = row['id']

            cursor.execute('''
                SELECT * FROM post_media
                WHERE post_id = ?
                ORDER BY created_at ASC
            ''', (post_id,))
            media = []
            for m in cursor.fetchall():
                media.append({
                    'id': m['id'],
                    'mediaType': m['media_type'],
                    'url': f'/api/posts/media/{m["file_path"]}',
                    'thumbnailUrl': f'/api/posts/media/{m["file_path"]}?thumb=1' if m['media_type'] == 'image' else f'/api/posts/media/{m["file_path"]}',
                    'createdAt': m['created_at']
                })

            cursor.execute('SELECT COUNT(*) as count FROM post_comments WHERE post_id = ?', (post_id,))
            comment_count = cursor.fetchone()['count']

            # 转发原帖信息
            repost = None
            if row['repost_from']:
                cursor.execute('SELECT * FROM posts WHERE id = ?', (row['repost_from'],))
                orig = cursor.fetchone()
                if orig:
                    cursor.execute('SELECT * FROM post_media WHERE post_id = ? ORDER BY created_at', (orig['id'],))
                    orig_media = [{
                        'id': m['id'],
                        'mediaType': m['media_type'],
                        'url': f'/api/posts/media/{m["file_path"]}',
                        'thumbnailUrl': f'/api/posts/media/{m["file_path"]}?thumb=1' if m['media_type'] == 'image' else f'/api/posts/media/{m["file_path"]}',
                        'createdAt': m['created_at']
                    } for m in cursor.fetchall()]
                    repost = {
                        'id': orig['id'],
                        'content': orig['content'],
                        'media': orig_media,
                        'createdAt': orig['created_at']
                    }

            posts.append({
                'id': post_id,
                'content': row['content'],
                'media': media,
                'commentCount': comment_count,
                'repost': repost,
                'createdAt': row['created_at'],
                'updatedAt': row['updated_at']
            })

        return jsonify({
            'posts': posts,
            'total': total,
            'page': page,
            'perPage': per_page,
            'totalPages': (total + per_page - 1) // per_page
        })

@posts_bp.route('', methods=['POST'])
def create_post():
    """创建新动态（支持多格式上传和转发）"""
    content = request.form.get('content', '')
    repost_from = request.form.get('repostFrom', '')
    now = datetime.now().isoformat()
    post_id = str(datetime.now().timestamp() * 1000)

    with get_db_conn() as conn:
        cursor = conn.cursor()

        # 如果是转发，校验原帖存在
        repost_data = None
        if repost_from:
            cursor.execute('SELECT * FROM posts WHERE id = ?', (repost_from,))
            repost_row = cursor.fetchone()
            if repost_row:
                repost_data = {
                    'id': repost_row['id'],
                    'content': repost_row['content'],
                    'createdAt': repost_row['created_at']
                }
            else:
                repost_from = ''  # 原帖不存在，当作普通帖子

        cursor.execute('''
            INSERT INTO posts (id, content, repost_from, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (post_id, content, repost_from, now, now))

        files = request.files.getlist('media')
        for file in files:
            if file.filename == '':
                continue

            if allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                media_type = 'image'
            elif allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
                media_type = 'video'
            else:
                continue

            file.seek(0, 2)
            size = file.tell()
            file.seek(0)

            if media_type == 'image' and size > MAX_IMAGE_SIZE:
                continue
            if media_type == 'video' and size > MAX_VIDEO_SIZE:
                continue

            file_path = save_media_file(file, post_id)
            if file_path:
                # 为图片生成缩略图
                if media_type == 'image':
                    full_path = os.path.join(UPLOAD_FOLDER, file_path)
                    generate_thumbnail(full_path)
                cursor.execute('''
                    INSERT INTO post_media (post_id, media_type, file_path, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (post_id, media_type, file_path, now))

        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        row = cursor.fetchone()

        cursor.execute('SELECT * FROM post_media WHERE post_id = ? ORDER BY created_at', (post_id,))
        media = [{
            'id': m['id'],
            'mediaType': m['media_type'],
            'url': f'/api/posts/media/{m["file_path"]}',
            'thumbnailUrl': f'/api/posts/media/{m["file_path"]}?thumb=1' if m['media_type'] == 'image' else f'/api/posts/media/{m["file_path"]}',
            'createdAt': m['created_at']
        } for m in cursor.fetchall()]

        result = {
            'id': post_id,
            'content': content,
            'media': media,
            'commentCount': 0,
            'createdAt': now,
            'updatedAt': now
        }
        if repost_data:
            result['repost'] = repost_data

        return jsonify(result), 201

@posts_bp.route('/<post_id>', methods=['GET'])
def get_post(post_id):
    """获取单条动态详情"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Post not found'}), 404

        cursor.execute('SELECT * FROM post_media WHERE post_id = ? ORDER BY created_at', (post_id,))
        media = [{
            'id': m['id'],
            'mediaType': m['media_type'],
            'url': f'/api/posts/media/{m["file_path"]}',
            'thumbnailUrl': f'/api/posts/media/{m["file_path"]}?thumb=1' if m['media_type'] == 'image' else f'/api/posts/media/{m["file_path"]}',
            'createdAt': m['created_at']
        } for m in cursor.fetchall()]

        cursor.execute('SELECT COUNT(*) as count FROM post_comments WHERE post_id = ?', (post_id,))
        comment_count = cursor.fetchone()['count']

        repost = None
        if row['repost_from']:
            cursor.execute('SELECT * FROM posts WHERE id = ?', (row['repost_from'],))
            orig = cursor.fetchone()
            if orig:
                cursor.execute('SELECT * FROM post_media WHERE post_id = ? ORDER BY created_at', (orig['id'],))
                orig_media = [{
                    'id': m['id'],
                    'mediaType': m['media_type'],
                    'url': f'/api/posts/media/{m["file_path"]}',
                    'thumbnailUrl': f'/api/posts/media/{m["file_path"]}?thumb=1' if m['media_type'] == 'image' else f'/api/posts/media/{m["file_path"]}',
                    'createdAt': m['created_at']
                } for m in cursor.fetchall()]
                repost = {
                    'id': orig['id'],
                    'content': orig['content'],
                    'media': orig_media,
                    'createdAt': orig['created_at']
                }

        return jsonify({
            'id': row['id'],
            'content': row['content'],
            'media': media,
            'commentCount': comment_count,
            'repost': repost,
            'createdAt': row['created_at'],
            'updatedAt': row['updated_at']
        })

@posts_bp.route('/<post_id>', methods=['PUT'])
def update_post(post_id):
    """更新动态内容"""
    data = request.get_json()
    now = datetime.now().isoformat()

    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM posts WHERE id = ?', (post_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Post not found'}), 404

        cursor.execute('''
            UPDATE posts SET content = ?, updated_at = ? WHERE id = ?
        ''', (data.get('content', ''), now, post_id))

        return jsonify({'id': post_id, 'updated': True})

@posts_bp.route('/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """删除动态及其媒体文件"""
    with get_db_conn() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT file_path FROM post_media WHERE post_id = ?', (post_id,))
        media_files = cursor.fetchall()

        cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Post not found'}), 404

        for m in media_files:
            filepath = os.path.join(UPLOAD_FOLDER, m['file_path'])
            if os.path.exists(filepath):
                os.remove(filepath)

        post_folder = os.path.join(UPLOAD_FOLDER, post_id)
        if os.path.exists(post_folder):
            try:
                os.rmdir(post_folder)
            except:
                pass

        return jsonify({'success': True})

@posts_bp.route('/media/<path:filename>', methods=['GET'])
def serve_media(filename):
    """提供媒体文件访问，支持 ?thumb=1 返回缩略图"""
    import os

    # 安全检查：防止路径遍历
    filename = filename.replace('..', '')
    use_thumb = request.args.get('thumb') == '1'

    if use_thumb:
        dir_name = os.path.dirname(filename)
        base_name = os.path.basename(filename)
        name_without_ext = base_name.rsplit('.', 1)[0]
        thumb_name = f"thumb_{name_without_ext}.jpg"
        thumb_filename = os.path.join(dir_name, thumb_name).replace('\\', '/') if dir_name else thumb_name
        thumb_filepath = os.path.join(UPLOAD_FOLDER, thumb_filename)
        if os.path.exists(thumb_filepath):
            filename = thumb_filename

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if ext in {'mp4', 'webm', 'ogg'}:
        mimetype = f'video/{ext}'
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)

    return send_from_directory(UPLOAD_FOLDER, filename)

# ========== 留言接口 ==========

@posts_bp.route('/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """获取某条帖子的所有留言"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM post_comments WHERE post_id = ? ORDER BY created_at ASC', (post_id,))
        comments = [{
            'id': row['id'],
            'postId': row['post_id'],
            'author': row['author'],
            'content': row['content'],
            'createdAt': row['created_at']
        } for row in cursor.fetchall()]
        return jsonify({'comments': comments})


@posts_bp.route('/<post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """给帖子添加留言"""
    data = request.get_json()
    if not data or not data.get('content', '').strip():
        return jsonify({'error': '留言内容不能为空'}), 400

    now = datetime.now().isoformat()
    comment_id = str(datetime.now().timestamp() * 1000)
    author = data.get('author', '匿名').strip() or '匿名'
    content = data['content'].strip()

    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM posts WHERE id = ?', (post_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Post not found'}), 404

        cursor.execute('''
            INSERT INTO post_comments (id, post_id, author, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (comment_id, post_id, author, content, now))

        return jsonify({
            'id': comment_id,
            'postId': post_id,
            'author': author,
            'content': content,
            'createdAt': now
        }), 201


@posts_bp.route('/<post_id>/comments/<comment_id>', methods=['DELETE'])
def delete_comment(post_id, comment_id):
    """删除留言"""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM post_comments WHERE id = ? AND post_id = ?', (comment_id, post_id))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Comment not found'}), 404
        return jsonify({'success': True})
