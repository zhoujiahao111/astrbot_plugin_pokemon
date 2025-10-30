import os


def count_py_files_lines(folder_path, depth=3, current_depth=1):
    """
    统计指定文件夹及其子文件夹中所有py文件的行数

    Args:
        folder_path: 要统计的文件夹路径
        depth: 要遍历的深度
        current_depth: 当前遍历深度(内部使用)
    """
    total_lines = 0
    py_files = []

    try:
        items = os.listdir(folder_path)
    except PermissionError:
        return total_lines, py_files

    for item in items:
        item_path = os.path.join(folder_path, item)

        if os.path.isfile(item_path):
            if item.endswith('.py'):
                try:
                    with open(item_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        line_count = len(lines)
                        total_lines += line_count
                        py_files.append((item_path, line_count))
                except Exception as e:
                    print(f"无法读取文件 {item_path}: {e}")

        elif os.path.isdir(item_path) and current_depth < depth:
            # 跳过旧代码文件夹
            if item == "旧代码":
                continue

            sub_lines, sub_files = count_py_files_lines(
                item_path, depth, current_depth + 1
            )
            total_lines += sub_lines
            py_files.extend(sub_files)

    return total_lines, py_files


def filter_test_files(files):
    """过滤出测试文件夹中的文件"""
    test_files = []
    for file_path, line_count in files:
        if "测试_工具" in file_path:
            test_files.append((file_path, line_count))
    return test_files


if __name__ == "__main__":
    folder_path = r"C:\file\AstrBot-4.2.1\data\plugins\astrbot_plugin_pokemon"

    # 统计所有文件（包含测试文件夹）
    total_lines, all_files = count_py_files_lines(folder_path, 3)

    # 找出测试文件夹中的文件
    test_files = filter_test_files(all_files)
    test_lines = sum(line_count for _, line_count in test_files)

    # 计算不包含测试文件夹的行数
    non_test_lines = total_lines - test_lines

    # 输出所有文件
    for file_path, line_count in all_files:
        print(f"{file_path}: {line_count}行")

    print("\n\n" + "=" * 50)
    print(f"项目代码总行数（不包含测试）: {non_test_lines}")
    print(f"项目代码总行数（包含测试）: {total_lines}")