"""
视频压缩工具
扫描当前目录下的所有视频文件，允许用户选择对哪个视频进行压缩
压缩时显示进度条，支持循环操作，优化信息展示，增加压缩比对和用时统计
"""

import os
import subprocess
import json
import sys
import time
from datetime import datetime
from pathlib import Path


def get_video_info(video_path):
    """获取视频原始基础信息（大小、分辨率、帧率、格式）"""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]
    try:
        # 使用二进制模式运行命令，以处理各种编码问题
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        # 尝试解码输出
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

        # 提取核心信息（仅基于原始文件）
        file_size = int(info['format']['size']) / 1024 / 1024  # 转换为MB
        # 寻找视频流（可能在索引位置不是0）
        video_stream = None
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        # 如果没有找到视频流，使用默认值
        if video_stream:
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            # 计算帧率
            r_frame_rate = video_stream.get('r_frame_rate', '30/1')
            if r_frame_rate and r_frame_rate != '0/0':
                try:
                    numerator, denominator = r_frame_rate.split('/')
                    fps = float(numerator) / float(denominator) if denominator != '0' else 30.0
                except:
                    fps = 30.0
            else:
                fps = 30.0
            codec_name = video_stream.get('codec_name', '').lower()
        else:
            # 没有视频流时使用默认值
            width = 0
            height = 0
            fps = 0.0
            codec_name = 'unknown'

        # 获取容器格式
        format_name = info['format']['format_name'].split(',')[0].lower()

        return {
            'size_mb': round(file_size, 2),
            'width': width,
            'height': height,
            'fps': round(fps, 1),
            'container_format': format_name,  # 容器格式
            'video_codec': codec_name         # 视频编码格式
        }
    except json.JSONDecodeError:
        print(f"❌ 无法解析视频信息JSON：文件路径 {video_path}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ ffprobe命令执行失败：{e}")
        return None
    except Exception as e:
        print(f"❌ 获取视频信息失败：{e}")
        return None


def compress_video_with_progress(input_path, output_path, progress_callback=None):
    """
    压缩视频并显示进度
    :param input_path: 原始视频路径
    :param output_path: 最终MP4输出路径
    :param progress_callback: 进度回调函数
    :return: (是否成功, 压缩用时(秒))
    """
    # 1. 获取原始视频信息
    video_info = get_video_info(input_path)
    if not video_info:
        print("❌ 视频信息获取失败，处理终止")
        return False, 0

    width = video_info['width']

    # 使用ffmpeg来获取视频总时长
    total_duration = get_video_duration(input_path)

    # 记录压缩开始时间
    start_time = time.time()

    # 构建ffmpeg命令
    cmd = [
        'ffmpeg', '-i', input_path,
        # 视频压缩核心参数（H.264+CRF27+码率限制）
        '-c:v', 'libx264', '-crf', '27', '-maxrate', '2000k', '-bufsize', '4000k',
        # 分辨率≤1080P，帧率25fps（机器视频足够）
        '-vf', f"scale='min(1920,{width})':-2,fps=25",
        # 音频编码（微信兼容）
        '-c:a', 'aac', '-b:a', '128k',
        # 强制输出MP4格式，覆盖文件
        '-f', 'mp4', '-y',
        # 关键：添加-progress参数，输出机器可读的进度信息
        '-progress', 'pipe:1',
        output_path
    ]

    # 执行ffmpeg命令并监控进度
    try:
        # 使用二进制模式运行进程，以便处理各种编码
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # 屏蔽普通stderr输出
            universal_newlines=True,     # 直接以文本模式读取
            bufsize=1,
            encoding='utf-8',
            errors='ignore'
        )

        # 监控进度
        current_time = 0.0
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            # 解析progress输出（key=value格式）
            if '=' in line:
                key, value = line.strip().split('=', 1)
                # 获取当前处理时间（time=xxx.xxx）
                if key == 'out_time_ms':
                    # out_time_ms是微秒，转换为秒
                    current_time = float(value) / 1000000
                # 获取总时长（duration=xxx.xxx）
                elif key == 'duration' and total_duration <= 0:
                    total_duration = float(value) if value != 'N/A' else 0

                # 计算并更新进度
                if total_duration > 0 and progress_callback and current_time > 0:
                    progress = min(100, int((current_time / total_duration) * 100))
                    progress_callback(progress)

        # 等待进程结束并获取返回码
        return_code = process.wait()

        # 计算压缩用时
        compress_time = round(time.time() - start_time, 2)

        # 检查输出文件是否存在
        if return_code == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            # 最后更新进度到100%
            if progress_callback:
                progress_callback(100)
            return True, compress_time
        else:
            print("❌ 视频处理失败，未生成有效文件")
            return False, compress_time

    except Exception as e:
        compress_time = round(time.time() - start_time, 2)
        print(f"❌ 压缩过程中出现错误: {e}")
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

        # 尝试解码输出
        try:
            output_str = result.stdout.decode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                import locale
                encoding = locale.getpreferredencoding()
                output_str = result.stdout.decode(encoding, errors='replace').strip()
            except UnicodeDecodeError:
                output_str = result.stdout.decode('latin-1', errors='replace').strip()

        return float(output_str)
    except subprocess.CalledProcessError:
        print("⚠️ 获取视频时长失败")
        return 0
    except ValueError:
        print("⚠️ 视频时长格式错误")
        return 0
    except Exception as e:
        print(f"⚠️ 获取视频时长时出现错误: {e}")
        return 0


