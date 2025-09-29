# coding=utf-8
from ..services import pokemon_services, player_services, team_services
from ..models import result
from ..game import bag, pokemon
from ..models.session import 会话类

async def 返回双方对战相关对象方法(
    会话: 会话类,
    敌人qq: int
) -> result.结果类:
    结果 = await player_services.判断用户是否注册方法(用户qq=敌人qq)
    if not 结果.数据信息:
        return result.结果类.失败方法("对方还没有注册为训练师哦")

    结果 = await team_services.获取用户当前队伍信息方法(会话.用户qq, 是否返回队伍ID=True, 是否返回队伍名称=True)

    if 结果.是否成功 and 结果.数据信息:
        本方宝可梦信息列表 = 结果.数据信息[0]
        本方队伍ID = 结果.数据信息[1]
        本方队伍名称 = 结果.数据信息[2]
    else:
        return result.结果类.失败方法("查询用户队伍信息失败")

    if not 本方宝可梦信息列表:
        return result.结果类.失败方法("_(´□`」 ∠)_ 这个队伍里还没有宝可梦, 被对方狠狠教训了")

    结果 = await pokemon_services.队伍批量转宝可梦对象方法(
        宝可梦信息列表=本方宝可梦信息列表,
        会话=会话
    )

    if 结果.是否成功:
        本方宝可梦对象列表 = 结果.数据信息
    else:
        return result.结果类.失败方法(结果.错误信息)

    结果 = await team_services.获取用户当前队伍信息方法(敌人qq, 是否返回队伍ID=False, 是否返回队伍名称=True)

    if 结果.是否成功 and 结果.数据信息:
        对方宝可梦信息列表 = 结果.数据信息[0]
        对方队伍名称 = 结果.数据信息[1]
    else:
        return result.结果类.失败方法("查询用户队伍信息失败")

    if not 对方宝可梦信息列表:
        return result.结果类.失败方法("对方队伍里还没有宝可梦, 不能趁人之危啦")

    结果 = await pokemon_services.队伍批量转宝可梦对象方法(
        宝可梦信息列表=对方宝可梦信息列表,
        会话=会话
    )

    if 结果.是否成功:
        对方宝可梦对象列表 = 结果.数据信息
    else:
        return result.结果类.失败方法(结果.错误信息)

    本方背包对象 = await bag.背包管理类.create(会话=会话)

    对方背包对象 = await bag.背包管理类.create(会话=会话)

    return 结果.成功方法({
        "本方宝可梦对象列表": 本方宝可梦对象列表,
        "对方宝可梦对象列表": 对方宝可梦对象列表,
        "本方背包对象": 本方背包对象,
        "对方背包对象": 对方背包对象,
        "本方队伍名称": 本方队伍名称,
        "对方队伍名称": 对方队伍名称,
        "本方队伍ID": 本方队伍ID
    })


async def 返回双方宝可梦最终属性方法(
    本方上场宝可梦对象: pokemon.宝可梦类,
    对方上场宝可梦对象: pokemon.宝可梦类,
    本方背包对象: bag.背包管理类,
    对方背包对象: bag.背包管理类,
    天气属性倍率字典: dict
) -> tuple[dict, dict]:
    结果 = await 本方背包对象.返回宝可梦属性倍率方法()

    if 结果.是否成功:
        本方最终属性字典 = pokemon_services.返回倍率影响后的属性方法(
            当前属性字典=本方上场宝可梦对象.当前属性字典,
            倍率字典=结果.数据信息,
            宝可梦属性列表=本方上场宝可梦对象.宝可梦属性列表,
            天气属性倍率字典=天气属性倍率字典,
            mega是否开启=本方上场宝可梦对象.mega是否开启
        )
    else:
        print("获取属性加成时出错", 结果.错误信息)
        本方最终属性字典 = 本方上场宝可梦对象.当前属性字典

    结果 = await 对方背包对象.返回宝可梦属性倍率方法()
    if 结果.是否成功:
        对方最终属性字典 = pokemon_services.返回倍率影响后的属性方法(
            当前属性字典=对方上场宝可梦对象.当前属性字典,
            倍率字典=结果.数据信息,
            宝可梦属性列表=本方上场宝可梦对象.宝可梦属性列表,
            天气属性倍率字典=天气属性倍率字典,
            mega是否开启=对方上场宝可梦对象.mega是否开启
        )
    else:
        print("获取属性加成时出错", 结果.错误信息)
        对方最终属性字典 = 对方上场宝可梦对象.当前属性字典

    return 本方最终属性字典, 对方最终属性字典
