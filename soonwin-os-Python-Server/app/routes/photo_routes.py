from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from datetime import datetime
from PIL import Image
import imghdr
from queue import Queue
import threading
from .. import db
from ..models.photo import Photo
from ..models.machine import Machine
from ..utils.auth_utils import get_user_role_from_token, is_admin_user

photo_bp = Blueprint('photo_bp', __name__, url_prefix='/api')

# 初始化全局压缩任务队列
compress_queue = Queue(maxsize=0)

def generate_filename(original_filename):
    """生成唯一文件名"""
    ext = original_filename.split('.')[-1].lower()
    # 格式：年月日时分秒_8位随机字符串.后缀
    new_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    return new_name

def get_date_dir(base_dir):
    """按日期生成存储子目录：./assets/MachinePhoto/2024/01/29"""
    date_str = datetime.now().strftime('%Y/%m/%d')
    full_dir = os.path.join(base_dir, date_str)
    # 递归创建目录（如果不存在）
    os.makedirs(full_dir, exist_ok=True)
    return full_dir

def generate_resized_image(img, max_side, save_path):
    """等比例缩放图片，最长边不超过指定值"""
    width, height = img.size
    # 计算缩放比例
    if max(width, height) > max_side:
        scale = max_side / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        # LANCZOS算法保证高质量缩放
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    # 保存图片，质量85兼顾体积和画质
    img.save(save_path, quality=85)
    print(f'Compress_Img Saved resized image at: {save_path}, Size: {img.size[0]}x{img.size[1]}')
    return save_path

def validate_image(file):
    """验证上传的图片文件"""
    # 1. 检查文件后缀（白名单）
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    if '.' not in file.filename or file.filename.split('.')[-1].lower() not in allowed_extensions:
        return False, "仅支持png/jpg/jpeg/webp格式的图片"

    # 2. 检查文件头（更可靠的格式验证）
    file.seek(0)  # 重置文件指针
    img_type = imghdr.what(file)
    file.seek(0)  # 重置指针，避免后续读取失败
    if img_type not in allowed_extensions:
        return False, "文件格式验证失败，非有效图片文件"

    return True, "验证通过"

def process_image(original_file, base_save_dir="./assets/MachinePhoto"):
    """
    处理上传图片，生成不同规格
    :param original_file: Flask上传的File对象
    :param base_save_dir: 基础存储目录
    :return: 各规格图片路径、原图宽高、是否需要后台压缩标记
    """
    # 1. 初始化存储目录（按日期分）
    save_dir = get_date_dir(base_save_dir)
    original_filename = generate_filename(original_file.filename)
    ext = original_filename.split('.')[-1].lower()
    file_prefix = original_filename.rsplit('.', 1)[0]

    # 2. 保存原图（供前端先使用）
    original_save_path = os.path.join(save_dir, original_filename)
    original_file.save(original_save_path)

    # 3. 打开原图并获取基础信息
    img = Image.open(original_save_path)
    original_width, original_height = img.size
    max_original_side = max(original_width, original_height)
    print(f'Compress_Img Original image size: {original_width}x{original_height}')
    # 4. 初始化返回结果
    result_paths = {
        "thumbnail": "",
        "normal": os.path.relpath(original_save_path, base_save_dir),  # 先存原图路径供前端使用
        "original": ""
    }
    need_compress = False  # 是否需要后台压缩标记

    # 5. 生成缩略图（必选，最长边400px，立即生成）
    thumbnail_path = os.path.join(save_dir, f"{file_prefix}_thumbnail.{ext}")
    result_paths["thumbnail"] = generate_resized_image(img.copy(), 400, thumbnail_path)
    result_paths["thumbnail"] = os.path.relpath(result_paths["thumbnail"], base_save_dir)

    # 6. 判断是否需要后台压缩
    if max_original_side > 1280:
        need_compress = True
        # 仅标记需要压缩，不立即执行，由后台线程处理

    return {
        "paths": result_paths,
        "original_width": original_width,
        "original_height": original_height,
        "need_compress": need_compress,
        "original_file_path": original_save_path,  # 原图物理路径，供后台压缩使用
        "file_prefix": file_prefix,
        "ext": ext,
        "save_dir": save_dir,
        "base_save_dir": base_save_dir
    }

