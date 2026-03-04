import os
import subprocess
import json
import sys
import time
import re
from datetime import datetime
from pathlib import Path
import threading
import logging
import shutil

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.simpledialog import askinteger
except ImportError:
    print("tkinter模块不可用，请安装Python GUI支持")
    exit(1)

# 临时变量存储视频压缩状态
video_states = {}

# 视频信息缓存
video_info_cache = {}

# 目录扫描缓存
dir_scan_cache = {}  # 格式: {dir_path: {'files': [file_list], 'timestamp': scan_time}}
dir_cache_ttl = 30  # 目录缓存有效期（秒）

# 配置日志记录（仅输出到控制台）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def prepend_to_log_file(filename, content):
    """在日志文件顶部添加新内容"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = ""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
            if existing_content:
                f.write('\n')
                f.write(existing_content)
    except Exception as e:
        print(f"写入日志文件时出错: {e}")

# 全局变量用于缓存当前压缩任务的日志记录
current_log_entries = []

def logger(level, message):
    """自定义日志记录函数，将日志缓存到内存中"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} | {level:<8} | {message}"
    # 输出到控制台
    print(log_entry)
    # 将日志条目添加到当前任务缓存中
    current_log_entries.append(log_entry)

def flush_log():
    """将缓存的日志条目作为整体写入文件顶部"""
    global current_log_entries
    if not current_log_entries:
        return

    # 将所有缓存的日志条目合并为一个字符串
    combined_log = '\n'.join(current_log_entries) + '\n'
    prepend_to_log_file('video_compress_log.txt', combined_log)

    # 清空缓存
    current_log_entries = []

def get_video_info(video_path):
    """获取视频完整信息（含码率）"""
    # 检查缓存
    if video_path in video_info_cache:
        return video_info_cache[video_path]

    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        try:
            output_str = result.stdout.decode('utf-8')
        except UnicodeDecodeError:
            try:
                import locale
                encoding = locale.getpreferredencoding()
                output_str = result.stdout.decode(encoding, errors='replace')
            except UnicodeDecodeError:
                output_str = result.stdout.decode('latin-1', errors='replace')

        info = json.loads(output_str)

        # 基础信息
        file_size = int(info['format']['size']) / 1024 / 1024  # MB
        duration = float(info['format'].get('duration', 0)) if info['format'].get('duration') != 'N/A' else 0

        # 视频流信息
        video_stream = None
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if video_stream:
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            # 帧率
            r_frame_rate = video_stream.get('r_frame_rate', '30/1')
            if r_frame_rate and r_frame_rate != '0/0':
                try:
                    numerator, denominator = r_frame_rate.split('/')
                    fps = float(numerator) / float(denominator) if denominator != '0' else 30.0
                except:
                    fps = 30.0
            else:
                fps = 30.0
            # 编码和码率
            codec_name = video_stream.get('codec_name', '').lower()
            bit_rate = int(video_stream.get('bit_rate', 0)) / 1000 if video_stream.get('bit_rate') else 0  # kbps
            # 计算像素数（用于码率评估）
            pixel_count = width * height
        else:
            width = 0
            height = 0
            fps = 0.0
            codec_name = 'unknown'
            bit_rate = 0
            pixel_count = 0

        # 容器格式
        format_name = info['format']['format_name'].split(',')[0].lower()

        video_info = {
            'size_mb': round(file_size, 2),
            'width': width,
            'height': height,
            'fps': round(fps, 1),
            'container_format': format_name,
            'video_codec': codec_name,
            'bit_rate_kbps': round(bit_rate, 1),
            'duration_sec': round(duration, 1),
            'pixel_count': pixel_count,
            'file_path': video_path,
            'file_name': os.path.basename(video_path)
        }

        # 存入缓存
        video_info_cache[video_path] = video_info

        return video_info
    except json.JSONDecodeError:
        print(f"[错误] 无法解析视频信息JSON：{video_path}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[错误] ffprobe命令执行失败：{e}")
        return None
    except Exception as e:
        print(f"[错误] 获取{os.path.basename(video_path)}信息失败：{e}")
        return None


def is_compressed_file(file_name):
    """判断是否为压缩后的文件"""
    pattern = r'_compressed_\d{8}_\d{6}'
    return bool(re.search(pattern, file_name))

def get_original_file_path(compressed_file_path):
    """
    根据压缩文件路径获取原文件路径
    检查当前目录、original文件夹和上一级目录中是否存在对应的原文件
    """
    # 获取压缩文件的基本信息
    dir_path = os.path.dirname(compressed_file_path)
    compressed_name = os.path.basename(compressed_file_path)

    # 从压缩文件名中提取原始文件名（去掉_compressed_日期时间部分）
    match = re.match(r'(.+)_compressed_\d{8}_\d{6}\.mp4', compressed_name)
    if not match:
        return None, "文件名格式不正确"

    original_name = match.group(1) + '.mp4'

    # 检查original文件夹中是否存在原文件
    original_dir = os.path.join(dir_path, 'original')
    original_in_original = os.path.join(original_dir, original_name)
    if os.path.exists(original_in_original):
        return original_in_original, None

    # 检查当前目录中是否存在原文件
    original_in_current = os.path.join(dir_path, original_name)
    if os.path.exists(original_in_current):
        return original_in_current, None

    # 检查上一级目录中是否存在原文件
    parent_dir = os.path.dirname(dir_path)
    if parent_dir and parent_dir != dir_path:  # 确保不是根目录
        original_in_parent = os.path.join(parent_dir, original_name)
        if os.path.exists(original_in_parent):
            return original_in_parent, None

    # 原文件不存在，返回错误信息
    return None, f"未找到原文件: {original_name}（已检查当前目录、original文件夹和上一级目录）"

