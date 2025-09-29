# coding=utf-8
import random
import copy
from ..core import database
from ..models import result
from ..models.enums import 表名类, 操作类
from ..models import session

# 预设一个通用招式池，包含一些常见且实用的招式
GENERIC_MOVES = ['撞击', '叫声', '拍击', '抓', '乱击']
POWERFUL_GENERIC_MOVES = ['泰山压顶', '劈开', '头锤', '踩踏']


def 初始招式学习方法(升级可学会招式列表: list) -> list:
    初始招式名称列表 = [i.招式名称 for i in 升级可学会招式列表 if i.等级 == 1]

    if len(初始招式名称列表) > 4:
        return random.sample(初始招式名称列表, 4)

    elif 1 <= len(初始招式名称列表) <= 4:
        # 少于等于4个，全部学习
        return 初始招式名称列表
    else:
        # 没有默认招式，根据可学习招式总数判断
        招式总数 = len(升级可学会招式列表)

        if 招式总数 < 9:
            # 认为是特殊宝可梦或技能过少, 补充强力技能
            return random.sample(POWERFUL_GENERIC_MOVES, random.randint(2, 3))
        else:
            # 普通宝可梦
            return random.sample(GENERIC_MOVES, random.randint(1, 3))


def 静态招式评分方法(招式字典: dict) -> float:
    """
    计算单个招式的静态评分。
    评分主要基于威力和命中率的期望值，PP提供少量加成。

    Args:
        招式字典 (dict): 包含招式"名称", "威力", "命中", "PP"的字典。

    Returns:
        float: 该招式的综合评分。
    """
    威力 = 招式字典.get("威力", 0)
    命中 = 招式字典.get("命中", 100)  # 默认为100，以处理无命中属性的招式
    pp = 招式字典.get("PP", 1)

    # 处理数据异常或变化招式（威力为0）
    if not all(isinstance(val, (int, float)) for val in [威力, 命中, pp]) or 威力 <= 0:
        # 对于变化招式等，可以给予一个基于PP的基础分，或未来扩展逻辑
        return pp * 0.5

        # 主要分数 = 威力 * 命中率 (期望伤害)
    # 例如：威力100，命中90，主要分为 100 * 0.9 = 90
    主要分 = 威力 * (命中 / 100.0)

    # PP加成 = PP值 * 权重 (PP越高，加成越多，但权重较低)
    # 例如：PP为15，加成为 15 * 0.5 = 7.5
    pp_加成 = pp * 0.5

    # 综合分 = 主要分 + PP加成
    综合分 = 主要分 + pp_加成

    return round(综合分, 2)

