from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from datetime import datetime
from .. import db
from ..models.video import Video
from ..models.machine import Machine
from ..models.business_operation_log import add_video_log
from ..models.simple_permission import get_user_role_from_token
from ..utils.simple_auth_utils import route_permission
from ..constants.simple_permission_constants import ROUTE_VIDEO, ROUTE_VIDEO_MANAGE
from ..utils.upload_utils import (
    validate_file_type,
    save_uploaded_file,
    process_video_with_variants,
    add_video_process_task,
    add_video_compress_task,
    UPLOAD_CONFIG,
    get_video_info,
    compress_video,
    generate_title_based_filename
)
from ..utils.auth_utils import get_user_id_from_token

video_bp = Blueprint('video_bp', __name__, url_prefix='/api')

def update_video_process_result_wrapper(video_id, status, paths=None, error_msg=None):
    """包装函数，用于更新视频处理结果，适配新的处理队列系统"""
    try:
        if status == "success" and paths:
            update_video_process_result(video_id, paths, status)
        elif status == "processing":
            update_video_process_status(video_id, status)
        elif status == "failed":
            update_video_process_status(video_id, status, error_msg)
    except Exception as e:
        print(f"更新视频处理结果失败: {str(e)}")

def update_video_process_status(video_id, status, error_msg=None, app_context=None):

    """更新视频处理状态"""

    try:

        # 使用提供的应用上下文或创建新的上下文

        if app_context:

            with app_context:

                video = Video.query.get(video_id)

                if video:

                    video.compress_status = status

                    if error_msg:

                        video.remark = f"{video.remark or ''} | 处理错误: {error_msg}" if video.remark else f"处理错误: {error_msg}"

                    db.session.commit()

        else:

            # 直接操作数据库

            video = Video.query.get(video_id)

            if video:

                video.compress_status = status

                if error_msg:

                    video.remark = f"{video.remark or ''} | 处理错误: {error_msg}" if video.remark else f"处理错误: {error_msg}"

                db.session.commit()

    except Exception as e:

        print(f"更新视频处理状态失败: {str(e)}")

def update_video_after_compress(video_id, compressed_path, original_file_path):

    """压缩完成后更新视频记录，但保留原始文件作为备份"""

    from extensions import db

    from ..models.video import Video

    import os



    try:

        video = Video.query.get(video_id)

        if video:

            # 获取压缩后的视频信息

            compressed_size = os.path.getsize(compressed_path)

            video_info = get_video_info(compressed_path)



            # 保存压缩后文件的相对路径到compressed_path字段
            # 使用与视频上传时相同的基础路径计算方法
            video.compressed_path = os.path.relpath(compressed_path, UPLOAD_CONFIG['VIDEO_UPLOAD_FOLDER']).replace('\\', '/')

            video.file_size = compressed_size  # 更新为压缩后文件大小

            if video_info:

                video.actual_width = video_info.get('width', 0)

                video.actual_height = video_info.get('height', 0)

                video.duration = video_info.get('fps', 0)  # 暂时用fps字段存储帧率信息



            # 设置压缩状态为完成

            video.compress_status = 'success'



            # 保存更改

            db.session.commit()



            print(f"视频 {video_id} 压缩完成，已更新相关信息")



    except Exception as e:

        print(f"更新视频记录失败: {str(e)}")

def update_video_process_result(video_id, paths, status, duration=None):
    """更新视频处理后的路径"""
    try:
        video = Video.query.get(video_id)
        if not video:
            return

        if paths.get("thumbnail"):
            video.thumbnail_path = paths["thumbnail"]

        # 暂时保留压缩路径字段，但不设置实际压缩功能
        # if paths.get("compressed"):
        #     video.compressed_path = paths["compressed"]

        video.compress_status = status

        # 如果有新的缩略图，更新文件大小和尺寸信息
        if paths.get("thumbnail"):
            thumbnail_path = os.path.join(".", "assets","Media", "Videos", paths["thumbnail"])
            if os.path.exists(thumbnail_path):
                # 更新视频尺寸（从缩略图获取，实际应从视频获取）
                from PIL import Image
                img = Image.open(thumbnail_path)
                video.original_width, video.original_height = img.size

        # 如果提供了时长信息
        if duration:
            video.duration = duration

        db.session.commit()
    except Exception as e:
        print(f"更新视频处理结果失败: {str(e)}")

