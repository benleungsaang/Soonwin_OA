from flask import Blueprint, request, jsonify, current_app, send_from_directory
from extensions import db
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import shutil
import zipfile
import sys
from pathlib import Path

# 添加assets/Components到Python路径
components_path = Path(__file__).parent.parent.parent / "assets" / "Components"
sys.path.insert(0, str(components_path))

from ..models.display_file import DisplayFile
from ..models.employee import Employee
from ..utils.auth_utils import require_auth as login_required, require_admin as admin_required
import json

# 调整为256KB（覆盖99%的PDF元数据，避免解析失败）
SAFE_METADATA_SIZE = 256 * 1024  # 262144字节

# 创建蓝图
display_file_bp = Blueprint('display_file', __name__)

def lightweight_linearize_pdf(input_path, output_path):
    """
    轻量级PDF线性化函数，优化PDF流式加载
    """
    try:
        # 检查PyPDF2是否已安装
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except ImportError:
            print("PyPDF2 not available, skipping linearization")
            # 如果PyPDF2未安装，直接复制原文件
            import shutil
            shutil.copy2(input_path, output_path)
            return True

        # 读取并重新写入PDF，以优化结构
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # 复制所有页面
        for page in reader.pages:
            writer.add_page(page)

        # 写入优化的PDF
        with open(output_path, 'wb') as out_file:
            writer.write(out_file)

        return True
    except Exception as e:
        print(f"PDF线性化失败: {str(e)}")
        # 如果线性化失败，使用原始文件
        try:
            import shutil
            shutil.copy2(input_path, output_path)
            return True  # 返回True表示使用原始文件
        except Exception:
            return False

# 展示文件上传目录
DISPLAY_FILE_FOLDER = 'assets/DisplayFiles'

def create_display_file_directories():
    """创建展示文件目录"""
    display_path = os.path.join(current_app.root_path, '..', DISPLAY_FILE_FOLDER)
    os.makedirs(display_path, exist_ok=True)

