"""博客管理相关路由"""
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file, abort
from app.utils.simple_auth_utils import route_permission
from app.utils.auth_utils import require_auth, require_admin, get_user_id_from_token, get_user_role_from_token
from app.constants.simple_permission_constants import ROUTE_BLOG_MANAGE
from app.models.blog import BlogPost, BlogMedia, BlogEditHistory, BlogComment, BlogLike, BlogFavorite
from app.utils.upload_utils import (
    save_uploaded_file, generate_unique_filename, sanitize_filename,
    process_image_with_variants, process_video_with_variants,
    compress_video, get_processing_queue, UPLOAD_CONFIG
)
from extensions import db

blog_bp = Blueprint('blog', __name__)

# 博客媒体文件基础存储路径（相对于 app 目录）
POSTS_MEDIA_BASE = 'assets/PostsMedia'

_blog_app_instance = None


def set_app_instance(app):
    """设置 Flask 应用实例到处理队列"""
    global _blog_app_instance
    _blog_app_instance = app
    processing_queue = get_processing_queue()
    processing_queue.set_app_instance(app)

    # 启动时恢复：将遗留的 pending 视频重新加入转码队列
    with app.app_context():
        try:
            pending_media = BlogMedia.query.filter_by(media_type='video', compress_status='pending').all()
            base_dir = _get_posts_media_dir()
            for media in pending_media:
                abs_path = os.path.join(base_dir, media.file_path)
                if os.path.exists(abs_path):
                    _add_blog_video_transcode_task(media.id, abs_path)
                    print(f"[Blog] 恢复转码任务: media_id={media.id}")
        except Exception as e:
            print(f"[Blog] 启动恢复转码任务失败: {e}")


def _get_posts_media_dir():
    """获取博客媒体文件的绝对存储目录"""
    if _blog_app_instance:
        base_dir = os.path.join(_blog_app_instance.root_path, '..', POSTS_MEDIA_BASE)
    else:
        base_dir = os.path.join(current_app.root_path, '..', POSTS_MEDIA_BASE)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _get_current_user_name():
    """获取当前用户名"""
    from app.utils.auth_utils import get_user_id_from_token
    user_id = get_user_id_from_token()
    if not user_id:
        return '匿名'
    try:
        from app.models.employee import Employee
        emp = Employee.query.filter_by(emp_id=user_id).first()
        return emp.name if emp else user_id
    except Exception:
        return user_id


def _update_blog_media_after_compress(media_id, compressed_path, original_path):
    """视频压缩完成后更新 BlogMedia 记录"""
    media = BlogMedia.query.get(media_id)
    if not media:
        return
    try:
        base_dir = _get_posts_media_dir()
        rel_path = os.path.relpath(compressed_path, base_dir).replace('\\', '/')
        media.file_path = rel_path
        media.compress_status = 'success'
        media.file_size = os.path.getsize(compressed_path)
        db.session.commit()
        # 删除原始视频文件
        if os.path.exists(original_path) and original_path != compressed_path:
            try:
                os.remove(original_path)
            except Exception as e:
                print(f"删除原始视频文件失败: {e}")
    except Exception as e:
        media.compress_status = 'failed'
        db.session.commit()
        print(f"博客视频转码更新失败: {e}")


def _add_blog_video_transcode_task(media_id, absolute_file_path):
    """添加博客视频转码任务到处理队列"""
    from ..utils.upload_utils import get_processing_queue

    def transcode_handler(media_id, input_path):
        try:
            media = BlogMedia.query.get(media_id)
            if not media:
                return
            media.compress_status = 'processing'
            db.session.commit()

            file_prefix = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.dirname(input_path)
            compressed_path = os.path.join(output_dir, f"{file_prefix}_compressed.mp4")

            # 博客视频强制转 H.264（浏览器兼容），不用 copy 逻辑
            import subprocess
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
                '-vf', "scale='min(1280,iw)':-2,fps=30",
                '-c:a', 'aac', '-b:a', '96k',
                '-f', 'mp4', '-y', compressed_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0 and os.path.exists(compressed_path) and os.path.getsize(compressed_path) > 0:
                _update_blog_media_after_compress(media_id, compressed_path, input_path)
            else:
                media = BlogMedia.query.get(media_id)
                if media:
                    media.compress_status = 'failed'
                    db.session.commit()
        except Exception as e:
            print(f"博客视频转码异常: {e}")
            try:
                media = BlogMedia.query.get(media_id)
                if media:
                    media.compress_status = 'failed'
                    db.session.commit()
            except Exception:
                pass

    processing_queue = get_processing_queue()
    processing_queue.add_task(
        task_type="blog_video_transcode",
        handler_func=transcode_handler,
        media_id=media_id,
        input_path=absolute_file_path
    )