def update_compress_status(photo_id, status, error_msg=None, app_context=None):

    """更新照片压缩状态"""

    from flask import current_app

    try:

        # 使用提供的应用上下文或创建新的上下文

        if app_context:

            with app_context:

                photo = Photo.query.get(photo_id)

                if photo:

                    photo.compress_status = status

                    if error_msg:

                        # 如果模型中没有error_msg字段，我们可以添加到备注字段中或使用其他方式

                        photo.remark = f"{photo.remark or ''} | 压缩错误: {error_msg}" if photo.remark else f"压缩错误: {error_msg}"

                    db.session.commit()

        else:

            # 直接操作数据库，不依赖current_app

            photo = Photo.query.get(photo_id)

            if photo:

                photo.compress_status = status

                if error_msg:

                    # 如果模型中没有error_msg字段，我们可以添加到备注字段中或使用其他方式

                    photo.remark = f"{photo.remark or ''} | 压缩错误: {error_msg}" if photo.remark else f"压缩错误: {error_msg}"

                db.session.commit()

    except Exception as e:

        print(f"更新压缩状态失败: {str(e)}")  # 使用print替代current_app.logger

def update_photo_compress_result(photo_id, paths, status, app_context=None, original_file_path=None):

    """更新压缩后的图片路径"""

    from flask import current_app



    try:

        # 使用提供的应用上下文或创建新的上下文

        if app_context:

            with app_context:

                photo = Photo.query.get(photo_id)

                if photo:

                    if paths.get("normal"):

                        photo.normal_path = paths["normal"]

                    if paths.get("original"):

                        photo.original_path = paths["original"]

                    photo.compress_status = status

                    

                    # 确定使用哪个图片来更新文件大小和尺寸 - 

                    # 如果存在original_path，使用original（最大2560px），否则使用normal（最大1280px）

                    size_source_path = None

                    if paths.get("original"):

                        size_source_path = os.path.join(".", "assets", "MachinePhoto", paths["original"])

                    elif paths.get("normal"):

                        size_source_path = os.path.join(".", "assets", "MachinePhoto", paths["normal"])

                    

                    if size_source_path and os.path.exists(size_source_path):

                        photo.file_size = os.path.getsize(size_source_path)

                        # 获取压缩后图片的尺寸

                        img = Image.open(size_source_path)

                        photo.original_width, photo.original_height = img.size

                    

                    # 如果有压缩后的original图片路径，删除原始上传的图片

                    if paths.get("original"):

                        if original_file_path and os.path.exists(original_file_path):

                            try:

                                os.remove(original_file_path)

                                print(f"原图已删除: {original_file_path}")

                            except Exception as e:

                                print(f"删除原图失败: {str(e)}")

                    

                    db.session.commit()

        else:

            # 直接操作数据库，不依赖current_app

            photo = Photo.query.get(photo_id)

            if photo:

                if paths.get("normal"):

                    photo.normal_path = paths["normal"]

                if paths.get("original"):

                    photo.original_path = paths["original"]

                photo.compress_status = status

                

                # 确定使用哪个图片来更新文件大小和尺寸 - 

                # 如果存在original_path，使用original（最大2560px），否则使用normal（最大1280px）

                size_source_path = None

                if paths.get("original"):

                    size_source_path = os.path.join(".", "assets", "MachinePhoto", paths["original"])

                elif paths.get("normal"):

                    size_source_path = os.path.join(".", "assets", "MachinePhoto", paths["normal"])

                

                if size_source_path and os.path.exists(size_source_path):

                    photo.file_size = os.path.getsize(size_source_path)

                    # 获取压缩后图片的尺寸

                    img = Image.open(size_source_path)

                    photo.original_width, photo.original_height = img.size

                

                # 如果有压缩后的original图片路径，删除原始上传的图片

                if paths.get("original"):

                    if original_file_path and os.path.exists(original_file_path):

                        try:

                            os.remove(original_file_path)

                            print(f"原图已删除: {original_file_path}")

                        except Exception as e:

                            print(f"删除原图失败: {str(e)}")

                

                db.session.commit()

    except Exception as e:

        print(f"更新压缩结果失败: {str(e)}")  # 使用print替代current_app.logger