@display_file_bp.route('/display-file/upload', methods=['POST'])
@login_required
@admin_required
def upload_display_file():
    """上传展示文件（仅管理员）"""
    try:
        create_display_file_directories()

        # 获取表单数据
        title = request.form.get('title', '').strip()
        file_type = request.form.get('file_type', '').strip()  # image_group 或 pdf
        display_mode = request.form.get('display_mode', '').strip()  # pagination 或 waterfall
        current_user = getattr(request, 'current_user', None)

        # 验证参数
        if not title:
            return jsonify({
                "code": 400,
                "msg": "标题不能为空",
                "data": None
            }), 400

        if file_type not in ['image_group', 'pdf']:
            return jsonify({
                "code": 400,
                "msg": "文件类型必须是 image_group 或 pdf",
                "data": None
            }), 400

        if display_mode not in ['pagination', 'waterfall']:
            return jsonify({
                "code": 400,
                "msg": "展示方式必须是 pagination 或 waterfall",
                "data": None
            }), 400

        # 验证是否包含文件
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "没有文件被上传",
                "data": None
            }), 400

        files = request.files.getlist('file')
        if len(files) == 0:
            return jsonify({
                "code": 400,
                "msg": "没有选择文件",
                "data": None
            }), 400

        # 验证文件数量
        if file_type == 'image_group' and len(files) > 50:
            return jsonify({
                "code": 400,
                "msg": "图片组最多只能上传50张图片",
                "data": None
            }), 400

        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
        for file in files:
            if file.filename == '':
                continue
            if '.' not in file.filename:
                return jsonify({
                    "code": 400,
                    "msg": "文件没有扩展名",
                    "data": None
                }), 400

            file_ext = file.filename.rsplit('.', 1)[1].lower()
            if file_ext not in allowed_extensions:
                return jsonify({
                    "code": 400,
                    "msg": f"不允许的文件类型: {file_ext}",
                    "data": None
                }), 400

            # 如果是 image_group 类型，只能上传图片
            if file_type == 'image_group' and file_ext not in {'png', 'jpg', 'jpeg', 'gif'}:
                return jsonify({
                    "code": 400,
                    "msg": "图片组类型只能上传图片文件",
                    "data": None
                }), 400

            # 如果是 pdf 类型，只能上传 PDF
            if file_type == 'pdf' and file_ext != 'pdf':
                return jsonify({
                    "code": 400,
                    "msg": "PDF类型只能上传PDF文件",
                    "data": None
                }), 400

        # 获取表单数据
        title = request.form.get('title', '').strip()
        file_type = request.form.get('file_type', '').strip()  # image_group 或 pdf
        display_mode = request.form.get('display_mode', '').strip()  # pagination 或 waterfall
        current_user = getattr(request, 'current_user', None)

        # 生成UUID用于创建文件夹或作为文件命名
        file_uuid = str(uuid.uuid4())

        # 确定保存路径
        display_path = os.path.join(current_app.root_path, '..', DISPLAY_FILE_FOLDER)

        if file_type == 'image_group':
            # 为图片组创建独立文件夹，确保唯一性
            base_folder_name = f"{file_uuid}_{secure_filename(title)}"
            group_folder = base_folder_name
            group_path = os.path.join(display_path, group_folder)

            # 如果文件夹已存在，添加数字后缀
            counter = 1
            while os.path.exists(group_path):
                group_folder = f"{base_folder_name}_{counter}"
                group_path = os.path.join(display_path, group_folder)
                counter += 1

            os.makedirs(group_path, exist_ok=True)

            # 先对上传的文件按原始文件名进行自然排序
            import re
            def natural_sort_key(file_obj):
                if file_obj.filename == '':
                    return ''
                filename = secure_filename(file_obj.filename)
                return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]

            # 按原始文件名进行自然排序
            sorted_files = sorted([f for f in files if f.filename != ''], key=natural_sort_key)

            # 生成一个统一的UUID前缀
            common_uuid_prefix = str(uuid.uuid4())

            saved_files = []
            # 使用统一的UUID前缀加上序号来保持排序
            for index, file in enumerate(sorted_files, start=1):
                if file.filename == '':
                    continue
                original_filename = secure_filename(file.filename)
                # 使用统一UUID前缀+序号来命名文件，这样即使按文件名排序也会保持正确的顺序
                unique_filename = f"{common_uuid_prefix}_{index:03d}_{original_filename}"
                save_path = os.path.join(group_path, unique_filename)

                # 保存文件
                file.save(save_path)
                saved_files.append(unique_filename)

            # 存储文件夹路径
            file_path_to_store = os.path.join(DISPLAY_FILE_FOLDER, group_folder)
            original_filename = f"{len(saved_files)}张图片"

            # 将图片数量写入页数字段
            pages = len(saved_files)
        else:
            # 对于PDF文件，只保存第一个文件
            file = files[0]
            original_filename = secure_filename(file.filename)
            unique_filename = f"{file_uuid}_{original_filename}"
            save_path = os.path.join(display_path, unique_filename)

            # 保存文件
            file.save(save_path)

            # 如果是PDF文件，进行线性化处理
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            file_path_to_store = os.path.join(DISPLAY_FILE_FOLDER, unique_filename)

        # 创建数据库记录
        display_file = DisplayFile(
            title=title,
            file_type=file_type,
            file_path=file_path_to_store,
            original_filename=original_filename,
            page_count=len(saved_files) if file_type == 'image_group' else None,  # 为图片组设置页数
            created_by=current_user.name if current_user else 'Unknown'
        )

        db.session.add(display_file)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "展示文件上传成功",
            "data": display_file.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"上传展示文件失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/display-file/list', methods=['GET'])