def time_str_to_seconds(time_str):
    """将时间字符串转换为秒数"""
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        else:
            return 0
    except:
        return 0


def get_video_files(directory='.'):
    """获取指定目录下的所有视频文件"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
    video_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if Path(file).suffix.lower() in video_extensions:
                full_path = os.path.join(root, file)
                video_files.append(full_path)

    return sorted(video_files)


def print_video_info_detail(video_path, title="视频信息"):
    """美化打印视频详细信息"""
    print(f"\n{'='*60}")
    print(f"📌 {title}")
    print('='*60)
    info = get_video_info(video_path)
    if info:
        print(f"📁 文件路径: {video_path}")
        print(f"🗂️  容器格式: {info['container_format']}")
        print(f"🔧 编码格式: {info['video_codec']}")
        print(f"📏 分辨率:    {info['width']}x{info['height']}")
        print(f"🎞️  帧率:      {info['fps']}fps")
        print(f"💾 文件大小:  {info['size_mb']} MB")
    else:
        print("❌ 无法获取视频信息")
    print('='*60)


def show_progress(progress):
    """美化显示进度条"""
    bar_length = 50
    filled_length = int(bar_length * progress // 100)
    bar = '🟢' * filled_length + '⚪' * (bar_length - filled_length)
    sys.stdout.write(f'\r⏳ 压缩进度: |{bar}| {progress}% ')
    sys.stdout.flush()

    # 当进度达到100%时，换行
    if progress >= 100:
        sys.stdout.write('\n✅ 压缩完成！\n')


def print_compress_comparison(original_path, compressed_path, compress_time):
    """打印压缩前后信息比对"""
    original_info = get_video_info(original_path)
    compressed_info = get_video_info(compressed_path)

    if not original_info or not compressed_info:
        print("\n⚠️  无法生成压缩比对信息")
        return

    # 计算压缩率
    size_reduction = original_info['size_mb'] - compressed_info['size_mb']
    compression_rate = round((size_reduction / original_info['size_mb']) * 100, 2)

    print(f"\n{'='*60}")
    print("📊 压缩前后信息比对")
    print('='*60)
    print(f"{'项目':<15} {'原始文件':<20} {'压缩后文件':<20}")
    print('-'*60)
    print(f"{'文件大小':<15} {original_info['size_mb']:>6.2f} MB {compressed_info['size_mb']:>12.2f} MB")
    print(f"{'分辨率':<15} {original_info['width']}x{original_info['height']:>11} {compressed_info['width']}x{compressed_info['height']:>11}")
    print(f"{'帧率':<15} {original_info['fps']:>14.1f} fps {compressed_info['fps']:>14.1f} fps")
    print(f"{'容器格式':<15} {original_info['container_format']:>14} {compressed_info['container_format']:>14}")
    print(f"{'编码格式':<15} {original_info['video_codec']:>14} {compressed_info['video_codec']:>14}")
    print('-'*60)
    print(f"🗜️  压缩大小:  {size_reduction:>10.2f} MB")
    print(f"📉 压缩率:    {compression_rate:>12.2f} %")
    print(f"⏱️  压缩用时:  {compress_time:>12.2f} 秒")
    print('='*60)


def main():
    """主函数"""
    print("=" * 60)
    print("🎬 视频压缩工具 v2.0")
    print("=" * 60)
    print("📌 功能说明：支持视频压缩、进度展示、信息比对、用时统计")
    print("=" * 60)

    while True:
        print("\n🔍 正在扫描当前目录下的视频文件...")
        video_files = get_video_files('.')

        if not video_files:
            print("\n❌ 未找到任何视频文件。")
        else:
            print(f"\n📋 找到 {len(video_files)} 个视频文件:\n")
            for i, video_file in enumerate(video_files, 1):
                # 简化显示文件名，过长时截断
                short_name = os.path.basename(video_file)
                if len(short_name) > 50:
                    short_name = short_name[:47] + "..."
                print(f"  {i:2d}. {short_name}")

        print(f"\n{'0'.rjust(3)}. 🚪 退出程序")
        if video_files:
            try:
                choice = input(f"\n请选择要压缩的视频文件 (1-{len(video_files)}) 或 0 退出: ").strip()
                if choice == '0':
                    print("\n👋 程序已退出。")
                    break

                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(video_files):
                    selected_video = video_files[choice_idx]
                    print(f"\n{'-'*60}")
                    print(f"✅ 您选择了: {os.path.basename(selected_video)}")
                    print(f"📂 文件路径: {selected_video}")
                    print("-"*60)
                    print("🔍 正在读取视频详细信息...")
                    # 打印原始视频信息
                    print_video_info_detail(selected_video, "原始视频信息")

                    # 生成输出文件名
                    base_name = os.path.splitext(os.path.basename(selected_video))[0]
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_name = f"{base_name}_compressed_{timestamp}.mp4"
                    output_path = os.path.join(os.path.dirname(selected_video), output_name)

                    print(f"\n📤 输出文件: {output_name}")
                    print(f"📌 输出路径: {os.path.dirname(output_path)}")

                    confirm = input("\n📝 确认开始压缩? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes', '']:
                        print("\n" + "="*60)
                        print("🚀 开始压缩视频...")
                        print("="*60)

                        # 执行压缩并显示进度
                        success, compress_time = compress_video_with_progress(
                            selected_video,
                            output_path,
                            progress_callback=show_progress
                        )

                        if success:
                            print(f"\n🎉 压缩成功! 输出文件: {output_path}")
                            # 打印压缩后信息和比对
                            print_video_info_detail(output_path, "压缩后视频信息")
                            print_compress_comparison(selected_video, output_path, compress_time)
                        else:
                            print("\n❌ 压缩失败!")
                    else:
                        print("\n🔄 取消压缩。")
                else:
                    print("\n⚠️  无效的选择，请重新输入。")
            except ValueError:
                print("\n⚠️  请输入有效的数字。")
            except KeyboardInterrupt:
                print("\n\n🔌 程序被用户中断。")
                break
        else:
            input("\n按回车键退出...")
            break

        # 询问是否继续
        if len(video_files) > 0:
            continue_choice = input("\n🔄 是否继续压缩其他视频? (y/N): ").strip().lower()
            if continue_choice not in ['y', 'yes', '']:
                print("\n👋 程序已退出。")
                break


if __name__ == "__main__":
    main()