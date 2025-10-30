# coding=utf-8
import json
import os
import random
import shutil

import requests
from lxml import etree

def 文本转lxml方法(文本:str) -> etree._Element:
    return etree.HTML(文本)


def 宝可梦详情页信息提取(html: etree._Element, 文件名) -> dict:
    # print(文件名)
    try:
        宝可梦名称 = html.xpath('//h1/span/text()')[0]
    except:
        print("名称获取失败")
        return {}

    编号: int = int(html.xpath('//a[@title="宝可梦列表（按全国图鉴编号）"]/text()')[0].strip("#"))

     # 使用匹配器和String合并文本
    简介信息列表 = []
    for p in html.xpath('//div[@class="mw-content-ltr mw-parser-output"]/p[count(preceding-sibling::h2) = 1]'):
        简介信息列表.append(p.xpath('string(.)'))

    简介信息 = "".join(简介信息列表)

    '''
    //s1.52poke.com/wiki/thumb/3/30/925Maushold-Three.png/300px-925Maushold-Three.png
    //s1.52poke.com/wiki/thumb/c/c0/924Tandemaus.png/250px-924Tandemaus.png
    '''
    宝可梦贴图列表 = html.xpath(
        '//a[@title="宝可梦列表（按全国图鉴编号）"]/ancestor::tbody[2]/tr[2]/td/table/tbody//span/a[@class="mw-file-description"]/img/@src'
    )

    for 宝可梦贴图 in 宝可梦贴图列表:
        if all([宝可梦贴图[:27] == "//s1.52poke.com/wiki/thumb/", "px-" in 宝可梦贴图[宝可梦贴图.rfind('/') + 1:]]):
            px数字 = int(宝可梦贴图[宝可梦贴图.rfind('/') + 1:].split('px')[0])
            if px数字 > 120:
                宝可梦贴图 = "https:" + 宝可梦贴图
                continue
            else:
                raise ValueError("贴图图片大小异常!!!")


    属性列表 = html.xpath(
        '//a[@title="宝可梦列表（按全国图鉴编号）"]/ancestor::tbody[2]/tr[3]/td[1]/table/tbody/tr/td/table[@class="roundy bgwhite fulltable"]/tbody/tr/td/a[contains(@title, "属性")]/@title'
    )

    if not 属性列表:
        raise ValueError("属性列表获取失败")

    # 去重
    seen = {}
    宝可梦属性列表 = []
    for item in 属性列表:
        if item not in seen:
            seen[item] = True
            宝可梦属性列表.append(item)

    if len(宝可梦属性列表) > 1:
        宝可梦属性列表 = 宝可梦属性列表[:2]

        if 宝可梦属性列表[0] == 宝可梦属性列表[1]:
            print(宝可梦属性列表)
            raise ValueError("属性列表重复了!!!")

    宝可梦属性列表 = [i.strip("（属性）") for i in 宝可梦属性列表]


    # 宝可梦分类 = html.xpath('//table[@class="roundy bgwhite fulltable"]/tbody/tr/td/a/text()')[0]
    # tbody/tr[3]/td[2]/table/tbody/tr/td/table/tbody/tr/td/a
    宝可梦分类 = html.xpath(
        '//a[@title="宝可梦列表（按全国图鉴编号）"]/ancestor::tbody[2]/tr[3]/td[2]/table/tbody/tr/td/table/tbody/tr/td/a/text()'
    )[0]

    身高, 体重 = html.xpath('//table[@class="fulltable"]/tbody//table//table[@class="roundy bgwhite fulltable"]/tbody/tr/td/text()')[:2]

    种族值表格 = html.xpath('//table[@style="white-space:nowrap"]/tbody')[0]
    种族值字典 = {} # 属性值是int !!!
    属性键值元组 = ("HP", "攻击", "防御", "特供", "特防", "速度")

    for 索引, 属性 in enumerate(种族值表格.xpath('tr')[2:-2]):
        种族值字典[属性键值元组[索引]] = int(属性.xpath('th[1]/span[@style="float:right"]/text()')[0])

    招式名称列表: list = html.xpath("//tr[@class='at-c bgwhite']/td[3]//b/a/text()")
    通用招式列表 = ["撞击", "叫声", "撒娇"]

    # 选择3-4个特殊招式, 并填充一个通用招式
    if len(招式名称列表) >= 4:
        招式名称列表 = 招式名称列表[:random.randint(3,4)]
    elif len(招式名称列表) < 1:
        招式名称列表: list = html.xpath("//tr[@class='at-c bgwhite']/td[3]//a/text()")

        if len(招式名称列表) >= 4:
            招式名称列表 = 招式名称列表[:random.randint(3, 4)]
        elif len(招式名称列表) < 1:
            print("没有招式")
            raise ValueError("招式异常")

    while len(招式名称列表) < 4:
        招式名称列表.append(通用招式列表[3-len(通用招式列表)])

    # 随机打乱招式列表
    random.shuffle(招式名称列表)


    return {
        "编号": 编号,
        "名称": 宝可梦名称,
        "贴图": 宝可梦贴图,
        "宝可梦属性": 宝可梦属性列表,
        "宝可梦分类": 宝可梦分类,
        "身高": 身高.strip(" \n"),
        "体重": 体重.strip(" \n"),
        "种族值字典": 种族值字典,
        "招式名称列表": 招式名称列表,
        "是否mega": None,
        "是否极巨化": None,
        "简介": 简介信息
    }