def _save_blog_media_file(file):
    """保存单个博客媒体文件，返回保存信息"""
    base_dir = _get_posts_media_dir()
    save_path, relative_path, filename = save_uploaded_file(file, base_dir)

    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    media_type = 'video' if ext in UPLOAD_CONFIG['VIDEO_ALLOWED_EXTENSIONS'] else 'image'

    return {
        'absolute_path': save_path,
        'relative_path': relative_path.replace('\\', '/'),
        'filename': filename,
        'media_type': media_type,
        'file_size': os.path.getsize(save_path),
        'ext': ext,
    }


# ============================================================
# 博文 CRUD
# ============================================================

@blog_bp.route('/posts', methods=['GET'])
@route_permission(ROUTE_BLOG_MANAGE)
def get_posts():
    """获取已发布的博文列表（分页+搜索+作者筛选）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)
        author = request.args.get('author', '', type=str)

        query = BlogPost.query.filter_by(is_deleted=0, is_draft=0)

        if author:
            query = query.filter(BlogPost.author == author)

        if search:
            query = query.filter(
                db.or_(
                    BlogPost.content.like(f'%{search}%'),
                    BlogPost.search_field.like(f'%{search}%')
                )
            )

        query = query.order_by(BlogPost.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        posts = []
        user_id = get_user_id_from_token()
        for post in pagination.items:
            post_dict = post.to_dict(include_media=True, include_repost=True)
            # 标记当前用户是否已点赞/收藏
            if user_id:
                post_dict['is_liked'] = BlogLike.query.filter_by(
                    post_id=post.id, user_id=user_id).first() is not None
                post_dict['is_favorited'] = BlogFavorite.query.filter_by(
                    post_id=post.id, user_id=user_id).first() is not None
            else:
                post_dict['is_liked'] = False
                post_dict['is_favorited'] = False
            posts.append(post_dict)

        return jsonify({
            'success': True,
            'data': {
                'posts': posts,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
            }
        })
    except Exception as e:
        print(f"获取博文列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts', methods=['POST'])
@route_permission(ROUTE_BLOG_MANAGE)
def create_post():
    """创建博文（支持两种模式）

    模式一（传统）：文件随 FormData 一并上传（media 字段）
    模式二（两阶段）：先逐个调 /posts/media/upload 上传文件，
                   再通过 uploaded_media 参数传入文件元数据 JSON
    """
    try:
        content = request.form.get('content', '')
        repost_from = request.form.get('repost_from', type=int)
        uploaded_media_json = request.form.get('uploaded_media', '')
        files = request.files.getlist('media')

        user_id = get_user_id_from_token()
        user_name = _get_current_user_name()

        has_uploaded = bool(uploaded_media_json)
        has_files = bool(files and any(f and f.filename for f in files))

        if not content and not has_files and not has_uploaded:
            return jsonify({'success': False, 'message': '内容或媒体不能都为空'}), 400

        post = BlogPost(
            content=content,
            author=user_name,
            author_id=user_id or '',
            repost_from=repost_from,
            search_field=content,
            edit_version=1,
        )
        db.session.add(post)
        db.session.flush()

        # 模式二：从预上传的文件元数据创建媒体记录
        if has_uploaded:
            try:
                uploaded_list = json.loads(uploaded_media_json)
                for item in uploaded_list:
                    _create_media_from_uploaded(item, post.id)
            except (json.JSONDecodeError, ValueError) as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'媒体数据格式错误: {str(e)}'}), 400

        # 模式一：处理直接上传的媒体文件（向后兼容）
        for file in files:
            if not file or not file.filename:
                continue
            _process_post_media(file, post.id)

        db.session.commit()

        # commit 之后再入队转码（避免 worker 线程查不到记录）
        _enqueue_video_tasks_for_post(post.id)

        return jsonify({'success': True, 'data': post.to_dict(include_media=True, include_repost=True)}), 201
    except Exception as e:
        db.session.rollback()
        print(f"创建博文失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def _process_post_media(file, post_id):
    """处理并保存博文媒体文件"""
    info = _save_blog_media_file(file)
    base_dir = _get_posts_media_dir()
    abs_path = info['absolute_path']
    ext = info['ext']

    thumbnail_path = ''
    display_path = ''
    width, height, duration = 0, 0, 0.0
    compress_status = 'success'

    file_prefix = os.path.splitext(info['filename'])[0]

    if info['media_type'] == 'image':
        try:
            result = process_image_with_variants(abs_path, base_dir, file_prefix, ext)
            if result and 'paths' in result:
                thumbnail_path = result['paths'].get('thumbnail', '')
                display_path = result['paths'].get('display', '')
                width = result.get('original_width', 0)
                height = result.get('original_height', 0)
        except Exception as e:
            print(f"图片处理失败: {e}")
            thumbnail_path = info['relative_path']  # fallback: 原图作为缩略图

    elif info['media_type'] == 'video':
        compress_status = 'pending'
        try:
            result = process_video_with_variants(abs_path, base_dir, file_prefix, ext)
            if result and 'paths' in result:
                thumbnail_path = result['paths'].get('thumbnail', '')
                duration = result.get('duration', 0.0)
                width = result.get('width', 0)
                height = result.get('height', 0)
        except Exception as e:
            print(f"视频缩略图生成失败: {e}")

    media = BlogMedia(
        post_id=post_id,
        media_type=info['media_type'],
        file_path=info['relative_path'],
        thumbnail_path=thumbnail_path,
        display_path=display_path,
        original_filename=info['filename'],
        file_size=info['file_size'],
        width=width,
        height=height,
        duration=duration,
        compress_status=compress_status,
    )
    db.session.add(media)
    db.session.flush()


def _create_media_from_uploaded(item, post_id):
    """从预上传的媒体文件元数据创建 BlogMedia 记录（两阶段上传用）

    与 _process_post_media 不同，此函数不操作文件系统 —— 文件已在上传阶段
    保存并处理完毕。它仅根据传入的元数据创建数据库记录。
    """
    compress_status = 'pending' if item.get('media_type') == 'video' else 'success'

    media = BlogMedia(
        post_id=post_id,
        media_type=item.get('media_type', 'image'),
        file_path=item.get('file_path', ''),
        thumbnail_path=item.get('thumbnail_path', ''),
        display_path=item.get('display_path', ''),
        original_filename=item.get('filename', ''),
        file_size=item.get('file_size', 0),
        width=item.get('width', 0),
        height=item.get('height', 0),
        duration=item.get('duration', 0.0),
        compress_status=compress_status,
    )
    db.session.add(media)
    db.session.flush()


def _enqueue_video_tasks_for_post(post_id):
    """在 commit 之后为博文的所有待转码视频加入队列（避免 race condition）"""
    media_list = BlogMedia.query.filter_by(post_id=post_id, media_type='video', compress_status='pending').all()
    base_dir = _get_posts_media_dir()
    for media in media_list:
        abs_path = os.path.join(base_dir, media.file_path)
        if os.path.exists(abs_path):
            _add_blog_video_transcode_task(media.id, abs_path)


# ============================================================
# 头像（必须在 /posts/<int:post_id> 之前注册，避免被当作 post_id 解析）
# ============================================================

@blog_bp.route('/posts/avatar/<emp_id>', methods=['GET'])
def serve_avatar(emp_id):
    """提供用户头像，无头像时返回默认SVG"""
    base_dir = os.path.join(current_app.root_path, '..', 'assets', 'PostsMedia', 'Avatar')
    base_dir = os.path.abspath(base_dir)
    for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        path = os.path.join(base_dir, f'{emp_id}.{ext}')
        if os.path.exists(path) and os.path.isfile(path):
            return send_file(path, conditional=True)
    # 无头像时返回默认人物剪影SVG
    from flask import make_response
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
      <rect width="100" height="100" fill="#eff6ff"/>
      <circle cx="50" cy="36" r="16" fill="#93c5fd"/>
      <ellipse cx="50" cy="78" rx="28" ry="20" fill="#93c5fd"/>
    </svg>'''
    resp = make_response(svg)
    resp.headers['Content-Type'] = 'image/svg+xml'
    resp.headers['Cache-Control'] = 'public, max-age=3600'
    return resp


@blog_bp.route('/posts/avatar/upload', methods=['POST'])
@require_auth
def upload_avatar():
    """上传用户头像"""
    try:
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({'success': False, 'message': '请先登录'}), 401

        file = request.files.get('file')
        if not file or not file.filename:
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            return jsonify({'success': False, 'message': '仅支持 JPG/PNG/GIF/WEBP 格式'}), 400

        base_dir = os.path.join(current_app.root_path, '..', 'assets', 'PostsMedia', 'Avatar')
        base_dir = os.path.abspath(base_dir)
        os.makedirs(base_dir, exist_ok=True)

        for old_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            old_path = os.path.join(base_dir, f'{user_id}.{old_ext}')
            if os.path.exists(old_path):
                os.remove(old_path)

        save_path = os.path.join(base_dir, f'{user_id}.{ext}')
        file.save(save_path)

        from PIL import Image
        img = Image.open(save_path)
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        img.save(os.path.join(base_dir, f'{user_id}_thumb.{ext}'), quality=85)

        return jsonify({
            'success': True,
            'data': {'avatar_url': f'/api/posts/avatar/{user_id}'}
        })
    except Exception as e:
        print(f"上传头像失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>', methods=['GET'])
@route_permission(ROUTE_BLOG_MANAGE)
def get_post(post_id):
    """获取单篇博文详情"""
    try:
        post = BlogPost.query.get(post_id)
        if not post:
            return jsonify({'success': False, 'message': '博文不存在'}), 404

        post_dict = post.to_dict(include_media=True, include_repost=True)

        user_id = get_user_id_from_token()
        if user_id:
            post_dict['is_liked'] = BlogLike.query.filter_by(
                post_id=post.id, user_id=user_id).first() is not None
            post_dict['is_favorited'] = BlogFavorite.query.filter_by(
                post_id=post.id, user_id=user_id).first() is not None
        else:
            post_dict['is_liked'] = False
            post_dict['is_favorited'] = False

        return jsonify({'success': True, 'data': post_dict})
    except Exception as e:
        print(f"获取博文详情失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>', methods=['PUT'])
@route_permission(ROUTE_BLOG_MANAGE)
def update_post(post_id):
    """更新博文（自动保存编辑历史）"""
    try:
        post = BlogPost.query.get(post_id)
        if not post:
            return jsonify({'success': False, 'message': '博文不存在'}), 404

        user_id = get_user_id_from_token()
        user_role = get_user_role_from_token()

        # 权限检查：仅作者或管理员
        if user_role != 'admin' and post.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限编辑此博文'}), 403

        content = request.form.get('content', post.content)
        keep_media_ids = request.form.get('keep_media_ids', '')  # 保留的媒体ID列表，逗号分隔
        uploaded_media_json = request.form.get('uploaded_media', '')
        files = request.files.getlist('media')

        # 保存编辑历史（版本号递增前保存当前版本）
        current_media_snapshot = json.dumps([{
            'id': m.id, 'media_type': m.media_type,
            'file_path': m.file_path, 'thumbnail_path': m.thumbnail_path,
            'compress_status': m.compress_status
        } for m in post.media_list.all()], ensure_ascii=False)

        history = BlogEditHistory(
            post_id=post.id,
            version=post.edit_version,
            content=post.content,
            media_snapshot=current_media_snapshot,
            edited_by=user_id or '',
        )
        db.session.add(history)

        # 更新博文内容
        post.content = content
        post.edit_version += 1
        post.search_field = content
        post.updated_at = datetime.now()

        # 处理保留的媒体：删除不需要的（仅删DB记录，保留物理文件供历史版本引用）
        if keep_media_ids:
            keep_ids = set(int(i) for i in keep_media_ids.split(',') if i.strip().isdigit())
            for media in post.media_list.all():
                if media.id not in keep_ids:
                    db.session.delete(media)

        # 模式二：从预上传的文件元数据创建媒体记录
        if uploaded_media_json:
            try:
                uploaded_list = json.loads(uploaded_media_json)
                for item in uploaded_list:
                    _create_media_from_uploaded(item, post.id)
            except (json.JSONDecodeError, ValueError) as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'媒体数据格式错误: {str(e)}'}), 400

        # 模式一：处理新上传的媒体文件（向后兼容）
        for file in files:
            if not file or not file.filename:
                continue
            _process_post_media(file, post.id)

        db.session.commit()

        # commit 之后再入队转码
        _enqueue_video_tasks_for_post(post.id)

        return jsonify({'success': True, 'data': post.to_dict(include_media=True, include_repost=True)})
    except Exception as e:
        db.session.rollback()
        print(f"更新博文失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@route_permission(ROUTE_BLOG_MANAGE)
def delete_post(post_id):
    """软删除博文"""
    try:
        post = BlogPost.query.get(post_id)
        if not post:
            return jsonify({'success': False, 'message': '博文不存在'}), 404

        user_id = get_user_id_from_token()
        user_role = get_user_role_from_token()

        if user_role != 'admin' and post.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限删除此博文'}), 403

        post.is_deleted = 1
        post.deleted_at = datetime.now()
        post.deleted_by = _get_current_user_name()
        db.session.commit()

        return jsonify({'success': True, 'message': '博文已移至回收站'})
    except Exception as e:
        db.session.rollback()
        print(f"删除博文失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 草稿管理
# ============================================================

@blog_bp.route('/posts/draft', methods=['GET'])
@require_auth
def get_draft():
    """获取当前用户的所有草稿"""
    try:
        user_id = get_user_id_from_token()
        drafts = BlogPost.query.filter_by(author_id=user_id, is_draft=1, is_deleted=0)\
            .order_by(BlogPost.updated_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [d.to_dict(include_media=True) for d in drafts]
        })
    except Exception as e:
        print(f"获取草稿失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/draft', methods=['POST'])
@require_auth
def save_draft():
    """保存草稿（允许多条草稿，支持两阶段上传）"""
    try:
        content = request.form.get('content', '')
        uploaded_media_json = request.form.get('uploaded_media', '')
        files = request.files.getlist('media')

        user_id = get_user_id_from_token()
        user_name = _get_current_user_name()

        has_uploaded = bool(uploaded_media_json)
        has_files = bool(files and any(f and f.filename for f in files))

        # 如果内容为空且无媒体，不保存
        if not content and not has_files and not has_uploaded:
            return jsonify({'success': False, 'message': '草稿内容不能为空'}), 400

        # 始终创建新草稿
        draft = BlogPost(
            content=content,
            author=user_name,
            author_id=user_id,
            is_draft=1,
            search_field=content,
        )
        db.session.add(draft)
        db.session.flush()

        # 模式二：从预上传的文件元数据创建媒体记录
        if has_uploaded:
            try:
                uploaded_list = json.loads(uploaded_media_json)
                for item in uploaded_list:
                    _create_media_from_uploaded(item, draft.id)
            except (json.JSONDecodeError, ValueError) as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'媒体数据格式错误: {str(e)}'}), 400

        # 模式一：处理直接上传的媒体文件（向后兼容）
        for file in files:
            if not file or not file.filename:
                continue
            _process_post_media(file, draft.id)

        db.session.commit()

        # commit 之后再入队转码
        _enqueue_video_tasks_for_post(draft.id)

        return jsonify({'success': True, 'data': draft.to_dict(include_media=True)})
    except Exception as e:
        db.session.rollback()
        print(f"保存草稿失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/draft/<int:draft_id>', methods=['DELETE'])
@require_auth
def delete_draft(draft_id):
    """彻底删除指定的草稿（不进入回收站）"""
    try:
        user_id = get_user_id_from_token()
        draft = BlogPost.query.get(draft_id)
        if not draft:
            return jsonify({'success': False, 'message': '草稿不存在'}), 404
        if draft.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限删除此草稿'}), 403
        if not draft.is_draft:
            return jsonify({'success': False, 'message': '该博文不是草稿'}), 400

        # 彻底删除媒体文件和DB记录
        for media in draft.media_list.all():
            try:
                abs_path = os.path.join(_get_posts_media_dir(), media.file_path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except Exception:
                pass
        db.session.delete(draft)
        db.session.commit()
        return jsonify({'success': True, 'message': '草稿已彻底删除'})
    except Exception as e:
        db.session.rollback()
        print(f"删除草稿失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>/publish', methods=['PUT'])
@require_auth
def publish_draft(post_id):
    """发布草稿为正式博文"""
    try:
        user_id = get_user_id_from_token()
        post = BlogPost.query.get(post_id)
        if not post:
            return jsonify({'success': False, 'message': '博文不存在'}), 404
        if post.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限操作'}), 403
        if not post.is_draft:
            return jsonify({'success': False, 'message': '该博文不是草稿'}), 400

        post.is_draft = 0
        post.created_at = datetime.now()
        post.updated_at = datetime.now()
        db.session.commit()

        return jsonify({'success': True, 'data': post.to_dict(include_media=True)})
    except Exception as e:
        db.session.rollback()
        print(f"发布草稿失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 回收站（管理员）
# ============================================================

@blog_bp.route('/posts/deleted', methods=['GET'])
@require_admin
def get_deleted_posts():
    """获取已删除的博文列表（仅管理员）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        query = BlogPost.query.filter_by(is_deleted=1).order_by(BlogPost.deleted_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        posts = [p.to_dict(include_media=True) for p in pagination.items]
        # 补充删除信息
        for i, post in enumerate(posts):
            p = pagination.items[i]
            posts[i]['deleted_at'] = p.deleted_at.strftime('%Y-%m-%d %H:%M:%S') if p.deleted_at else None
            posts[i]['deleted_by'] = p.deleted_by or ''

        return jsonify({
            'success': True,
            'data': {
                'posts': posts,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
            }
        })
    except Exception as e:
        print(f"获取已删除博文失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>/restore', methods=['PUT'])
@require_admin
def restore_post(post_id):
    """恢复已删除的博文"""
    try:
        post = BlogPost.query.get(post_id)
        if not post:
            return jsonify({'success': False, 'message': '博文不存在'}), 404

        post.is_deleted = 0
        post.deleted_at = None
        post.deleted_by = None
        db.session.commit()

        return jsonify({'success': True, 'message': '博文已恢复'})
    except Exception as e:
        db.session.rollback()
        print(f"恢复博文失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/permanent-delete', methods=['DELETE'])
@require_admin
def permanent_delete_posts():
    """彻底删除博文（含物理文件）"""
    try:
        data = request.get_json() or {}
        post_ids = data.get('post_ids', [])
        if not post_ids:
            return jsonify({'success': False, 'message': '请指定要删除的博文ID'}), 400

        for post_id in post_ids:
            post = BlogPost.query.get(post_id)
            if not post:
                continue
            # 删除媒体物理文件
            for media in post.media_list.all():
                try:
                    abs_path = os.path.join(_get_posts_media_dir(), media.file_path)
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                    if media.thumbnail_path:
                        thumb_path = os.path.join(_get_posts_media_dir(), media.thumbnail_path)
                        if os.path.exists(thumb_path):
                            os.remove(thumb_path)
                except Exception:
                    pass
            # 删除数据库记录（级联删除 media, comments, likes, edit_histories）
            db.session.delete(post)

        db.session.commit()
        return jsonify({'success': True, 'message': f'已彻底删除 {len(post_ids)} 条博文'})
    except Exception as e:
        db.session.rollback()
        print(f"彻底删除失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 编辑历史（管理员可查看完整内容）
# ============================================================

@blog_bp.route('/posts/<int:post_id>/history', methods=['GET'])
@require_admin
def get_edit_history(post_id):
    """获取博文的编辑历史列表（仅管理员）"""
    try:
        post = BlogPost.query.get(post_id)
        if not post:
            return jsonify({'success': False, 'message': '博文不存在'}), 404

        histories = BlogEditHistory.query.filter_by(post_id=post_id)\
            .order_by(BlogEditHistory.version.desc()).all()

        return jsonify({
            'success': True,
            'data': {
                'current_version': post.edit_version,
                'history': [h.to_dict(include_full_content=True) for h in histories],
            }
        })
    except Exception as e:
        print(f"获取编辑历史失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>/history/<int:version>', methods=['GET'])
@require_admin
def get_history_version(post_id, version):
    """获取特定历史版本的完整数据"""
    try:
        history = BlogEditHistory.query.filter_by(post_id=post_id, version=version).first()
        if not history:
            return jsonify({'success': False, 'message': '版本不存在'}), 404

        return jsonify({'success': True, 'data': history.to_dict(include_full_content=True)})
    except Exception as e:
        print(f"获取历史版本失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 评论/留言
# ============================================================

@blog_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
@route_permission(ROUTE_BLOG_MANAGE)
def get_comments(post_id):
    """获取博文的评论列表"""
    try:
        comments = BlogComment.query.filter_by(post_id=post_id, is_deleted=0)\
            .order_by(BlogComment.created_at.asc()).all()
        return jsonify({'success': True, 'data': [c.to_dict() for c in comments]})
    except Exception as e:
        print(f"获取评论失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@require_auth
def create_comment(post_id):
    """添加评论"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'success': False, 'message': '评论内容不能为空'}), 400

        user_name = _get_current_user_name()
        user_id = get_user_id_from_token()

        comment = BlogComment(
            post_id=post_id,
            author=user_name,
            author_id=user_id or '',
            content=content,
        )
        db.session.add(comment)

        # 更新博文的搜索字段
        post = BlogPost.query.get(post_id)
        if post:
            post.search_field = f"{post.search_field} {content}"[:2000]
            post.updated_at = datetime.now()

        db.session.commit()

        return jsonify({'success': True, 'data': comment.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        print(f"添加评论失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
@route_permission(ROUTE_BLOG_MANAGE)
def delete_comment(post_id, comment_id):
    """删除评论"""
    try:
        comment = BlogComment.query.get(comment_id)
        if not comment or comment.post_id != post_id:
            return jsonify({'success': False, 'message': '评论不存在'}), 404

        user_id = get_user_id_from_token()
        user_role = get_user_role_from_token()
        if user_role != 'admin' and comment.author_id != user_id:
            return jsonify({'success': False, 'message': '无权限删除此评论'}), 403

        comment.is_deleted = 1
        db.session.commit()

        return jsonify({'success': True, 'message': '评论已删除'})
    except Exception as e:
        db.session.rollback()
        print(f"删除评论失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 收藏
# ============================================================

@blog_bp.route('/posts/favorites', methods=['GET'])
@route_permission(ROUTE_BLOG_MANAGE)
def get_favorites():
    """获取当前用户收藏的博文列表"""
    try:
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({'success': True, 'data': {'posts': [], 'total': 0}})

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)

        # 查询用户收藏的博文ID
        fav_post_ids = db.select(BlogFavorite.post_id).where(BlogFavorite.user_id == user_id).scalar_subquery()
        query = BlogPost.query.filter(
            BlogPost.id.in_(fav_post_ids),
            BlogPost.is_deleted == 0,
            BlogPost.is_draft == 0
        )

        if search:
            query = query.filter(
                db.or_(
                    BlogPost.content.like(f'%{search}%'),
                    BlogPost.search_field.like(f'%{search}%')
                )
            )

        query = query.order_by(BlogPost.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        posts = []
        for post in pagination.items:
            d = post.to_dict(include_media=True, include_repost=True)
            d['is_favorited'] = True
            posts.append(d)

        return jsonify({
            'success': True,
            'data': {
                'posts': posts,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
            }
        })
    except Exception as e:
        print(f"获取收藏列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 点赞
# ============================================================

@blog_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@require_auth
def toggle_like(post_id):
    """切换点赞状态"""
    try:
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({'success': False, 'message': '请先登录'}), 401

        existing = BlogLike.query.filter_by(post_id=post_id, user_id=user_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'success': True, 'data': {'liked': False}})
        else:
            like = BlogLike(post_id=post_id, user_id=user_id)
            db.session.add(like)
            db.session.commit()
            return jsonify({'success': True, 'data': {'liked': True}})
    except Exception as e:
        db.session.rollback()
        print(f"点赞操作失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>/favorite', methods=['POST'])
@require_auth
def toggle_favorite(post_id):
    """切换收藏状态"""
    try:
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({'success': False, 'message': '请先登录'}), 401

        existing = BlogFavorite.query.filter_by(post_id=post_id, user_id=user_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'success': True, 'data': {'favorited': False}})
        else:
            fav = BlogFavorite(post_id=post_id, user_id=user_id)
            db.session.add(fav)
            db.session.commit()
            return jsonify({'success': True, 'data': {'favorited': True}})
    except Exception as e:
        db.session.rollback()
        print(f"收藏操作失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@blog_bp.route('/posts/<int:post_id>/likes', methods=['GET'])
@require_auth
def get_post_likes(post_id):
    """获取点赞该博文的用户列表"""
    try:
        from app.models.employee import Employee
        likes = BlogLike.query.filter_by(post_id=post_id).order_by(BlogLike.created_at.desc()).all()
        users = []
        for like in likes:
            emp = Employee.query.filter_by(emp_id=like.user_id).first()
            users.append({
                'user_id': like.user_id,
                'name': emp.name if emp else like.user_id,
            })
        return jsonify({'success': True, 'data': users})
    except Exception as e:
        print(f"获取点赞列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 媒体文件访问
# ============================================================

# 博客媒体文件现在由 app/__init__.py 中 app 级路由 serve_blog_media_file 提供
# （app 级路由在 Waitress 下处理大文件视频更稳定，与视频管理模块一致）


@blog_bp.route('/posts/media/upload', methods=['POST'])
@route_permission(ROUTE_BLOG_MANAGE)
def upload_media():
    """单独上传媒体文件（含完整处理：缩略图生成、视频元数据提取）

    此端点是两阶段上传的核心：前端先逐个调用此接口上传文件，
    全部完成后再调用 POST /posts 提交博文元数据 + 文件引用。
    这样每个文件有独立的超时和进度，不会因为合并上传导致误报超时。
    """
    try:
        file = request.files.get('file')
        if not file or not file.filename:
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        info = _save_blog_media_file(file)
        base_dir = _get_posts_media_dir()
        abs_path = info['absolute_path']
        ext = info['ext']
        file_prefix = os.path.splitext(info['filename'])[0]

        thumbnail_path = ''
        display_path = ''
        width, height, duration = 0, 0, 0.0

        if info['media_type'] == 'image':
            try:
                result = process_image_with_variants(abs_path, base_dir, file_prefix, ext)
                if result and 'paths' in result:
                    thumbnail_path = result['paths'].get('thumbnail', '')
                    display_path = result['paths'].get('display', '')
                    width = result.get('original_width', 0)
                    height = result.get('original_height', 0)
            except Exception:
                thumbnail_path = info['relative_path']

        elif info['media_type'] == 'video':
            # 视频也在此处生成缩略图和提取元数据，
            # 避免这些耗时操作堆积在 POST /posts 的单个请求中
            try:
                result = process_video_with_variants(abs_path, base_dir, file_prefix, ext)
                if result and 'paths' in result:
                    thumbnail_path = result['paths'].get('thumbnail', '')
                    duration = result.get('duration', 0.0)
                    width = result.get('width', 0)
                    height = result.get('height', 0)
            except Exception as e:
                print(f"视频缩略图生成失败: {e}")

        return jsonify({
            'success': True,
            'data': {
                'file_path': info['relative_path'],
                'thumbnail_path': thumbnail_path,
                'display_path': display_path,
                'media_type': info['media_type'],
                'file_size': info['file_size'],
                'filename': info['filename'],
                'width': width,
                'height': height,
                'duration': duration,
            }
        })
    except Exception as e:
        print(f"上传媒体文件失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


