from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from datetime import datetime
from PIL import Image
from .. import db
from ..models.photo import Photo
from ..models.machine import Machine
from ..models.business_operation_log import add_photo_log
from ..utils.auth_utils import get_user_role_from_token, is_admin_user, get_user_id_from_token
from ..utils.upload_utils import (
    generate_unique_filename,
    get_date_dir,
    validate_file_type,
    save_uploaded_file,
    process_image_with_variants,
    add_image_compress_task,
    get_processing_queue,
    UPLOAD_CONFIG
)

photo_bp = Blueprint('photo_bp', __name__, url_prefix='/api')

def update_photo_compress_result_wrapper(photo_id, status, paths=None, error_msg=None):
    """包装函数，用于更新照片压缩结果，适配新的处理队列系统"""
    try:
        # 直接调用原始的更新函数
        if status == "success" and paths:
            update_photo_compress_result(photo_id, paths, status, original_file_path=None)
        elif status == "processing":
            update_compress_status(photo_id, status)
        elif status == "failed":
            update_compress_status(photo_id, status, error_msg)
    except Exception as e:
        print(f"更新照片压缩结果失败: {str(e)}")

def validate_file_type_from_path(file_path, allowed_extensions):
    """
    从文件路径验证文件类型
    :param file_path: 文件路径
    :param allowed_extensions: 允许的扩展名列表
    :return: (是否有效, 消息)
    """
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('image/'):
        # 进一步验证扩展名
        import os
        _, ext = os.path.splitext(file_path)
        if ext.lower() in allowed_extensions:
            return True, "文件类型有效"
    return False, "文件类型不允许，仅支持图片文件"


def process_image_from_path(file_path, base_save_dir):
    """
    从文件路径处理图片，生成不同规格
    :param file_path: 文件路径
    :param base_save_dir: 基础存储目录
    :return: 各个规格图片路径、原图宽高、是否需要后台压缩标记
    """
    import os
    import uuid
    from PIL import Image
    from ..utils.upload_utils import process_image_with_variants

    # 获取文件信息
    ext = os.path.splitext(file_path)[1].lower()[1:]  # 去掉点号
    file_prefix = os.path.splitext(os.path.basename(file_path))[0]

    # 打开原图并获取基础信息
    img = Image.open(file_path)
    original_width, original_height = img.size
    max_original_side = max(original_width, original_height)
    print(f'Compress_Img Original image size: {original_width}x{original_height}')

    # 生成图片变体（仅生成缩略图用于立即显示）
    max_sizes = {'thumbnail': 400}  # 立即生成缩略图
    result = process_image_with_variants(file_path, base_save_dir, file_prefix, ext, max_sizes)

    # 初始化返回结果
    result_paths = {
        "thumbnail": result['paths'].get('thumbnail', os.path.relpath(file_path, "./assets/Media/Photos")),
        "normal": os.path.relpath(file_path, "./assets/Media/Photos"),  # 先存原图路径供前端使用
        "original": ""
    }

    need_compress = False  # 是否需要后台压缩标记

    # 判断是否需要后台压缩
    if max_original_side > 1280:
        need_compress = True
        # 仅标记需要压缩，不立即执行，由后台线程处理

    return {
        "paths": result_paths,
        "original_width": original_width,
        "original_height": original_height,
        "need_compress": need_compress,
        "original_file_path": file_path,  # 原图物理路径，供后台压缩使用
        "file_prefix": file_prefix,
        "ext": ext,
        "save_dir": os.path.dirname(file_path),
        "base_save_dir": base_save_dir,
        "file_size": os.path.getsize(file_path),
        "compress_status": "pending"
    }


def process_image(original_file, base_save_dir="./assets/Media/Photos"):
    """
    处理上传图片，生成不同规格
    :param original_file: Flask上传的File对象
    :param base_save_dir: 基础存储目录
    :return: 各个规格图片路径、原图宽高、是否需要后台压缩标记
    """
    # 1. 保存原图
    original_save_path, relative_path, unique_filename = save_uploaded_file(original_file, base_save_dir)

    # 2. 获取文件信息
    ext = unique_filename.split('.')[-1].lower()
    file_prefix = unique_filename.rsplit('.', 1)[0]

    # 3. 打开原图并获取基础信息
    img = Image.open(original_save_path)
    original_width, original_height = img.size
    max_original_side = max(original_width, original_height)
    print(f'Compress_Img Original image size: {original_width}x{original_height}')

    # 4. 生成图片变体（仅生成缩略图用于立即显示）
    max_sizes = {'thumbnail': 400}  # 立即生成缩略图
    result = process_image_with_variants(original_save_path, base_save_dir, file_prefix, ext, max_sizes)

    # 5. 初始化返回结果
    result_paths = {
        "thumbnail": result['paths'].get('thumbnail', relative_path),
        "normal": relative_path,  # 先存原图路径供前端使用
        "original": ""
    }

    need_compress = False  # 是否需要后台压缩标记

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
        "save_dir": os.path.dirname(original_save_path),
        "base_save_dir": base_save_dir
    }