def 列表url提取方法(html: etree._Element) -> list:
    print(html.xpath('//td[@class="rdexn-msp"]/a/@href'))

def 读取文件方法(path='') -> str:
    #path = "config.config"

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# 排序结果 = [None] * 1025
#
# for 索引, 名称 in enumerate(os.listdir(r"C:\file\.自学\python-311\程序\宝可梦图鉴爬取\宝可梦详情页面")):
#     html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", 名称)))
#     结果 = 宝可梦详情页信息提取(html, 名称)
#
#     排序结果[结果['编号'] - 1] = 结果
#
# import json
# # 转换为JSON
# json_output = json.dumps(排序结果, ensure_ascii=False, indent=2)
#
# # 如果需要保存到文件
# with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'w', encoding='utf-8') as f:
#     f.write(json_output)


# 原始文本 = 读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", "触手百合.html"))

# html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", "一家鼠.html")))
# 结果 = 宝可梦详情页信息提取(html, "仙子伊布")
# print(结果)

# html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "网页", "宝可梦列表.html")))
# 结果 = 列表url提取方法(html)

def 解析进化链(进化数据列表, 当前宝可梦名称, 索引字典: dict):
    if not 进化数据列表:
        return {}

    # 使用迭代器可以方便地成对处理“进化条件”和“进化结果”
    数据迭代器 = iter(进化数据列表)

    # 提取进化链的第一个宝可梦（未进化形态）

    初始宝可梦内容 = next(数据迭代器)[0]
    # 通过分割换行符并取最后一部分来提取名称
    宝可梦名称 = 初始宝可梦名称 = 初始宝可梦内容.strip().split('\n')[-1]

    for i in range(1, len(初始宝可梦名称)):
        if 索引字典.get(初始宝可梦名称[:i*-1], "no") != "no":
            宝可梦名称 = 初始宝可梦名称[:i*-1]
            break

    if 宝可梦名称 == 初始宝可梦名称:
        return {
                    "进化至_索引": " !人工填写 ",
                    "进化等级": " !人工填写 ",
                }
        # raise ValueError("名称错误", 进化数据列表, 当前宝可梦名称)


    下一个结束 = False
    if 当前宝可梦名称 == 宝可梦名称:
        下一个结束 = True

    # 初始化最终的进化链字典
    进化链字典 = {}
    #
    # # 循环处理后续的进化阶段
    计数器 = 0
    while True:
        # 提取进化条件
        try:
            进化条件内容 = next(数据迭代器)[0]
        except:
            # print("迭代结束", 当前宝可梦名称, 进化数据列表)
            return {}

        if '→' in 进化条件内容:

            条件解析:str = 进化条件内容.replace('→', '').strip()
            try:
                # 提取数字 等级16以上
                条件 = int(条件解析[2:-2])
            except:
                try:
                    # '通过对战达到25以上（随机）（99%概'  25以上
                    条件 = int(条件解析.split("以上")[0][-2:])
                except:
                    条件 = None

            # 提取进化后的宝可梦信息
            进化后宝可梦内容 = next(数据迭代器)[0]
            初始宝可梦名称 = 进化后宝可梦内容.strip().split('\n')[-1]

            for i in range(1, len(初始宝可梦名称)):
                if 索引字典.get(初始宝可梦名称[:i * -1], "no") != "no":
                    宝可梦名称 = 初始宝可梦名称[:i * -1]
                    break

            if 宝可梦名称 == 初始宝可梦名称:
                raise ValueError("名称错误", 进化数据列表)

            if 下一个结束 or (当前宝可梦名称 == 宝可梦名称 and 下一个结束):
                if 条件 == None:
                    print(当前宝可梦名称, ":", 条件解析, "进化至",宝可梦名称)
                    种族值字典 = 图鉴[索引字典[当前宝可梦名称]]["种族值字典"]
                    总和 = sum(种族值字典.values())
                    if 总和 <= 200:
                        条件 = 7  # 低种族值（如刺尾虫195 → 7级）
                    elif 200 < 总和<= 300:
                        条件 = 16  # 中等偏低（如伞电蜥289 → 16级）
                    elif 300 < 总和 <= 400:
                        条件 = 25  # 中等（如皮卡丘320 → 25级）
                    elif 400 < 总和 <= 500:
                        条件 = 36  # 较高（如伊布465 → 36级）
                    else:
                        条件 = 45  # 高种族值（如准神）
                    # 条件 = int(input(":"))


                return {
                    "进化至_索引": 索引字典[宝可梦名称],
                    "进化等级": 条件,
                }

            if 当前宝可梦名称 == 宝可梦名称:
                下一个结束 = True

        计数器 += 1

        if 计数器 > len(进化数据列表)-3:
            break
    # return
    # raise ValueError("错误, 进化链解析失败", 进化数据列表)
    return 进化链字典

