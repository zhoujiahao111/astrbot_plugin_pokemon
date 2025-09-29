# coding=utf-8
from ..models import result
from ..models.enums import 领养阶段类, 缓存类型类, 表名类, 操作类
from ..core import database
from ..game import bag
from ..utils import text_utils
from ..models import increment
from ..models.session import 会话类
from ..dtos import 道具管理器

async def 购买商品方法(
    会话: 会话类,
    数量: int,
    输入名称: str
) -> result.结果类:
    """物品ID是道具.json的索引!从0开始, 而商店指令里的物品ID是序号, 从1开始, 注意区分"""
    结果 = text_utils.名称模糊匹配方法(
        [i for i in 会话.json管理器.道具.获取所有物品名称()], 输入名称, 是否返回索引=True
    )

    if 结果.是否成功:
        名称, 索引 = 结果.数据信息
    else:
        return result.结果类.失败方法(结果.错误信息)

    道具模型 = 会话.json管理器.道具.根据索引获取物品(索引)
    商品价格: int = 道具模型.价格
    能否重复购买: bool = 道具模型.能否重复购买

    if 数量 < 1:
        return result.结果类.失败方法(f"等等, 这是什么意思? 买{数量}个???")

    db = await database.获取数据库对象()

    结果列表 = await db.查询方法([
        {
            "表名": 表名类.用户表,
            "查询数据": '金钱',
            "条件": {
                "用户ID": 会话.用户qq
            }
        },
        {
            "表名": 表名类.用户物品表,
            "查询数据": "数量",
            "条件": {
                "物品名称": 名称,
                "用户ID": 会话.用户qq
            }
        }
    ])
    金钱结果 = 结果列表[0]
    数量结果 = 结果列表[1]

    if 金钱结果.是否成功:
        余额: int = 金钱结果.数据信息[0]
    else:
        return result.结果类.失败方法("出错了, 查询用户余额时失误")

    if 余额 < 商品价格 * 数量:
        变量字典 = {"总价": 商品价格 * 数量, "余额": 余额, "差值": (商品价格 * 数量) - 余额}
        return result.结果类.成功方法(
            会话.json管理器.随机文案.获取随机文案("购买商品余额不足", 变量字典)
        )
    if 数量结果.是否成功:
        if 数量结果.数据信息:
            现有数量: int = 数量结果.数据信息[0]
        else:
            现有数量 = 0
    else:
        return result.结果类.失败方法("不好, 查询商品数量时出错了")

    # 判断能不能重复购买
    if not 能否重复购买:
        if 现有数量:
            return result.结果类.失败方法("不给! 这个商品不能重复购买哦")
        if 数量 > 1:
            return result.结果类.失败方法("不行, 这个商品只能拥有一个哦")

    # 开始购买
    结果 = await db.写入方法([
        {
            "表名": 表名类.用户表,
            "操作": 操作类.更新,
            "数据": {"金钱": increment.增量类(-商品价格 * 数量)},
            "条件": {"用户ID": 会话.用户qq}
        },
        {
            "表名": 表名类.用户物品表,
            "操作": 操作类.更新或写入,
            "数据": {"数量": increment.增量类(数量)},
            "条件": {"用户ID": 会话.用户qq, "物品名称": 名称}
        },
    ]
    )

    if 结果.是否成功:
        文案字典 = {
            "数量": 数量,
            "已有数量": 现有数量,
            "购买后数量": 数量+现有数量,
            "名称": 名称,
            "量词": 道具模型.量词
        }
        return result.结果类.成功方法(
            会话.json管理器.随机文案.获取随机文案("道具购买成功", 文案字典)
        )
    else:
        return result.结果类.失败方法("购买失败! 请联系管理员")


def 返回道具名称对应索引方法(道具管理器: 道具管理器, 名称: str) -> int:
    raise RuntimeError("这是一个废弃的方法")
    # for 索引, 物品名称 in enumerate(道具管理器.获取所有物品名称()):
    #     if 物品名称 == 名称:
    #         return 索引
    # return -1