def update_compress_status(photo_id, status, error_msg=None, app_context=None):
    """更新照片压缩状态"""
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
                        size_source_path = os.path.join(".", "assets","Media", "Photos", paths["original"])
                    elif paths.get("normal"):
                        size_source_path = os.path.join(".", "assets","Media", "Photos", paths["normal"])

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
                    size_source_path = os.path.join(".", "assets","Media", "Photos", paths["original"])
                elif paths.get("normal"):
                    size_source_path = os.path.join(".", "assets","Media", "Photos", paths["normal"])


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

# 全局变量来存储应用实例
app_instance = None

def set_app_instance(app):
    global app_instance
    app_instance = app
    # 初始化处理队列
    from ..utils.upload_utils import get_processing_queue
    processing_queue = get_processing_queue()
    processing_queue.set_app_instance(app)

@photo_bp.route('/photos', methods=['GET'])
def get_photos():
    """获取照片列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        # 获取machine_id参数
        machine_id_raw = request.args.get('machine_id')
        
        # 只有在machine_id_raw不为空字符串且不为None时才处理
        if machine_id_raw is not None and machine_id_raw != '':
            try:
                # 尝试将传入的值作为整数处理
                machine_id = int(machine_id_raw)
                # 如果传入的是整数，直接使用
            except (ValueError, TypeError):
                # 如果无法转换为整数，假定是型号，查找机器
                machine = Machine.query.filter_by(model=machine_id_raw).first()
                if machine:
                    # 如果机器存在，使用其型号
                    machine_id = machine.model
                else:
                    # 如果型号不存在，使用特殊值确保返回空结果
                    machine_id = -1  # 使用特殊标记
        else:
            # 如果没有提供machine_id参数，设为None
            machine_id = None

        # 使用通用函数检查用户权限
        is_admin = is_admin_user()

        # 构建查询
        query = Photo.query



        # 如果有搜索词，添加搜索过滤条件
        if search:
            query = query.filter(Photo.search_field.like(f'%{search}%'))

        # 机器ID筛选
        if machine_id is not None:
            if machine_id == -1:  # 特殊情况：型号不存在，返回空结果
                query = query.filter(Photo.id == -1)  # 不存在的ID，确保空结果
            elif machine_id != 0 and str(machine_id) != '0':
                # machine_id现在可能是型号字符串或整数ID，直接匹配
                query = query.filter(Photo.machine_id == machine_id)
            else:  # machine_id == 0，表示查找没有关联机器的项目
                query = query.filter((Photo.machine_id == 0) | (Photo.machine_id.is_(None)))

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

@photo_bp.route('/photos/batch-upload', methods=['POST'])
def batch_upload_photos():
    """批量图片上传接口"""
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data or 'files_data' not in data:
            return jsonify({'success': False, 'message': '未提供批量上传数据'}), 400

        files_data = data['files_data']
        if not isinstance(files_data, list):
            return jsonify({'success': False, 'message': 'files_data必须是数组'}), 400

        results = []
        for file_data in files_data:
            try:
                # 提取文件信息
                file_content = file_data.get('file_content')  # Base64编码的文件内容
                title = file_data.get('title', '')
                tags = file_data.get('tags', '')
                machine_id = file_data.get('machine_id', '')
                remark = file_data.get('remark', '')

                if not file_content:
                    results.append({'success': False, 'message': '缺少文件内容', 'title': title})
                    continue

                # 解码Base64文件内容
                import base64
                file_bytes = base64.b64decode(file_content)
                
                # 创建类似File对象的结构
                from io import BytesIO
                file_stream = BytesIO(file_bytes)
                
                # 获取当前用户信息，作为上传者
                user_role = get_user_role_from_token()
                uploader = file_data.get('uploader', user_role or 'system')

                # 验证图片文件
                import mimetypes
                # 临时保存文件以进行类型验证
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(file_bytes)
                    temp_filename = temp_file.name
                
                # 验证文件类型
                is_valid, msg = validate_file_type_from_path(temp_filename, UPLOAD_CONFIG['IMAGE_ALLOWED_EXTENSIONS'])
                if not is_valid:
                    os.unlink(temp_filename)  # 删除临时文件
                    results.append({'success': False, 'message': msg, 'title': title})
                    continue

                # 生成文件名
                import uuid
                ext = mimetypes.guess_extension(mimetypes.guess_type(temp_filename)[0]) or '.jpg'
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                
                # 保存文件
                base_save_dir = UPLOAD_CONFIG['IMAGE_UPLOAD_FOLDER']
                date_dir = get_date_dir()
                save_dir = os.path.join(base_save_dir, date_dir)
                os.makedirs(save_dir, exist_ok=True)
                
                save_path = os.path.join(save_dir, unique_filename)
                with open(save_path, 'wb') as f:
                    f.write(file_bytes)
                
                # 处理图片
                process_result = process_image_from_path(save_path, save_dir)
                
                # 构建搜索字段
                search_field = f"{title} {tags} {remark}"
                if machine_id:
                    from app.models.machine import Machine
                    machine = Machine.query.filter_by(model=machine_id).first()
                    if machine:
                        search_field += f" {machine.model} {machine.original_model}"

                # 创建照片记录
                from app.models.photo import Photo
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
                    file_size=process_result["file_size"],
                    compress_status=process_result["compress_status"]
                )

                from .. import db
                db.session.add(photo)
                db.session.commit()

                # 记录照片创建日志
                try:
                    from app.models.business_operation_log import add_photo_log
                    from ..utils.auth_utils import get_user_id_from_token
                    user_id = get_user_id_from_token()
                    add_photo_log(
                        photo_id=photo.id,
                        operation_type='create',
                        operator_id=user_id,
                        details={
                            "action": "create",
                            "user": user_role,
                            "photo_data": {
                                "title": title,
                                "tags": tags,
                                "machine_id": machine_id,
                                "remark": remark,
                                "file_size": process_result["file_size"],
                                "original_path": process_result["paths"]["original"],
                                "thumbnail_path": process_result["paths"]["thumbnail"]
                            }
                        }
                    )
                except Exception as log_error:
                    print(f"记录照片创建日志失败: {str(log_error)}")

                results.append({
                    'success': True,
                    'message': '上传成功',
                    'photo_id': photo.id,
                    'title': title
                })
                
            except Exception as e:
                results.append({
                    'success': False, 
                    'message': f'上传失败: {str(e)}', 
                    'title': file_data.get('title', '未知文件')
                })

        return jsonify({
            'success': True,
            'message': f'批量上传完成',
            'results': results
        })

    except Exception as e:
        print(f"批量上传照片失败: {str(e)}")
        return jsonify({'success': False, 'message': f'批量上传失败：{str(e)}'}), 500


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
        is_valid, msg = validate_file_type(file, UPLOAD_CONFIG['IMAGE_ALLOWED_EXTENSIONS'])
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400

        # 处理图片
        process_result = process_image(file, UPLOAD_CONFIG['IMAGE_UPLOAD_FOLDER'])

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

        # 记录照片创建日志
        try:
            user_id = get_user_id_from_token()
            add_photo_log(
                photo_id=photo.id,
                operation_type='create',
                operator_id=user_id,
                details={
                    "action": "create",
                    "user": user_role,
                    "photo_data": {
                        "title": title,
                        "tags": tags,
                        "machine_id": machine_id,
                        "remark": remark,
                        "file_size": process_result["original_file_path"] and os.path.getsize(process_result["original_file_path"]),
                        "original_path": process_result["paths"]["original"],
                        "thumbnail_path": process_result["paths"]["thumbnail"]
                    }
                }
            )
        except Exception as log_error:
            print(f"记录照片创建日志失败: {str(log_error)}")

        # 判断是否需要压缩，若是则放入队列
        if process_result["need_compress"]:
            add_image_compress_task(
                photo_id=photo.id,
                original_file_path=process_result["original_file_path"],
                file_prefix=process_result["file_prefix"],
                ext=process_result["ext"],
                save_dir=process_result["save_dir"],
                base_save_dir=process_result["base_save_dir"],
                max_sizes={'normal': 1280, 'original': 2560},  # 按需压缩到指定尺寸
                update_func=update_photo_compress_result_wrapper  # 使用包装函数更新数据库
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

        # 移除权限限制，允许所有用户查看照片
        photo_dict = photo.to_dict()

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

        # 移除普通用户的权限限制，允许所有用户更新照片
        # 如果需要保留权限控制，可以在这里添加特定逻辑

        data = request.get_json()

        # 记录更新前的数据
        old_data = {
            "title": photo.title,
            "tags": photo.tags,
            "machine_id": photo.machine_id,
            "remark": photo.remark
        }

        # 更新字段
        updated_fields = {}
        if 'title' in data and photo.title != data['title']:
            updated_fields['title'] = {"old": photo.title, "new": data['title']}
            photo.title = data['title']
        if 'tags' in data and photo.tags != data['tags']:
            updated_fields['tags'] = {"old": photo.tags, "new": data['tags']}
            photo.tags = data['tags']
        if 'machine_id' in data and photo.machine_id != data['machine_id']:
            updated_fields['machine_id'] = {"old": photo.machine_id, "new": data['machine_id']}
            photo.machine_id = data['machine_id']
        if 'remark' in data and photo.remark != data['remark']:
            updated_fields['remark'] = {"old": photo.remark, "new": data['remark']}
            photo.remark = data['remark']

        # 重新构建搜索字段
        search_field = f"{photo.title} {photo.tags} {photo.remark}"
        if photo.machine_id:
            machine = Machine.query.filter_by(model=photo.machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"
        photo.search_field = search_field

        db.session.commit()

        # 如果有字段被更新，则记录日志
        if updated_fields:
            try:
                user_id = get_user_id_from_token()
                add_photo_log(
                    photo_id=photo.id,
                    operation_type='update',
                    operator_id=user_id,
                    details={
                        "action": "update",
                        "user": user_role,
                        "updated_fields": updated_fields,
                        "photo_data": {
                            "id": photo.id,
                            "title": photo.title,
                            "tags": photo.tags,
                            "machine_id": photo.machine_id,
                            "remark": photo.remark
                        }
                    }
                )
            except Exception as log_error:
                print(f"记录照片更新日志失败: {str(log_error)}")

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

        # 移除普通用户的权限限制，允许所有用户删除照片
        # 如果需要保留权限控制，可以在这里添加特定逻辑

        # 删除物理文件
        if photo.thumbnail_path:
            try:
                full_thumbnail_path = os.path.join(".", "assets","Media", "Photos", photo.thumbnail_path)
                if os.path.exists(full_thumbnail_path):
                    os.remove(full_thumbnail_path)
            except Exception as e:
                print(f"删除缩略图文件失败: {str(e)}")  # 使用print替代current_app.logger

        if photo.normal_path:
            try:
                full_normal_path = os.path.join(".", "assets","Media", "Photos", photo.normal_path)
                if os.path.exists(full_normal_path):
                    os.remove(full_normal_path)
            except Exception as e:
                print(f"删除普通图文件失败: {str(e)}")  # 使用print替代current_app.logger

        if photo.original_path:
            try:
                full_original_path = os.path.join(".", "assets","Media", "Photos", photo.original_path)
                if os.path.exists(full_original_path):
                    os.remove(full_original_path)
            except Exception as e:
                print(f"删除原图文件失败: {str(e)}")  # 使用print替代current_app.logger

        # 记录删除前的详细信息
        photo_data = {
            "id": photo.id,
            "title": photo.title,
            "tags": photo.tags,
            "machine_id": photo.machine_id,
            "remark": photo.remark,
            "thumbnail_path": photo.thumbnail_path,
            "normal_path": photo.normal_path,
            "original_path": photo.original_path,
            "file_size": photo.file_size,
            "uploader": photo.uploader,
            "upload_time": photo.upload_time.isoformat() if photo.upload_time else None
        }

        # 从数据库删除记录
        db.session.delete(photo)
        db.session.commit()

        # 记录照片删除日志
        try:
            user_id = get_user_id_from_token()
            add_photo_log(
                photo_id=photo.id,
                operation_type='delete',
                operator_id=user_id,
                details={
                    "action": "delete",
                    "user": user_role,
                    "photo_data": photo_data
                }
            )
        except Exception as log_error:
            print(f"记录照片删除日志失败: {str(log_error)}")

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