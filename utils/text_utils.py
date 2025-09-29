# coding=utf-8
import json
import random
import re
from rapidfuzz import fuzz
from pypinyin import pinyin, Style

from ..models import result
import os

def 判断文本能否通过审核方法(文本: str, 违禁词列表: list) -> result.结果类:
    for 违禁词 in 违禁词列表:
        if 违禁词 in 文本:
            return result.结果类.失败方法("不！可！以！检测到违规内容啦~ 请修改后再试！(｀へ´)")
    return result.结果类.成功方法("")


def 名称模糊匹配方法(
    名称列表: list[str],
    用户输入: str,
    是否返回索引: bool = False
) -> result.结果类:
    """对名称列表进行模糊匹配。"""
    def _文字转为分词拼音方法(输入: str) -> str:
        return " ".join([item[0] for item in pinyin(输入, style=Style.NORMAL, errors='ignore')])

    if not 用户输入 or not 名称列表:
        return result.结果类.失败方法("输入或物品列表为空")

    if not isinstance(名称列表, list) or not all(isinstance(n, str) for n in 名称列表):
        return result.结果类.失败方法("名称列表格式错误，应为字符串列表 list[str]")

    汉字相似度阈值 = 30
    拼音相似度阈值 = 72
    最大数量 = 10
    结果列表 = []

    是否是拼音输入 = bool(re.match(r'^[a-zA-Z\s]+$', 用户输入))
    用户输入拼音 = 用户输入.lower() if 是否是拼音输入 else _文字转为分词拼音方法(用户输入)

    带拼音的名称列表 = [(名称, _文字转为分词拼音方法(名称)) for 名称 in 名称列表]

    for 索引, (名称, 物品拼音) in enumerate(带拼音的名称列表):
        if 名称 == 用户输入:
            return result.结果类.成功方法((名称, 索引) if 是否返回索引 else 名称)

        拼音相似度 = fuzz.token_set_ratio(物品拼音, 用户输入拼音)

        if 是否是拼音输入:
            # 如果用户输入的是拼音，则只比较拼音相似度
            if 拼音相似度 >= 拼音相似度阈值:
                结果列表.append((拼音相似度, 名称, 索引))
        else:
            # 如果用户输入的是中文，则同时比较中文和拼音相似度
            中文相似度 = max(fuzz.partial_ratio(名称, 用户输入), fuzz.ratio(名称, 用户输入))
            if 中文相似度 >= 汉字相似度阈值 or 拼音相似度 >= 拼音相似度阈值:
                # 使用两者中更高的分数作为排序依据
                综合得分 = max(拼音相似度, 中文相似度)
                结果列表.append((综合得分, 名称, 索引))

    if not 结果列表:
        return result.结果类.失败方法("没有匹配的名称哦")

    结果列表.sort(key=lambda x: x[0], reverse=True)
    建议名称列表 = [name for score, name, index in 结果列表[:最大数量]]

    提示信息 = "没有找到完全匹配的名称，您是不是想输入：\n" + '\n'.join(建议名称列表)
    return result.结果类.失败方法(提示信息)