def 爬取进化信息(html, 当前宝可梦名称, 索引字典):
    try:
        span_element = html.xpath('//span[@id="进化" or @id="進化"]')[0]
        parent = span_element.getparent()
        table = parent.xpath('following-sibling::table[1]')[0]
        进化表格 = table.xpath("tbody/tr")

        if len(进化表格) > 1:
            print(当前宝可梦名称)
        # 进化数据列表 = []
        # for td in 进化表格.xpath('td'):
        #     进化数据列表.append([td.xpath('string()').strip()])
        #
        # 整理后的进化链 = 解析进化链(进化数据列表, 当前宝可梦名称, 索引字典)

    except:
        整理后的进化链 = {
            "进化至_索引": " !人工填写 ",
            "进化等级": " !人工填写 ",
        }
    # return 整理后的进化链
    return
    # print(当前宝可梦名称, 整理后的进化链, '\n')

def 爬取基础经验值和成长速度(html, 名称, 信息):
    try:
        经验值 = int(html.xpath("//small[text()='基础经验值：']/following-sibling::span/text()")[-1].strip())
    except:
        try:
            经验值 = int(html.xpath("//small[text()='基础经验值：']")[0].getparent().xpath("text()")[0].strip())
        except Exception as e:
            经验值 = 0
            # raise ValueError(f"{名称}, {str(e)}")

    if 经验值 < 10:
        种族值总和 = sum(信息["种族值字典"].values())
        if 种族值总和 < 200:
            经验值 = 种族值总和 // 6
        elif 种族值总和 < 300:
            经验值 = 种族值总和 // 5
        elif 种族值总和 < 400:
            经验值 = 种族值总和 // 4
        elif 种族值总和 < 500:
            经验值 = 种族值总和 // 3.2
        elif 种族值总和 < 600:
            经验值 = 种族值总和 // 2.8
        elif 种族值总和 < 700:
            经验值 = 种族值总和 // 2.6
        else:
            经验值 = 种族值总和 // 2.2

    try:
        标签 = html.xpath("//a[text()='100级时经验值']")[0].getparent()
        成长速度 = 标签.xpath("following-sibling::table[1]//small/text()")[0]
    except Exception as e:
        成长速度 = "较慢"

    成长速度 = ["最快", "快", "较快", "较慢", "慢", "最慢"].index(成长速度.strip("()（）"))

    return 经验值 ,成长速度


    # if len(整理列表) < 2:
    #     print(f"https://wiki.52poke.com/wiki/{文件名.replace('.html','')}#可学会招式表")
    # print(len(整理列表))
    # if len(整理列表) < 1:# and "图图犬" not in 文件名 and "果然" not in 文件名 and "拳海参" not in 文件名:
    #     print(整理列表)
    #     raise ValueError("整理列表太少")
        # print(解析列表)
# html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", "妙蛙种子.html")))
# 结果 = 爬取基础经验值和成长速度(html)

