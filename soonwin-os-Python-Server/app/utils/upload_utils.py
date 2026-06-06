"""
通用上传处理工具模块
用于处理文件上传、压缩、队列等通用功能
"""

import os
import uuid
from datetime import datetime
import subprocess
import json
from queue import Queue
import threading
from flask import current_app
from werkzeug.utils import secure_filename
import imghdr
from PIL import Image

# 上传配置
UPLOAD_CONFIG = {
    'TEMP_UPLOAD_FOLDER': 'assets/TempFiles',
    'IMAGE_UPLOAD_FOLDER': 'assets/Media/Photos',
    'VIDEO_UPLOAD_FOLDER': 'assets/Media/Videos',
    'IMAGE_ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'webp'},
    'VIDEO_ALLOWED_EXTENSIONS': {'mp4', 'avi', 'mov', 'mkv', 'wmv'},
    'ALL_ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'webp', 'mp4', 'avi', 'mov', 'mkv', 'wmv', 'pdf', 'doc', 'docx', 'xls', 'xlsx'},
    'VIDEO_SIZE_THRESHOLD': 100,  # 视频大小阈值，单位MB
    'VIDEO_MAX_WIDTH': 1920,      # 视频最大宽度
    'VIDEO_MAX_HEIGHT': 1080      # 视频最大高度
}

def create_upload_directories():
    """创建上传目录"""
    for folder_key, folder_path in UPLOAD_CONFIG.items():
        if folder_key.endswith('_FOLDER'):
            full_path = os.path.join(current_app.root_path, '..', folder_path)
            os.makedirs(full_path, exist_ok=True)

def get_video_info(video_path):
    """获取视频原始基础信息（大小、分辨率、帧率、格式）"""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]
    try:
        # 在Windows上使用locale.getpreferredencoding()可能会导致编码问题
        # 尝试使用 'utf-8' 并设置 errors='ignore' 或 'replace'
        try:
            result = subprocess.check_output(cmd, encoding='utf-8', stderr=subprocess.PIPE)
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试使用系统默认编码，并允许错误处理
            import locale
            encoding = locale.getpreferredencoding()
            try:
                result = subprocess.check_output(cmd, stderr=subprocess.PIPE)
                result = result.decode(encoding, errors='replace')
            except UnicodeDecodeError:
                # 作为最后手段，使用latin-1编码
                result = subprocess.check_output(cmd, stderr=subprocess.PIPE)
                result = result.decode('latin-1', errors='replace')

        info = json.loads(result)

        # 提取核心信息（仅基于原始文件）
        file_size = int(info['format']['size']) / 1024 / 1024  # 转换为MB
        stream = info['streams'][0] if info['streams'] else {}
        width = int(stream.get('width', 0))
        height = int(stream.get('height', 0))
        fps = eval(stream.get('r_frame_rate', '30/1')) if 'r_frame_rate' in stream else 30
        format_name = info['format']['format_name'].split(',')[0].lower()  # 原始格式

        return {
            'size_mb': round(file_size, 2),
            'width': width,
            'height': height,
            'fps': round(fps, 1),
            'format': format_name
        }
    except json.JSONDecodeError:
        print(f"无法解析视频信息JSON：文件路径 {video_path}")
        return None
    except Exception as e:
        print(f"获取视频信息失败：{e}")
        return None

