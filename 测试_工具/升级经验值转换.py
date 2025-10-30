import json

# 文件路径
file_path = r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json"

# 成长速度映射表
growth_rate_map = ["最快", "快", "较快", "较慢", "慢", "最慢"]

# 读取JSON文件
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 修改所有宝可梦的成长速度字段
for pokemon in data:
    if "成长速度" in pokemon:
        speed_index = pokemon["成长速度"]
        if isinstance(speed_index, int) and 0 <= speed_index < len(growth_rate_map):
            pokemon["成长速度"] = growth_rate_map[speed_index]

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("修改完成！")