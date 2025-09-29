# coding=utf-8
from ..models import result
from ..models.enums import 表名类, 操作类
from ..core import database
from ..services import team_services
from ..utils import text_utils
from ..models.session import 会话类


async def 执行删除队伍方法(
    会话: 会话类,
    队伍序号: int,
    缓存信息: dict
) -> result.结果类:
    结果 = await team_services.返回队伍序号对应队伍ID方法(会话, 队伍序号, 是否包含名称=True)

    if 结果.是否成功:
        if 结果.数据信息:
            队伍ID, 队伍名称 = 结果.数据信息
        else:
            return result.结果类.失败方法(f"似乎序号:{队伍序号}是无效的哦")
    else:
        return result.结果类.失败方法(结果.错误信息)

    if 缓存信息:
        # 已经二次确认了
        if 缓存信息["数据"] == 队伍序号:
            db = await database.获取数据库对象()

            结果列表 = await db.查询方法([
                {
                    "表名": 表名类.用户表,
                    "查询数据": '当前队伍ID',
                    "条件": {
                        "用户ID": 会话.用户qq
                    }
                },
                {
                    "表名": 表名类.队伍成员表,
                    "查询数据": '宝可梦ID',
                    "条件": {
                        "队伍ID": 队伍ID
                    }
                },
                {
                    "表名": 表名类.宝可梦表,
                    "查询数据": ['盒子序号'],
                    "条件": {
                        "用户ID": 会话.用户qq
                    }
                },
            ])

            当前队伍ID = 结果列表[0].数据信息[0]
            宝可梦ID列表 = 结果列表[1].数据信息
            最大盒子序号 = max((x.get('盒子序号') for x in 结果列表[2].数据信息 if x.get('盒子序号') is not None), default=-1)

            任务列表 = []
            if 当前队伍ID == 队伍ID:
                任务列表.append({
                        "表名": 表名类.用户表,
                        "操作": 操作类.更新,
                        "数据": {"当前队伍ID": None},
                        "条件": {"用户ID": 会话.用户qq}
                    })

            for 索引, id in enumerate(宝可梦ID列表):
                任务列表.append(
                    {
                        "表名": 表名类.宝可梦表,
                        "操作": 操作类.更新,
                        "数据": {"盒子序号": 最大盒子序号 + 索引 + 1},
                        "条件": {"主键ID": id}
                    }
                )

            任务列表.append(
                {
                    "表名": 表名类.队伍信息表,
                    "操作": 操作类.删除,
                    "条件": {"队伍ID": 队伍ID}
                }
            )

            结果 = await db.写入方法(任务列表)

            if 结果.是否成功:
                return result.结果类.失败方法(f"成功删除序号为{队伍序号}的队伍了")
            else:
                return result.结果类.失败方法("奇怪, 居然删除失败了")
        else:
            return result.结果类.失败方法("等等, 两次输入的队伍序号不一样啦")

    return 结果.成功方法((队伍序号, 队伍名称))

async def 执行切换队伍方法(
    会话: 会话类,
    队伍序号或名称: str
) -> result.结果类:
    if 队伍序号或名称.isdigit():
        结果 = await team_services.返回队伍序号对应队伍ID方法(会话.用户qq, int(队伍序号或名称), 是否包含名称=True)

        if 结果.是否成功:
            if 结果.数据信息:
                队伍ID, 队伍名称 = 结果.数据信息
            else:
                return result.结果类.失败方法(f"似乎序号:{队伍序号或名称}是无效的哦")
        else:
            print("获取队伍ID时发生了错误" + 结果.错误信息)
            return result.结果类.失败方法("获取队伍ID时发生了错误")
    else:
        db = await database.获取数据库对象()

        结果 = await db.单次查询方法(
            {
                "表名": 表名类.队伍信息表,
                "查询数据": ['队伍ID', '队伍名称'],
                "条件": {
                    "用户ID": 会话.用户qq
                }
            }
        )

        if 结果.是否成功:
            队伍信息 = 结果.数据信息

            结果 = text_utils.名称模糊匹配方法(
                [i['队伍名称'] for i in 队伍信息],
                队伍序号或名称,
                是否返回索引=True
            )

            if 结果.是否成功:
                队伍名称, 索引 = 结果.数据信息
                队伍ID = 队伍信息[索引]['队伍ID']
            else:
                return result.结果类.失败方法(结果.错误信息)
        else:
            return result.结果类.失败方法("查询队伍信息时发生了错误")

    # 尝试切换队伍
    return await team_services.队伍切换方法(
        队伍ID=队伍ID,
        队伍名称=队伍名称,
        会话=会话
    )