def compress_video(input_path, output_path, size_threshold=100):
    """
    一步式处理视频：同步完成格式转换（→MP4）+ 按需压缩
    仅基于原始文件大小判断是否压缩，压缩后不校验大小，无二次压缩
    :param input_path: 原始视频路径
    :param output_path: 最终MP4输出路径
    :param size_threshold: 原始文件大小阈值（MB），默认100
    """
    # 1. 获取原始视频信息
    video_info = get_video_info(input_path)
    if not video_info:
        print("视频信息获取失败，处理终止")
        return None

    size_mb = video_info['size_mb']
    width = video_info['width']
    fps = video_info['fps']
    is_mp4 = (video_info['format'].lower() == 'mp4')

    # 2. 分场景执行一步式命令
    if size_mb > size_threshold:
        # 场景1：原始文件>100MB → 同步转MP4+标准压缩（适配机器视频）
        print(f"原始文件{size_mb}MB>100MB，同步转MP4+标准压缩...")
        cmd = [
            'ffmpeg', '-i', input_path,
            # 视频压缩核心参数（H.264+CRF27+码率限制）
            '-c:v', 'libx264', '-crf', '27', '-maxrate', '2000k', '-bufsize', '4000k',
            # 分辨率≤1080P，帧率25fps（机器视频足够）
            '-vf', f"scale='min(1920,{width})':-2,fps=25",
            # 音频编码（微信兼容）
            '-c:a', 'aac', '-b:a', '128k',
            # 强制输出MP4格式，覆盖文件
            '-f', 'mp4', '-y', output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    elif width > 1920 or fps > 30:
        # 场景2：原始文件≤100MB但分辨率/帧率过高 → 同步转MP4+轻度压缩
        print(f"原始文件{size_mb}MB≤100MB，分辨率/帧率过高，同步转MP4+轻度压缩...")
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264', '-crf', '24', '-maxrate', '2500k', '-bufsize', '5000k',
            '-vf', f"scale='min(1920,{width})':-2,fps=30",
            '-c:a', 'copy' if is_mp4 else 'aac',  # MP4音频直接复制，非MP4转AAC
            '-f', 'mp4', '-y', output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    else:
        # 场景3：原始文件≤100MB且画质达标 → 仅转MP4（优先无损复制）
        print(f"原始文件{size_mb}MB≤100MB且画质达标，仅同步转MP4（无损）...")
        try:
            # 优先无损复制流（最快）
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'copy', '-c:a', 'copy',
                '-f', 'mp4', '-y', output_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                # 如果无损复制失败，记录错误并继续到有损编码
                try:
                    stderr_str = result.stderr.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    import locale
                    encoding = locale.getpreferredencoding()
                    stderr_str = result.stderr.decode(encoding, errors='replace')
                print(f"无损复制失败: {stderr_str}")
                raise  # 重新抛出异常以触发有损编码
        except:
            # 复制失败（如编码不兼容）→ 轻度编码转MP4（保证成功）
            print("无损转格式失败，轻度编码转MP4...")
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac',
                '-f', 'mp4', '-y', output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 3. 验证输出文件
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"视频处理完成，输出文件：{output_path}")
        return output_path
    else:
        print("视频处理失败，未生成有效文件")
        return None

def add_video_compress_task(video_id, original_file_path, base_save_dir, app_instance):
    """添加视频压缩任务到处理队列"""
    processing_queue = get_processing_queue()
    task = {
        'type': 'video_compress',
        'video_id': video_id,
        'original_file_path': original_file_path,
        'base_save_dir': base_save_dir,
        'app_instance': app_instance
    }
    processing_queue.add_task(task)

def sanitize_filename(filename):
    """清理文件名，确保在Windows中合法"""
    # 移除Windows不支持的字符，包括换行符和制表符
    invalid_chars = '<>:"/\\|?*\r\n\t'
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

def generate_title_based_filename(title, original_filename):
    """根据标题生成文件名，格式：标题_年月日时分秒"""
    # 获取文件扩展名
    ext = original_filename.split('.')[-1].lower()

    # 清理标题，移除Windows不支持的字符，包括换行符
    invalid_chars = '<>:"/\\|?*\r\n\t'
    for char in invalid_chars:
        title = title.replace(char, '_')

    # 限制标题长度，避免文件名过长
    if len(title) > 80:
        title = title[:80]

    # 添加时间戳
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # 生成文件名
    filename = f"{title}_{timestamp}.{ext}"
    return filename

def generate_unique_filename(original_filename):
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

def validate_file_type(file, allowed_extensions=None):
    """验证上传的文件类型"""
    if allowed_extensions is None:
        allowed_extensions = UPLOAD_CONFIG['ALL_ALLOWED_EXTENSIONS']

    # 1. 检查文件后缀（白名单）
    if '.' not in file.filename or file.filename.split('.')[-1].lower() not in allowed_extensions:
        return False, f"仅支持{', '.join(allowed_extensions)}格式的文件"

    # 2. 检查文件头（更可靠的格式验证，主要针对图片）
    if any(ext in allowed_extensions for ext in UPLOAD_CONFIG['IMAGE_ALLOWED_EXTENSIONS']):
        file.seek(0)  # 重置文件指针
        img_type = imghdr.what(file)
        file.seek(0)  # 重置指针，避免后续读取失败
        if img_type not in UPLOAD_CONFIG['IMAGE_ALLOWED_EXTENSIONS']:
            return False, "文件格式验证失败，非有效图片文件"

    return True, "验证通过"