# with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'r', encoding='utf-8') as f:
#     图鉴 = json.loads(f.read())
#
# with open(r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\名称索引.json", 'r', encoding='utf-8') as f:
#     索引字典 = json.loads(f.read())
#
# for 索引, 文件名 in enumerate(os.listdir(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\测试\宝可梦详情页面')):
#     html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", 文件名)))
#     经验值, 成长速度 = 爬取基础经验值和成长速度(html, 文件名.strip(".html"), 图鉴[索引字典[文件名.strip(".html")]])
#     图鉴[索引字典[文件名.strip(".html")]]["战胜经验值"] = 经验值
#     图鉴[索引字典[文件名.strip(".html")]]["成长速度"] = 成长速度
#
# json_output = json.dumps(图鉴, ensure_ascii=False, indent=2)
#
# # 如果需要保存到文件
# with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'w', encoding='utf-8') as f:
#     f.write(json_output)



# 招式提取方法(文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", "凯西.html"))), "凯西")
# 招式提取方法(文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", "龟脚脚.html"))), "龟脚脚.html")





# with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'r', encoding='utf-8') as f:
#     图鉴 = json.loads(f.read())
#
#
# with open(r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\名称索引.json", 'r', encoding='utf-8') as f:
#     索引字典 = json.loads(f.read())

# html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", "伊布.html")))
# 结果 = 爬取进化信息(html, "伊布",索引字典)

# for 索引, 文件名 in enumerate(os.listdir(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\宝可梦详情页面')):
#     html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", 文件名)))
#     结果 = 爬取进化信息(html, 文件名.strip(".html"), 索引字典)

    # 图鉴[索引字典[文件名.strip(".html")]]["进化信息"] = 结果
# print(图鉴[0])
#
# json_output = json.dumps(图鉴, ensure_ascii=False, indent=2)
#
# # 如果需要保存到文件
# with open(r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\json\宝可梦图鉴.json', 'w', encoding='utf-8') as f:
#     f.write(json_output)

# html = 文本转lxml方法(读取文件方法(os.path.join(os.getcwd(), "宝可梦详情页面", "三海地鼠.html")))
# 结果 = 爬取进化信息(html, "三海地鼠",索引字典)
#
# 路径 = r'C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\images'
# 基础路径 = r"C:\file\ruanjian\qq机器人\AstrBot\data\plugins\astrbot_plugin_pokemon\data\images"
#
# for i in 图鉴:
#     if "webp" in i["贴图"]:
#         名称 = i["贴图"]
#     else:
#         名称 = i["贴图"][i["贴图"].rfind("/")+1:]
#
#     图片路径 = os.path.join(路径,"pokemon", 名称)
#
#
#     if not os.path.exists(图片路径):
#         print(f"不存在! 编号 {i['编号']} 名称 {i['名称']} 贴图 {i['贴图']}")
#
#     # i["贴图"] = 名称.strip()
#
#     # shutil.move(图片路径, os.path.join(基础路径,"pokemon", 名称))
#
#     if i["mega"]:
#         if "webp" in i["mega"]:
#             名称 = i["mega"]
#         else:
#             名称 = i["mega"][i["mega"].rfind("/")+1:]
#
#         图片路径 = os.path.join(路径, "pokemon_mega", 名称)
#
#         if not os.path.exists(图片路径):
#             print(f"mega不存在! 编号 {i['编号']} 名称 {i['名称']} mega贴图 {i['mega']}")
#
#         # i["mega"] = 名称.strip()
#         # shutil.move(图片路径, os.path.join(基础路径,"pokemon_mega", 名称))
#
#     if i["极巨化"]:
#         if "webp" in i["极巨化"]:
#             名称 = i["极巨化"]
#         else:
#             名称 = i["极巨化"][i["极巨化"].rfind("/")+1:]
#
#         图片路径 = os.path.join(路径,"pokemon_gigantamax", 名称)
#
#         if not os.path.exists(图片路径):
#             print(f"极巨化不存在! 编号 {i['编号']} 名称 {i['名称']} 极巨化贴图 {i['极巨化']}")

        # i["极巨化"] = 名称.strip()
        # shutil.move(图片路径, os.path.join(基础路径,"pokemon_gigantamax", 名称))

# import json
# # 转换为JSON
# json_output = json.dumps(图鉴, ensure_ascii=False, indent=2)
#
# # 如果需要保存到文件
# with open(r'C:\file\.自学\python-311\程序\宝可梦图鉴爬取\宝可梦图鉴.json', 'w', encoding='utf-8') as f:
#     f.write(json_output)

# print(图鉴[14])