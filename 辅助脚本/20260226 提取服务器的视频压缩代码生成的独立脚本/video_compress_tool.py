"""
视频压缩工具 v4.0
- 启动即展示所有视频完整信息
- 过滤已压缩文件
- 压缩前智能预判效果（预估压缩率+分级建议）
- 自适应压缩参数（避免负压缩）
- PowerShell兼容，表格精准对齐
"""

import os
import subprocess
import json
import sys
import time
import re
from datetime import datetime
from pathlib import Path


def get_video_info(video_path):
    """获取视频完整信息（含码率）"""
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

        return {
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
    预判压缩效果
    :param video_info: 视频信息字典
    :return: (预估压缩率%, 建议等级, 推荐CRF值, 建议说明)
    """
    if not video_info:
        return 0, "未知", 27, "无法获取视频信息"

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
    recommended_crf = 27
    suggestion = "推荐压缩"

    if codec == 'hevc' or codec == 'h265':
        # HEVC转H264，压缩率约40-60%
        estimated_compression = min(60, max(40, 100 - (target_bitrate / bit_rate * 100) if bit_rate > 0 else 50))
        recommended_crf = 27
        suggestion = "✅ 推荐压缩（HEVC转H264，压缩率高）"

    elif codec == 'h264':
        # H264二次压缩
        if bit_rate > target_bitrate * 1.5:
            # 原始码率远高于合理值，压缩率高
            estimated_compression = min(80, max(40, 100 - (target_bitrate / bit_rate * 100)))
            recommended_crf = 28
            suggestion = "✅ 推荐压缩（原始码率过高，压缩空间大）"
        elif bit_rate > target_bitrate:
            # 原始码率略高，有压缩空间
            estimated_compression = min(30, max(10, 100 - (target_bitrate / bit_rate * 100)))
            recommended_crf = 30
            suggestion = "⚠️ 谨慎压缩（压缩空间有限，约10-30%）"
        else:
            # 原始码率已很低，可能负压缩
            estimated_compression = -5  # 预估轻微变大
            recommended_crf = 32
            suggestion = "❌ 不建议压缩（原始码率已最优，可能越压越大）"

    else:
        # 其他编码（mpeg4、vp9等）
        estimated_compression = min(50, max(20, 100 - (target_bitrate / bit_rate * 100) if bit_rate > 0 else 30))
        recommended_crf = 29
        suggestion = "✅ 推荐压缩（老旧编码，压缩空间大）"

    # 修正预估压缩率（确保合理范围）
    estimated_compression = max(-10, min(90, estimated_compression))

    return round(estimated_compression, 1), suggestion, recommended_crf, f"""
预判依据：
- 原始编码：{codec} | 原始码率：{bit_rate} kbps
- 目标码率：{target_bitrate} kbps | 帧率：{fps}→25 fps
- 分辨率：{video_info['width']}x{video_info['height']}
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


def get_custom_crf():
    """让用户自定义CRF值"""
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
    cmd = [
        'ffmpeg', '-i', input_path,
        '-c:v', 'libx264', '-crf', str(crf), '-maxrate', maxrate, '-bufsize', bufsize,
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


def main():
    """主函数：带压缩预判"""
    print("="*80)
    print("🎬 视频压缩工具 v4.0 (智能预判 | 自适应参数 | 过滤压缩文件)")
    print("="*80)

    # 启动扫描
    print("\n[扫描] 正在扫描并读取视频文件完整信息...")
    video_files = get_video_files('.')
    print_all_video_info(video_files)

    if not video_files:
        input("\n按回车键退出...")
        return

    # 循环选择压缩
    while True:
        print(f"\n{'0'.rjust(4)}. [退出] 退出程序")
        try:
            choice = input(f"\n请选择要压缩的视频文件 (1-{len(video_files)}) 或 0 退出: ").strip()
            if choice == '0':
                print("\n[退出] 程序已退出。")
                break

            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(video_files):
                selected_video = video_files[choice_idx]
                selected_info = get_video_info(selected_video)

                print(f"\n{'-'*80}")
                print(f"[选择] 您选择了: {selected_info['file_name'] if selected_info else os.path.basename(selected_video)}")
                print(f"[路径] {selected_video}")
                print("-"*80)

                # 显示压缩预判
                if selected_info:
                    print_compression_prediction(selected_info)
                    # 获取推荐CRF
                    _, _, recommended_crf, _ = predict_compression_effect(selected_info)
                else:
                    recommended_crf = 27
                    print("[提示] 无法获取视频信息，使用默认CRF=27")

                # 让用户选择是否自定义CRF
                custom_crf = get_custom_crf()
                final_crf = custom_crf if custom_crf is not None else recommended_crf
                print(f"\n[确认] 最终使用CRF值: {final_crf}")

                # 生成输出文件名
                base_name = os.path.splitext(os.path.basename(selected_video))[0]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_name = f"{base_name}_compressed_{timestamp}.mp4"
                output_path = os.path.join(os.path.dirname(selected_video), output_name)

                print(f"\n[输出] 压缩后文件名: {output_name}")

                # 最终确认
                confirm = input("\n[最终确认] 是否开始压缩? (y/N): ").strip().lower()
                if confirm in ['y', 'yes', '']:
                    print("\n" + "="*80)
                    print(f"[开始] 正在压缩视频（CRF={final_crf}）...")
                    print("="*80)

                    # 执行压缩
                    success, compress_time = compress_video_with_progress(
                        selected_video,
                        output_path,
                        crf=final_crf,
                        progress_callback=show_progress
                    )

                    if success:
                        print(f"\n[成功] 压缩完成！输出文件: {output_path}")
                        # 打印比对信息
                        print_compress_comparison(selected_video, output_path, compress_time)
                    else:
                        print("\n[失败] 压缩失败!")
                else:
                    print("\n[取消] 已取消压缩。")
            else:
                print(f"\n[提示] 无效的选择，请输入1~{len(video_files)}之间的数字")
        except ValueError:
            print("\n[提示] 请输入有效的数字（如 1、2、0）")
        except KeyboardInterrupt:
            print("\n\n[中断] 程序被用户中断。")
            break

        # 询问是否继续
        continue_choice = input("\n[继续] 是否压缩其他视频? (y/N): ").strip().lower()
        if continue_choice not in ['y', 'yes', '']:
            print("\n[退出] 程序已退出。")
            break


if __name__ == "__main__":
    main()