def allowed_file(filename):
    """验证上传的文件类型"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in UPLOAD_CONFIG['ALL_ALLOWED_EXTENSIONS']


def get_file_type(filename):
    """根据文件扩展名确定文件类型"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in UPLOAD_CONFIG['IMAGE_ALLOWED_EXTENSIONS']:
        return 'image'
    elif ext in UPLOAD_CONFIG['VIDEO_ALLOWED_EXTENSIONS']:
        return 'video'
    else:
        return 'other'

def save_uploaded_file(file, base_save_dir, use_date_subdir=True, custom_filename=None):
    """
    保存上传的文件到指定目录
    :param file: Flask上传的File对象
    :param base_save_dir: 基础存储目录
    :param use_date_subdir: 是否使用日期子目录
    :param custom_filename: 自定义文件名（可选）
    :return: 保存的文件路径
    """
    # 获取或生成文件名
    if custom_filename:
        original_filename = sanitize_filename(custom_filename)
    else:
        original_filename = generate_unique_filename(file.filename)

    # 确定保存路径
    if use_date_subdir:
        save_dir = get_date_dir(base_save_dir)
        save_path = os.path.join(save_dir, original_filename)
    else:
        os.makedirs(base_save_dir, exist_ok=True)
        save_path = os.path.join(base_save_dir, original_filename)

    # 保存文件
    file.save(save_path)

    # 返回相对于基础目录的路径
    relative_path = os.path.relpath(save_path, base_save_dir).replace('\\', '/')
    return save_path, relative_path, original_filename

def process_image_with_variants(file_path, base_save_dir, file_prefix, ext, max_sizes=None):
    """
    处理图片，生成不同尺寸的变体
    :param file_path: 原图路径
    :param base_save_dir: 基础存储目录
    :param file_prefix: 文件前缀
    :param ext: 文件扩展名
    :param max_sizes: 最大尺寸配置 {'variant_name': max_size}
    :return: 各变体的路径
    """
    if max_sizes is None:
        # 默认图片尺寸配置
        max_sizes = {
            'thumbnail': 400,    # 缩略图最大400px
            'normal': 1280,      # 普通图最大1280px
            'original': 2560     # 原图最大2560px
        }

    img = Image.open(file_path)
    original_width, original_height = img.size
    max_original_side = max(original_width, original_height)

    result_paths = {}

    # 按配置生成各尺寸图片
    for variant, max_size in max_sizes.items():
        if max_original_side > max_size:
            # 需要压缩
            scale = max_size / max_original_side
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 确定保存路径
            save_dir = os.path.dirname(file_path)

            if variant == 'thumbnail':
                # 缩略图统一保存为 WebP（比 JPEG/PNG 节省 25-35% 空间，所有现代浏览器均支持）
                webp_path = os.path.join(save_dir, f"{file_prefix}_thumbnail.webp")
                # RGBA/LA/P 模式需转为 RGB（WebP lossy 不支持 alpha，缩略图无需透明度）
                if resized_img.mode in ('RGBA', 'LA', 'P'):
                    resized_img = resized_img.convert('RGB')
                resized_img.save(webp_path, 'WEBP', quality=80)
                result_paths[variant] = os.path.relpath(webp_path, base_save_dir).replace('\\', '/')
            else:
                variant_path = os.path.join(save_dir, f"{file_prefix}_{variant}.{ext}")
                resized_img.save(variant_path, quality=85)
                result_paths[variant] = os.path.relpath(variant_path, base_save_dir).replace('\\', '/')
        else:
            # 不需要压缩，使用原图
            result_paths[variant] = os.path.relpath(file_path, base_save_dir).replace('\\', '/')

    return {
        'paths': result_paths,
        'original_width': original_width,
        'original_height': original_height,
        'needs_processing': max_original_side > min(max_sizes.values())
    }