def trigger_compress_task(photo_id, original_file_path, file_prefix, ext, save_dir, base_save_dir, max_original_side, app_instance):

    """将压缩任务放入队列"""

    task = {

        "photo_id": photo_id,

        "original_file_path": original_file_path,

        "file_prefix": file_prefix,

        "ext": ext,

        "save_dir": save_dir,

        "base_save_dir": base_save_dir,

        "max_original_side": max_original_side,

        "app_instance": app_instance  # 保存Flask应用实例

    }

    compress_queue.put(task)

def compress_photo_worker():

    """常驻消费线程：串行处理压缩任务"""

    while True:

        try:

            # 阻塞等待队列任务，无任务时挂起（不占用CPU）

            task = compress_queue.get(timeout=3600)  # 1小时超时，避免永久阻塞

            photo_id = task["photo_id"]

            original_file_path = task["original_file_path"]

            file_prefix = task["file_prefix"]

            ext = task["ext"]

            save_dir = task["save_dir"]

            base_save_dir = task["base_save_dir"]

            max_original_side = task["max_original_side"]

            app_instance = task.get("app_instance")  # 获取Flask应用实例

            # 更新压缩状态为处理中

            update_compress_status(photo_id, "processing", app_context=app_instance.app_context() if app_instance else None)

            # 打开原图执行压缩

            img = Image.open(original_file_path)

            result_paths = {}

            # 按规则压缩

            if max_original_side > 2560:

                # 压缩至2560px存original

                original_path = os.path.join(save_dir, f"{file_prefix}_original.{ext}")

                result_paths["original"] = generate_resized_image(img.copy(), 2560, original_path)

                # 压缩至1280px更新normal

                normal_path = os.path.join(save_dir, f"{file_prefix}_normal.{ext}")

                result_paths["normal"] = generate_resized_image(img.copy(), 1280, normal_path)

            else:

                # 2560≥最长边>1280：压缩至1280px更新normal，不生成original

                normal_path = os.path.join(save_dir, f"{file_prefix}_normal.{ext}")

                result_paths["normal"] = generate_resized_image(img.copy(), 1280, normal_path)
                result_paths["original"] = ""

            # 转换为相对路径并更新数据库
            db_paths = {}
            if result_paths["original"]:
                db_paths["original"] = os.path.relpath(result_paths["original"], base_save_dir)
            db_paths["normal"] = os.path.relpath(result_paths["normal"], base_save_dir)

            update_photo_compress_result(photo_id, db_paths, "success", app_context=app_instance.app_context() if app_instance else None, original_file_path=original_file_path)

            # 标记任务完成，避免队列内存泄漏

            compress_queue.task_done()

        except Exception as e:

            # 压缩失败，更新状态并记录错误

            if 'photo_id' in locals():

                update_compress_status(photo_id, "failed", str(e), app_context=app_instance.app_context() if app_instance else None)

            compress_queue.task_done()

            continue

# 全局变量来存储应用实例
app_instance = None

def set_app_instance(app):
    global app_instance
    app_instance = app
    # 启动消费线程（Flask启动时执行）
    compress_thread = threading.Thread(target=compress_photo_worker, daemon=True)
    compress_thread.start()

