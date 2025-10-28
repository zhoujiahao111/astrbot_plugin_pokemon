import os
import glob

def get_all_py_files(root_path, ignore_list):
    """
    获取所有Python文件，忽略指定文件夹
    
    Args:
        root_path: 根目录路径
        ignore_list: 忽略的文件夹名称列表
    
    Returns:
        list: 包含所有Python文件路径的列表
    """
    py_files = []
    
    for root, dirs, files in os.walk(root_path):
        # 计算相对于根目录的相对路径
        relative_path = os.path.relpath(root, root_path)
        
        # 如果是根目录本身，继续处理
        if relative_path == '.':
            # 检查根目录的直接子文件夹
            for dir_name in dirs[:]:  # 使用切片复制避免修改遍历中的列表
                if dir_name in ignore_list:
                    print(f"跳过子文件夹: {dir_name}")
                    dirs.remove(dir_name)  # 从dirs中移除，避免os.walk进入该目录
            continue
        
        # 获取相对路径的第一级目录（直接子文件夹）
        first_level_dir = relative_path.split(os.sep)[0]
        
        # 如果第一级目录在忽略列表中，跳过整个分支
        if first_level_dir in ignore_list:
            print(f"跳过文件夹分支: {root}")
            dirs.clear()  # 清空dirs，避免os.walk进入子目录
            continue
        
        # 查找所有.py文件
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                py_files.append(full_path)
    
    return py_files

def write_py_files_to_txt(py_files, output_path, root_path):
    """
    将Python文件内容写入到txt文件中
    
    Args:
        py_files: Python文件路径列表
        output_path: 输出文件路径
        root_path: 根目录路径（用于计算相对路径）
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for py_file in py_files:
            # 计算相对于根目录的相对路径
            relative_path = os.path.relpath(py_file, root_path)
            
            # 写入文件路径
            f.write(f"{relative_path}\n")
            f.write("=" * 50 + "\n")
            
            try:
                # 读取并写入文件内容
                with open(py_file, 'r', encoding='utf-8') as py_f:
                    content = py_f.read()
                    f.write(content)
            except Exception as e:
                f.write(f"读取文件时出错: {e}\n")
            
            f.write("\n" + "=" * 50 + "\n\n")

def main():
    # 获取脚本所在目录的父目录（绝对路径）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    print(f"扫描目录: {parent_dir}")
    
    # 忽略列表
    ignore_list = ['测试', '备份', '.idea', '.venv', '测试_工具', '备份', "旧代码", '说明文档', "tests", 'data', "__pycache__"]
    
    # 获取所有Python文件
    py_files = get_all_py_files(parent_dir, ignore_list)
    
    print(f"找到 {len(py_files)} 个Python文件")
    
    # 获取桌面路径
    username = os.getlogin()
    desktop_path = os.path.join("C:\\Users", username, "Desktop", "python_files_content.txt")
    
    # 写入文件
    write_py_files_to_txt(py_files, desktop_path, parent_dir)
    
    print(f"文件已保存到: {desktop_path}")

if __name__ == "__main__":
    main()