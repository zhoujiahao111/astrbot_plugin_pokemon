import os
import ast
from typing import Dict, List, Tuple
from pathlib import Path

def logical_lines(path: str) -> int:
    """统计文件有效代码行数（除去空行与 # 注释）"""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for line in f if line.strip() and not line.strip().startswith("#"))

def top_level_functions_and_docs(file_path: str) -> List[Tuple[str, str]]:
    """返回 [(函数名, docstring首行), ...] 前两个顶层函数"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            node = ast.parse(f.read(), filename=file_path)
    except Exception:
        return []

    docs = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(item) or ""
            docs.append((item.name, doc.split("\n")[0].strip() if doc else ""))
            if len(docs) >= 2:
                break
    return docs

def scan_project(root: str) -> Dict[str, Dict[str, any]]:
    """扫描项目，返回 文件夹->文件信息 的嵌套结构"""
    results: Dict[str, Dict[str, any]] = {}
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # 过滤掉要跳过的文件夹
        dirnames[:] = [d for d in dirnames if d.lower() not in {s.lower() for s in SKIP_FOLDERS}]
        py_files = [f for f in filenames if f.lower().endswith(".py") and f != "__init__.py"]
        if not py_files:
            continue

        rel_folder = os.path.relpath(dirpath, root)
        folder_entry = results.setdefault(rel_folder, {})

        # 计算文件夹总有效行数
        total_lines = 0
        for py in py_files:
            full = os.path.join(dirpath, py)
            total_lines += logical_lines(full)

        folder_entry["_total_lines"] = total_lines

        # 控制是否只取前 3 个
        target_files = py_files if 是否显示所有文件 else py_files[:3]

        for py in target_files:
            full = os.path.join(dirpath, py)
            lines = logical_lines(full)
            if 是否输出doc:
                docs = top_level_functions_and_docs(full)
            else:
                docs = []
            folder_entry[py] = {"lines": lines, "docs": docs}

    return results

def print_results(results: Dict[str, Dict[str, any]]):
    """按需求格式化输出"""
    for folder, data in results.items():
        total = data.pop("_total_lines", 0)
        print(f"文件夹: {folder}  合计 {total} 行" if 是否输出py行数 else f"文件夹: {folder}")
        for py, info in data.items():
            print(f"    {py}  {info['lines']} 行" if 是否输出py行数 else f"    {py}")
            if 是否输出doc:
                for func_name, first_line in info["docs"]:
                    print(f"        {func_name}: {first_line}")
        print()


# -------------------- 用户配置 --------------------
PROJECT_PATH = Path(__file__).resolve().parents[3] / 'plugins' / 'astrbot_plugin_pokemon'

SKIP_FOLDERS = {"备份", "测试_工具", "说明文档", ".idea", ".venv", "__pycache__", "旧代码"}
是否显示所有文件 = True      # True = 列出全部 .py；False = 仅前 3 个
# 是否显示所有文件 = False
是否输出doc = True      # True = 打印 docstring；False = 不打印
# 是否输出doc = False

是否输出py行数 = True
# 是否输出py行数 = False
# -------------------------------------------------

if __name__ == "__main__":
    print_results(scan_project(PROJECT_PATH))