@photo_bp.route('/photos', methods=['GET'])
def get_photos():
    """获取照片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')

        # 使用通用函数检查用户权限
        is_admin = is_admin_user()

        # 构建查询
        query = Photo.query

        # 如果是非管理员用户，限制只能看到自己上传的照片
        if not is_admin:
            # 从请求中获取当前用户信息
            user_role = get_user_role_from_token()
            if user_role:
                query = query.filter(Photo.uploader == user_role)

        # 如果有搜索词，添加搜索过滤条件
        if search:
            query = query.filter(Photo.search_field.like(f'%{search}%'))

        # 按上传时间倒序排列
        query = query.order_by(Photo.upload_time.desc())

        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        photos = pagination.items

        # 根据用户权限处理数据
        photos_data = []
        for photo in photos:
            photo_dict = photo.to_dict()
            if not is_admin:
                # 非管理员用户不显示某些字段（如果需要）
                pass
            photos_data.append(photo_dict)

        return jsonify({
            'success': True,
            'data': {
                'photos': photos_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        })
    except Exception as e:
        print(f"获取照片列表失败: {str(e)}")  # 使用print替代current_app.logger
        return jsonify({'success': False, 'message': str(e)}), 500

@photo_bp.route('/photos', methods=['POST'])
def upload_photo():
    """图片上传接口：先入库返回，后台异步压缩"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未提供文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        # 获取当前用户信息，作为上传者
        user_role = get_user_role_from_token()
        uploader = request.form.get('uploader', user_role or 'system')  # 优先使用从前端传来的上传者信息，如果获取不到则使用当前用户或system

        # 获取其他字段
        title = request.form.get('title', '')
        tags = request.form.get('tags', '')
        machine_id = request.form.get('machine_id', type=int)
        remark = request.form.get('remark', '')
        print(f'Uploader: {uploader}, Title: {title}, Tags: {tags}, Machine ID: {machine_id}, Remark: {remark}')

        # 验证图片文件
        is_valid, msg = validate_image(file)
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400

        # 处理图片
        process_result = process_image(file, "./assets/MachinePhoto")

        # 构建搜索字段
        search_field = f"{title} {tags} {remark}"
        if machine_id:
            machine = Machine.query.filter_by(model=machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"

        # 创建照片记录
        photo = Photo(
            title=title,
            tags=tags,
            machine_id=machine_id,
            remark=remark,
            search_field=search_field,
            uploader=uploader,
            original_path=process_result["paths"]["original"] if process_result["paths"]["original"] else None,
            thumbnail_path=process_result["paths"]["thumbnail"],
            normal_path=process_result["paths"]["normal"],
            original_width=process_result["original_width"],
            original_height=process_result["original_height"],
            file_size=os.path.getsize(process_result["original_file_path"]),
            compress_status="pending"
        )

        db.session.add(photo)
        db.session.commit()

        # 判断是否需要压缩，若是则放入队列
        if process_result["need_compress"]:
            trigger_compress_task(
                photo_id=photo.id,
                original_file_path=process_result["original_file_path"],
                file_prefix=process_result["file_prefix"],
                ext=process_result["ext"],
                save_dir=process_result["save_dir"],
                base_save_dir=process_result["base_save_dir"],
                max_original_side=max(process_result["original_width"], process_result["original_height"]),
                app_instance=app_instance
            )

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '上传成功',
            'data': {
                'id': photo.id,
                'title': photo.title,
                'normal_path': photo.normal_path,
                'thumbnail_path': photo.thumbnail_path,
                'compress_status': photo.compress_status
            }
        }), 200
    except Exception as e:
        print(f"上传图片失败: {str(e)}")  # 使用print替代current_app.logger
        return jsonify({'success': False, 'message': f'上传失败：{str(e)}'}), 500

@photo_bp.route('/photos/<int:photo_id>', methods=['GET'])
def get_photo(photo_id):
    """获取单个照片信息"""
    try:
        # 使用通用函数检查用户权限
        is_admin = is_admin_user()

        photo = Photo.query.get(photo_id)
        if not photo:
            return jsonify({'success': False, 'message': '照片不存在'}), 404

        # 根据用户权限处理数据
        photo_dict = photo.to_dict()
        if not is_admin:
            # 非管理员用户检查是否有权限查看此照片
            user_role = get_user_role_from_token()
            if user_role and photo.uploader != user_role:
                return jsonify({'success': False, 'message': '权限不足，无法查看此照片'}), 403

        return jsonify({
            'success': True,
            'data': photo_dict
        })
    except Exception as e:
        print(f"获取照片信息失败: {str(e)}")  # 使用print替代current_app.logger
        return jsonify({'success': False, 'message': str(e)}), 500

