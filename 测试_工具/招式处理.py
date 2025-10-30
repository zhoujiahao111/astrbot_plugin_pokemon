import json
import os


def balance_pokemon_moves_pp(file_path: str):
    """
    检测并动态调整宝可梦招式的PP值以实现平衡。

    该函数会读取一个包含招式数据的JSON文件，
    根据设定的高威力、高命中规则来下调招式的PP值，
    然后将修改后的数据写回原文件。

    Args:
        file_path (str): 招式JSON文件的路径。
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件路径不存在 -> '{file_path}'")
        return

    try:
        # 使用 'utf-8' 编码读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            moves_data = json.load(f)

        print("开始检测和调整招式PP...\n")
        adjusted_moves_log = []

        # 遍历字典中的每一个招式
        for move_name, move_stats in moves_data.items():
            # 确保招式数据包含所有必要的键值
            if all(k in move_stats for k in ["威力", "命中", "PP"]):
                power = move_stats.get("威力", 0)
                accuracy = move_stats.get("命中", 0)
                original_pp = move_stats.get("PP", 0)

                # 主要判断条件：威力 > 110, 命中 >= 70, PP > 2
                if power > 110 and accuracy >= 70 and original_pp > 2:
                    new_pp = original_pp
                    # 根据威力细分调整规则
                    if power >= 140:
                        new_pp = 1  # 威力极高的招式（如爆音波），PP降至1
                    else:  # 威力在 111 到 139 之间
                        new_pp = 2  # 其他高威力招式，PP降至2

                    # 如果计算出的新PP与原始PP不同，则进行更新
                    if new_pp != original_pp:
                        moves_data[move_name]["PP"] = new_pp
                        adjusted_moves_log.append(
                            f'招式: "{move_name}" (威力: {power}, 命中: {accuracy}) '
                            f'的PP已从 {original_pp} 调整为 {new_pp}'
                        )

        # 如果有招式被调整，则输出日志并写回文件
        if adjusted_moves_log:
            print("检测到平衡性问题，以下招式的PP值已被自动调整：")
            for log in adjusted_moves_log:
                print(f"- {log}")

            # 将修改后的数据写回JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                # ensure_ascii=False 保证中文字符正常显示, indent=2 实现格式化美观输出
                json.dump(moves_data, f, ensure_ascii=False, indent=2)

            print(f"\n招式数据已成功更新并保存至: '{file_path}'")
        else:
            print("所有招式均符合平衡标准，无需调整。")

    except json.JSONDecodeError:
        print(f"错误：文件 '{file_path}' 的JSON格式无效，请检查文件内容。")
    except Exception as e:
        print(f"在处理过程中发生了一个未知错误: {e}")


# --- 如何使用 ---
if __name__ == "__main__":
    # 将这里的路径替换成您自己的 "招式.json" 文件的实际路径
    json_file_path = r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\招式.json"

    # 执行平衡调整方法
    balance_pokemon_moves_pp(json_file_path)