def 生成学习新招式操作字典方法(宝可梦ID: int, 当前招式列表: list[dict], 新招式列表: list[dict]) -> tuple[list[dict], dict]:
    """
    处理宝可梦学习多个新招式，并根据综合价值智能抉择。

    规则:
    1. 招式上限为4个。如果招式栏未满，优先填充。
    2. 综合评估所有当前招式和新招式，选出最优的4个组合。
    3. 为了用户体验，即使所有新招式评分都较低，也必须强制学习至少一个最好的新招式，
       替换掉当前最弱的招式。
    4. 新学习的招式在比较时会有一定的评分加成，以鼓励学习。

    Args:
        宝可梦ID (int): 宝可梦的唯一标识ID。
        当前招式列表 (list[dict]): 当前宝可梦持有的招式数据列表。
                                    格式统一为：[{"招式名称": {"属性": "一般", ...}}]
                                    或 [{"名称": "招式名称", "属性": "一般", ...}}]
        新招式列表 (list[dict]): 新学习的招式的数据列表。
                                    格式统一为：[{"招式名称": {"属性": "一般", ...}}]
                                    或 [{"名称": "招式名称", "属性": "一般", ...}}]

    Returns:
        tuple[list[dict], dict]: (适配数据库写入方法的列表, 学习技能的文案信息)
    """
    if not 新招式列表:
        return [], {"是否学习": False}

    当前招式名称集合 = {next(iter(m.keys())) for m in 当前招式列表 if m}
    新招式名称集合 = {next(iter(nm.keys())) for nm in 新招式列表 if nm}

    当前招式评分 = [(静态招式评分方法(m), m) for m in 当前招式列表]
    学习倾向加成 = 1.25
    新招式评分 = [(静态招式评分方法(m) * 学习倾向加成, m) for m in 新招式列表]
    所有候选招式 = sorted(当前招式评分 + 新招式评分, key=lambda x: x[0], reverse=True)
    潜在最终组合_带分数 = 所有候选招式[:4]
    潜在最终组合 = [move for score, move in 潜在最终组合_带分数]
    包含新招式 = any(招式名称 in 新招式名称集合
                     for m in 潜在最终组合 if m
                     for 招式名称 in [next(iter(m.keys()))])

    最终招式字典列表 = []
    if len(当前招式列表) < 4 or 包含新招式:
        最终招式字典列表 = 潜在最终组合
    else:
        最弱的旧招式 = min(当前招式评分, key=lambda x: x[0])[1]
        最强的新招式 = max(新招式评分, key=lambda x: x[0])[1]
        temp_list = copy.deepcopy(当前招式列表)
        replaced = False
        for i, move in enumerate(temp_list):
            if move["名称"] == 最弱的旧招式["名称"]:
                temp_list[i] = 最强的新招式
                replaced = True
                break
        if not replaced:
            print(f"警告:无法替换最弱的旧招式'{最弱的旧招式['名称']}', 这是一个奇怪的bug")
            最终招式字典列表 = 潜在最终组合
        else:
            最终招式字典列表 = temp_list

    最终招式名称集合 = {next(iter(m.keys())) for m in 最终招式字典列表 if m}

    # 计算出具体学会和遗忘的招式
    已学会的新招式 = list(最终招式名称集合.intersection(新招式名称集合))
    被遗忘的旧招式 = list(当前招式名称集合 - 最终招式名称集合)

    # 生成并返回数据库操作字典列表, 默认清空旧数据，然后插入新数据
    return ([{
        '表名': 表名类.招式表,
        '操作': 操作类.删除,
        '条件': {'宝可梦ID': 宝可梦ID}  # 使用传入的 宝可梦ID
    },
        {
            '表名': 表名类.招式表,
            '操作': 操作类.插入,
            '数据': [{"宝可梦ID": 宝可梦ID, "招式名称": next(iter(i.keys()))} for i in 最终招式字典列表 if i]
        }
    ],
    {
        "是否学习": len(已学会的新招式) > 0,
        "新技能列表": 已学会的新招式,
        "被遗忘技能列表": 被遗忘的旧招式
    })


async def 返回招式数据方法(宝可梦ID: int, 会话: session.会话类) -> list[dict]:
    # 获取招式名称
    db = await database.获取数据库对象()

    结果 = await db.单次查询方法({
            "表名": 表名类.招式表,
            "查询数据": '招式名称',
            "条件": {"宝可梦ID": 宝可梦ID}
    })

    if not 结果.是否成功:
        raise RuntimeError(f"宝可梦ID={宝可梦ID} 招式数据缺失")

    if len(结果.数据信息) > 4:
        raise ValueError(f"宝可梦ID={宝可梦ID} 技能数量超过4个")
    elif len(结果.数据信息) is []:
        raise ValueError(f"宝可梦ID={宝可梦ID} 没有任何招式")

    结果列表 = []
    for i in 结果.数据信息:
        结果列表.append(
            {i: 会话.json管理器.招式.获取招式(i)}
        )

    return 结果列表

def 获取新招式(当前等级, 新等级, 升级可学会招式列表, 会话: session.会话类) -> list:
    新招式数据列表 = []
    for i in 升级可学会招式列表:
        if 当前等级 < i.等级 <= 新等级:
            新招式数据列表.append({i.招式名称: 会话.json管理器.招式.获取招式(i.招式名称)})

    return 新招式数据列表
