from flask import Blueprint, request, jsonify, current_app
from extensions import db
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import shutil

# 创建蓝图
upload_bp = Blueprint('upload', __name__)

# 临时上传目录
TEMP_UPLOAD_FOLDER = 'assets/TempFiles'
# 已删除文件目录
DELETED_FILES_FOLDER = 'assets/DeleteFiles'
# 资源上传目录
ASSET_UPLOAD_FOLDER = 'assets'

def create_upload_directories():
    """创建上传目录"""
    temp_path = os.path.join(current_app.root_path, '..', TEMP_UPLOAD_FOLDER)
    asset_path = os.path.join(current_app.root_path, '..', ASSET_UPLOAD_FOLDER)
    deleted_path = os.path.join(current_app.root_path, '..', DELETED_FILES_FOLDER)
    
    os.makedirs(temp_path, exist_ok=True)
    os.makedirs(asset_path, exist_ok=True)
    os.makedirs(deleted_path, exist_ok=True)

def sanitize_filename(filename):
    """清理文件名，确保在Windows中合法"""
    # 移除Windows不支持的字符
    invalid_chars = '<>:\"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # 限制文件名长度
    name, ext = os.path.splitext(filename)
    if len(name) > 100:  # 限制文件名长度
        name = name[:100]
    if len(ext) > 10:  # 限制扩展名长度
        ext = ext[:10]
    
    sanitized = name + ext
    return sanitized

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件到临时位置"""
    try:
        create_upload_directories()
        
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
        
        # 获取目标位置参数
        target_path = request.form.get('target_path', '').strip()
        
        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
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
        
        # 生成安全的文件名
        original_filename = secure_filename(file.filename)
        sanitized_filename = sanitize_filename(original_filename)
        unique_filename = f"{uuid.uuid4().hex}_{sanitized_filename}"
        
        # 确定保存路径
        if target_path:
            # 如果提供了目标路径，使用该路径
            full_target_path = os.path.join(current_app.root_path, '..', target_path)
            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)
            save_path = os.path.join(full_target_path, unique_filename)
        else:
            # 否则保存到临时位置
            temp_path = os.path.join(current_app.root_path, '..', TEMP_UPLOAD_FOLDER)
            save_path = os.path.join(temp_path, unique_filename)
        
        # 保存文件
        file.save(save_path)
        
        # 返回文件路径信息
        relative_path = os.path.relpath(save_path, os.path.join(current_app.root_path, '..'))
        
        return jsonify({
            "code": 200,
            "msg": "文件上传成功",
            "data": {
                "original_filename": original_filename,
                "filename": unique_filename,
                "path": relative_path,
                "size": os.path.getsize(save_path),
                "target_path_provided": bool(target_path)
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"上传文件失败: {str(e)}",
            "data": None
        }), 500

@upload_bp.route('/upload/move', methods=['POST'])
def move_file():
    """移动文件位置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400
        
        source_path = data.get('source_path')
        target_path = data.get('target_path')
        
        if not source_path or not target_path:
            return jsonify({
                "code": 400,
                "msg": "源路径和目标路径都必须提供",
                "data": None
            }), 400
        
        # 转换为绝对路径
        base_path = os.path.join(current_app.root_path, '..')
        source_abs_path = os.path.join(base_path, source_path)
        target_abs_path = os.path.join(base_path, target_path)
        
        # 验证源文件存在
        if not os.path.exists(source_abs_path):
            return jsonify({
                "code": 400,
                "msg": "源文件不存在",
                "data": None
            }), 400
        
        # 创建目标目录
        os.makedirs(os.path.dirname(target_abs_path), exist_ok=True)
        
        # 移动文件
        shutil.move(source_abs_path, target_abs_path)
        
        return jsonify({
            "code": 200,
            "msg": "文件移动成功",
            "data": {
                "source_path": source_path,
                "target_path": os.path.relpath(target_abs_path, base_path)
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"移动文件失败: {str(e)}",
            "data": None
        }), 500

@upload_bp.route('/upload/delete', methods=['POST'])
def delete_file():
    """删除指定路径文件（实际上是移动到删除文件目录）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求数据不能为空",
                "data": None
            }), 400
        
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({
                "code": 400,
                "msg": "文件路径必须提供",
                "data": None
            }), 400
        
        # 转换为绝对路径
        base_path = os.path.join(current_app.root_path, '..')
        abs_file_path = os.path.join(base_path, file_path)
        
        # 验证文件存在
        if not os.path.exists(abs_file_path):
            return jsonify({
                "code": 400,
                "msg": "文件不存在",
                "data": None
            }), 400
        
        # 创建删除文件目录
        deleted_path = os.path.join(base_path, DELETED_FILES_FOLDER)
        os.makedirs(deleted_path, exist_ok=True)
        
        # 生成移动后的新文件名（添加时间戳避免冲突）
        filename = os.path.basename(abs_file_path)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        new_filename = f"{name}_{timestamp}{ext}"
        new_file_path = os.path.join(deleted_path, new_filename)
        
        # 移动文件到删除目录
        shutil.move(abs_file_path, new_file_path)
        
        # 获取相对于项目根目录的路径
        relative_new_path = os.path.relpath(new_file_path, base_path)
        
        return jsonify({
            "code": 200,
            "msg": "文件移动到删除目录成功",
            "data": {
                "original_path": file_path,
                "moved_to_path": relative_new_path
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"移动文件到删除目录失败: {str(e)}",
            "data": None
        }), 500

@upload_bp.route('/upload/chunk', methods=['POST'])
def upload_chunk():
    """分块上传文件"""
    try:
        create_upload_directories()
        
        # 获取分块数据
        chunk = request.files.get('chunk')
        chunk_index = int(request.form.get('chunk_index', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
        original_filename = request.form.get('filename', 'unknown')
        file_identifier = request.form.get('file_identifier', str(uuid.uuid4()))
        
        # 清理文件名
        original_filename = secure_filename(original_filename)
        sanitized_filename = sanitize_filename(original_filename)
        
        # 创建临时分块存储目录
        chunk_dir = os.path.join(current_app.root_path, '..', TEMP_UPLOAD_FOLDER, 'chunks')
        os.makedirs(chunk_dir, exist_ok=True)
        
        # 保存当前分块
        chunk_filename = f"{file_identifier}_chunk_{chunk_index}"
        chunk_path = os.path.join(chunk_dir, chunk_filename)
        chunk.save(chunk_path)
        
        # 检查是否所有分块都已上传
        if chunk_index == total_chunks - 1:
            # 所有分块都已上传，合并文件
            final_filename = f"{file_identifier}_{sanitized_filename}"
            temp_path = os.path.join(current_app.root_path, '..', TEMP_UPLOAD_FOLDER)
            final_path = os.path.join(temp_path, final_filename)
            
            with open(final_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_file_path = os.path.join(chunk_dir, f"{file_identifier}_chunk_{i}")
                    if os.path.exists(chunk_file_path):
                        with open(chunk_file_path, 'rb') as chunk_file:
                            final_file.write(chunk_file.read())
                        # 删除已合并的分块
                        os.remove(chunk_file_path)
            
            # 删除空的分块目录
            if not os.listdir(chunk_dir):
                os.rmdir(chunk_dir)
            
            # 返回文件路径信息
            relative_path = os.path.relpath(final_path, os.path.join(current_app.root_path, '..'))
            
            return jsonify({
                "code": 200,
                "msg": "文件上传成功",
                "data": {
                    "original_filename": original_filename,
                    "filename": final_filename,
                    "path": relative_path,
                    "size": os.path.getsize(final_path),
                    "file_identifier": file_identifier
                }
            })
        
        return jsonify({
            "code": 200,
            "msg": "分块上传成功",
            "data": {
                "chunk_index": chunk_index,
                "file_identifier": file_identifier
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"分块上传失败: {str(e)}",
            "data": None
        }), 500