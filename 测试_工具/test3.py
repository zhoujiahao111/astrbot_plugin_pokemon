import json


def extract_evolution_items():
    # 文件路径
    file_path = r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json"

    # 存储进化道具的集合
    evolution_items = set()

    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as file:
            pokemon_data = json.load(file)

        # 检查数据是否为列表
        if isinstance(pokemon_data, list):
            # 迭代每个宝可梦
            for pokemon in pokemon_data:
                # 检查是否有进化信息且为列表
                if "进化信息" in pokemon and isinstance(pokemon["进化信息"], list):
                    # 迭代每个进化信息
                    for evolution in pokemon["进化信息"]:
                        # 检查是否有进化道具字段且不为空
                        if "进化道具" in evolution and evolution["进化道具"]:
                            evolution_items.add(evolution["进化道具"])

        # 输出所有进化道具名称
        print("所有进化道具名称：")
        for item in sorted(evolution_items):
            print(item)

        print(f"\n总共找到 {len(evolution_items)} 种不同的进化道具")

        return evolution_items

    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
    except json.JSONDecodeError:
        print("错误：JSON文件格式不正确")
    except Exception as e:
        print(f"发生错误：{e}")


# 执行函数
if __name__ == "__main__":
    extract_evolution_items()