def process_video_with_variants(file_path, base_save_dir, file_prefix, ext):
    """
    处理视频，生成缩略图等变体（需要ffmpeg支持）
    :param file_path: 原视频路径
    :param base_save_dir: 基础存储目录
    :param file_prefix: 文件前缀
    :param ext: 文件扩展名（兼容原参数，实际未使用，可后续按需删除）
    :return: 各变体路径+视频元信息+是否需要压缩
    """
    # 简化：直接初始化返回路径，减少冗余赋值
    result_paths = {'thumbnail': ''}
    duration, width, height = 0.0, 0, 0

    # 核心：ffprobe获取视频元信息（不能简化，必要性见上文）
    try:
        ffprobe_cmd = [
            'ffprobe', '-v', 'quiet', '-show_format', '-show_streams',
            '-print_format', 'json', file_path
        ]
        # 修复编码问题：先获取字节输出，然后手动解码
        res = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            try:
                stdout_str = res.stdout.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                # 如果UTF-8失败，尝试系统默认编码
                import locale
                encoding = locale.getpreferredencoding()
                stdout_str = res.stdout.decode(encoding, errors='replace')

            video_info = json.loads(stdout_str)
            # 简化：合并时长/宽高获取逻辑，减少嵌套
            for stream in video_info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width, height = stream.get('width', 0), stream.get('height', 0)
                    duration = float(stream.get('duration', 0)) or float(video_info.get('format', {}).get('duration', 0))
                    break
    except json.JSONDecodeError:
        print("无法解析视频元信息JSON")
    except UnicodeDecodeError as e:
        print(f"解码视频信息输出失败: {e}")
    except Exception as e:
        print(f"获取视频信息失败: {str(e)}")

    # 核心：ffmpeg生成缩略图（核心参数不能简化，冗余逻辑已删除）
    try:
        # 修改：将缩略图保存在与视频文件相同的目录中
        video_dir = os.path.dirname(file_path)
        thumbnail_path = os.path.join(video_dir, f"{file_prefix}_thumbnail.jpg")
        # 简化：一行逻辑覆盖所有截取场景（优先10秒，不足则取中间点，至少1秒）
        safe_ss = min(10.0, max(1.0, duration * 0.5)) if duration > 0 else 1.0

        # 核心参数（不能简化）：-ss(时间点)、-vframes(1帧)、-vf(缩放)、-y(覆盖)
        ffmpeg_cmd = [
            'ffmpeg', '-i', file_path, '-ss', str(safe_ss), '-vframes', '1',
            '-vf', 'scale=400:300:force_original_aspect_ratio=decrease',
            '-y', thumbnail_path
        ]
        res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            # 核心：相对路径返回（现在相对于base_save_dir，但指向正确的缩略图位置）
            result_paths['thumbnail'] = os.path.relpath(thumbnail_path, base_save_dir).replace('\\', '/')
        else:
            # 尝试解码错误信息
            try:
                stderr_str = res.stderr.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                import locale
                encoding = locale.getpreferredencoding()
                stderr_str = res.stderr.decode(encoding, errors='replace')
            print(f"生成缩略图失败: {stderr_str}")
    # 简化：合并同类异常，减少重复提示
    except FileNotFoundError:
        print("ffmpeg/ffprobe未安装，无法处理视频缩略图")
    except Exception as e:
        print(f"生成缩略图异常: {str(e)}")

    # 核心：是否需要压缩的判断（不能简化，双维度判断缺一不可）
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        needs_processing = (file_size_mb > UPLOAD_CONFIG['VIDEO_SIZE_THRESHOLD'] or
                            width > UPLOAD_CONFIG['VIDEO_MAX_WIDTH'] or
                            height > UPLOAD_CONFIG['VIDEO_MAX_HEIGHT'])
    except Exception as e:
        print(f"判断视频是否需要压缩失败: {str(e)}")
        needs_processing = False

    # 简化：返回值无冗余，直接返回核心信息
    return {
        'paths': result_paths, 'duration': round(duration, 2),  # 保留2位小数更整洁
        'width': width, 'height': height, 'needs_processing': needs_processing
    }