def 构造宝可梦奖励文案(文案信息: dict, 经验值: int) -> list[tuple[str, dict]]:
    """
    根据宝可梦的奖励结算信息，构造用于生成随机文案的事件列表。
    """
    奖励事件列表 = []

    宝可梦昵称 = 文案信息.get("旧昵称") or 文案信息.get("宝可梦昵称", "某只宝可梦")

    # 升级
    if 文案信息.get("是否升级"):
        识别码 = "宝可梦_升级"
        变量字典 = {
            "宝可梦": 宝可梦昵称,
            "旧等级": 文案信息["旧等级"],
            "新等级": 文案信息["新等级"]
        }
        奖励事件列表.append((识别码, 变量字典))

    # 单一路径进化成功
    if 文案信息.get("是否进化"):
        # 单一路径进化成功
        if 文案信息["旧昵称"] != 文案信息["新昵称"]:
            识别码 = "宝可梦_进化_改名"
            变量字典 = {
                "旧昵称": 文案信息["旧昵称"],
                "新昵称": 文案信息["新昵称"]
            }
        else:
            识别码 = "宝可梦_进化_留名"
            变量字典 = {
                "昵称": 文案信息["旧昵称"],
                "旧种族": 文案信息["旧名称"],
                "新种族": 文案信息["新名称"]
            }
        奖励事件列表.append((识别码, 变量字典))
    elif 文案信息.get("可进化"):
        # 处理多路径进化，提示用户选择
        识别码 = "宝可梦_可多路径进化"
        进化选项 = 文案信息.get("进化选项", [])
        进化路线文案列表 = []

        for 选项 in 进化选项:
            新名称 = 选项.get("新名称", "未知宝可梦")

            # 构造进化条件描述
            条件描述 = []
            if "进化等级" in 选项:
                条件描述.append(f"等级达到 {选项['进化等级']}")
            if "进化道具" in 选项:
                条件描述.append(f"使用「{选项['进化道具']}」")
            if "亲密度" in 选项:
                条件描述.append(f"亲密度达到 {选项['亲密度']}")
            if "进化条件备注" in 选项 and 选项['进化条件备注']:
                条件描述.append(选项['进化条件备注'])

            # 组合成最终的路线文案
            if 条件描述:
                单条路线文案 = f"进化到 **{新名称}** (条件: {', '.join(条件描述)})"
            else:
                单条路线文案 = f"进化到 **{新名称}** (满足特殊条件)"

            进化路线文案列表.append(单条路线文案)

        变量字典 = {
            "宝可梦": 宝可梦昵称,
            "进化路线列表": 进化路线文案列表,  # 将路线作为列表传递，以便后续可以格式化（如用换行符连接）
            "指令提示": "使用 `!临时代码! 进化 [目标名称]` 来完成进化"
        }
        奖励事件列表.append((识别码, 变量字典))

    if 文案信息.get("是分支进化"):
        识别码 = "宝可梦_分支进化提示"
        变量字典 = {
            "宝可梦": 宝可梦昵称,
            "进化选项文本": 文案信息.get("分支进化选项文本", "多种形态")
        }
        奖励事件列表.append((识别码, 变量字典))

    # 学习新招式
    if 文案信息.get("是否学习"):
        新技能文本 = "、".join(文案信息["新技能列表"])
        if 文案信息.get("被遗忘技能列表"):
            识别码 = "宝可梦_替换招式"
            变量字典 = {
                "宝可梦": 宝可梦昵称,
                "新招式": 新技能文本,
                "旧招式": "、".join(文案信息["被遗忘技能列表"])
            }
        else:
            识别码 = "宝可梦_学习新招式"
            变量字典 = {
                "宝可梦": 宝可梦昵称,
                "新招式": 新技能文本
            }
        奖励事件列表.append((识别码, 变量字典))

    # 如果以上事件都未发生，则仅获得经验
    if not 奖励事件列表:
        识别码 = "宝可梦_获得经验"
        变量字典 = {
            "宝可梦": 宝可梦昵称,
            "经验值": 经验值
        }
        奖励事件列表.append((识别码, 变量字典))

    return 奖励事件列表

def 读取json方法(json名称: str):
    脚本目录 = os.path.dirname(os.path.abspath(__file__))

    # 构建完整的 JSON 文件路径
    json路径 = os.path.join(
        os.path.join(
            os.path.dirname(脚本目录),
            'data',
            'json'
        ),
        json名称 + ".json"
    )

    # 确保路径是绝对路径
    json路径 = os.path.abspath(json路径)

    if not os.path.exists(json路径):
        raise FileNotFoundError(json路径)

    with open(json路径, "r", encoding="utf-8") as f:
        return json.loads(f.read())
