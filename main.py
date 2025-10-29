# coding=utf-8
import asyncio
import math
from concurrent.futures import ThreadPoolExecutor
import astrbot.api.event.filter as filter
from astrbot.api.all import AstrMessageEvent, MessageChain, Image, Plain, Node, Reply, At, Nodes
from astrbot.api.star import Context, Star, register

import inspect
from functools import wraps
import time

from .core import json_manager
from .utils import image_utils, text_utils, validators
from .repository import pokemon_repository, battle_repository, team_repository, item_repository, user_repository
from .game import bag, battle
from .services import player_services, bag_services, image_data_services, pokemon_services, team_services, \
    battle_services
from .models.session import 会话类
from .models.enums import 领养阶段类, 缓存类型类

def 检查用户注册状态(func):
    @wraps(func)
    async def wrapper(self, 事件: AstrMessageEvent, *args, **kwargs):

        用户qq = validators.验证用户qq方法(事件.get_sender_id())
        结果 = await player_services.判断用户是否注册方法(用户qq=用户qq)

        if not 结果.数据信息:
            yield 事件.plain_result("您还没有获取第一只宝可梦伙伴哦\n使用「/pm 领养」即可")
            return

        # 调用原始函数，但先不 await，以获取其返回的协程或异步生成器对象
        目标对象 = func(self, 事件, *args, **kwargs)

        # 检查返回的是否为异步生成器
        if inspect.isasyncgen(目标对象):
            # 如果是异步生成器，使用 async for 迭代并逐个 yield 其产生的值
            async for item in 目标对象:
                yield item
        else:
            结果 = await 目标对象
            if 结果 is not None:
                yield 结果

    return wrapper


def 会话初始化(函数):
    @wraps(函数)
    async def 初始化(self, 事件: AstrMessageEvent, *args, **kwargs):
        会话 = 会话类(
            json管理器=self.json管理器,
            配置=self.配置,
            事件=事件
        )
        事件.会话 = 会话

        async for item in 函数(self, 事件, *args, **kwargs):
            yield item

    return 初始化


@register("astrbot_plugin_pokemon", "周佳豪", "宝可梦插件, 文字版宝可梦游戏", "1.0.0",
          "https://www.bilibili.com/video/BV16p4y1w7U3/")
