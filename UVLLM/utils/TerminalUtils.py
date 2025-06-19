import os
import sys
import time
import shutil

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    """
    打印进度条以显示当前操作的进度。
    
    Args:
        iteration (int): 当前迭代次数
        total (int): 总迭代次数
        prefix (str): 进度条前缀字符串
        suffix (str): 进度条后缀字符串
        decimals (int): 百分比精度的小数位数
        length (int): 进度条的字符长度
        fill (str): 进度条填充字符
        print_end (str): 打印结束字符（如"\r"表示回车）
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    # 如果迭代完成，打印新行
    if iteration == total: 
        print()

def print_stage_header(stage_name, description=""):
    """
    打印阶段标题，使其在终端中更加明显。
    
    Args:
        stage_name (str): 阶段名称
        description (str, optional): 阶段描述
    """
    terminal_width = shutil.get_terminal_size().columns
    print("\n" + "=" * terminal_width)
    print(f" {stage_name} ".center(terminal_width, "="))
    if description:
        print(f" {description} ".center(terminal_width))
    print("=" * terminal_width + "\n")

def print_result(success, message="", details=None):
    """
    打印结果，用不同的颜色区分成功和失败。
    
    Args:
        success (bool): 是否成功
        message (str): 结果消息
        details (str, optional): 详细信息
    """
    if success:
        print(f"\033[92m✓ SUCCESS: {message}\033[0m")
    else:
        print(f"\033[91m✗ FAILURE: {message}\033[0m")
    
    if details:
        print(f"  Details: {details}")

def save_file_with_backup(content, file_path, backup_dir=None, backup_suffix="_original"):
    """
    保存文件并备份原始文件。
    
    Args:
        content (str): 要写入文件的内容
        file_path (str): 目标文件路径
        backup_dir (str, optional): 备份目录。如果为None，则在原始目录中创建备份。
        backup_suffix (str, optional): 备份文件后缀
    
    Returns:
        tuple: (成功标志, 备份文件路径或错误消息)
    """
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 如果文件存在，先备份
        backup_path = None
        if os.path.exists(file_path):
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
                backup_filename = f"{os.path.basename(file_path)}{backup_suffix}"
                backup_path = os.path.join(backup_dir, backup_filename)
            else:
                backup_path = f"{file_path}{backup_suffix}"
            
            shutil.copy2(file_path, backup_path)
        
        # 写入新内容
        with open(file_path, 'w') as f:
            f.write(content)
        
        return True, backup_path
    except Exception as e:
        return False, str(e)

def create_output_summary(repair_info, output_path):
    """
    创建修复结果摘要文件。
    
    Args:
        repair_info (dict): 修复信息字典
        output_path (str): 输出文件路径
    """
    with open(output_path, 'w') as f:
        f.write("# RTL Repair Summary\n\n")
        f.write(f"## Project: {repair_info.get('project', 'Unknown')}\n")
        f.write(f"## Version: {repair_info.get('version', 'Unknown')}\n\n")
        
        f.write("### Repair Statistics\n")
        f.write(f"- Total Time: {repair_info.get('total_time', 0):.2f} seconds\n")
        f.write(f"- Preprocess Time: {repair_info.get('preprocess_time', 0):.2f} seconds\n")
        f.write(f"- Mismatch Time: {repair_info.get('mismatch_time', 0):.2f} seconds\n")
        f.write(f"- Suspicious Time: {repair_info.get('suspicious_time', 0):.2f} seconds\n")
        f.write(f"- Success: {repair_info.get('success', False)}\n\n")
        
        if 'history' in repair_info and repair_info['history']:
            f.write("### Repair History\n")
            for i, entry in enumerate(repair_info['history']):
                f.write(f"#### Iteration {i+1}\n")
                f.write(f"- Score: {entry.get('score', 'N/A')}\n")
                f.write(f"- File: {entry.get('codepath', 'N/A')}\n")
                if 'fix' in entry and entry['fix']:
                    f.write(f"- Fix: {entry['fix']}\n")
                f.write("\n")
