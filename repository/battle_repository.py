# coding=utf-8
from ..core import database
from ..models import result
from ..models.enums import 表名类, 操作类
from ..models.session import 会话类
from ..models import increment
from ..repository import pokemon_repository, user_repository
from ..utils import text_utils


async def 战斗奖励发放方法(会话: 会话类, 当前队伍ID: int, 奖励字典: dict) -> result.结果类:
    db = await database.获取数据库对象()

    # 初始化操作列表和文案列表
    操作列表 = []
    文案列表 = []

    # 处理金钱奖励
    获得的金钱 = 奖励字典.get("金钱", 0)
    if 获得的金钱 > 0:
        操作列表.append(await user_repository.更新用户金钱方法(会话.用户qq, increment.增量类(获得的金钱)))
        金钱变量字典 = {"金钱": 获得的金钱}
        文案列表.append(会话.json管理器.随机文案.获取随机文案("获得金钱", 金钱变量字典))

    # 查询队伍中的宝可梦
    结果列表 = await db.查询方法([
        {
            "表名": 表名类.队伍成员表,
            "查询数据": "宝可梦ID",
            "条件": {"队伍ID": 当前队伍ID}
        },
        {
            "表名": 表名类.宝可梦表,
            "查询数据": "昵称",
            "条件": {"主键ID": ("索引", 0)}
        }
    ])

    宝可梦ID结果 = 结果列表[0]
    宝可梦昵称结果 = 结果列表[1]

    if not 宝可梦ID结果.是否成功 or not 宝可梦昵称结果.是否成功:
        return result.结果类.失败方法("查询用户当前队伍中的宝可梦失败了，或者查询昵称失败。")

    # 迭代处理每只宝可梦的经验奖励
    获得的经验 = 奖励字典.get("经验值", 0)

    if 获得的经验 > 0:
        for 宝可梦ID, 宝可梦昵称 in zip(宝可梦ID结果.数据信息, 宝可梦昵称结果.数据信息):
            计算结果 = await pokemon_repository.计算经验与相关操作方法(会话, 宝可梦ID, 获得的经验)

            if not 计算结果.是否成功:
                print(f"为宝可梦 {宝可梦昵称}(ID: {宝可梦ID}) 计算经验时失败: {计算结果.错误信息}")
                continue

            if 计算结果.数据信息:
                单个宝可梦操作列表, 文案信息 = 计算结果.数据信息
            else:
                # 一般是等级大于100, 无需增加经验值
                continue

            操作列表.extend(单个宝可梦操作列表)

            文案信息["宝可梦昵称"] = 宝可梦昵称

            单个宝可梦奖励事件列表 = text_utils.构造宝可梦奖励文案(文案信息, 获得的经验)

            for 识别码, 变量字典 in 单个宝可梦奖励事件列表:
                文案 = 会话.json管理器.随机文案.获取随机文案(识别码, 变量字典)
                文案列表.append(文案)

    # 执行所有数据库操作
    if not 操作列表:
        return result.结果类.成功方法(["战斗结束了，但没有获得任何奖励。"])

    写入结果 = await db.写入方法(操作列表)

    if 写入结果.是否成功:
        return result.结果类.成功方法(文案列表)
    else:
        print(f"战斗奖励发放失败: {写入结果.错误信息}")
        return 写入结果.失败方法("发放战斗奖励时，数据库发生未知错误！")