class 宝可梦插件类(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.通用操作缓存: dict = {}
        self.通用操作缓存_锁 = asyncio.Lock()

        self.线程池 = ThreadPoolExecutor()

        self.json管理器 = json_manager.json管理器()

        self.配置 = config

        self.缓存超时时长 = config.get("cache_max_timeout", 120)

        asyncio.create_task(self._清理缓存方法())
        

    async def _清理缓存方法(self):
        """
        定时清理所有用户的过期缓存项。
        """
        while True:
            await asyncio.sleep(self.缓存超时时长)

            当前时间 = time.time()
            待处理的过期项 = []

            async with self.通用操作缓存_锁:
                空的qq键列表 = []
                # 遍历每个用户
                for qq, 用户操作集 in self.通用操作缓存.items():
                    # 找到该用户所有已过期的操作类型

                    过期的操作类型列表 = [
                        操作类型 for 操作类型, 信息 in 用户操作集.items()
                        if 信息["到期时间"] < 当前时间
                    ]

                    # 移除过期的操作
                    for 操作类型 in 过期的操作类型列表:
                        信息 = 用户操作集.pop(操作类型)
                        待处理的过期项.append((信息["事件"], 操作类型, qq))

                    # 如果一个用户的所有操作都已过期并被移除，则标记这个用户以便从顶层缓存中删除
                    if not 用户操作集:
                        空的qq键列表.append(qq)

                # 清理没有任何待处理操作的用户
                for qq in 空的qq键列表:
                    del self.通用操作缓存[qq]

            # 在锁之外处理网络IO，避免长时间阻塞
            for 事件, 消息类型, qq in 待处理的过期项:
                try:
                    if 消息类型 is 缓存类型类.领养宝可梦:
                        输出 = "时间过去太久了, 请重新使用「/pm 领养」 来获取心仪的伙伴吧。"
                    elif 消息类型 is 缓存类型类.删除队伍:
                        输出 = "删除队伍的确认已超时，操作已取消。"
                    else:
                        输出 = "没什么事情, 只是程序可能出错了, 记录了不存在的操作类型"

                    await 事件.send(
                        事件.chain_result([
                            At(qq=qq),
                            Plain(输出)
                        ]))

                except Exception as e:
                    print(f"处理过期项时发生错误: {e}")

    @filter.command_group("pm")
    async def pm(self, event: AstrMessageEvent):
        yield event.plain_result(f"指令存在。")
        return



    @pm.command("领养", alias={"领养", "获取", "领养宝可梦"})
    @会话初始化
    async def 领养宝可梦方法(self, 事件: AstrMessageEvent, 选择: str = None):
        """来领养一只宝可梦吧。"""
        会话: 会话类 = 事件.会话

        注册结果 = await player_services.判断用户是否注册方法(会话.用户qq)

        if 注册结果.数据信息:
            宝可梦总数 = await user_repository.获取用户宝可梦总数方法(会话)

            if 宝可梦总数 > 0:
                yield 事件.plain_result("哎呀~ 训练家已经领取过初始宝可梦了呢！使用 「/pm 队伍」可以查看宝可梦哦")
                return
            elif 宝可梦总数 == -1:
                yield 事件.plain_result("奇怪, 获取你的宝可梦总数时出现了重大错误")
                return

        async with self.通用操作缓存_锁:
            缓存信息: dict = self.通用操作缓存.get(会话.用户qq, {}).get(缓存类型类.领养宝可梦, {})
            当前阶段 = 缓存信息.get("阶段", 领养阶段类.首次执行)
            存储数据 = 缓存信息.get("数据", None)
            已警告 = 缓存信息.get("已警告", False)

            if 选择 is None and 当前阶段 != 领养阶段类.首次执行 and 已警告 == False:
                缓存信息["已警告"] = True
                if 会话.用户qq not in self.通用操作缓存:
                    self.通用操作缓存[会话.用户qq] = {}
                self.通用操作缓存[会话.用户qq][缓存类型类.领养宝可梦] = 缓存信息

                yield 事件.plain_result("再次输入「/pm 领养」将会重新开始选择")
                return

            # 判断并执行状态机阶段返回任务
            elif 选择 == "返回":
                if 当前阶段 is 领养阶段类.首次执行 or 当前阶段 is 领养阶段类.已查看组合:
                    yield 事件.plain_result("当前阶段无需返回哦, 请输入「/pm 领养」来查看组合信息")

                elif 当前阶段 is 领养阶段类.已查看宝可梦信息:
                    self.通用操作缓存[会话.用户qq] = {
                        缓存类型类.领养宝可梦: {
                            "到期时间": time.time() + self.缓存超时时长,
                            "阶段": 领养阶段类.已查看组合,
                            "事件": 事件
                        }
                    }
                    yield 事件.plain_result("成功返回至查看组合信息阶段, 请使用「/pm 领养 组合名称或序号」")
                else:
                    yield 事件.plain_result("当前处于未知阶段, 无法返回, 建议使用两次「/pm 领养」来重置")

                return

                # 缓存无记录 或者 已经警告的情况下继续不携带参数
            elif 当前阶段 is 领养阶段类.首次执行 or (已警告 and 选择 is None):
                yield 事件.plain_result(
                    player_services.输出初始伙伴组合信息方法(会话.json管理器.初始伙伴)
                )

                self.通用操作缓存[会话.用户qq] = {
                    缓存类型类.领养宝可梦: {
                        "到期时间": time.time() + self.缓存超时时长,
                        "阶段": 领养阶段类.已查看组合,
                        "事件": 事件
                    }
                }

                return

            # 第一次查看组合信息, 或者查看过宝可梦详情, 还输入了页数控制参数
            elif 当前阶段 is 领养阶段类.已查看组合 or (
                当前阶段 == 领养阶段类.已查看宝可梦信息 and
                选择 in ["上一页", "下一页"]
            ):
                输出内容, 选择的名称, 是否成功, 新页数 = player_services.输出伙伴组合详细信息方法(
                    会话.json管理器.初始伙伴,
                    会话.json管理器.宝可梦图鉴,
                    选择,
                    存储数据
                )

                if 是否成功:
                    self.通用操作缓存[会话.用户qq] = {
                        缓存类型类.领养宝可梦: {
                            "到期时间": time.time() + self.缓存超时时长,
                            "阶段": 领养阶段类.已查看宝可梦信息,
                            "数据": 选择的名称,
                            "页数": 新页数,
                            "事件": 事件
                        }
                    }

                    节点列表 = []
                    for item in 输出内容:
                        if isinstance(item, str):
                            节点列表.append(
                                Node(
                                    uin=会话.机器人qq,
                                    content=[Plain(item)]
                                )
                            )
                        elif isinstance(item, tuple) and len(item) == 3:
                            贴图数据, 序号, 简介 = item
                            # 把图片和文字一次性塞到同一个 Node 里
                            节点列表.append(
                                Node(
                                    uin=会话.机器人qq,
                                    content=[
                                        Image.fromBytes(贴图数据),  # 图片
                                        Plain(f"#{序号} {简介}")
                                    ]
                                )
                            )
                        else:
                            # 例外的特殊情况, 应该不会执行吧
                            节点列表.append(
                                Node(
                                    uin=会话.机器人qq,
                                    content=[Plain(str(item))]
                                )
                            )

                    yield 事件.chain_result([Nodes(nodes=节点列表)])
                else:
                    # 内容为str格式的报错信息
                    yield 事件.plain_result(输出内容)
                return

            elif 当前阶段 == 领养阶段类.已查看宝可梦信息:
                输出信息, 是否成功 = await player_services.执行用户注册方法(
                    会话=会话,
                    选择=选择,
                    存储数据=存储数据,
                    是否新用户=False if 注册结果.数据信息 else True
                )

                if 是否成功:
                    self.通用操作缓存.pop(会话.用户qq, None)
                yield 事件.plain_result(输出信息)
            else:
                yield 事件.plain_result("奇怪, 看上去出现了比较严重的错误, 建议联系机器人的管理员")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @pm.command("强制改名", alias={"宝可梦强制重命名", "宝可梦强制修改名字"})
    @会话初始化
    async def 宝可梦强制改名方法(self, 事件: AstrMessageEvent, 主键ID: int, 新名称: str):
        """仅限管理员 主键ID是会话.用户qq号 名称无审核"""
        会话: 会话类 = 事件.会话
        结果 = await pokemon_repository.执行宝可梦改名方法(
            会话=会话,
            新名称=新名称,
            主键ID=主键ID,
            是否检测违禁词=False
        )

        yield 事件.plain_result(结果.数据信息 if 结果.是否成功 else 结果.错误信息)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @pm.command("强制添加宝可梦", alias={"宝可梦强制添加", "宝可梦添加", "添加宝可梦"})
    @会话初始化
    async def 强制添加宝可梦方法(self, 事件: AstrMessageEvent, 用户ID: int, 编号: str):
        """仅限管理员 编号是宝可梦图鉴的编号,并非索引"""
        会话: 会话类 = 事件.会话

        if not all([用户ID, 编号]):
            yield 事件.plain_result(
                f"管理员大人, 填写的参数不全哦, 需要输入[用户ID 宝可梦编号(非索引) 队伍ID 队伍位置(0开始,最大为5)]\n不添加队伍和队伍位置时, "
                f"默认放入盒子哦\n使用空格间隔参数, 另外请谨慎使用"
            )
            return

        结果 = pokemon_services.宝可梦生成方法(会话=会话, 编号=编号)

        if 结果.是否成功:
            宝可梦数据: dict = 结果.数据信息
        else:
            print(f"宝可梦生成失败 " + 结果.错误信息)
            yield 事件.plain_result("管理员大人, 宝可梦生成失败了")
            return

        宝可梦数据["用户ID"] = 用户ID

        结果 = await pokemon_services.宝可梦添加方法(
            用户ID=用户ID,
            宝可梦数据=宝可梦数据
        )

        if 结果.是否成功:
            yield 事件.plain_result(
                f"管理员大人, 已成功为用户{用户ID} 添加{宝可梦数据['昵称']}")
        else:
            yield 事件.plain_result(结果.错误信息)

        return

    @pm.command("改名", alias={"改名宝可梦", "宝可梦重命名", "宝可梦修改名字"})
    @检查用户注册状态
    @会话初始化
    async def 宝可梦改名方法(self, 事件: AstrMessageEvent, 位置序号: int, 新名称: str):
        """位置序号是宝可梦在队内的位置哦,从1开始, 名称长度1到10字"""
        会话: 会话类 = 事件.会话

        结果 = await pokemon_repository.执行宝可梦改名方法(
            会话=会话,
            新名称=新名称,
            位置序号=位置序号,
            是否检测违禁词=True
        )

        yield 事件.plain_result(结果.数据信息 if 结果.是否成功 else 结果.错误信息)

    @pm.command("商店", alias={"shop", "查看商店", "宝可梦商店"})
    @检查用户注册状态
    @会话初始化
    async def 查看商店方法(self, 事件: AstrMessageEvent, 页数: int = 1):
        节点列表 = []
        会话: 会话类 = 事件.会话

        所有道具 = 会话.json管理器.道具.获取所有物品()
        道具总数 = len(所有道具)
        单页数量 = 会话.商店聊天记录商品数量

        if 道具总数 == 0:
            yield 事件.plain_result("商店里还没有任何商品哦！")
            return

        # 确保单页数量大于0，避免除零错误
        if 单页数量 <= 0:
            yield 事件.plain_result("错误：商店配置的单页商品数量无效，请联系管理员。")
            return

        总页数 = math.ceil(道具总数 / 单页数量)

        if not (1 <= 页数 <= 总页数):
            yield 事件.plain_result(f"页数无效！当前商店共有 {总页数} 页，请输入 1 到 {总页数} 之间的页码。")
            return

        # 计算当前页的道具起始和结束索引
        起始索引 = (页数 - 1) * 单页数量
        结束索引 = 起始索引 + 单页数量
        本页道具列表 = 所有道具[起始索引:结束索引]

        # 在列表最前面添加页数和翻页提示
        页眉文本 = f"当前是第 {页数}/{总页数} 页\n"
        页眉文本 += f"使用 /pm 商店 <页数> 可跳转页面\n"
        页眉文本 += "--------------------\n"

        is_first_item = True

        for 道具信息 in 本页道具列表:
            结果 = image_utils.读取图片方法(类别="goods", 名称=道具信息.贴图, 是否转为jpg=True)

            if not 结果.是否成功:
                print(f"{道具信息.名称}的贴图读取失败: {结果.错误信息}")
                yield 事件.plain_result(f"糟糕, {道具信息.名称}的图片似乎损坏了, 请联系管理员修复。")
                # 单个商品错误
                return

            贴图数据: bytes = 结果.数据信息
            商品详情 = f"名称: {道具信息.名称}\n💰️: {道具信息.价格}元\n描述: {道具信息.描述}\n\n\n"

            content_list = []
            if is_first_item:
                content_list.append(Plain(页眉文本))
                is_first_item = False

            content_list.extend([
                Image.fromBytes(贴图数据),
                Plain(商品详情)
            ])

            节点列表.append(
                Node(
                    uin=会话.机器人qq,
                    content=content_list
                )
            )

        if 节点列表:
            yield 事件.chain_result([Nodes(nodes=节点列表)])
        else:
            yield 事件.plain_result(f"未能获取第 {页数} 页的商品列表，建议联系管理员。")

    @pm.command("购买", alias={"buy", "购买商品", "购买物品"})
    @检查用户注册状态
    @会话初始化
    async def 商品购买方法(self, 事件: AstrMessageEvent, 名称: str, 数量: int = 1):
        """建议先使用「/pm 商店」查看商品"""
        会话: 会话类 = 事件.会话

        结果 = await bag_services.购买商品方法(
            会话=会话,
            输入名称=名称,
            数量=数量
        )

        if 结果.是否成功:
            yield 事件.plain_result(结果.数据信息)
        else:
            yield 事件.plain_result(结果.错误信息)

    @pm.command("背包", alias={"我的背包", "打开背包", "查看物品"})
    @检查用户注册状态
    @会话初始化
    async def 查看背包方法(self, 事件: AstrMessageEvent):
        """查看背包图片"""
        # 查询用户的物品
        会话 = 事件.会话
        结果 = await item_repository.查询用户物品方法(会话.用户qq)

        if not 结果.是否成功:
            yield 事件.plain_result(结果.错误信息)
            return

        结果 = await asyncio.get_running_loop().run_in_executor(
            self.线程池,
            image_utils.图片生成处理器,
            image_data_services.生成背包图片信息方法,
            结果.数据信息
        )

        if not 结果.是否成功:
            yield 事件.plain_result("查看失败了, 似乎是图片生成时出错了")
            return

        yield 事件.chain_result([
            Image.fromBytes(结果.数据信息)
        ])

    async def 使用物品方法(self, 事件: AstrMessageEvent, 物品名称: str, 数量或序号: int = 1):
        """
        使用背包中的道具。
        """
        会话: 会话类 = 事件.会话

        if 数量或序号 < 1:
            yield 事件.plain_result("数量或序号必须是大于0的整数。")
            return

        结果 = await item_repository.执行使用物品方法(
            会话=会话,
            物品名称=物品名称,
            数量或序号=数量或序号
        )

        yield 事件.plain_result(结果.数据信息 if 结果.是否成功 else 结果.错误信息)

    @pm.command("新建队伍", alias={"创建队伍", "新建队伍", "队伍创建", "建立队伍", "生成队伍"})
    @检查用户注册状态
    @会话初始化
    async def 新建队伍方法(self, 事件: AstrMessageEvent, 名称: str):
        """新建一只队伍,需要名称"""
        会话: 会话类 = 事件.会话

        用户背包对象 = await bag.背包管理类.create(会话=会话)

        结果 = await pokemon_services.新建宝可梦队伍方法(
            会话=会话,
            队伍名称=名称,
            用户背包对象=用户背包对象,
        )

        if 结果.是否成功:
            yield 事件.plain_result(结果.数据信息)
        else:
            yield 事件.plain_result(结果.错误信息)

    @pm.command("删除队伍", alias={"清空队伍", "解体队伍"})
    @检查用户注册状态
    @会话初始化
    async def 删除队伍方法(self, 事件: AstrMessageEvent, 队伍序号: int):
        """输入队伍序号即可删除队伍哦"""
        会话: 会话类 = 事件.会话

        async with self.通用操作缓存_锁:
            用户缓存字典 = self.通用操作缓存.get(会话.用户qq, {})
            缓存信息 = 用户缓存字典.get(缓存类型类.删除队伍, False)

            结果 = await team_repository.执行删除队伍方法(
                会话=会话,
                队伍序号=队伍序号,
                缓存信息=缓存信息
            )

            if 结果.是否成功:
                if 缓存信息:
                    del self.通用操作缓存[会话.用户qq]
                else:
                    用户缓存字典[缓存类型类.删除队伍] = {
                        "到期时间": time.time() + self.缓存超时时长,
                        "数据": 队伍序号,
                        "事件": 事件
                    }
                    self.通用操作缓存[会话.用户qq] = 用户缓存字典
                    yield 事件.plain_result(
                        f"请注意, 这是一个危险的操作!\n请再次确定是否要删除序号:{结果.数据信息[0]}, 名称为{结果.数据信息[1]}的队伍!\n请输入「/pm 删除队伍 {队伍序号}」 来确定删除")
            else:
                yield 事件.plain_result(结果.错误信息)

    @pm.command("切换", alias={"切换队伍", "队伍切换", "使用队伍"})
    @检查用户注册状态
    @会话初始化
    async def 切换队伍方法(self, 事件: AstrMessageEvent, 队伍序号或名称: str):
        """切换用户的默认队伍"""
        会话: 会话类 = 事件.会话

        结果 = await team_repository.执行切换队伍方法(会话, 队伍序号或名称)

        yield 事件.plain_result(结果.数据信息 if 结果.是否成功 else 结果.错误信息)

    @pm.command("队伍", alias={"查看队伍", "查询队伍", "队伍查看", "队伍查询", "查看队伍信息", "队伍信息"})
    @检查用户注册状态
    @会话初始化
    async def 查看队伍信息方法(self, 事件: AstrMessageEvent):
        """查看本队的宝可梦信息"""
        会话: 会话类 = 事件.会话

        结果 = await team_repository.执行查看队伍信息方法(会话=会话)

        if 结果.是否成功:
            队伍名称, 队伍真实序号, 队伍信息 = 结果.数据信息
        else:
            yield 事件.plain_result(结果.错误信息)
            return

        结果 = await asyncio.get_running_loop().run_in_executor(
            self.线程池,
            image_utils.图片生成处理器,
            image_data_services.生成宝可梦队列信息配置方法,
            队伍信息,
            事件.get_sender_name(),
            队伍名称,
            会话,
            队伍真实序号
        )

        if not 结果.是否成功:
            yield 事件.plain_result("查看失败了, 似乎是图片生成时出错了")
            return

        yield 事件.chain_result([
            Image.fromBytes(结果.数据信息)
        ])

    @pm.command("队伍列表", alias={"所有队伍", "全部队伍", "查看所有队伍", "查看全部队伍"})
    @检查用户注册状态
    @会话初始化
    async def 查看全部队伍信息方法(self, 事件: AstrMessageEvent, 页数: int = 1):
        会话: 会话类 = 事件.会话

        结果 = await team_services.获取全部队伍信息方法(会话, 页数)

        if not 结果.是否成功:
            yield 事件.plain_result(str(结果.错误信息))
            return

        if not 结果.数据信息:
            yield 事件.plain_result("还没有队伍哦, 使用「/pm 新建队伍 [队伍名称]」来创建吧")
            return

        结果 = await asyncio.get_running_loop().run_in_executor(
            self.线程池,
            image_utils.图片生成处理器,
            image_data_services.生成队伍列表信息配置方法,
            会话,
            结果.数据信息[0],
            结果.数据信息[1]
        )

        if not 结果.是否成功:
            yield 事件.plain_result("图片位置信息生成失败了")
            return

        yield 事件.chain_result([
            Image.fromBytes(结果.数据信息)
        ])

    @pm.command("入队", alias={"队伍添加宝可梦", "队伍增加", "队伍加入", "加入队伍", "如对"})
    @检查用户注册状态
    @会话初始化
    async def 宝可梦加入队伍方法(self, 事件: AstrMessageEvent, 盒子序号: int, 队伍序号: int = None):
        """请先使用「/pm 盒子」查看宝可梦编号, 根据编号来添加宝可梦至指定默认队伍, 也可以指定队伍序号"""
        会话: 会话类 = 事件.会话

        结果 = await team_repository.添加宝可梦入队方法(
            会话=会话,
            盒子序号=盒子序号,
            队伍序号=队伍序号
        )

        yield 事件.plain_result(结果.数据信息 if 结果.是否成功 else 结果.错误信息)

    @pm.command("离队", alias={"踢出宝可梦", "离开队伍", "李队", "里队"})
    @检查用户注册状态
    @会话初始化
    async def 宝可梦离开队伍方法(self, 事件: AstrMessageEvent, 位置序号: int, 队伍序号: int = None):
        """宝可梦离开后自动进入盒子, 可指定队伍"""
        会话: 会话类 = 事件.会话

        结果 = await team_repository.执行宝可梦离队方法(
            会话=会话,
            位置序号=位置序号,
            队伍序号=队伍序号
        )

        yield 事件.plain_result(结果.数据信息 if 结果.是否成功 else 结果.错误信息)

    @pm.command("盒子", alias={"宝可梦盒子", "查看所有宝可梦", "查看盒子"})
    @检查用户注册状态
    @会话初始化
    async def 查看宝可梦盒子方法(self, 事件: AstrMessageEvent, 页数: int = 1):
        """列出未加入队伍的宝可梦, 支持分页查看"""
        会话: 会话类 = 事件.会话

        结果 = await pokemon_repository.执行查看盒子方法(
            会话=会话,
            页数=页数
        )

        if 结果.是否成功:
            盒子宝可梦信息列表, 最终页, 页数 = 结果.数据信息
        else:
            yield 事件.plain_result(结果.错误信息)
            return

        结果 = await asyncio.get_running_loop().run_in_executor(
            self.线程池,
            image_utils.图片生成处理器,
            image_data_services.生成宝可梦盒子信息配置方法,
            盒子宝可梦信息列表,
            会话,
            页数,
            最终页
        )

        if not 结果.是否成功:
            yield 事件.plain_result("查看失败了, 似乎是图片生成时出错了")
            return

        yield 事件.chain_result([
            Image.fromBytes(结果.数据信息)
        ])

    @pm.command("对决", alias={"对战", "决斗", "攻击", "进攻", "战斗"})
    @检查用户注册状态
    @会话初始化
    async def 对战方法(self, 事件: AstrMessageEvent):
        # 辅助函数, 用于线程池调用
        def 执行返回战斗图方法(数据, 模式):
            if 模式 == 1:
                return 战斗对象.返回战斗图方法(
                    背景图名称,
                    数据["本方宝可梦对象"].提取画战斗图所需数据(),
                    数据["对方宝可梦对象"].提取画战斗图所需数据()
                )
            elif 模式 == 2:
                return 战斗对象.返回战斗图方法(
                    数据["背景图名称"],
                    数据["左侧宝可梦数据"],
                    数据["右侧宝可梦数据"],
                    数据["本方开启mega"],
                    数据["本方开启极巨化"],
                    数据["对方开启mega"],
                    数据["对方开启极巨化"],
                )

        会话: 会话类 = 事件.会话
        消息列表: list = 事件.message_obj.message
        节点列表 = []

        # for i in 消息列表:
        #     if isinstance(i, At):
        #         敌人qq: str = int(i.qq)
        #         break
        # else:
        #     yield 事件.plain_result("没有指定敌人哦, 需要@对方, 并且不要复制@内容")
        #     return
        # ! 临时代码 ! 用于对战
        # 敌人qq = 2971074480
        敌人qq = 3351714298
        # if 会话.用户qq == 敌人qq:
        #     yield 事件.plain_result("不能和自己对战哦")
        #     return

        结果 = await battle_services.返回双方对战相关对象方法(会话, 敌人qq)

        if 结果.是否成功:
            对战相关信息 = 结果.数据信息
        else:
            yield 事件.plain_result(结果.错误信息)
            return

        # 获取双方昵称
        本方昵称 = 事件.get_sender_name()

        # 请求 = await 事件.bot.api.call_action(
        #     'get_stranger_info', user_id=str(敌人qq)
        # )

        # 对方昵称 = 请求.get("nick", 敌人qq)
        对方昵称 = "测试敌人"

        战斗对象 = battle.战斗类(
            会话=会话,
            本方队伍宝可梦信息列表=对战相关信息["本方宝可梦对象列表"],
            对方队伍宝可梦信息列表=对战相关信息["对方宝可梦对象列表"],
            本方背包对象=对战相关信息["本方背包对象"],
            对方背包对象=对战相关信息["对方背包对象"],
            本方队伍名称=对战相关信息["本方队伍名称"],
            对方队伍名称=对战相关信息["对方队伍名称"],
            本方昵称=本方昵称,
            对方昵称=对方昵称,
        )

        背景图名称 = image_data_services.返回背景图名称()

        初始战场图节点 = None
        if 会话.是否生成战场图:
            结果 = await asyncio.get_running_loop().run_in_executor(
                self.线程池,
                执行返回战斗图方法,
                {
                    "本方宝可梦对象": 对战相关信息["本方宝可梦对象列表"][0],
                    "对方宝可梦对象": 对战相关信息["对方宝可梦对象列表"][0]
                },
                1
            )

            if 结果.是否成功:
                if 会话.是否立即发送第一张战场图:
                # if True:
                    yield 事件.chain_result([Image.fromBytes(结果.数据信息)])
                else:
                    初始战场图节点 = Node(
                        uin=会话.机器人qq,
                        name="解说员",
                        content=[Image.fromBytes(结果.数据信息)]
                    )
            else:
                yield 事件.plain_result("对战失败了, 似乎是图片生成时出错了")
                return

        # 开始对战
        对战记录列表, 奖励字典 = await 战斗对象.队伍对战方法(背景图名称)

        # 发放战斗结束奖励
        结果 = await battle_repository.战斗奖励发放方法(会话, 当前队伍ID=对战相关信息["本方队伍ID"], 奖励字典=奖励字典)

        if 结果.是否成功:
            print(结果.数据信息)
            对战记录列表.append([("文本", "\n".join(结果.数据信息))])
        else:
            print("对战执行失败, 奖励发放出错: "+结果.错误信息)
            yield 事件.plain_result("对战执行失败, 奖励发放出错")
            return

        节点列表 = []

        # 如果生成了初始战场图且不立即发送，则添加到节点列表开头
        if 初始战场图节点 is not None:
            节点列表.append(初始战场图节点)

        for 消息块 in 对战记录列表:
            消息块内容列表 = []
            文本缓存 = ""

            for 内容元组 in 消息块:
                类型 = 内容元组[0]
                数据 = 内容元组[1]

                if 类型 == "文本":
                    try:
                        文本缓存 += 数据 + "\n"
                    except Exception as e:
                        print(数据 ,e)
                elif 类型 == "图片":
                    if 文本缓存:
                        # 将回合开始到图片之前的文本缓存
                        消息块内容列表.append(Plain(文本缓存))
                        文本缓存 = ""

                    结果 = await asyncio.get_running_loop().run_in_executor(
                        self.线程池,
                        执行返回战斗图方法,
                        数据,
                        2
                    )

                    if 结果.是否成功:
                        消息块内容列表.append(Image.fromBytes(结果.数据信息))
                    else:
                        print("错误 极巨化或mega的战斗图生产失败: " + 结果.错误信息)
                        yield 事件.plain_result("对战失败了, 似乎是图片生成时出错了")
                        return

            if 文本缓存:
                消息块内容列表.append(Plain(文本缓存.rstrip('\n')))

            if 消息块内容列表:
                yield 事件.chain_result(消息块内容列表)
                # 节点列表.append(Node(
                #     uin=会话.机器人qq,
                #     name="解说员",
                #     content=消息块内容列表
                # ))

        # if 节点列表:
        #     yield 事件.chain_result([Nodes(nodes=节点列表)])