def process_video(original_file, base_save_dir="./assets/Media/Videos", title=""):
    """
    处理上传视频，生成缩略图等
    :param original_file: Flask上传的File对象
    :param base_save_dir: 基础存储目录
    :param title: 视频标题，用于生成文件名
    :return: 视频路径、缩略图路径等信息
    """
    # 生成自定义文件名，如果提供了标题
    custom_filename = None
    if title:
        custom_filename = generate_title_based_filename(title, original_file.filename)

    # 保存原视频
    original_save_path, relative_path, unique_filename = save_uploaded_file(original_file, base_save_dir, custom_filename=custom_filename)

    # 获取文件信息
    ext = unique_filename.split('.')[-1].lower()
    file_prefix = unique_filename.rsplit('.', 1)[0]

    # 生成视频缩略图（立即生成，但不进行视频压缩）
    result = process_video_with_variants(original_save_path, base_save_dir, file_prefix, ext)

    # 获取视频基本信息
    file_size = os.path.getsize(original_save_path)

    return {
        "paths": {
            "thumbnail": result['paths'].get('thumbnail', ''),
            "original": relative_path,
            "compressed": ""
        },
        "file_size": file_size,
        "duration": result.get('duration', 0.0),
        "original_width": result.get('width', 0),
        "original_height": result.get('height', 0),
        "need_processing": result['needs_processing'],
        "original_file_path": original_save_path,  # 原视频物理路径
        "file_prefix": file_prefix,
        "ext": ext,
        "save_dir": os.path.dirname(original_save_path),
        "base_save_dir": base_save_dir
    }