class ProcessingQueue:
    """
    通用处理队列，用于异步处理上传后的文件
    支持图片压缩、视频转码等异步任务
    """

    def __init__(self, maxsize=0):
        self.queue = Queue(maxsize=maxsize)
        self.worker_thread = None
        self.app_instance = None

    def set_app_instance(self, app):
        """设置Flask应用实例"""
        self.app_instance = app
        if self.worker_thread is None:
            self.start_worker()

    def start_worker(self):
        """启动处理工作线程"""
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _worker(self):
        """处理工作线程"""
        from flask import Flask

        while True:
            try:
                # 阻塞等待队列任务
                task = self.queue.get(timeout=3600)  # 1小时超时

                # 获取任务信息
                task_type = task.get('task_type')
                handler_func = task.get('handler_func')
                handler_args = task.get('handler_args', {})

                print(f"开始处理 {task_type} 任务")

                try:
                    # 执行处理函数
                    if handler_func and callable(handler_func):
                        # 如果有应用上下文，使用它
                        if self.app_instance:
                            with self.app_instance.app_context():
                                handler_func(**handler_args)
                        else:
                            handler_func(**handler_args)
                    else:
                        print(f"无效的处理函数: {handler_func}")
                except Exception as e:
                    print(f"处理 {task_type} 任务时出错: {str(e)}")
                finally:
                    # 标记任务完成
                    self.queue.task_done()

            except Exception as e:
                # 队列超时或其他错误，继续循环
                continue

    def add_task(self, task_type, handler_func, **handler_args):
        """添加处理任务到队列"""
        task = {
            'task_type': task_type,
            'handler_func': handler_func,
            'handler_args': handler_args
        }
        self.queue.put(task)

    def get_queue_size(self):
        """获取队列大小"""
        return self.queue.qsize()

# 全局处理队列实例
processing_queue = ProcessingQueue()

def add_image_compress_task(photo_id, original_file_path, file_prefix, ext, save_dir, base_save_dir,
                           max_sizes=None, update_func=None):
    """
    添加图片压缩任务到队列
    :param photo_id: 照片ID
    :param original_file_path: 原文件路径
    :param file_prefix: 文件前缀
    :param ext: 文件扩展名
    :param save_dir: 保存目录
    :param base_save_dir: 基础目录
    :param max_sizes: 最大尺寸配置
    :param update_func: 更新数据库的回调函数
    """
    def compress_image_handler(photo_id, original_file_path, file_prefix, ext, save_dir,
                              base_save_dir, max_sizes, update_func):
        """实际的图片压缩处理器"""
        try:
            # 更新状态为处理中
            if update_func:
                update_func(photo_id, "processing")

            # 处理图片变体
            result = process_image_with_variants(
                original_file_path, base_save_dir, file_prefix, ext, max_sizes
            )

            # 更新完成状态
            if update_func:
                update_func(photo_id, "success", result['paths'])

            # 删除原始文件（如果已生成压缩版本）
            if result['paths'].get('original'):
                try:
                    os.remove(original_file_path)
                    print(f"原图已删除: {original_file_path}")
                except Exception as e:
                    print(f"删除原图失败: {str(e)}")
        except Exception as e:
            print(f"图片压缩失败: {str(e)}")
            if update_func:
                update_func(photo_id, "failed", error_msg=str(e))

    # 添加任务到队列
    processing_queue.add_task(
        task_type="image_compress",
        handler_func=compress_image_handler,
        photo_id=photo_id,
        original_file_path=original_file_path,
        file_prefix=file_prefix,
        ext=ext,
        save_dir=save_dir,
        base_save_dir=base_save_dir,
        max_sizes=max_sizes,
        update_func=update_func
    )

def add_video_process_task(video_id, original_file_path, file_prefix, ext, save_dir, base_save_dir,
                           update_func=None):
    """
    添加视频处理任务到队列（缩略图生成等）
    :param video_id: 视频ID
    :param original_file_path: 原文件路径
    :param file_prefix: 文件前缀
    :param ext: 文件扩展名
    :param save_dir: 保存目录
    :param base_save_dir: 基础目录
    :param update_func: 更新数据库的回调函数
    """
    def process_video_handler(video_id, original_file_path, file_prefix, ext, save_dir,
                             base_save_dir, update_func):
        """实际的视频处理器"""
        try:
            # 更新状态为处理中
            if update_func:
                update_func(video_id, "processing")

            # 处理视频变体
            result = process_video_with_variants(
                original_file_path, base_save_dir, file_prefix, ext
            )

            # 更新完成状态
            if update_func:
                update_func(video_id, "success", result['paths'])
        except Exception as e:
            print(f"视频处理失败: {str(e)}")
            if update_func:
                update_func(video_id, "failed", error_msg=str(e))

    # 添加任务到队列
    processing_queue.add_task(
        task_type="video_process",
        handler_func=process_video_handler,
        video_id=video_id,
        original_file_path=original_file_path,
        file_prefix=file_prefix,
        ext=ext,
        save_dir=save_dir,
        base_save_dir=base_save_dir,
        update_func=update_func
    )

