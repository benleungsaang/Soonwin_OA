from flask import Blueprint, request, jsonify, current_app, send_from_directory
from extensions import db
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import shutil
import zipfile
from ..models.display_file import DisplayFile
from ..models.employee import Employee
from ..utils.auth_utils import require_auth as login_required, require_admin as admin_required
import json

# 创建蓝图
display_file_bp = Blueprint('display_file', __name__)

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
        
        # 验证是否包含文件
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "没有文件被上传",
                "data": None
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 400,
                "msg": "没有选择文件",
                "data": None
            }), 400
        
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
        
        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
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
        
        # 生成安全的文件名
        original_filename = secure_filename(file.filename)
        file_uuid = str(uuid.uuid4())
        unique_filename = f"{file_uuid}_{original_filename}"
        
        # 确定保存路径
        display_path = os.path.join(current_app.root_path, '..', DISPLAY_FILE_FOLDER)
        save_path = os.path.join(display_path, unique_filename)
        
        # 保存文件
        file.save(save_path)
        
        # 创建数据库记录
        display_file = DisplayFile(
            title=title,
            file_type=file_type,
            display_mode=display_mode,
            file_path=os.path.join(DISPLAY_FILE_FOLDER, unique_filename),
            original_filename=original_filename,
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
        
        # 对于图片组，返回文件路径
        # 如果是单个图片，则返回单个图片路径
        # 如果需要展示多个图片，后端需要扩展逻辑来处理ZIP或图片集合
        file_path = display_file.file_path
        image_urls = [f"/api/{file_path}"]  # 假设是单个图片文件
        
        # 如果文件是ZIP格式，需要解压并返回所有图片
        if display_file.original_filename.lower().endswith('.zip'):
            # 这里需要实现ZIP解压逻辑
            import zipfile
            import os
            from werkzeug.utils import secure_filename
            
            zip_path = os.path.join(current_app.root_path, '..', display_file.file_path)
            if os.path.exists(zip_path):
                extract_dir = zip_path.replace('.zip', '_extracted')
                if not os.path.exists(extract_dir):
                    os.makedirs(extract_dir, exist_ok=True)
                    # 解压ZIP文件
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                
                # 获取解压目录中的所有图片文件
                allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
                image_files = []
                for filename in os.listdir(extract_dir):
                    if os.path.splitext(filename)[1].lower() in allowed_extensions:
                        image_files.append(filename)
                
                # 按文件名排序
                image_files.sort()
                
                # 构建图片URL列表
                image_urls = []
                for img_file in image_files:
                    image_path = os.path.relpath(os.path.join(extract_dir, img_file), 
                                               os.path.join(current_app.root_path, '..'))
                    image_urls.append(f"/api/{image_path.replace(os.sep, '/')}")

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

@display_file_bp.route('/display-file/<int:file_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_display_file(file_id):
    """删除展示文件（仅管理员）"""
    try:
        display_file = DisplayFile.query.get_or_404(file_id)
        
        # 删除物理文件
        file_path = os.path.join(current_app.root_path, '..', display_file.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
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

@display_file_bp.route('/display-file/file/<path:filename>')
def serve_display_file(filename):
    """提供展示文件服务"""
    try:
        # 构建文件路径
        # filename 是文件名，例如 'uuid_filename.pdf'
        # 文件实际存储在 'assets/DisplayFiles/' 目录下
        file_path = os.path.join(current_app.root_path, '..', DISPLAY_FILE_FOLDER)
        return send_from_directory(file_path, filename)
    except Exception as e:
        return jsonify({
            "code": 404,
            "msg": f"文件不存在: {str(e)}",
            "data": None
        }), 404