@video_bp.route('/videos', methods=['GET'])
@route_permission(ROUTE_VIDEO)
def get_videos():
    """获取视频列表"""
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
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 构建查询
        pagination = Video.get_paginated_videos(
            page=page,
            per_page=per_page,
            search=search,
            machine_id=machine_id,
            is_admin=is_admin,
            uploader=None  # 移除权限限制，所有用户都能看到所有视频
        )

        videos = pagination.items

        # 根据用户权限处理数据
        videos_data = []
        for video in videos:
            video_dict = video.to_dict()
            if not is_admin:
                # 非管理员用户不显示某些字段（如果需要）
                pass
            videos_data.append(video_dict)

        return jsonify({
            'success': True,
            'data': {
                'videos': videos_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        })
    except Exception as e:
        print(f"获取视频列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@video_bp.route('/videos', methods=['POST'])
@route_permission(ROUTE_VIDEO)
def upload_video():
    """视频上传接口：先入库返回，后台异步处理缩略图等"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未提供文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        # 获取当前用户信息，作为上传者
        user_role = get_user_role_from_token()
        uploader = request.form.get('uploader', user_role or 'system')

        # 获取其他字段
        title = request.form.get('title', '')
        tags = request.form.get('tags', '')
        machine_id = request.form.get('machine_id', '')  # 机器ID是型号字符串，不是整数
        remark = request.form.get('remark', '')
        print(f'Uploader: {uploader}, Title: {title}, Tags: {tags}, Machine ID: {machine_id}, Remark: {remark}')

        # 验证视频文件
        is_valid, msg = validate_file_type(file, UPLOAD_CONFIG['VIDEO_ALLOWED_EXTENSIONS'])
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400

        # 处理视频
        process_result = process_video(file, UPLOAD_CONFIG['VIDEO_UPLOAD_FOLDER'], title=title)

        # 构建搜索字段
        search_field = f"{title} {tags} {remark}"
        if machine_id:  # 检查machine_id是否不为空字符串
            machine = Machine.query.filter_by(model=machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"

        # 创建视频记录
        video = Video(
            title=title,
            tags=tags,
            machine_id=machine_id,
            remark=remark,
            search_field=search_field,
            uploader=uploader,
            original_path=process_result["paths"]["original"],
            thumbnail_path=process_result["paths"]["thumbnail"],
            compressed_path=process_result["paths"]["compressed"] if process_result["paths"]["compressed"] else None,
            original_width=process_result["original_width"],
            original_height=process_result["original_height"],
            duration=process_result["duration"],
            file_size=process_result["file_size"],
            compress_status="pending"  # 初始状态为待处理
        )

        db.session.add(video)
        db.session.commit()

        # 记录视频创建日志
        try:
            user_id = get_user_id_from_token()
            add_video_log(
                video_id=video.id,
                operation_type='create',
                operator_id=user_id,
                details={
                    "action": "create",
                    "user": user_role,
                    "video_data": {
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
            print(f"记录视频创建日志失败: {str(log_error)}")

        # ========== 核心优化部分 ==========
        # 1. 转换文件大小为MB（保留2位小数）
        file_size_mb = round(process_result["file_size"] / (1024 * 1024), 2)
        size_threshold = UPLOAD_CONFIG['VIDEO_SIZE_THRESHOLD']
        
        # 2. 判断文件大小是否超过阈值
        is_size_over = file_size_mb > size_threshold
        
        # 3. 处理分辨率判断（适配横竖屏）
        original_w = process_result["original_width"]
        original_h = process_result["original_height"]
        max_w = UPLOAD_CONFIG['VIDEO_MAX_WIDTH']
        max_h = UPLOAD_CONFIG['VIDEO_MAX_HEIGHT']
        
        # 区分横竖屏：宽>高为横屏，否则为竖屏
        is_landscape = original_w > original_h
        
        # 横屏：宽≤1920 且 高≤1080；竖屏：宽≤1080 且 高≤1920（交换阈值）
        if is_landscape:
            is_resolution_over = original_w > max_w or original_h > max_h
            resolution_desc = f"横屏 {original_w}x{original_h}"
            resolution_threshold = f"{max_w}x{max_h}"
        else:
            is_resolution_over = original_w > max_h or original_h > max_w  # 竖屏用高的阈值当宽，宽的阈值当高
            resolution_desc = f"竖屏 {original_w}x{original_h}"
            resolution_threshold = f"{max_h}x{max_w}"  # 竖屏阈值交换
        
        # 4. 分开打印判断结果（清晰展示每个条件的状态）
        print(f"视频大小判断：{file_size_mb}MB {'>' if is_size_over else '≤'} {size_threshold}MB（阈值）")
        print(f"视频分辨率判断：{resolution_desc} {'>' if is_resolution_over else '≤'} {resolution_threshold}（阈值）")
        
        # 5. 最终判断是否需要压缩（任一条件满足即需要）
        needs_compress = is_size_over or is_resolution_over
        
        if needs_compress:
            print(f"视频需要压缩：大小超标={is_size_over}，分辨率超标={is_resolution_over}")
            # 如果视频需要压缩，添加到压缩队列
            add_video_compress_task(
                video_id=video.id,
                original_file_path=process_result["original_file_path"],
                base_save_dir=process_result["base_save_dir"],
                app_instance=app_instance
            )
        elif process_result["need_processing"]:
            # 否则，添加到一般处理队列（生成缩略图等）
            add_video_process_task(
                video_id=video.id,
                original_file_path=process_result["original_file_path"],
                file_prefix=process_result["file_prefix"],
                ext=process_result["ext"],
                save_dir=process_result["save_dir"],
                base_save_dir=process_result["base_save_dir"],
                update_func=update_video_process_result_wrapper
            )
        # ========== 核心优化部分结束 ==========

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '上传成功',
            'data': {
                'id': video.id,
                'title': video.title,
                'original_path': video.original_path,
                'thumbnail_path': video.thumbnail_path,
                'compress_status': video.compress_status
            }
        }), 200
    except Exception as e:
        print(f"上传视频失败: {str(e)}")
        return jsonify({'success': False, 'message': f'上传失败：{str(e)}'}), 500

@video_bp.route('/videos/<int:video_id>', methods=['GET'])
@route_permission(ROUTE_VIDEO)
def get_video(video_id):
    """获取单个视频信息"""
    try:
        # 使用通用函数检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        video = Video.get_video_by_id(video_id, is_admin, None)  # 移除权限限制
        if not video:
            return jsonify({'success': False, 'message': '视频不存在'}), 404

        return jsonify({
            'success': True,
            'data': video.to_dict()
        })
    except Exception as e:
        print(f"获取视频信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@video_bp.route('/videos/<int:video_id>', methods=['PUT'])
@route_permission(ROUTE_VIDEO)
def update_video(video_id):
    """更新视频信息"""
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'success': False, 'message': '视频不存在'}), 404

        # 获取当前用户信息
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 记录更新前的数据
        old_data = {
            "title": video.title,
            "tags": video.tags,
            "machine_id": video.machine_id,
            "remark": video.remark
        }

        data = request.get_json()

        # 更新字段
        updated_fields = {}
        if 'title' in data and video.title != data['title']:
            updated_fields['title'] = {"old": video.title, "new": data['title']}
            video.title = data['title']
        if 'tags' in data and video.tags != data['tags']:
            updated_fields['tags'] = {"old": video.tags, "new": data['tags']}
            video.tags = data['tags']
        if 'machine_id' in data and video.machine_id != data['machine_id']:
            updated_fields['machine_id'] = {"old": video.machine_id, "new": data['machine_id']}
            video.machine_id = data['machine_id']
        if 'remark' in data and video.remark != data['remark']:
            updated_fields['remark'] = {"old": video.remark, "new": data['remark']}
            video.remark = data['remark']

        # 重新构建搜索字段
        search_field = f"{video.title} {video.tags} {video.remark}"
        if video.machine_id:
            machine = Machine.query.filter_by(model=video.machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"
        video.search_field = search_field

        db.session.commit()

        # 如果有字段被更新，则记录日志
        if updated_fields:
            try:
                user_id = get_user_id_from_token()
                add_video_log(
                    video_id=video.id,
                    operation_type='update',
                    operator_id=user_id,
                    details={
                        "action": "update",
                        "user": user_role,
                        "updated_fields": updated_fields,
                        "video_data": {
                            "id": video.id,
                            "title": video.title,
                            "tags": video.tags,
                            "machine_id": video.machine_id,
                            "remark": video.remark
                        }
                    }
                )
            except Exception as log_error:
                print(f"记录视频更新日志失败: {str(log_error)}")

        return jsonify({
            'success': True,
            'message': '视频更新成功',
            'data': video.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print(f"更新视频失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@video_bp.route('/videos/<int:video_id>', methods=['DELETE'])
@route_permission(ROUTE_VIDEO)
def delete_video(video_id):
    """删除视频"""
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'success': False, 'message': '视频不存在'}), 404

        # 获取当前用户信息
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        # 记录删除前的视频数据
        video_data = {
            "title": video.title,
            "tags": video.tags,
            "machine_id": video.machine_id,
            "remark": video.remark,
            "original_path": video.original_path,
            "thumbnail_path": video.thumbnail_path,
            "compressed_path": video.compressed_path,
            "file_size": video.file_size,
            "uploader": video.uploader
        }

        # 设置软删除标记及相关信息，不删除物理文件
        video.is_deleted = 1
        video.delete_time = datetime.now()  # 记录删除时间
        video.delete_operator = user_role or 'system'  # 记录删除操作人
        db.session.commit()

        # 记录视频删除日志
        try:
            user_id = get_user_id_from_token()
            add_video_log(
                video_id=video.id,
                operation_type='delete',
                operator_id=user_id,
                details={
                    "action": "delete",
                    "user": user_role,
                    "video_data": video_data
                }
            )
        except Exception as log_error:
            print(f"记录视频删除日志失败: {str(log_error)}")

        return jsonify({
            'success': True,
            'message': '视频删除成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"删除视频失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@video_bp.route('/videos/machines', methods=['GET'])
@route_permission(ROUTE_VIDEO)
def get_machines_for_videos():
    """获取机器列表（用于视频关联）"""
    try:
        # 获取所有未删除的机器
        machines = Machine.query.filter_by(is_deleted=0).all()

        machine_list = []
        for machine in machines:
            machine_list.append({
                'model': machine.model,  # 机器型号作为ID
                'original_model': machine.original_model
            })

        return jsonify({
            'success': True,
            'data': machine_list
        })
    except Exception as e:
        print(f"获取机器列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 获取已删除视频（回收站功能）
@video_bp.route('/videos/deleted', methods=['GET'])
@route_permission(ROUTE_VIDEO_MANAGE)
def get_deleted_videos():
    """获取已删除的视频列表（回收站）"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')

        # 构建查询
        pagination = Video.get_deleted_videos_paginated(
            page=page,
            per_page=per_page,
            search=search,
            is_admin=is_admin,
            uploader=get_user_role_from_token()
        )

        videos = pagination.items

        # 根据用户权限处理数据
        videos_data = []
        for video in videos:
            video_dict = video.to_dict()
            videos_data.append(video_dict)

        return jsonify({
            'success': True,
            'data': {
                'videos': videos_data,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        })
    except Exception as e:
        print(f"获取已删除视频列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 物理删除视频（从回收站彻底删除）
@video_bp.route('/videos/physical_delete', methods=['DELETE'])
@route_permission(ROUTE_VIDEO)
def physical_delete_videos():
    """物理删除视频（从回收站彻底删除）"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        data = request.get_json()
        video_ids = data.get('video_ids', [])

        if not video_ids:
            return jsonify({'success': False, 'message': '未选择要删除的视频'}), 400

        # 查询要删除的视频
        videos = Video.query.filter(Video.id.in_(video_ids)).all()

        # 获取视频详细信息用于日志记录（在删除前保存）
        video_details_for_logs = {}
        for video in videos:
            video_details_for_logs[video.id] = {
                "id": video.id,
                "title": video.title,
                "tags": video.tags,
                "machine_id": video.machine_id,
                "remark": video.remark,
                "original_path": video.original_path,
                "thumbnail_path": video.thumbnail_path,
                "compressed_path": video.compressed_path
            }

        for video in videos:
            # 删除物理文件
            if video.thumbnail_path:
                try:
                    full_thumbnail_path = os.path.join(".", "assets", "Media", "Videos", video.thumbnail_path)
                    if os.path.exists(full_thumbnail_path):
                        os.remove(full_thumbnail_path)
                except Exception as e:
                    print(f"删除缩略图文件失败: {str(e)}")

            if video.original_path:
                try:
                    full_original_path = os.path.join(".", "assets", "Media", "Videos", video.original_path)
                    if os.path.exists(full_original_path):
                        os.remove(full_original_path)
                except Exception as e:
                    print(f"删除原视频文件失败: {str(e)}")

            if video.compressed_path:
                try:
                    full_compressed_path = os.path.join(".", "assets", "Media", "Videos", video.compressed_path)
                    if os.path.exists(full_compressed_path):
                        os.remove(full_compressed_path)
                except Exception as e:
                    print(f"删除压缩视频文件失败: {str(e)}")

        # 从数据库彻底删除记录
        Video.query.filter(Video.id.in_(video_ids)).delete(synchronize_session=False)
        
        # 记录物理删除日志（必须在提交之前完成）
        try:
            user_id = get_user_id_from_token()
            user_role = get_user_role_from_token()
            # 使用之前保存的视频数据，而不是数据库对象（因为数据库对象会被删除）
            for video_id in video_ids:
                add_video_log(
                    video_id=video_id,
                    operation_type='physical_delete',
                    operator_id=user_id,
                    details={
                        "action": "physical_delete",
                        "user": user_role,
                        "title": video_details_for_logs[video_id]["title"],  # 使用保存的标题
                        "video_data": video_details_for_logs[video_id]  # 使用保存的完整视频数据
                    }
                )
        except Exception as log_error:
            print(f"记录视频物理删除日志失败: {str(log_error)}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'成功物理删除 {len(video_ids)} 个视频'
        })
    except Exception as e:
        db.session.rollback()
        print(f"物理删除视频失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 恢复已删除的视频
@video_bp.route('/videos/restore', methods=['POST'])
@route_permission(ROUTE_VIDEO)
def restore_videos():
    """恢复已删除的视频"""
    try:
        # 检查用户权限
        user_role = get_user_role_from_token()
        is_admin = user_role == 'admin'

        data = request.get_json()
        video_ids = data.get('video_ids', [])

        if not video_ids:
            return jsonify({'success': False, 'message': '未选择要恢复的视频'}), 400

        # 查询要恢复的视频
        videos = Video.query.filter(Video.id.in_(video_ids), Video.is_deleted == 1).all()

        # 更新视频记录，清除删除标记和删除信息
        for video in videos:
            video.is_deleted = 0  # 取消删除标记
            video.delete_time = None  # 清除删除日期
            video.delete_operator = None  # 清除删除操作人

        db.session.commit()

        # 记录恢复视频日志
        try:
            user_id = get_user_id_from_token()
            user_role = get_user_role_from_token()
            for video in videos:
                add_video_log(
                    video_id=video.id,
                    operation_type='restore',
                    operator_id=user_id,
                    details={
                        "action": "restore",
                        "user": user_role,
                        "video_data": {
                            "id": video.id,
                            "title": video.title,
                            "restore_message": f"恢复视频ID: {video.id}"
                        }
                    }
                )
        except Exception as log_error:
            print(f"记录视频恢复日志失败: {str(log_error)}")

        return jsonify({
            'success': True,
            'message': f'成功恢复 {len(videos)} 个视频'
        })
    except Exception as e:
        db.session.rollback()
        print(f"恢复视频失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 全局变量来存储应用实例
app_instance = None

def set_app_instance(app):
    global app_instance
    app_instance = app
    # 初始化处理队列（在应用启动时已初始化）
    pass