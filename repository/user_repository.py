# coding=utf-8
from ..models import increment
from ..models.enums import 表名类, 操作类
from ..core import database


def 更新用户金钱方法(用户qq: int, 修改值: int | increment.增量类) -> dict:
    """
    更新用户金钱的增加操作
    """

    return {
        "表名": 表名类.用户表,
        "操作": 操作类.更新,
        "数据": {"金钱": 修改值},
        "条件": {"用户ID": 用户qq}
    }


async def 获取用户宝可梦总数方法(会话) -> int:
    db = await database.获取数据库对象()

    结果 = await db.单次查询方法(
        {
            "表名": 表名类.宝可梦表,
            "查询数据": "主键ID",
            "条件": {
                "用户ID": 会话.用户qq,
            }
        }
    )

    if 结果.是否成功:
        return len(结果.数据信息)
    else:
        print("获取用户宝可梦总数时发生奇怪的错误: "+结果.错误信息)
        return -1