@login_required
def get_display_file_list():
    """获取展示文件列表"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # 限制每页最多100条记录
        per_page = min(per_page, 100)

        query = DisplayFile.query.order_by(DisplayFile.created_at.desc())

        # 执行分页查询
        paginated_files = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        files = [file.to_dict() for file in paginated_files.items]

        return jsonify({
            "code": 200,
            "msg": "获取展示文件列表成功",
            "data": {
                "files": files,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": paginated_files.total,
                    "pages": paginated_files.pages
                }
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取展示文件列表失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/display-file/<int:file_id>', methods=['GET'])
@login_required
def get_display_file(file_id):
    """获取单个展示文件详情"""
    try:
        display_file = DisplayFile.query.get_or_404(file_id)

        return jsonify({
            "code": 200,
            "msg": "获取展示文件详情成功",
            "data": display_file.to_dict()
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取展示文件详情失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/display-file/<string:uuid>', methods=['GET'])
def get_display_file_by_uuid(uuid):
    """通过UUID获取展示文件详情（用于前端展示，不需登录）"""
    try:
        display_file = DisplayFile.query.filter_by(uuid=uuid).first_or_404()

        return jsonify({
            "code": 200,
            "msg": "获取展示文件详情成功",
            "data": display_file.to_dict()
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取展示文件详情失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/display-file/<string:uuid>/images', methods=['GET'])
def get_image_group(uuid):
    """获取图片组中的所有图片（用于前端展示）"""
    try:
        display_file = DisplayFile.query.filter_by(uuid=uuid).first_or_404()

        if display_file.file_type != 'image_group':
            return jsonify({
                "code": 400,
                "msg": "该文件不是图片组类型",
                "data": None
            }), 400

        # 获取图片组文件夹路径
        file_path = display_file.file_path
        group_path = os.path.join(current_app.root_path, '..', file_path)

        if not os.path.exists(group_path):
            return jsonify({
                "code": 400,
                "msg": "图片组文件夹不存在",
                "data": None
            }), 400

        # 获取文件夹中的所有图片文件
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        image_files = []

        for filename in os.listdir(group_path):
            if os.path.splitext(filename)[1].lower() in allowed_extensions:
                image_files.append(filename)

        # 按文件名自然排序（处理数字排序如 1,2,3,10 而不是 1,10,2,3）
        import re
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
        image_files.sort(key=natural_sort_key)
        # 构建图片URL列表 - 使用新的静态文件服务路由
        image_urls = []
        for img_file in image_files:
            # 提取文件夹名称并构建正确的URL路径
            folder_name = os.path.basename(file_path)
            image_urls.append(f"/api/assets/DisplayFiles/{folder_name}/{img_file}")

        return jsonify({
            "code": 200,
            "msg": "获取图片组成功",
            "data": {
                "uuid": uuid,
                "title": display_file.title,
                "total_images": len(image_urls),
                "images": image_urls
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取图片组失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/display-file/<int:file_id>', methods=['PUT'])
@login_required
@admin_required
def update_display_file(file_id):
    """更新展示文件信息（仅管理员）"""
    try:
        display_file = DisplayFile.query.get_or_404(file_id)

        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400

        # 更新允许的字段
        if 'title' in data:
            display_file.title = data['title']
        if 'page_count' in data:
            display_file.page_count = data['page_count']

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "文件信息更新成功",
            "data": display_file.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新文件信息失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/display-file/<int:file_id>/page-count', methods=['PUT'])
@login_required
@admin_required
def update_display_file_page_count(file_id):
    """更新展示文件页数（仅管理员）"""
    try:
        display_file = DisplayFile.query.get_or_404(file_id)

        # 获取请求数据
        data = request.get_json()
        if not data or 'page_count' not in data:
            return jsonify({
                "code": 400,
                "msg": "页数参数缺失",
                "data": None
            }), 400

        page_count = data['page_count']
        if page_count is not None and (not isinstance(page_count, int) or page_count < 0):
            return jsonify({
                "code": 400,
                "msg": "页数必须是非负整数",
                "data": None
            }), 400

        # 只有当当前页数为空时才更新
        if display_file.page_count is None or display_file.page_count == 0:
            display_file.page_count = page_count
        else:
            # 如果页数已存在但与新值不同，也更新
            if display_file.page_count != page_count:
                display_file.page_count = page_count

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "页数更新成功",
            "data": display_file.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"更新页数失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/display-file/<int:file_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_display_file(file_id):
    """删除展示文件（仅管理员）"""
    try:
        display_file = DisplayFile.query.get_or_404(file_id)

        # 删除物理文件或文件夹
        file_path = os.path.join(current_app.root_path, '..', display_file.file_path)
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                # 如果是单个文件，直接删除
                os.remove(file_path)
            elif os.path.isdir(file_path):
                # 如果是文件夹（图片组），删除整个文件夹
                import shutil
                shutil.rmtree(file_path)

        # 删除数据库记录
        db.session.delete(display_file)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "删除展示文件成功",
            "data": None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": f"删除展示文件失败: {str(e)}",
            "data": None
        }), 500

@display_file_bp.route('/assets/DisplayFiles/<path:filename>')
def serve_display_files(filename):
    """
    服务DisplayFiles目录下的静态文件（图片和PDF等）
    """
    try:
        # 构建文件路径，确保安全，防止路径遍历攻击
        display_path = os.path.join(current_app.root_path, '..', DISPLAY_FILE_FOLDER)
        display_path = os.path.abspath(display_path)

        requested_path = os.path.abspath(os.path.join(display_path, filename))

        # 确保请求的路径在DisplayFiles目录内
        if not requested_path.startswith(display_path):
            return jsonify({
                "code": 400,
                "msg": "非法路径访问",
                "data": None
            }), 400

        if not os.path.exists(requested_path):
            return jsonify({
                "code": 404,
                "msg": f"文件不存在: {filename}",
                "data": None
            }), 404

        # 检查文件扩展名，如果是PDF则使用带Range请求支持的逻辑
        import mimetypes
        mimetype, _ = mimetypes.guess_type(requested_path)
        if mimetype == 'application/pdf':
            # 对PDF文件使用Range请求支持的逻辑
            return serve_pdf_with_range_support(requested_path, filename)
        else:
            # 对非PDF文件使用普通发送方式
            from flask import send_file
            response = send_file(requested_path, mimetype=mimetype)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"文件服务错误: {str(e)}",
            "data": None
        }), 500


def serve_pdf_with_range_support(file_path, original_filename):
    """
    服务PDF文件：提供Range请求支持，用于流式加载
    """
    try:
        file_size = os.path.getsize(file_path)

        # 解析Range请求头
        range_header = request.headers.get('Range')
        if range_header:
            try:
                # 解析Range：bytes=start-end
                range_part = range_header.replace('bytes=', '')
                start_str, end_str = range_part.split('-')
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1

                # 校验Range合法性
                if start < 0 or end >= file_size or start > end:
                    return "Requested Range Not Satisfiable", 416

                # 返回206分段数据
                chunk_size = end - start + 1

                def generate_chunk():
                    with open(file_path, 'rb') as f:
                        f.seek(start)
                        remaining = chunk_size
                        while remaining > 0:
                            read_size = min(4096, remaining)
                            data = f.read(read_size)
                            if not data:
                                break
                            remaining -= read_size
                            yield data

                from flask import Response
                response = Response(generate_chunk(), status=206, mimetype='application/pdf')
                response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                response.headers['Accept-Ranges'] = 'bytes'
                response.headers['Content-Length'] = str(chunk_size)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Expose-Headers'] = 'Content-Range, Accept-Ranges, Content-Length, Content-Type'
                return response

            except Exception as e:
                return f"Range解析失败：{str(e)}", 400
        else:
            # 首次请求：直接返回完整文件，但告知支持Range
            from flask import send_file
            response = send_file(
                file_path,
                mimetype='application/pdf',
                as_attachment=False
            )
            response.headers['Accept-Ranges'] = 'bytes'  # 保留Range支持
            response.headers['Content-Length'] = str(file_size)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Range, Accept-Ranges, Content-Length, Content-Type'
            return response
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"PDF文件服务错误: {str(e)}",
            "data": None
        }), 500


@display_file_bp.route('/display-file/file/<path:filename>')
def serve_display_file(filename):
    """
    服务PDF文件：保留Range支持，首次请求返回完整文件（避免解析失败）
    """
    try:
        # 从路径中提取真正的文件名
        actual_filename = os.path.basename(filename)

        # 构建文件路径
        file_path = os.path.join(current_app.root_path, '..', DISPLAY_FILE_FOLDER)
        file_path = os.path.normpath(file_path)

        # 手动构建完整文件路径
        full_path = os.path.join(file_path, actual_filename)
        full_path = os.path.normpath(full_path)

        # 检查文件是否存在
        if not os.path.exists(full_path):
            return jsonify({
                "code": 404,
                "msg": f"文件不存在: {actual_filename}",
                "data": None
            }), 404

        file_size = os.path.getsize(full_path)

        # 解析Range请求头（后续页面加载用）
        range_header = request.headers.get('Range')
        if range_header:
            try:
                # 解析Range：bytes=start-end
                range_part = range_header.replace('bytes=', '')
                start_str, end_str = range_part.split('-')
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1

                # 校验Range合法性
                if start < 0 or end >= file_size or start > end:
                    return "Requested Range Not Satisfiable", 416

                # 返回206分段数据（后续页面加载）
                chunk_size = end - start + 1

                def generate_chunk():
                    with open(full_path, 'rb') as f:
                        f.seek(start)
                        remaining = chunk_size
                        while remaining > 0:
                            read_size = min(4096, remaining)
                            data = f.read(read_size)
                            if not data:
                                break
                            remaining -= read_size
                            yield data

                from flask import Response
                response = Response(generate_chunk(), status=206, mimetype='application/pdf')
                response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                response.headers['Accept-Ranges'] = 'bytes'
                response.headers['Content-Length'] = str(chunk_size)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Expose-Headers'] = 'Content-Range, Accept-Ranges, Content-Length, Content-Type'
                return response

            except Exception as e:
                return f"Range解析失败：{str(e)}", 400
        else:
            # 首次请求：直接返回完整文件（避免解析失败）
            # 关键：返回200状态码，但告知支持Range
            from flask import send_file
            response = send_file(
                full_path,
                mimetype='application/pdf',
                as_attachment=False
            )
            response.headers['Accept-Ranges'] = 'bytes'  # 保留Range支持
            response.headers['Content-Length'] = str(file_size)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Range, Accept-Ranges, Content-Length, Content-Type'
            return response
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"文件服务错误: {str(e)}",
            "data": None
        }), 500