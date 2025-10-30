# # coding=utf-8
# import os
# import random
#
# import requests
# from lxml import etree
# import json
#
#
# def 文本转lxml方法(文本:str) -> etree._Element:
#     return etree.HTML(文本)
import json
import os


# def 道具方法():
#     b= []
#     for i in 道具:
#         print(i["生效场景"])
#         # i["生效场景"] = i["生效场景"][0]
#
#         b.append(i)
#     return b
#
# with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\道具.json', 'r', encoding='utf-8') as f:
#     道具: dict = json.loads(f.read())
#
#
# json_output = json.dumps(道具方法(), ensure_ascii=False, indent=2)

# 如果需要保存到文件
# with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\道具.json', 'w', encoding='utf-8') as f:
#     f.write(json_output)
# "精灵球": {
#     "贴图": "精灵球.png",
#     "生效场景": ["野外冒险"],
#     "类型": "即时捕获",
#     "效果参数": {
#       "基础捕获率": 0.3
#     },
#     "消耗类型": ["次数", 1],
#     "价格": 600,
#     "描述": "用于投向野生宝可梦并将其捕捉的球。它是胶囊样式的。"
#   },

def 查询贴图有效性方法():

    for i in 宝可梦图鉴:
        images文件夹路径 = os.path.join(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'data',
                'images'
            )
        )

        if not os.path.exists(os.path.join(
            images文件夹路径,
            "pokemon",
            i["贴图"]
        )):

            print("没有!", i["贴图"])

        if i["mega"]:
            if not os.path.exists(os.path.join(
                images文件夹路径,
                "pokemon_mega",
                i["mega"]
            )):
                print("没有mega!", i["mega"])

        if i["极巨化"]:
            if not os.path.exists(os.path.join(
                images文件夹路径,
                "pokemon_gigantamax",
                i["极巨化"]
            )):
                print("没有极巨化!", i["极巨化"])


with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'r', encoding='utf-8') as f:
    宝可梦图鉴: dict = json.loads(f.read())


查询贴图有效性方法()