@photo_bp.route('/photos/<int:photo_id>', methods=['PUT'])
def update_photo(photo_id):
    """更新照片信息"""
    try:
        photo = Photo.query.get(photo_id)
        if not photo:
            return jsonify({'success': False, 'message': '照片不存在'}), 404

        # 获取当前用户信息
        user_role = get_user_role_from_token()
        is_admin = is_admin_user()

        # 普通用户只能更新自己上传的照片，管理员可以更新任意照片
        if not is_admin and user_role and photo.uploader != user_role:
            return jsonify({'success': False, 'message': '权限不足，无法更新此照片'}), 403

        data = request.get_json()

        # 更新字段
        if 'title' in data:
            photo.title = data['title']
        if 'tags' in data:
            photo.tags = data['tags']
        if 'machine_id' in data:
            photo.machine_id = data['machine_id']
        if 'remark' in data:
            photo.remark = data['remark']

        # 重新构建搜索字段
        search_field = f"{photo.title} {photo.tags} {photo.remark}"
        if photo.machine_id:
            machine = Machine.query.filter_by(model=photo.machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"
        photo.search_field = search_field

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '照片更新成功',
            'data': photo.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print(f"更新照片失败: {str(e)}")  # 使用print替代current_app.logger
        return jsonify({'success': False, 'message': str(e)}), 500

@photo_bp.route('/photos/<int:photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """删除照片"""
    try:
        photo = Photo.query.get(photo_id)
        if not photo:
            return jsonify({'success': False, 'message': '照片不存在'}), 404

        # 获取当前用户信息
        user_role = get_user_role_from_token()
        is_admin = is_admin_user()

        # 普通用户只能删除自己上传的照片，管理员可以删除任意照片
        if not is_admin and user_role and photo.uploader != user_role:
            return jsonify({'success': False, 'message': '权限不足，无法删除此照片'}), 403

        # 删除物理文件
        if photo.thumbnail_path:
            try:
                full_thumbnail_path = os.path.join(".", "assets", "MachinePhoto", photo.thumbnail_path)
                if os.path.exists(full_thumbnail_path):
                    os.remove(full_thumbnail_path)
            except Exception as e:
                print(f"删除缩略图文件失败: {str(e)}")  # 使用print替代current_app.logger

        if photo.normal_path:
            try:
                full_normal_path = os.path.join(".", "assets", "MachinePhoto", photo.normal_path)
                if os.path.exists(full_normal_path):
                    os.remove(full_normal_path)
            except Exception as e:
                print(f"删除普通图文件失败: {str(e)}")  # 使用print替代current_app.logger

        if photo.original_path:
            try:
                full_original_path = os.path.join(".", "assets", "MachinePhoto", photo.original_path)
                if os.path.exists(full_original_path):
                    os.remove(full_original_path)
            except Exception as e:
                print(f"删除原图文件失败: {str(e)}")  # 使用print替代current_app.logger

        # 从数据库删除记录
        db.session.delete(photo)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '照片删除成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"删除照片失败: {str(e)}")  # 使用print替代current_app.logger
        return jsonify({'success': False, 'message': str(e)}), 500

@photo_bp.route('/photos/machines', methods=['GET'])
def get_machines_for_photos():
    """获取机器列表（用于照片关联）"""
    try:
        # 获取所有未删除的机器
        machines = Machine.query.filter_by(is_deleted=0).all()

        machine_list = []
        for machine in machines:
            machine_list.append({
                'model': machine.model,
                'original_model': machine.original_model
            })

        return jsonify({
            'success': True,
            'data': machine_list
        })
    except Exception as e:
        print(f"获取机器列表失败: {str(e)}")  # 使用print替代current_app.logger
        return jsonify({'success': False, 'message': str(e)}), 500