# coding=utf-8
from ..models import result
from ..models.enums import 操作类, 表名类
from ..core import database
from ..game import bag, item_effects
from ..utils import text_utils
from ..models.session import 会话类
async def 查询用户物品方法(用户qq: int) -> result.结果类:

    db = await database.获取数据库对象()
    return await db.单次查询方法(
        {
            "表名": 表名类.用户物品表,
            "查询数据": ['物品名称', '数量'],
            "条件": {
                "用户ID": 用户qq
            }
        }
    )

async def 执行使用物品方法(
    会话: 会话类,
    物品名称: str,
    数量或序号: str
) -> result.结果类:
    用户背包对象 = await bag.背包管理类.create(会话=会话)

    结果 = text_utils.名称模糊匹配方法([i for i in 用户背包对象.用户道具数量字典.keys()], 物品名称, 是否返回索引=False)

    if 结果.是否成功:
        匹配名称 = 结果.数据信息
    else:
        return result.结果类.失败方法(结果.错误信息)

    用户现有数量 = 用户背包对象.用户道具数量字典[匹配名称]

    # 将 数量或序号 传递给核心效果方法
    结果 = await item_effects.道具生效方法(会话, 匹配名称, 数量或序号, 用户现有数量)

    if 结果.是否成功:
        return result.结果类.成功方法(结果.数据信息)
    else:
        return result.结果类.失败方法(结果.错误信息)