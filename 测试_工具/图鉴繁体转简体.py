# coding=utf-8
import json
from opencc import OpenCC

# 1. 读取原始 JSON
with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'r', encoding='utf-8') as f:
    data = json.load(f)          # data 是一个 list[dict]

# 2. 初始化 OpenCC 转换器与阈值
cc = OpenCC('t2s')               # 繁 -> 简
THRESHOLD = 0.01                 # 5% 字符被简化就视为“有繁体”

def contains_enough_traditional(text: str, threshold=THRESHOLD) -> bool:
    """
    判断一段文本是否含有足够比例的繁体字
    """
    if not text:
        return False

    simplified = cc.convert(text)
    diff_count = sum(1 for a, b in zip(text, simplified) if a != b)
    return diff_count / len(text) >= threshold

# 3. 遍历并转换
for item in data:
    if "简介" in item and isinstance(item["简介"], str):
        raw = item["简介"]

        if contains_enough_traditional(raw):
            item["简介"] = cc.convert(raw)   # 原地替换

# 4. 保存回文件（或数据库、Redis 等）
with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("处理完成，共 {} 条记录已检查并更新。".format(len(data)))
