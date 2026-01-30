from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from datetime import datetime
from .. import db
from ..models.video import Video
from ..models.machine import Machine
from ..utils.auth_utils import get_user_role_from_token, is_admin_user
from ..utils.upload_utils import (
    validate_file_type,
    save_uploaded_file,
    process_video_with_variants,
    add_video_process_task,
    add_video_compress_task,
    UPLOAD_CONFIG,
    get_video_info,
    compress_video
)

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

            video.compressed_path = os.path.relpath(compressed_path, UPLOAD_CONFIG['MEDIA_BASE_FOLDER'])

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

def process_video(original_file, base_save_dir="./assets/Media/Videos"):
    """
    处理上传视频，生成缩略图等
    :param original_file: Flask上传的File对象
    :param base_save_dir: 基础存储目录
    :return: 视频路径、缩略图路径等信息
    """
    # 保存原视频
    original_save_path, relative_path, unique_filename = save_uploaded_file(original_file, base_save_dir)

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
        is_admin = is_admin_user()

        # 构建查询
        pagination = Video.get_paginated_videos(
            page=page,
            per_page=per_page,
            search=search,
            machine_id=machine_id,
            is_admin=is_admin,
            uploader=get_user_role_from_token() if not is_admin else None
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
        machine_id = request.form.get('machine_id', type=int)
        remark = request.form.get('remark', '')
        print(f'Uploader: {uploader}, Title: {title}, Tags: {tags}, Machine ID: {machine_id}, Remark: {remark}')

        # 验证视频文件
        is_valid, msg = validate_file_type(file, UPLOAD_CONFIG['VIDEO_ALLOWED_EXTENSIONS'])
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400

        # 处理视频
        process_result = process_video(file, UPLOAD_CONFIG['VIDEO_UPLOAD_FOLDER'])

        # 构建搜索字段
        search_field = f"{title} {tags} {remark}"
        if machine_id:
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

        # 判断是否需要后台处理，若是则放入队列
        file_size_mb = process_result["file_size"] / (1024 * 1024)  # 转换为MB
        needs_compress = (file_size_mb > UPLOAD_CONFIG['VIDEO_SIZE_THRESHOLD'] or 
                         process_result["original_width"] > UPLOAD_CONFIG['VIDEO_MAX_WIDTH'] or 
                         process_result["original_height"] > UPLOAD_CONFIG['VIDEO_MAX_HEIGHT'])

        if needs_compress:
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
def get_video(video_id):
    """获取单个视频信息"""
    try:
        # 使用通用函数检查用户权限
        is_admin = is_admin_user()

        video = Video.get_video_by_id(video_id, is_admin, get_user_role_from_token())
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
def update_video(video_id):
    """更新视频信息"""
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'success': False, 'message': '视频不存在'}), 404

        # 获取当前用户信息
        user_role = get_user_role_from_token()
        is_admin = is_admin_user()

        # 普通用户只能更新自己上传的视频，管理员可以更新任意视频
        if not is_admin and user_role and video.uploader != user_role:
            return jsonify({'success': False, 'message': '权限不足，无法更新此视频'}), 403

        data = request.get_json()

        # 更新字段
        if 'title' in data:
            video.title = data['title']
        if 'tags' in data:
            video.tags = data['tags']
        if 'machine_id' in data:
            video.machine_id = data['machine_id']
        if 'remark' in data:
            video.remark = data['remark']

        # 重新构建搜索字段
        search_field = f"{video.title} {video.tags} {video.remark}"
        if video.machine_id:
            machine = Machine.query.filter_by(model=video.machine_id).first()
            if machine:
                search_field += f" {machine.model} {machine.original_model}"
        video.search_field = search_field

        db.session.commit()

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
def delete_video(video_id):
    """删除视频"""
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'success': False, 'message': '视频不存在'}), 404

        # 获取当前用户信息
        user_role = get_user_role_from_token()
        is_admin = is_admin_user()

        # 普通用户只能删除自己上传的视频，管理员可以删除任意视频
        if not is_admin and user_role and video.uploader != user_role:
            return jsonify({'success': False, 'message': '权限不足，无法删除此视频'}), 403

        # 删除物理文件
        if video.thumbnail_path:
            try:
                full_thumbnail_path = os.path.join(".", "assets","Media", "Videos", video.thumbnail_path)
                if os.path.exists(full_thumbnail_path):
                    os.remove(full_thumbnail_path)
            except Exception as e:
                print(f"删除缩略图文件失败: {str(e)}")

        if video.original_path:
            try:
                full_original_path = os.path.join(".", "assets","Media", "Videos", video.original_path)
                if os.path.exists(full_original_path):
                    os.remove(full_original_path)
            except Exception as e:
                print(f"删除原视频文件失败: {str(e)}")

        if video.compressed_path:
            try:
                full_compressed_path = os.path.join(".", "assets","Media", "Videos", video.compressed_path)
                if os.path.exists(full_compressed_path):
                    os.remove(full_compressed_path)
            except Exception as e:
                print(f"删除压缩视频文件失败: {str(e)}")

        # 从数据库删除记录（软删除）
        video.is_deleted = 1
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '视频删除成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"删除视频失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@video_bp.route('/videos/machines', methods=['GET'])
def get_machines_for_videos():
    """获取机器列表（用于视频关联）"""
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
        print(f"获取机器列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 全局变量来存储应用实例
app_instance = None

def set_app_instance(app):
    global app_instance
    app_instance = app
    # 初始化处理队列（在应用启动时已初始化）
    pass