def add_video_compress_task(video_id, original_file_path, base_save_dir, app_instance):
    """
    添加视频压缩任务到队列
    :param video_id: 视频ID
    :param original_file_path: 原文件路径
    :param base_save_dir: 基础目录
    :param app_instance: Flask应用实例
    """
    def compress_video_handler(video_id, original_file_path, base_save_dir, app_instance):
        """实际的视频压缩处理器"""
        try:
            from ..routes.video_routes import update_video_after_compress
            import os

            # 获取原始文件信息
            original_size_mb = os.path.getsize(original_file_path) / (1024 * 1024)
            print(f"开始压缩视频，原文件大小: {original_size_mb:.2f}MB")

            # 生成压缩后的文件路径
            file_prefix = os.path.basename(original_file_path).rsplit('.', 1)[0]
            compressed_path = os.path.join(os.path.dirname(original_file_path), f"{file_prefix}_compressed.mp4")

            # 执行压缩
            result_path = compress_video(original_file_path, compressed_path, UPLOAD_CONFIG['VIDEO_SIZE_THRESHOLD'])

            if result_path:
                print(f"视频压缩成功: {result_path}")

                # 确认压缩文件确实存在
                if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
                    print(f"确认压缩文件存在且非空，准备更新数据库")

                    # 更新数据库记录
                    if app_instance:
                        with app_instance.app_context():
                            update_video_after_compress(video_id, result_path, original_file_path)
                    else:
                        update_video_after_compress(video_id, result_path, original_file_path)

                    # 数据库更新成功后，安全地删除原始文件
                    try:
                        os.remove(original_file_path)
                        print(f"已删除原视频文件: {original_file_path}")
                    except Exception as e:
                        print(f"删除原视频文件失败: {str(e)}")
                        # 如果删除失败，保留原文件，但仍然标记为压缩成功
                else:
                    print(f"压缩文件不存在或为空，压缩失败: {result_path}")
                    # 更新数据库状态为失败
                    if app_instance:
                        with app_instance.app_context():
                            # 从数据库获取视频记录并更新状态
                            from .. import db
                            from ..models.video import Video
                            video = Video.query.get(video_id)
                            if video:
                                video.compress_status = 'failed'
                                db.session.commit()
                    else:
                        # 直接操作数据库
                        from .. import db
                        from ..models.video import Video
                        video = Video.query.get(video_id)
                        if video:
                            video.compress_status = 'failed'
                            db.session.commit()
            else:
                print(f"视频压缩失败")
                # 如果压缩失败，也要尝试更新数据库状态
                if app_instance:
                    with app_instance.app_context():
                        # 从数据库获取视频记录并更新状态
                        from .. import db
                        from ..models.video import Video
                        video = Video.query.get(video_id)
                        if video:
                            video.compress_status = 'failed'
                            db.session.commit()
                else:
                    # 直接操作数据库
                    from .. import db
                    from ..models.video import Video
                    video = Video.query.get(video_id)
                    if video:
                        video.compress_status = 'failed'
                        db.session.commit()
        except Exception as e:
            print(f"视频压缩处理失败: {str(e)}")
            try:
                # 如果压缩失败，也要尝试更新数据库状态
                if app_instance:
                    with app_instance.app_context():
                        # 从数据库获取视频记录并更新状态
                        from .. import db
                        from ..models.video import Video
                        video = Video.query.get(video_id)
                        if video:
                            video.compress_status = 'failed'
                            db.session.commit()
                else:
                    # 直接操作数据库
                    from .. import db
                    from ..models.video import Video
                    video = Video.query.get(video_id)
                    if video:
                        video.compress_status = 'failed'
                        db.session.commit()
            except Exception as db_error:
                print(f"更新视频压缩失败状态也失败: {str(db_error)}")

    # 添加任务到队列
    processing_queue.add_task(
        task_type="video_compress",
        handler_func=compress_video_handler,
        video_id=video_id,
        original_file_path=original_file_path,
        base_save_dir=base_save_dir,
        app_instance=app_instance
    )

def get_processing_queue():
    """获取全局处理队列实例"""
    return processing_queue
