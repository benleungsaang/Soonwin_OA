import os
import sys

def pdf_to_jpg(pdf_path, dpi=150):
    """
    使用PyMuPDF将PDF文件转换为多个JPG图片
    :param pdf_path: PDF文件路径
    :param dpi: 图像分辨率，默认150 DPI
    """
    # 获取PDF文件名（不含扩展名）用于命名输出图片
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("正在安装PyMuPDF...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
        import fitz
    
    try:
        # 打开PDF文件
        pdf_document = fitz.open(pdf_path)
        
        print(f"PDF文件共 {len(pdf_document)} 页")
        
        # 遍历每一页
        for page_num in range(len(pdf_document)):
            # 获取页面
            page = pdf_document.load_page(page_num)
            
            # 设置缩放比例（DPI/72，因为默认DPI是72）
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # 渲染页面为图像
            pix = page.get_pixmap(matrix=mat)
            
            # 生成JPG文件名
            jpg_filename = f"{base_name}_page_{page_num+1}.jpg"
            
            # 保存为JPG图片
            pix.save(jpg_filename)
            
            print(f"已保存: {jpg_filename}")
        
        # 关闭PDF文档
        pdf_document.close()
        print("转换完成!")
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")

if __name__ == "__main__":
    # 获取当前目录下所有的PDF文件
    current_dir = os.getcwd()
    pdf_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("当前目录下没有找到PDF文件")
    else:
        print(f"在当前目录找到 {len(pdf_files)} 个PDF文件: {pdf_files}")
        
        # 处理每个PDF文件
        for pdf_file in pdf_files:
            pdf_path = os.path.join(current_dir, pdf_file)
            print(f"\n正在处理: {pdf_file}")
            pdf_to_jpg(pdf_path, dpi=150)