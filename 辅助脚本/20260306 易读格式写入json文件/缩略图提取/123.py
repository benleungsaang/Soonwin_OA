import os
import openpyxl
from pathlib import Path

def batch_rename_files(excel_file_path):
    """
    根据Excel文件中的Model和Original_Model列批量重命名文件

    参数:
    excel_file_path: Excel文件的路径（xlsx格式）
    """
    # 检查Excel文件是否存在
    if not os.path.exists(excel_file_path):
        print(f"错误：找不到Excel文件 {excel_file_path}")
        return

    try:
        # 加载Excel文件
        workbook = openpyxl.load_workbook(excel_file_path)
        # 获取第一个工作表（如果需要指定工作表名，可以修改为 workbook['工作表名']）
        worksheet = workbook.active

        # 存储重命名结果
        rename_results = {
            "成功": [],
            "文件不存在": [],
            "重命名失败": []
        }

        # 跳过表头，从第二行开始读取数据
        # 假设第一列是Model (A列)，第二列是Original_Model (B列)
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            # 获取Model和Original_Model值，处理空值
            model = row[0] if row[0] is not None else ""
            original_model = row[1] if row[1] is not None else ""

            # 跳过空行
            if not model or not original_model:
                continue

            # 遍历当前目录下的所有文件，查找匹配Original_Model的文件
            current_dir = Path.cwd()
            matched_files = []

            # 查找包含Original_Model的文件（模糊匹配）
            for file in current_dir.iterdir():
                if file.is_file() and original_model in file.name:
                    matched_files.append(file)

            if not matched_files:
                rename_results["文件不存在"].append(f"未找到包含 {original_model} 的文件")
                continue

            # 对找到的文件进行重命名
            for file in matched_files:
                try:
                    # 构建新文件名：model (Original_Model).扩展名
                    file_ext = file.suffix  # 获取文件扩展名
                    new_filename = f"{model} ({original_model}){file_ext}"
                    new_filepath = current_dir / new_filename

                    # 重命名文件
                    file.rename(new_filepath)
                    rename_results["成功"].append(f"{file.name} -> {new_filename}")

                except Exception as e:
                    rename_results["重命名失败"].append(f"{file.name} 重命名失败: {str(e)}")

        # 打印重命名结果
        print("\n=== 重命名结果汇总 ===")
        print(f"✅ 成功重命名: {len(rename_results['成功'])} 个文件")
        for item in rename_results['成功']:
            print(f"  {item}")

        if rename_results['文件不存在']:
            print(f"\n❌ 文件不存在: {len(rename_results['文件不存在'])} 个")
            for item in rename_results['文件不存在']:
                print(f"  {item}")

        if rename_results['重命名失败']:
            print(f"\n⚠️  重命名失败: {len(rename_results['重命名失败'])} 个")
            for item in rename_results['重命名失败']:
                print(f"  {item}")

    except Exception as e:
        print(f"处理Excel文件时出错: {str(e)}")
    finally:
        # 确保关闭工作簿
        if 'workbook' in locals():
            workbook.close()

if __name__ == "__main__":
    # 设置Excel文件名（请根据实际情况修改）
    EXCEL_FILE = "model_mapping.xlsx"

    # 执行批量重命名
    batch_rename_files(EXCEL_FILE)