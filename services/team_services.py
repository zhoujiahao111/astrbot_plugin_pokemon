# coding=utf-8
from ..models import result, increment
from ..core import database
from ..models.enums import 表名类, 操作类
from ..models.session import 会话类
from ..services import team_services

async def 队伍切换方法(队伍ID: int, 队伍名称: str, 会话: 会话类) -> result.结果类:
    db = await database.获取数据库对象()
    
    结果 = await db.写入方法([
        {
            "表名": 表名类.用户表,
            "操作": 操作类.更新,
            "数据": {"当前队伍ID": 队伍ID},
            "条件": {"用户ID": 会话.用户qq}
        }
    ])

    if 结果.是否成功:
        return result.结果类.成功方法(f"成功切换成名称为{队伍名称}的队伍, 使用`/pm 队伍` 可以查看队伍详情哦")
    else:
        return result.结果类.失败方法("唉, 队伍切换失败了")


async def 获取未加入队伍宝可梦(会话: 会话类) -> result.结果类:
    db = await database.获取数据库对象()

    结果 = await db.单次查询方法(
        {
            "表名": 表名类.宝可梦表,
            "查询数据": ["主键ID", "编号", "昵称", "经验", "天赋", "盒子序号"],
            "条件": {
                "用户ID": 会话.用户qq,
                "盒子序号": "NOT NULL"
            }
        }
    )

    if not 结果.是否成功:
        return 结果

    for 宝可梦信息 in 结果.数据信息:
        宝可梦 = 会话.json管理器.宝可梦图鉴.根据编号获取宝可梦(宝可梦信息["编号"])
        宝可梦信息["成长速度"] = 宝可梦.成长速度

    return 结果

async def 判断用户是否存在队伍方法(会话: 会话类) -> result.结果类:
    db = await database.获取数据库对象()

    return await db.单次查询方法(
        {
            "表名": 表名类.队伍信息表,
            "查询数据": "队伍ID",
            "条件": {
                "用户ID": 会话.用户qq,
            }
        }
    )

async def 获取用户当前队伍信息方法(
    用户qq: int,
    是否返回队伍ID: bool = True,
    是否返回队伍名称: bool = False,
    是否返回队伍长度: bool = False,
) -> result.结果类:

    结果 = await 获取当前队伍ID方法(用户qq)

    if 结果.是否成功:
        if 结果.数据信息:
            当前队伍ID = 结果.数据信息
        else:
            return result.结果类.失败方法("没有正在使用的队伍哦, 建议使用「/pm 切换 [队伍名称或序号]」来指定队伍")
    else:
        return result.结果类.失败方法("查询用户的当前队伍时出错了")

    db = await database.获取数据库对象()

    结果 = await db.join查询方法(
        查询字段=[db.获取数据表方法(表名类.宝可梦表)],
        主模型=表名类.队伍成员表,
        连接信息=[
            {
                "模型": 表名类.宝可梦表,
                "条件": db.获取数据表方法(表名类.队伍成员表).宝可梦ID == db.获取数据表方法(表名类.宝可梦表).主键ID,
                "类型": "INNER"
            }
        ],
        筛选条件=[db.获取数据表方法(表名类.队伍成员表).队伍ID == 当前队伍ID]
    )

    if 结果.是否成功:
        队伍信息 = 结果.数据信息
    else:
        return result.结果类.失败方法("查询宝可梦信息时出错了")

    返回列表 = [队伍信息]
    if 是否返回队伍ID:
        返回列表.append(当前队伍ID)

    if 是否返回队伍名称:
        结果 = await db.单次查询方法(
            {
                "表名": 表名类.队伍信息表,
                "查询数据": "队伍名称",
                "条件": {
                    "队伍ID": 当前队伍ID
                }
            }
        )

        if 结果.是否成功:
            返回列表.append(结果.数据信息[0])
        else:
            return result.结果类.失败方法("查询队伍名称时出错了")

    if 是否返回队伍长度:
        返回列表.append(len(队伍信息))

    return result.结果类.成功方法(返回列表)


