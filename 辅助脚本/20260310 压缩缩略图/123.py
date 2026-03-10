import os
from PIL import Image
from pathlib import Path

def create_thumbnail(image_path, size=(300, 300), quality=60):
    """
    为单张图片创建 300x300 的缩略图

    参数:
    image_path: 原始图片路径
    size: 缩略图尺寸，默认 (300, 300)
    quality: 压缩质量（1-100），默认 60（低质量，满足缩略图需求）
    """
    try:
        # 打开图片
        with Image.open(image_path) as img:
            # 处理图片旋转（保留EXIF信息，解决手机拍照旋转问题）
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    orientation = exif.get(0x0112, 1)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)

            # 生成缩略图（保持比例，填充到300x300，避免拉伸变形）
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # 创建新画布（300x300），将缩略图居中放置（解决非正方形图片留白问题）
            new_img = Image.new("RGB", size, (255, 255, 255))
            offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
            new_img.paste(img, offset)

            # 构建新文件名：原文件名 + thumb + 扩展名
            img_path = Path(image_path)
            new_filename = f"{img_path.stem}_thumb{img_path.suffix}"
            new_filepath = img_path.parent / new_filename

            # 保存缩略图（PNG格式不支持quality参数，自动忽略）
            new_img.save(new_filepath, quality=quality, optimize=True)

            return True, f"成功生成缩略图: {new_filename}"

    except Exception as e:
        return False, f"处理失败 {image_path}: {str(e)}"

def batch_create_thumbnails():
    """批量处理当前目录下的所有图片文件"""
    # 支持的图片格式
    SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

    # 获取当前目录下的所有文件
    current_dir = os.getcwd()
    image_files = [
        f for f in os.listdir(current_dir)
        if os.path.isfile(f) and Path(f).suffix.lower() in SUPPORTED_FORMATS
    ]

    if not image_files:
        print("⚠️  当前目录下未找到支持的图片文件")
        return

    # 统计处理结果
    success_count = 0
    fail_count = 0
    fail_details = []

    print(f"📁 开始处理当前目录下的图片，共找到 {len(image_files)} 张图片")
    print("-" * 50)

    # 批量处理
    for img_file in image_files:
        success, msg = create_thumbnail(img_file)
        if success:
            success_count += 1
            print(f"✅ {msg}")
        else:
            fail_count += 1
            fail_details.append(msg)
            print(f"❌ {msg}")

    # 输出汇总结果
    print("-" * 50)
    print(f"📊 处理完成 | 成功: {success_count} | 失败: {fail_count}")
    if fail_details:
        print("\n❌ 失败详情:")
        for detail in fail_details:
            print(f"  - {detail}")

if __name__ == "__main__":
    # 安装依赖提示（首次运行需执行）
    try:
        import PIL
    except ImportError:
        print("⚠️  未检测到Pillow库，正在尝试自动安装...")
        os.system("pip install pillow")
        # 安装后重新导入
        from PIL import Image

    # 执行批量生成缩略图
    batch_create_thumbnails()

    # 暂停（方便Windows用户查看结果）
    input("\n按Enter键退出...")