async def 执行查看队伍信息方法(会话: 会话类) -> result.结果类:
    结果 = await team_services.判断用户是否存在队伍方法(会话)

    if not 结果.数据信息:
        return result.结果类.失败方法("没有找到队伍哦\n可以使用「/pm 新建队伍」")
    else:
        全部队伍id: list = 结果.数据信息

    结果 = await team_services.获取用户当前队伍信息方法(会话.用户qq)
    if 结果.是否成功:
        队伍信息 = 结果.数据信息[0]
        当前队伍ID = 结果.数据信息[1]
    else:
        return 结果

    队伍真实序号 = 全部队伍id.index(当前队伍ID) + 1

    if not 队伍信息:
        return result.结果类.失败方法("队伍中没有找到宝可梦\n使用「/pm 入队」可以添加哦")

    db = await database.获取数据库对象()

    结果 = await db.单次查询方法(
        {
            "表名": 表名类.队伍信息表,
            "查询数据": "队伍名称",
            "条件": {
                "队伍ID": 当前队伍ID
            }
        }
    )

    if not 结果.是否成功:
        print(f"队伍名称查询失败" + 结果.错误信息)
        return result.结果类.失败方法("失误了, 没有找到队伍名称")

    return result.结果类.成功方法((结果.数据信息[0], 队伍真实序号, 队伍信息))

async def 添加宝可梦入队方法(会话: 会话类, 盒子序号: int, 队伍序号: int) -> result.结果类:
    if 队伍序号 is None:
        结果 = await team_services.获取当前队伍ID方法(会话.用户qq)

        if 结果.是否成功:
            队伍ID = 结果.数据信息
        else:
            return 结果.失败方法(str(结果.错误信息))

    else:
        结果 = await team_services.返回队伍序号对应队伍ID方法(会话.用户qq, 队伍序号)

        if 结果.是否成功:
            if 结果.数据信息:
                队伍ID = 结果.数据信息
            else:
                return 结果.失败方法(f"似乎序号:{队伍序号}是无效的哦")
        else:

            return 结果.失败方法("获取队伍ID时发生了错误")

    db = await database.获取数据库对象()

    # 查询对应的宝可梦
    结果 = await db.单次查询方法(
        {
            "表名": 表名类.宝可梦表,
            "查询数据": "主键ID",
            "条件": {
                "用户ID": 会话.用户qq,
                "盒子序号": "NOT NULL",
                "排序": "盒子序号 ASC"
            }
        }
    )

    # 将用户输入的序号转为索引, 这样允许数据库的盒子序号为空值, 也无需批量修改序号, 无需保持连续
    if 盒子序号 < 1:
        return 结果.失败方法("无效的序号哦, 序号从1开始")
    elif 盒子序号 > len(结果.数据信息):
        return 结果.失败方法(f"不行呢, 你的盒子里只有{len(结果.数据信息)}只宝可梦哦")

    if 结果.是否成功:
        宝可梦ID = 结果.数据信息[盒子序号 - 1]
    else:
        return 结果.失败方法("查询盒子里的宝可梦时遭遇意外了")

    # 获取队伍里的最大位置
    结果 = await db.单次查询方法(
        {
            "表名": 表名类.队伍成员表,
            "查询数据": "位置索引",
            "条件": {
                "队伍ID": 队伍ID,
                '排序': '位置索引 DESC'
            }
        }
    )

    if 结果.是否成功:
        if 结果.数据信息:
            位置索引 = max(结果.数据信息) + 1
        else:
            # 说明队伍为空
            位置索引 = 0

    else:
        return 结果.失败方法("查询队伍信息时遭遇意外了")

    if 位置索引 > 5:
        return 结果.失败方法("不行啦, 这个队伍已经满员了\n可以使用`/pm 新建队伍` 或者 `/pm 离队` 哦")

    结果 = await db.写入方法([
        {
            "表名": 表名类.队伍成员表,
            "操作": 操作类.插入,
            "数据": {
                "队伍ID": 队伍ID,
                "宝可梦ID": 宝可梦ID,
                "位置索引": 位置索引
            }
        },
        {
            "表名": 表名类.宝可梦表,
            "操作": 操作类.更新,
            "数据": {"盒子序号": None},
            "条件": {"主键ID": 宝可梦ID}
        }
    ])

    if 结果.是否成功:
        return result.结果类.成功方法("宝可梦入队成功啦, 使用`/pm 队伍` 可以查看哦")
    else:
        print("宝可梦入队失败: "+结果.错误信息)
        return result.结果类.失败方法("宝可梦入队失败了")