async def 获取全部队伍信息方法(会话: 会话类, 页数: int) -> result.结果类:
    db = await database.获取数据库对象()

    结果 = await db.单次查询方法(
        {
            "表名": 表名类.队伍信息表,
            "查询数据": "队伍ID",
            "条件": {
                "用户ID": 会话.用户qq
            }
        }
    )

    if not 结果.是否成功:
        return result.结果类.失败方法("统计用户所有队伍时出错了")

    队伍数量 = len(set(结果.数据信息))

    if 队伍数量 == 0:
        return result.结果类.失败方法("还没有创建队伍哦, 可以使用`/pm 新建队伍 [队伍名称]` ")

    每页数量 = 4
    最大页数 = (队伍数量 + 每页数量 - 1) // 每页数量
    页数 = min(最大页数, max(1, 页数))

    结果 = await db.单次查询方法(
        {
            "表名": 表名类.队伍信息表,
            "查询数据": ["队伍ID", "队伍名称", "队伍序号"],
            "条件": {
                "用户ID": 会话.用户qq,
                "分页大小": 每页数量,
                "页码": 页数,
                "排序": "队伍序号 ASC"
            }
        }
    )

    if 结果.是否成功:
        队伍信息列表 = 结果.数据信息
    else:
        return result.结果类.失败方法("查询所有队伍时出错了")

    队伍ID列表 = [队伍['队伍ID'] for 队伍 in 队伍信息列表]

    if not 队伍ID列表:
        return result.结果类.成功方法("该页没有队伍信息。")

    # 获取所有相关宝可梦
    队伍信息表_obj = db.获取数据表方法(表名类.队伍信息表)
    队伍成员表_obj = db.获取数据表方法(表名类.队伍成员表)
    宝可梦表_obj = db.获取数据表方法(表名类.宝可梦表)

    结果 = await db.join查询方法(
        查询字段=[
            队伍信息表_obj.队伍ID,
            宝可梦表_obj.昵称,
            宝可梦表_obj.经验,
            宝可梦表_obj.编号
        ],
        主模型=表名类.队伍信息表,
        连接信息=[
            {
                "模型": 表名类.队伍成员表,
                "条件": 队伍信息表_obj.队伍ID == 队伍成员表_obj.队伍ID,
                "类型": "LEFT"
            },
            {
                "模型": 表名类.宝可梦表,
                "条件": 队伍成员表_obj.宝可梦ID == 宝可梦表_obj.主键ID,
                "类型": "LEFT"
            }
        ],
        筛选条件=[队伍信息表_obj.队伍ID.in_(队伍ID列表)],
        排序规则=[
            队伍信息表_obj.队伍序号.asc(),
            队伍成员表_obj.位置索引.asc()
        ],
        分页大小=None,
        页码=1
    )

    if not 结果.是否成功:
        return result.结果类.失败方法("获取队伍中的宝可梦信息失败")

    宝可梦按队伍分组 = {}

    for 记录 in 结果.数据信息:
        if 记录.get('昵称') is not None:
            队伍ID = 记录['队伍ID']

            if 队伍ID not in 宝可梦按队伍分组:
                宝可梦按队伍分组[队伍ID] = []

            宝可梦信息 = {
                '昵称': 记录['昵称'],
                '经验': 记录['经验'],
                '编号': 记录['编号']
            }
            宝可梦按队伍分组[队伍ID].append(宝可梦信息)

    最终格式化列表 = []
    for 队伍 in 队伍信息列表:
        当前队伍ID = 队伍['队伍ID']

        新队伍条目 = 队伍.copy()
        新队伍条目['宝可梦列表'] = 宝可梦按队伍分组.get(当前队伍ID, [])

        最终格式化列表.append(新队伍条目)

    return result.结果类.成功方法((最终格式化列表, 页数))

async def 获取当前队伍ID方法(用户qq) -> result.结果类:
    """直接返回id本身或报错"""
    db = await database.获取数据库对象()

    结果 = await db.单次查询方法(
        {
            "表名": 表名类.用户表,
            "查询数据": "当前队伍ID",
            "条件": {
                "用户ID": 用户qq
            }
        }
    )

    if 结果.是否成功:
        return 结果.成功方法(结果.数据信息[0])
    else:
        return 结果.失败方法(结果.错误信息)

async def 返回队伍序号对应队伍ID方法(用户qq: int, 队伍序号: int, 是否包含名称: bool = False) -> result.结果类:
    db = await database.获取数据库对象()

    结果 = await db.单次查询方法(
        {
            "表名": 表名类.队伍信息表,
            "查询数据": ["队伍ID", "队伍名称"] if 是否包含名称 else "队伍ID",
            "条件": {
                "用户ID": 用户qq
            }
        }
    )

    if 结果.是否成功:
        try:
            try:
                队伍信息 = 结果.数据信息[队伍序号 - 1]
            except:
                return 结果.失败方法("不对, 你没有这么多队伍哦")

            if 是否包含名称:
                return 结果.成功方法([队伍信息["队伍ID"], 队伍信息["队伍名称"]])
            else:
                return 结果.成功方法(队伍信息["队伍ID"])

        except Exception as e:
            return 结果.失败方法("序号映射ID时匹配时出错: " + str(e))
    else:
        return 结果.失败方法("查询队伍信息时遭遇意外了")