def check_compressed_file_exists(original_file_path):
    """
    检查原文件是否有对应的压缩文件
    检查当前目录、original文件夹和上一级目录中是否存在对应的压缩文件
    """
    # 获取原文件的基本信息
    dir_path = os.path.dirname(original_file_path)
    original_name = os.path.basename(original_file_path)
    base_name = os.path.splitext(original_name)[0]

    # 检查当前目录中是否存在压缩文件
    try:
        for f in os.listdir(dir_path):
            if f.startswith(f"{base_name}_compressed_") and f.endswith(".mp4"):
                compressed_path = os.path.join(dir_path, f)
                return compressed_path, None
    except Exception as e:
        pass

    # 检查original文件夹中是否存在压缩文件
    original_dir = os.path.join(dir_path, 'original')
    if os.path.exists(original_dir):
        try:
            for f in os.listdir(original_dir):
                if f.startswith(f"{base_name}_compressed_") and f.endswith(".mp4"):
                    compressed_path = os.path.join(original_dir, f)
                    return compressed_path, None
        except Exception as e:
            pass

    # 检查上一级目录中是否存在压缩文件
    parent_dir = os.path.dirname(dir_path)
    if parent_dir and parent_dir != dir_path:  # 确保不是根目录
        try:
            for f in os.listdir(parent_dir):
                if f.startswith(f"{base_name}_compressed_") and f.endswith(".mp4"):
                    compressed_path = os.path.join(parent_dir, f)
                    return compressed_path, None
        except Exception as e:
            pass

    # 未找到压缩文件，返回错误信息
    return None, None


def get_dir_files(dir_path):
    """获取目录中的文件列表（使用缓存）"""
    global dir_scan_cache

    current_time = time.time()

    # 检查缓存是否有效
    if dir_path in dir_scan_cache:
        cache_entry = dir_scan_cache[dir_path]
        if current_time - cache_entry['timestamp'] < dir_cache_ttl:
            return cache_entry['files']

    # 缓存无效或不存在，重新扫描目录
    try:
        files = os.listdir(dir_path)
        # 更新缓存
        dir_scan_cache[dir_path] = {
            'files': files,
            'timestamp': current_time
        }
        return files
    except Exception as e:
        print(f"[警告] 扫描目录失败: {e}")
        return []