async def 执行宝可梦离队方法(会话: 会话类, 位置序号: int, 队伍序号: int = None, 队伍ID: int = None) -> result.结果类:
    """
    使指定位置的宝可梦离开队伍，并将其安全移入盒子。
    """
    try:
        if 队伍ID is None:
            if 队伍序号 is None:
                # 采用默认队伍
                结果 = await team_services.获取当前队伍ID方法(会话.用户qq)
                if not 结果.是否成功:
                    return 结果.失败方法(结果.错误信息)  # 直接返回外部方法的错误结果
                队伍ID = 结果.数据信息
            else:
                # 采用指定序号的队伍
                结果 = await team_services.返回队伍序号对应队伍ID方法(会话.用户qq, 队伍序号)
                if not 结果.是否成功 or not 结果.数据信息:
                    return 结果.失败方法(f"似乎序号:{队伍序号}是无效的哦")
                队伍ID = 结果.数据信息
    except Exception as e:
        return result.结果类.失败方法(f"获取队伍ID时发生意外错误: {e}")

    db = await database.获取数据库对象()

    # 查询对应的宝可梦
    结果列表 = await db.查询方法([
        {
            "表名": 表名类.队伍成员表,
            "查询数据": "宝可梦ID",
            "条件": {
                "队伍ID": 队伍ID,
            }
        },
        {
            "表名": 表名类.宝可梦表,
            "查询数据": "盒子序号",
            "条件": {
                "用户ID": 会话.用户qq,
                "盒子序号": "NOT NULL",
            }
        }
    ])

    宝可梦ID结果 = 结果列表[0]
    盒子序号结果 = 结果列表[1]

    if 宝可梦ID结果.是否成功:
        if len(宝可梦ID结果.数据信息) >= 位置序号:
            宝可梦ID = 宝可梦ID结果.数据信息[位置序号 - 1]
        else:
            return result.结果类.失败方法(f"不行, 当前队伍只有{len(宝可梦ID结果.数据信息)}只宝可梦哦")
    else:
        print("队伍成员表查询失败: " + 宝可梦ID结果.错误信息)
        return result.结果类.失败方法(f"队伍成员结果查询失败")

    if 盒子序号结果.是否成功:
        if 盒子序号结果.数据信息:  # 检查数据是否非空
            盒子序号 = max(盒子序号结果.数据信息) + 1
        else:
            盒子序号 = 1
    else:
        print("盒子序号查询失败: " + 盒子序号结果.错误信息)
        return result.结果类.失败方法(f"盒子序号结果查询失败")

    结果 = await db.写入方法([
        {
            "表名": 表名类.宝可梦表,
            "操作": 操作类.更新,
            "数据": {"盒子序号": 盒子序号},
            "条件": {"主键ID": 宝可梦ID}
        },
        {
            "表名": 表名类.队伍成员表,
            "操作": 操作类.删除,
            "条件": {"队伍ID": 队伍ID, "宝可梦ID": 宝可梦ID}
        }
    ])

    if 结果.是否成功:
        return result.结果类.成功方法(f"宝可梦已成功离开队伍，并返回盒子！")
    else:
        print("离队失败"+结果.错误信息)
        return result.结果类.失败方法(f"宝可梦离队失败了")