def get_video_files(directory='.'):
    """获取指定目录下的所有视频文件（过滤压缩后的文件）"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
    video_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if is_compressed_file(file):
                continue
            if Path(file).suffix.lower() in video_extensions:
                full_path = os.path.join(root, file)
                video_files.append(full_path)

    return sorted(video_files)


def print_all_video_info(video_files):
    """启动时打印所有视频文件的完整信息"""
    print("\n" + "="*80)
    print("📋 扫描到的视频文件完整信息（已过滤压缩后的文件）")
    print("="*80)

    if not video_files:
        print("[提示] 未找到任何未压缩的视频文件")
        return

    # 表头
    header = (
        f"{'序号':<4} {'文件名':<40} {'大小(MB)':<10} {'分辨率':<12} {'帧率(fps)':<8} {'编码':<8} {'码率(kbps)':<10}"
    )
    print(header)
    print("-"*80)

    # 每个文件信息
    for idx, file_path in enumerate(video_files, 1):
        info = get_video_info(file_path)
        if info:
            short_name = info['file_name'][:37] + "..." if len(info['file_name']) > 40 else info['file_name']
            line = (
                f"{idx:<4} {short_name:<40} {info['size_mb']:<10.2f} {f'{info["width"]}x{info["height"]}':<12} "
                f"{info['fps']:<8.1f} {info['video_codec']:<8} {info['bit_rate_kbps']:<10.1f}"
            )
            print(line)
        else:
            short_name = os.path.basename(file_path)[:37] + "..." if len(os.path.basename(file_path)) > 40 else os.path.basename(file_path)
            line = f"{idx:<4} {short_name:<40} {'-':<10} {'-':<12} {'-':<8} {'-':<8} {'-':<10}"
            print(line)
    print("="*80)


def predict_compression_effect(video_info):
    """
    预判压缩效果（优化版本）
    :param video_info: 视频信息字典
    :return: (预估压缩率%, 建议等级, 推荐CRF值, 建议说明)
    """
    if not video_info:
        return 0, "未知", 24, "无法获取视频信息"

    # 核心判断参数
    codec = video_info['video_codec']
    bit_rate = video_info['bit_rate_kbps']
    fps = video_info['fps']
    pixel_count = video_info['pixel_count']
    duration = video_info['duration_sec']

    # 1. 计算目标码率（基于分辨率的合理码率）
    target_bitrate = 0
    if pixel_count <= 960*540:  # 标清
        target_bitrate = 800
    elif pixel_count <= 1280*720:  # 720P
        target_bitrate = 1200
    elif pixel_count <= 1920*1080:  # 1080P
        target_bitrate = 1800
    else:  # 4K及以上
        target_bitrate = 3000

    # 2. 调整目标码率（帧率修正）
    target_bitrate = target_bitrate * (25 / fps) if fps > 0 else target_bitrate

    # 3. 基于编码类型调整CRF和预估压缩率
    estimated_compression = 0
    recommended_crf = 24  # 默认值调整
    suggestion = "推荐压缩"

    if codec == 'hevc' or codec == 'h265':
        # HEVC转H264，压缩率约40-60%
        estimated_compression = min(60, max(40, 100 - (target_bitrate / bit_rate * 100) if bit_rate > 0 else 50))
        recommended_crf = 23  # 降低以保持更好质量
        suggestion = "✅ 推荐压缩（HEVC转H264，压缩率高）"

    elif codec == 'h264':
        # H264二次压缩
        if bit_rate > target_bitrate * 1.5:
            # 原始码率远高于合理值，压缩率高
            estimated_compression = min(80, max(40, 100 - (target_bitrate / bit_rate * 100)))
            recommended_crf = 23  # 降低
            suggestion = "✅ 推荐压缩（原始码率过高，压缩空间大）"
        elif bit_rate > target_bitrate:
            # 原始码率略高，有压缩空间
            estimated_compression = min(30, max(10, 100 - (target_bitrate / bit_rate * 100)))
            recommended_crf = 25  # 降低
            suggestion = "⚠️ 谨慎压缩（压缩空间有限，约10-30%）"
        else:
            # 原始码率已很低，可能负压缩
            estimated_compression = -5  # 预估轻微变大
            recommended_crf = 27  # 降低
            suggestion = "❌ 不建议压缩（原始码率已最优，可能越压越大）"

    else:
        # 其他编码（mpeg4、vp9等）
        estimated_compression = min(50, max(20, 100 - (target_bitrate / bit_rate * 100) if bit_rate > 0 else 30))
        recommended_crf = 24  # 降低
        suggestion = "✅ 推荐压缩（老旧编码，压缩空间大）"

    # 修正预估压缩率（确保合理范围）
    estimated_compression = max(-10, min(90, estimated_compression))

    return round(estimated_compression, 1), suggestion, recommended_crf, f"""
    预判依据：
    - 原始编码：{codec} | 原始码率：{bit_rate} kbps
    - 目标码率：{target_bitrate} kbps | 帧率：{fps}→25 fps
    - 分辨率：{video_info['width']}x{video_info['height']}
    """
    """
    预判压缩效果（优化版本）
    :param video_info: 视频信息字典
    :return: (预估压缩率%, 建议等级, 推荐CRF值, 建议说明)
    """


def print_compression_prediction(video_info):
    """打印压缩预判结果"""
    print("\n" + "="*80)
    print("🔍 压缩效果预判")
    print("="*80)

    compression_rate, suggestion, crf, reason = predict_compression_effect(video_info)

    print(f"[预估压缩率] {compression_rate}% ({'减小' if compression_rate > 0 else '增大'})")
    print(f"[推荐CRF值] {crf}（值越大压缩越狠，20-35为合理范围）")
    print(f"[压缩建议] {suggestion}")
    print(f"[预判依据] {reason}")
    print("="*80)


def get_custom_crf_with_current_value(recommended_crf):
    """让用户自定义CRF值，同时显示当前推荐值"""
    print(f"\n[参考] 推荐的CRF值为: {recommended_crf}")
    while True:
        try:
            crf_input = input("\n请输入自定义CRF值（20-35，回车使用推荐值）：").strip()
            if not crf_input:
                return None
            crf = int(crf_input)
            if 20 <= crf <= 35:
                return crf
            else:
                print("[提示] CRF值需在20-35之间")
        except ValueError:
            print("[提示] 请输入有效的数字")


def compress_video_with_progress(input_path, output_path, crf=27, progress_callback=None):
    """压缩视频（自适应CRF参数）"""
    video_info = get_video_info(input_path)
    if not video_info:
        print("[错误] 视频信息获取失败，处理终止")
        return False, 0

    width = video_info['width']
    total_duration = video_info['duration_sec'] if video_info['duration_sec'] > 0 else get_video_duration(input_path)
    start_time = time.time()

    # 自适应码率限制（基于分辨率）
    pixel_count = video_info['pixel_count']
    if pixel_count <= 960*540:
        maxrate = '800k'
        bufsize = '1600k'
    elif pixel_count <= 1280*720:
        maxrate = '1200k'
        bufsize = '2400k'
    elif pixel_count <= 1920*1080:
        maxrate = '1800k'
        bufsize = '3600k'
    else:
        maxrate = '3000k'
        bufsize = '6000k'

    # 构建ffmpeg命令
    # 获取CPU核心数，用于设置线程数
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    thread_count = min(cpu_count, 8)  # 最多使用8个线程，避免过度占用资源

    cmd = [
        'ffmpeg', '-i', input_path,
        '-c:v', 'libx264', '-crf', str(crf), '-maxrate', maxrate, '-bufsize', bufsize,
        '-threads', str(thread_count),  # 使用多线程编码，提高性能
        '-vf', f"scale='min(1920,{width})':-2,fps=25",
        '-c:a', 'aac', '-b:a', '96k',  # 降低音频码率，进一步减小体积
        '-f', 'mp4', '-y',
        '-progress', 'pipe:1',
        output_path
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            bufsize=1,
            encoding='utf-8',
            errors='ignore'
        )

        current_time = 0.0
        last_progress = -1
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            if '=' in line:
                key, value = line.strip().split('=', 1)
                if key == 'out_time_ms':
                    if value.strip() and value != 'N/A':
                        try:
                            current_time = float(value) / 1000000
                        except:
                            current_time = 0.0
                elif key == 'duration' and total_duration <= 0:
                    if value.strip() and value != 'N/A':
                        try:
                            total_duration = float(value)
                        except:
                            total_duration = 0.0

                if total_duration > 0 and progress_callback and current_time > 0:
                    progress = min(100, int((current_time / total_duration) * 100))
                    if progress != last_progress:
                        progress_callback(progress)
                        last_progress = progress

        return_code = process.wait()
        compress_time = round(time.time() - start_time, 2)

        if return_code == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            if progress_callback and last_progress != 100:
                progress_callback(100)

            # 压缩成功后，将原文件移动到original文件夹
            try:
                import shutil
                video_dir = os.path.dirname(input_path)
                original_dir = os.path.join(video_dir, 'original')

                # 创建original文件夹
                if not os.path.exists(original_dir):
                    os.makedirs(original_dir)

                # 获取原文件名
                original_name = os.path.basename(input_path)
                original_target = os.path.join(original_dir, original_name)

                # 如果目标文件已存在，添加时间戳
                if os.path.exists(original_target):
                    name, ext = os.path.splitext(original_name)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    original_target = os.path.join(original_dir, f"{name}_{timestamp}{ext}")

                # 移动原文件
                shutil.move(input_path, original_target)
                print(f"[信息] 原文件已移动到: {original_target}")
            except Exception as e:
                print(f"[警告] 移动原文件失败: {e}")

            return True, compress_time
        else:
            print("[错误] 视频处理失败，未生成有效文件")
            return False, compress_time

    except Exception as e:
        compress_time = round(time.time() - start_time, 2)
        print(f"[错误] 压缩过程中出现错误: {e}")
        return False, compress_time


def get_video_duration(video_path):
    """获取视频时长（秒）"""
    cmd = [
        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', video_path
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        try:
            output_str = result.stdout.decode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                import locale
                encoding = locale.getpreferredencoding()
                output_str = result.stdout.decode(encoding, errors='replace').strip()
            except UnicodeDecodeError:
                output_str = result.stdout.decode('latin-1', errors='replace').strip()

        if output_str == 'N/A' or not output_str:
            return 0.0
        return float(output_str)
    except subprocess.CalledProcessError:
        print("[警告] 获取视频时长失败")
        return 0.0
    except ValueError:
        print("[警告] 视频时长格式错误")
        return 0.0
    except Exception as e:
        print(f"[警告] 获取视频时长时出现错误: {e}")
        return 0.0


def show_progress(progress):
    """显示进度条（PowerShell兼容）"""
    bar_length = 50
    filled_length = int(bar_length * progress // 100)
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f'\r[进度] 压缩进度: |{bar}| {progress}% ')
    sys.stdout.flush()

    if progress >= 100:
        sys.stdout.write('\n[完成] 压缩完成！\n')


def print_compress_comparison(original_path, compressed_path, compress_time):
    """打印压缩前后信息比对"""
    original_info = get_video_info(original_path)
    compressed_info = get_video_info(compressed_path)

    if not original_info or not compressed_info:
        print("\n[警告] 无法生成压缩比对信息")
        return

    size_reduction = original_info['size_mb'] - compressed_info['size_mb']
    compression_rate = round((size_reduction / original_info['size_mb']) * 100, 2) if original_info['size_mb'] > 0 else 0.0

    print("\n" + "="*80)
    print("[对比] 压缩前后信息比对")
    print("="*80)
    print(f"{'项目':<12} {'原始文件':<25} {'压缩后文件':<25}")
    print("-"*80)
    print(f"{'文件大小':<12} {f'{original_info["size_mb"]:.2f} MB':<25} {f'{compressed_info["size_mb"]:.2f} MB':<25}")
    print(f"{'分辨率':<12} {f'{original_info["width"]}x{original_info["height"]}':<25} {f'{compressed_info["width"]}x{compressed_info["height"]}':<25}")
    print(f"{'帧率':<12} {f'{original_info["fps"]:.1f} fps':<25} {f'{compressed_info["fps"]:.1f} fps':<25}")
    print(f"{'编码格式':<12} {original_info['video_codec']:<25} {compressed_info['video_codec']:<25}")
    print(f"{'码率':<12} {f'{original_info["bit_rate_kbps"]:.1f} kbps':<25} {f'{compressed_info["bit_rate_kbps"]:.1f} kbps':<25}")
    print("-"*80)
    print(f"[实际压缩结果] 减少大小: {size_reduction:>6.2f} MB | 压缩率: {compression_rate:>6.2f}% | 用时: {compress_time:>6.2f} 秒")
    print("="*80)


def compress_video_gui(input_path, output_path, crf=27):
    """
    为GUI界面优化的视频压缩函数，不使用进度回调
    """
    # 记录日志
    logger('info', f"开始压缩视频: {input_path} -> {output_path}, CRF={crf}")

    video_info = get_video_info(input_path)
    if not video_info:
        logger('error', f"视频信息获取失败: {input_path}")
        return False, 0

    width = video_info['width']
    start_time = time.time()

    # 自适应码率限制（基于分辨率）
    pixel_count = video_info['pixel_count']
    if pixel_count <= 960*540:
        maxrate = '800k'
        bufsize = '1600k'
    elif pixel_count <= 1280*720:
        maxrate = '1200k'
        bufsize = '2400k'
    elif pixel_count <= 1920*1080:
        maxrate = '1800k'
        bufsize = '3600k'
    else:
        maxrate = '3000k'
        bufsize = '6000k'

    # 构建ffmpeg命令
    # 获取CPU核心数，用于设置线程数
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    thread_count = min(cpu_count, 8)  # 最多使用8个线程，避免过度占用资源

    cmd = [
        'ffmpeg', '-i', input_path,
        '-c:v', 'libx264', '-crf', str(crf), '-maxrate', maxrate, '-bufsize', bufsize,
        '-threads', str(thread_count),  # 使用多线程编码，提高性能
        '-vf', f"scale='min(1920,{width})':-2,fps=25",
        '-c:a', 'aac', '-b:a', '96k',  # 降低音频码率，进一步减小体积
        '-f', 'mp4', '-y',
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        compress_time = round(time.time() - start_time, 2)

        # 检查输出文件是否有效
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger('info', f"压缩成功: {output_path}, 用时: {compress_time}秒")

            return True, compress_time
        else:
            logger('error', f"压缩失败，输出文件无效: {output_path}")
            return False, compress_time

    except subprocess.CalledProcessError as e:
        compress_time = round(time.time() - start_time, 2)
        logger('error', f"压缩过程中出现错误: {e}")
        return False, compress_time
    except Exception as e:
        compress_time = round(time.time() - start_time, 2)
        logger('error', f"压缩过程中出现异常: {e}")
        return False, compress_time


class VideoCompressGUI:
    def __init__(self, root):
        # 尝试导入tkinterdnd2
        try:
            from tkinterdnd2 import TkinterDnD, DND_FILES
            # 如果传入的root不是DnD实例，创建新的DnD窗口
            if not isinstance(root, TkinterDnD.Tk):
                self.root = TkinterDnD.Tk()
                self.root.title("视频压缩工具 v5.0")
                self.root.geometry("1000x800")
                self.root.minsize(800, 600)
            else:
                self.root = root
        except ImportError:
            # 如果没有tkinterdnd2，使用普通tk窗口
            self.root = root

        # 设置窗口属性（如果尚未设置）
        if not hasattr(root, 'tk') or not isinstance(root, tk.Tk) or root != self.root:
            self.root.title("视频压缩工具 v5.0")
            self.root.geometry("1000x800")
            self.root.minsize(800, 600)

        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加标题（包含拖拽提示）
        self.title_label = ttk.Label(main_frame, text="视频压缩工具 - 请将视频文件拖拽到窗口，或点击按钮选择文件", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=(0, 10))

        # 尝试导入tkinterdnd2
        try:
            from tkinterdnd2 import TkinterDnD, DND_FILES
            # 绑定拖放事件到主窗口
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)

            # 创建拖拽区域
            self.drop_frame = tk.Frame(main_frame, bg="lightgray", height=100)
            self.drop_frame.pack(fill=tk.X, pady=(0, 20))
            self.drop_frame.pack_propagate(False)  # 保持固定高度

        except ImportError:
            # 如果没有tkinterdnd2，使用按钮选择文件
            hint_label = ttk.Label(main_frame, text="请将视频文件拖拽到窗口，或点击下方按钮选择文件", font=("Arial", 12))
            hint_label.pack(pady=(0, 10))
            self.select_button = ttk.Button(main_frame, text="选择视频文件", command=self.select_files)
            self.select_button.pack(pady=(0, 20))

        # 添加当前任务显示
        self.current_task_label = ttk.Label(main_frame, text="当前任务: 无", font=("Arial", 10))
        self.current_task_label.pack(pady=(5, 5))

        # 添加进度条框架
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 进度文本
        self.progress_text = ttk.Label(progress_frame, text="准备就绪", font=("Arial", 10))
        self.progress_text.pack(side=tk.RIGHT)

        # 添加按钮容器（包含执行全部压缩和删除全部任务）
        action_buttons_frame = tk.Frame(main_frame)
        action_buttons_frame.pack(fill=tk.X, pady=10)

        # 添加执行全部压缩按钮（全屏宽，绿色背景）
        self.compress_all_button = tk.Button(
            action_buttons_frame,
            text="▶ 执行全部压缩",
            command=self.compress_all,
            bg="#4CAF50",  # 绿色
            fg="white",     # 白色文字
            font=("Arial", 12, "bold"),
            relief=tk.RAISED,
            bd=2
        )
        self.compress_all_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=10)

        # 添加删除全部任务按钮（红色背景）
        self.clear_all_button = tk.Button(
            action_buttons_frame,
            text="🗑 删除全部任务",
            command=self.clear_all_tasks,
            bg="#F44336",  # 红色
            fg="white",     # 白色文字
            font=("Arial", 12, "bold"),
            relief=tk.RAISED,
            bd=2
        )
        self.clear_all_button.pack(side=tk.RIGHT, padx=(5, 0))

        # 添加任务状态文本框
        status_frame = ttk.LabelFrame(main_frame, text="任务状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.status_text = tk.Text(status_frame, height=8, state=tk.NORMAL)
        status_scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)

        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建视频按钮容器
        self.buttons_frame = ttk.Frame(main_frame)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 滚动区域
        self.canvas = tk.Canvas(self.buttons_frame)
        scrollbar = ttk.Scrollbar(self.buttons_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 存储视频按钮的字典
        self.video_buttons = {}
        self.button_frames = {}  # 存储按钮框架，用于删除按钮
        self.pending_tasks = []  # 存储待处理任务
        self.total_tasks = 0     # 总任务数
        self.completed_tasks = 0 # 已完成任务数
        self.active_tasks = 0    # 活跃任务数
        self.is_processing_queue = False  # 是否正在处理队列
        self.current_task_name = ""       # 当前任务名称

        # GUI更新节流相关变量
        self.last_gui_update_time = 0  # 上次GUI更新时间
        self.gui_update_interval = 0.5  # GUI更新间隔（秒）
        self.last_progress_update = -1  # 上次进度值

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_drop(self, event):
        """处理拖拽事件"""
        files = self.root.tk.splitlist(event.data)
        video_files = []
        missing_original_files = []  # 记录缺失原文件的压缩文件
        skipped_files = []  # 记录已存在压缩文件的原文件

        for file_path in files:
            # 检查是否为视频文件
            if self.is_video_file(file_path):
                # 检查是否为已压缩文件
                if self.is_already_compressed_file(file_path):
                    # 检查原文件是否存在
                    original_path, error_msg = get_original_file_path(file_path)
                    if original_path is None:
                        # 原文件缺失，记录下来
                        missing_original_files.append((file_path, error_msg))
                    # 原文件存在，直接忽略压缩文件
                    status_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 忽略操作: 拖入的文件已压缩，原文件也存在: {file_path}\n"
                    self.status_text.insert("1.0", status_msg)
                    continue
                # 检查原文件是否有对应的压缩文件
                compressed_path, _ = check_compressed_file_exists(file_path)
                if compressed_path:
                    # 已存在压缩文件，记录下来并跳过
                    skipped_files.append((file_path, compressed_path))
                    status_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 跳过: 已存在压缩文件 {os.path.basename(compressed_path)}"
                    self.status_text.insert("1.0", status_msg)
                    continue

                video_files.append(file_path)

        # 处理非压缩文件
        if video_files:
            self.process_video_files(video_files)

        # 如果有缺失原文件的压缩文件，显示警告
        if missing_original_files:
            warning_msg = "以下压缩文件的原文件已丢失：\n\n"
            for compressed_path, error_msg in missing_original_files:
                warning_msg += f"• {os.path.basename(compressed_path)}\n  {error_msg}\n\n"
            self.root.after(0, lambda: messagebox.showwarning("警告", warning_msg))


    def is_already_compressed_file(self, file_path):
        """检查文件名是否包含已压缩标识"""
        return is_compressed_file(os.path.basename(file_path))

    def select_files(self):
        """通过按钮选择文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v *.3gp"),
                ("所有文件", "*.*")
            ]
        )
        if file_paths:
            video_files = []
            for f in file_paths:
                if self.is_video_file(f) and not self.is_already_compressed_file(f):
                    video_files.append(f)
            if video_files:
                self.process_video_files(video_files)
            else:
                self.root.after(0, lambda: messagebox.showwarning("警告", "没有选择有效的非压缩视频文件"))
    def start_compress(self, video_path, crf, is_from_queue=False):
        """开始压缩视频"""
        # 获取视频所在目录
        video_dir = os.path.dirname(video_path)
        # 创建compressed子目录
        compressed_dir = os.path.join(video_dir, "compressed")
        if not os.path.exists(compressed_dir):
            os.makedirs(compressed_dir)
        # 生成输出文件路径
        video_name = os.path.basename(video_path)
        name, ext = os.path.splitext(video_name)
        output_path = os.path.join(compressed_dir, f"{name}_compressed{ext}")

        # 检查输出文件是否已存在
        if os.path.exists(output_path):
            response = messagebox.askyesno(
                "文件已存在",
                f"压缩文件已存在：{output_path}\n是否覆盖？"
            )
            if not response:
                if not is_from_queue:
                    self.active_tasks -= 1
                    self.completed_tasks += 1
                    self.update_progress()
                return

        # 更新任务状态
        if not is_from_queue:
            self.active_tasks += 1
            self.total_tasks += 1
            self.update_progress()

        # 在新线程中执行压缩
        def compress_thread():
            try:
                self.current_task_name = video_name
                logger("INFO", f"开始压缩: {video_path}")
                logger("INFO", f"输出路径: {output_path}")
                logger("INFO", f"CRF值: {crf}")

                start_time = time.time()
                compress_video_gui(video_path, output_path, crf)
                compress_time = time.time() - start_time

                # 记录压缩结果
                video_states[video_path] = {
                    'compressed': True,
                    'output_path': output_path,
                    'compress_time': compress_time
                }

                logger("INFO", f"压缩完成: {output_path}")
                print_compress_comparison(video_path, output_path, compress_time)

                # 更新GUI
                self.root.after(0, lambda: self.update_title())
                self.root.after(0, lambda: self.update_button_state(video_path, True))

            except Exception as e:
                logger("ERROR", f"压缩失败: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"压缩失败: {str(e)}"))
                self.root.after(0, lambda: self.update_button_state(video_path, False))
            finally:
                if not is_from_queue:
                    self.active_tasks -= 1
                    self.completed_tasks += 1
                    self.update_progress()
                else:
                    # 如果是队列任务，继续处理下一个
                    self.root.after(0, self.process_next_in_queue)

        # 启动压缩线程
        threading.Thread(target=compress_thread, daemon=True).start()

    def is_video_file(self, file_path):
        """判断是否为视频文件"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        return Path(file_path).suffix.lower() in video_extensions

    def process_video_files(self, video_files):
        """处理视频文件列表"""
        for video_path in video_files:
            if video_path not in self.video_buttons:
                self.add_video_button(video_path)

    def add_video_button(self, video_path):
        """为视频添加按钮和删除按钮"""
        video_info = get_video_info(video_path)
        if not video_info:
            return

        # 检查是否存在已压缩的同名文件
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        dir_path = os.path.dirname(video_path)
        compressed_dir = os.path.join(dir_path, "compressed")  # 压缩文件保存在compressed子目录中
        dir_files = get_dir_files(dir_path)  # 使用缓存的目录扫描结果

        # 检查compressed子目录中是否存在已压缩文件
        compressed_files = []
        if os.path.exists(compressed_dir):
            compressed_dir_files = get_dir_files(compressed_dir)
            compressed_files = [f for f in compressed_dir_files if
                               f.startswith(base_name + "_compressed_") and f.endswith(".mp4")]

        # 获取压缩预判
        compression_rate, suggestion, recommended_crf, _ = predict_compression_effect(video_info)

        # 检查视频是否已完成压缩
        is_completed = video_path in video_states and video_states[video_path] == 'completed'

        # 创建按钮文本
        button_text = (
            f"📹 {video_info['file_name']}\n"
            f"📊 大小: {video_info['size_mb']}MB | 分辨率: {video_info['width']}x{video_info['height']} | "
            f"码率: {video_info['bit_rate_kbps']}kbps\n"
            f"⚡ 预判压缩率: {compression_rate}% | 推荐CRF: {recommended_crf} | {suggestion}"
        )

        # 如果存在已压缩文件或已在状态中记录，则添加完成标识
        if is_completed or compressed_files:
            button_text += "\n✅ [可能已完成压缩]"
            bg_color = "#C8E6C9"  # 浅绿色
            fg_color = "black"
        else:
            bg_color = "#BBDEFB"  # 浅蓝色
            fg_color = "black"

        # 创建一个框架来包含按钮和删除按钮
        button_frame = tk.Frame(self.scrollable_frame, bg="#f5f5f5", relief=tk.RAISED, bd=1)
        button_frame.pack(fill=tk.X, pady=5, padx=5)

        # 创建压缩按钮
        compress_button = tk.Button(
            button_frame,
            text=f"▶ {button_text}",
            command=lambda path=video_path, info=video_info, crf=recommended_crf: self.compress_video(path, info, crf),
            wraplength=800,
            justify=tk.LEFT,
            height=4,
            bg=bg_color,
            fg=fg_color,
            font=("Arial", 10),
            relief=tk.FLAT,
            bd=0,
            cursor="hand2"
        )
        compress_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # 创建删除按钮
        delete_button = tk.Button(
            button_frame,
            text="🗑 删除",
            command=lambda: self.remove_video_button(video_path),
            bg="#EF5350",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            bd=2,
            cursor="hand2",
            width=8
        )
        delete_button.pack(side=tk.RIGHT, padx=(5, 0))

        # 存储按钮引用
        self.video_buttons[video_path] = compress_button
        self.button_frames[video_path] = button_frame

        # 更新标题
        self.update_title()

    def remove_video_button(self, video_path):
        """删除视频按钮"""
        if video_path in self.video_buttons:
            # 销毁按钮框架
            self.button_frames[video_path].destroy()
            # 从字典中移除引用
            del self.video_buttons[video_path]
            del self.button_frames[video_path]
            # 如果视频在状态中，也从状态中删除
            if video_path in video_states:
                del video_states[video_path]

            # 更新标题
            self.update_title()

    def clear_all_tasks(self):
        """删除全部任务按钮"""
        if not self.video_buttons:
            messagebox.showinfo("提示", "没有任务可删除")
            return

        # 确认删除
        response = messagebox.askyesno("确认删除", f"确定要删除全部 {len(self.video_buttons)} 个任务吗？")
        if not response:
            return

        # 清空所有按钮和状态
        for video_path in list(self.video_buttons.keys()):
            self.remove_video_button(video_path)

        # 清空待处理任务
        self.pending_tasks = []
        self.total_tasks = 0
        self.completed_tasks = 0
        self.active_tasks = 0

        # 重置进度条
        self.progress_var.set(0)
        self.progress_text.config(text="准备就绪")
        self.current_task_label.config(text="当前任务: 无")

        # 更新标题
        self.update_title()

    def update_title(self):
        """更新标题显示任务统计"""
        total_count = len(self.video_buttons)
        completed_count = sum(1 for path in self.video_buttons.keys()
                             if path in video_states and video_states[path] == 'completed')
        # 检查是否有已压缩的同名文件（使用与add_video_button一致的逻辑）
        for path in self.video_buttons.keys():
            base_name = os.path.splitext(os.path.basename(path))[0]
            dir_path = os.path.dirname(path)
            compressed_dir = os.path.join(dir_path, "compressed")
            compressed_files = []
            if os.path.exists(compressed_dir):
                compressed_dir_files = get_dir_files(compressed_dir)
                compressed_files = [f for f in compressed_dir_files if
                                   f.startswith(base_name + "_compressed_") and f.endswith(".mp4")]
            if compressed_files and path not in video_states:
                completed_count += 1
        pending_count = total_count - completed_count

        self.title_label.config(text=f"视频压缩工具 (总计: {total_count}, 未压缩: {pending_count})")

# 压缩成功后，将原文件移动到original文件夹
    def move_original_to_folder(original_path, video_dir):
        """将原文件移动到original文件夹"""
        try:
            # 创建original文件夹
            original_dir = os.path.join(video_dir, 'original')
            if not os.path.exists(original_dir):
                os.makedirs(original_dir)

            # 获取原文件名
            original_name = os.path.basename(original_path)
            original_target = os.path.join(original_dir, original_name)

            # 如果目标文件已存在，添加时间戳
            if os.path.exists(original_target):
                name, ext = os.path.splitext(original_name)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                original_target = os.path.join(original_dir, f"{name}_{timestamp}{ext}")

            # 移动原文件
            shutil.move(original_path, original_target)
            logger('info', f"原文件已移动到: {original_target}")
            return True
        except Exception as e:
            logger('error', f"移动原文件失败: {e}")
            return False


    def compress_all(self):
        """执行全部压缩 - 排队逐个处理，跳过已有压缩文件的任务"""
        self.pending_tasks = []
        for video_path in self.video_buttons.keys():
            # 检查是否已完成压缩
            is_completed = video_path in video_states and video_states[video_path] == 'completed'
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            dir_path = os.path.dirname(video_path)

            # 检查当前目录中是否存在已压缩文件
            compressed_files = []
            for f in os.listdir(dir_path):
                if f.startswith(base_name + "_compressed_") and f.endswith(".mp4"):
                    compressed_files.append(f)

            # 如果没有完成压缩且没有已压缩文件，则添加到待处理队列
            if not is_completed and not compressed_files:
                video_info = get_video_info(video_path)
                if video_info:
                    compression_rate, suggestion, recommended_crf, _ = predict_compression_effect(video_info)
                    self.pending_tasks.append((video_path, recommended_crf))

        if not self.pending_tasks:
            messagebox.showinfo("提示", "没有需要压缩的视频文件（已跳过已有压缩文件的任务）")
            return

        # 更新任务统计
        self.total_tasks = len(self.pending_tasks)
        self.completed_tasks = 0

        # 更新进度条信息
        self.progress_var.set(0)
        self.progress_text.config(text=f"当前: 0%, 总计: 0/{self.total_tasks}")

        # 开始处理队列
        self.is_processing_queue = True
        self.process_next_in_queue()


    def process_next_in_queue(self):
        """处理队列中的下一个任务"""
        if not self.pending_tasks or not self.is_processing_queue:
            # 队列已完成
            if self.completed_tasks == self.total_tasks and self.total_tasks > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    "全部完成",
                    f"所有压缩任务已完成！"
                ))
            return

        # 获取下一个任务
        video_path, crf = self.pending_tasks.pop(0)

        # 启动压缩任务
        thread = threading.Thread(target=self.start_compress, args=(video_path, crf, True))
        thread.daemon = True
        thread.start()

    def compress_video(self, video_path, video_info, recommended_crf):
        """压缩视频 - 在新线程中执行以避免界面冻结"""
        # 直接弹出输入框，使用推荐CRF值作为默认值
        crf = askinteger("CRF值", "请输入CRF值 (20-35):",
                         initialvalue=recommended_crf, minvalue=20, maxvalue=35)
        if crf is None:
            return  # 用户取消操作

        # 启动压缩任务
        thread = threading.Thread(target=self.start_compress, args=(video_path, crf, False))
        thread.daemon = True
        thread.start()

    def start_compress(self, video_path, crf, is_from_queue=False):
        """开始压缩视频"""
        try:
            # 清空日志缓存，确保每个压缩任务的日志独立
            global current_log_entries
            current_log_entries = []

            # 增加活动任务计数
            self.active_tasks += 1

            # 设置当前任务名称
            self.current_task_name = os.path.basename(video_path)
            self.root.after(0, lambda: self.current_task_label.config(text=f"当前任务: {self.current_task_name}"))

            # 添加状态信息到文本框
            status_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 开始压缩: {self.current_task_name}\n"
            self.root.after(0, lambda: self.status_text.insert("1.0", status_msg))

            # 生成输出文件名（保存在原路径）
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_name = f"{base_name}_compressed_{timestamp}.mp4"
            output_path = os.path.join(os.path.dirname(video_path), output_name)

            # 记录开始压缩日志
            logger('info', "="*60)
            logger('info', f"开始压缩视频: {os.path.basename(video_path)}")
            logger('info', f"输出文件: {os.path.basename(output_path)}")
            logger('info', f"CRF值: {crf}")

            # 获取压缩前的视频信息
            original_info = get_video_info(video_path)
            if original_info:
                logger('info', f"原始信息 - 大小: {original_info['size_mb']}MB, "
                           f"分辨率: {original_info['width']}x{original_info['height']}, "
                           f"码率: {original_info['bit_rate_kbps']}kbps")

            # 执行压缩
            def update_progress(progress):
                # 节流机制：限制GUI更新频率
                current_time = time.time()
                if (current_time - self.last_gui_update_time < self.gui_update_interval and
                    progress != 100 and progress - self.last_progress_update < 5):
                    return  # 跳过此次更新

                self.last_gui_update_time = current_time
                self.last_progress_update = progress

                self.root.after(0, lambda: self.progress_var.set(progress))
                if is_from_queue:
                    # 对于队列任务，显示当前任务进度和总体统计
                    overall_progress = int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0
                    self.progress_text.config(text=f"当前: {progress}%, 总计: {self.completed_tasks}/{self.total_tasks} ({overall_progress}%)")
                else:
                    # 对于单独任务，只显示当前进度
                    self.progress_text.config(text=f"当前: {progress}%")

            success, compress_time = compress_video_with_progress(
                video_path,
                output_path,
                crf=crf,
                progress_callback=update_progress
            )

            # 更新完成任务计数
            self.completed_tasks += 1
            # 减少活动任务计数
            self.active_tasks -= 1

            # 如果是队列中的任务，处理下一个
            if is_from_queue:
                # 更新进度条到100%表示当前任务完成
                self.root.after(0, lambda: self.progress_var.set(100))
                # 更新文本显示
                overall_progress = int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0
                self.progress_text.config(text=f"当前: 100%, 总计: {self.completed_tasks}/{self.total_tasks} ({overall_progress}%)")

                # 延迟处理下一个任务，让用户看到当前任务完成
                self.root.after(1000, self.process_next_in_queue)
            else:
                # 单独任务完成后，恢复到准备状态
                self.root.after(0, lambda: self.progress_var.set(0))
                self.progress_text.config(text="准备就绪")

            if success:
                # 获取压缩后的视频信息
                compressed_info = get_video_info(output_path)

                # 添加完成状态信息到文本框
                completion_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 完成压缩: {self.current_task_name} (用时: {compress_time}s)\n"
                self.root.after(0, lambda: self.status_text.insert("1.0", completion_msg))

                # 添加比对信息
                if original_info and compressed_info:
                    size_reduction = original_info['size_mb'] - compressed_info['size_mb']
                    compression_rate = round((size_reduction / original_info['size_mb']) * 100, 2) if original_info['size_mb'] > 0 else 0.0
                    comparison_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 比对结果: {original_info['size_mb']:.2f}MB → {compressed_info['size_mb']:.2f}MB, 压缩率: {compression_rate}%\n"
                    self.root.after(0, lambda: self.status_text.insert("1.0", comparison_msg))

                # 记录成功日志
                if original_info and compressed_info:
                    size_reduction = original_info['size_mb'] - compressed_info['size_mb']
                    compression_rate = round((size_reduction / original_info['size_mb']) * 100, 2) if original_info['size_mb'] > 0 else 0.0

                    logger('info', f"压缩完成: {os.path.basename(output_path)}")
                    logger('info', f"压缩结果 - 原始: {original_info['size_mb']}MB -> 压缩后: {compressed_info['size_mb']}MB")
                    logger('info', f"压缩率: {compression_rate}%, 用时: {compress_time}秒")
                    logger('info', f"压缩后信息 - 大小: {compressed_info['size_mb']}MB, "
                               f"分辨率: {compressed_info['width']}x{compressed_info['height']}, "
                               f"码率: {compressed_info['bit_rate_kbps']}kbps")
                    logger('info', "="*60)

                    # 将所有日志条目作为整体写入文件
                    flush_log()

                # 更新按钮颜色为绿色（表示完成）
                button = self.video_buttons.get(video_path)
                if button:
                    current_text = button.cget("text")
                    if "[已完成]" not in current_text:
                        button.config(bg="lightgreen", text=current_text + "\n[已完成]")

                # 记录到全局状态
                video_states[video_path] = 'completed'

                # 更新标题
                self.root.after(0, self.update_title)

            else:
                # 添加失败状态信息到文本框
                failure_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 压缩失败: {self.current_task_name}\n"
                self.root.after(0, lambda: self.status_text.insert("1.0", failure_msg))

                # 记录失败日志
                logger('error', f"压缩失败: {os.path.basename(video_path)}")
                logger('info', "="*60)

                # 将所有日志条目作为整体写入文件
                flush_log()

                # 更新标题
                self.root.after(0, self.update_title)

                # 如果是队列处理，也要继续下一个
                if is_from_queue:
                    self.root.after(1000, self.process_next_in_queue)

            # 清除当前任务名称
            self.current_task_name = ""
            self.root.after(0, lambda: self.current_task_label.config(text="当前任务: 无"))

        except Exception as e:
            # 添加异常状态信息到文本框
            error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] 异常: {str(e)}\n"
            self.root.after(0, lambda: self.status_text.insert("1.0", error_msg))

            logger('error', f"压缩过程中出现异常: {e}")

            # 将所有日志条目作为整体写入文件
            flush_log()

            # 减少活动任务计数
            self.active_tasks -= 1
            # 更新标题
            self.root.after(0, self.update_title)

            # 清除当前任务名称
            self.current_task_name = ""
            self.root.after(0, lambda: self.current_task_label.config(text="当前任务: 无"))

            # 如果是队列处理，也要继续下一个
            if is_from_queue:
                # 更新进度，即使失败也标记为完成
                self.root.after(1000, self.process_next_in_queue)

            # 在主线程中显示错误消息
            self.root.after(0, lambda: messagebox.showerror("错误", f"压缩过程中出现异常: {e}"))

def main():
    """主函数：启动GUI界面"""
    print("="*80)
    print("🎬 视频压缩工具 v5.0 (GUI界面 | 拖拽支持 | 日志记录 | 进度条显示)")
    print("="*80)

    # 启动GUI界面
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        root = tk.Tk()

    # 设置窗口属性
    root.title("视频压缩工具 v5.0")
    root.geometry("1000x800")  # 设置初始窗口大小
    root.minsize(800, 600)    # 设置最小窗口大小

    app = VideoCompressGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()