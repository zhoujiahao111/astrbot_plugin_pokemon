# coding=utf-8
import random
from datetime import datetime, timedelta
from ..core import database
from ..models import result, increment
from ..models.enums import 表名类, 操作类, 效果类型类
from ..services import bag_services, team_services, pokemon_services
from ..models.session import 会话类
from ..repository import pokemon_repository
from ..utils import text_utils
from ..dtos import 道具管理器, 道具模型


class 背包管理类:
    def __init__(self, 会话: "会话类", 用户道具数量字典: dict[str, int]):
        """
        构造函数保持不变，但现在只存储用户的动态数据。
        """
        self.会话 = 会话
        self.用户道具数量字典: dict[str, int] = 用户道具数量字典

    @classmethod
    async def create(cls, 会话: "会话类"):
        """
        异步初始化方法。
        逻辑从获取字典改为获取列表，然后转换为更高效的 "名称->数量" 字典。
        """
        用户道具列表 = await cls.返回用户道具列表(会话.用户qq)
        用户道具数量字典 = {item['物品名称']: int(item['数量']) for item in 用户道具列表}
        return cls(会话, 用户道具数量字典)

    @staticmethod
    async def 返回用户道具列表(用户qq) -> list[dict]:
        """
        此方法用于从数据库获取原始数据，名称调整为“列表”以更准确地反映其返回类型。
        """
        db = await database.获取数据库对象()
        结果 = await db.单次查询方法({
            "表名": 表名类.用户物品表,
            "查询数据": ['物品名称', '数量'],
            "条件": {"用户ID": 用户qq}
        })
        return 结果.数据信息 if 结果.是否成功 else []

    def 返回队伍上限修正值方法(self) -> int:
        """
        重构后：遍历用户拥有的道具，查询其静态数据，判断效果类型。
        这比遍历所有静态道具更高效。
        """
        total_bonus = 0
        for item_name in self.用户道具数量字典.keys():
            道具: "道具模型" = self.会话.json管理器.道具.根据名称获取物品(item_name)
            if not 道具:
                continue

            for 效果 in 道具.效果列表:
                if 效果.效果类型 == "队伍上限":
                    # 原逻辑是只要有就加成，不看数量。如果需要按数量叠加，可以乘以数量。
                    # total_bonus += 效果.效果参数.get("加成值", 0) * self.用户道具数量字典[item_name]
                    total_bonus += int(效果.效果参数.get("加成值", 0))

        return total_bonus

    def 返回道具先攻值方法(self) -> int:
        """
        重构后：同样是遍历用户持有的道具，查找具备“先行攻击”效果的道具。
        """
        # 筛选出用户拥有的，且具有“先行攻击”效果的道具
        先攻道具列表 = []
        for item_name in self.用户道具数量字典.keys():
            道具: "道具模型" = self.会话.json管理器.道具.根据名称获取物品(item_name)
            if not 道具:
                continue

            for 效果 in 道具.效果列表:
                if 效果.效果类型 == "先行攻击":
                    先攻道具列表.append(效果)  # 将效果对象加入列表

        # 遍历筛选出的效果，计算最终结果
        for 效果 in 先攻道具列表:
            try:
                # Pydantic模型保证了效果参数字典的存在，但内部key仍需安全获取
                概率 = float(效果.效果参数.get("生效概率", 0))
                效果值 = int(效果.效果参数.get("效果值", 10))

                if random.random() < 概率:
                    return 效果值
            except (ValueError, TypeError):
                continue

        return 0

    async def 返回宝可梦属性倍率方法(self) -> "result.结果类":
        属性倍率字典 = {"HP": 1, "攻击": 1, "防御": 1, "特攻": 1, "特防": 1, "速度": 1}

        # 1. 处理激活效果表中的道具 (持续时间类)
        结果 = await self.返回生效的道具列表()
        if not 结果.是否成功:
            return 结果.失败方法("激活效果数据获取失败")

        for 激活道具 in 结果.数据信息:
            item_name = 激活道具["物品名称"]
            道具: "道具模型" = self.会话.json管理器.道具.根据名称获取物品(item_name)
            if not 道具:
                print(f"激活的道具 '{item_name}' 在静态数据中未找到，已忽略。")
                continue

            for 效果 in 道具.效果列表:
                if 效果.效果类型 == "属性修改":
                    加成类型 = 效果.效果参数.get("加成类型")
                    加成值 = 效果.效果参数.get("加成值", 1)
                    if 加成类型 in 属性倍率字典:
                        属性倍率字典[加成类型] *= float(加成值)
                    else:
                        print(f'道具 "{item_name}" 的加成类型 "{加成类型}" 无效，已忽略。')

        # 处理背包内直接生效的道具
        for item_name in self.用户道具数量字典.keys():
            道具: "道具模型" = self.会话.json管理器.道具.根据名称获取物品(item_name)
            if not 道具:
                continue

            if 道具.使用规则.消耗方式 == "购买生效":
                for 效果 in 道具.效果列表:
                    if 效果.效果类型 == "属性修改":
                        加成类型 = 效果.效果参数.get("加成类型")
                        加成值 = 效果.效果参数.get("加成值", 1)
                        if 加成类型 in 属性倍率字典:
                            属性倍率字典[加成类型] *= float(加成值)

        return 结果.成功方法(属性倍率字典)

    async def 返回生效的道具列表(self) -> "result.结果类":
        """此方法无需改动，它只负责查询数据库。"""
        db = await database.获取数据库对象()
        return await db.单次查询方法({
            "表名": 表名类.激活效果表,
            "查询数据": ['物品名称', '到期日期'],
            "条件": {"用户ID": self.会话.用户qq}
        })

    def _check_item_effect_exist(self, effect_type: str) -> bool:
        """
        内部辅助方法，用于检查用户是否拥有具备特定效果类型的道具。
        """
        for item_name in self.用户道具数量字典.keys():
            道具: "道具模型" = self.会话.json管理器.道具.根据名称获取物品(item_name)
            if 道具:
                for 效果 in 道具.效果列表:
                    if 效果.效果类型 == effect_type:
                        return True
        return False

    def 有无极巨腕带(self) -> bool:
        """重构后：使用辅助方法进行检查。"""
        return self._check_item_effect_exist("开启极巨化")

    def 有无超级环(self) -> bool:
        """重构后：使用辅助方法进行检查。"""
        return self._check_item_effect_exist("开启mega")

    # async def 道具生效方法(self, 匹配名称: str, 数量: int) -> result.结果类:
    #     索引 = bag_services.返回道具名称对应索引方法(self.用户物品列表, 匹配名称)
        #
        # if 索引 < 0:
        #     return result.结果类.失败方法("出现意外, 没有找到匹配的物品")
        #
        # 道具信息字典: dict = self.用户物品列表[索引]
        #
        # # 先判断道具是否可使用
        # 道具类型: str = 道具信息字典.get('类型')
        # 道具消耗信息: list = 道具信息字典.get('消耗类型')
        #
        # if not 道具消耗信息:
        #     return result.结果类.失败方法(f"道具【{道具信息字典['名称']}】信息不完整，无法使用。")
        #
        # 道具消耗类型: str = 道具消耗信息[0]
        #
        # if 道具消耗类型 == "购买生效":
        #     return result.结果类.失败方法(f"道具【{道具信息字典['名称']}】购买后即自动生效，无需主动使用。")
        #
        # elif 道具类型 == "即时捕获":
        #     return result.结果类.失败方法("精灵球只能在遇到宝可梦时自动使用哦。")
        #
        # elif 道具消耗类型 == "时间":
        #     return await self.使用持续生效类道具方法(道具信息字典)
        #
        # elif 道具消耗类型 == "次数":
        #     # 先判断数量是否大于0
        #     if 道具信息字典["数量"] < 1:
        #         return result.结果类.失败方法("这个道具已经用完了, 需要去商店购买哦")
        #
        #     if 道具类型 == "等级":
        #         return await self.使用宝可梦全队升级道具方法(
        #             道具信息字典['名称'],
        #         )
        #
        #     elif 道具类型 == "心情恢复":
        #         return await self.宝可梦全队心情增加方法(道具信息字典["效果参数"]['加成值'], 道具信息字典['名称'])
        #
        #     elif 道具类型 == "宝可梦概率":
        #         return result.结果类.失败方法(f"不能直接使用哦, 下一次冒险会自动使用这个道具的")
        #
        #     else:
        #         # 未知的“次数”类道具
        #         return result.结果类.失败方法(f"道具【{道具信息字典['名称']}】的使用方式很特别，现在还不能这样使用。")
        #
        # return result.结果类.失败方法("这个道具似乎不能在这里使用。")

    def 返回道具数量更新字典(self, 道具名称: str, 数量: int) -> dict:
        return {
            "表名": 表名类.用户物品表,
            "操作": 操作类.更新,
            "数据": {
                "数量": increment.增量类(数量),
            },
            "条件": {
                "用户ID": self.会话.用户qq,
                "物品名称": 道具名称
            }
        }

    async def 使用持续生效类道具方法(self, 道具信息字典: dict) -> result.结果类:
        道具名称 = 道具信息字典["名称"]
        db = await database.获取数据库对象()

        # 检查数据库中是否已存在同名且未过期的道具效果
        结果 = await db.单次查询方法(
            {
                "表名": 表名类.激活效果表,
                "查询数据": "到期日期",
                "条件": {
                    "用户ID": self.会话.用户qq,
                    "物品名称": 道具名称
                }
            }
        )

        if 结果.是否成功:
            if 结果.数据信息:
                到期日期 = 结果.数据信息[0]
            else:
                到期日期 = None
        else:
            return 结果.失败方法("查询正在生效的道具时失败了")

        消耗类型 = 道具信息字典["消耗类型"]

        if 到期日期:
            # 判断之前的道具是否过期了
            时间对象 = datetime.strptime(到期日期, '%Y-%m-%d %H:%M:%S')
            当前时间 = datetime.now()

            if 当前时间 > 时间对象:
                # 之前的道具过期了, 可以直接修改注册日期, 无需插入新数据
                过期时间 = 当前时间 + timedelta(seconds=int(道具信息字典["消耗类型"][1]))

                操作列表 = [{
                    "表名": 表名类.激活效果表,
                    "操作": 操作类.更新,
                    "数据": {
                        "到期日期": 过期时间.strftime("%Y-%m-%d %H:%M:%S"),
                        "物品名称": 道具名称
                    },
                    "条件": {
                        "用户ID": self.会话.用户qq,
                        "物品名称": 道具名称
                    }
                }]

            else:
                return 结果.失败方法(f"{道具名称}正在生效, 请勿重复使用哦")

        else:
            # 说明数据库里没有重复的道具, 需要插入
            if 消耗类型[0] != "时间":
                # 确保道具是持续生效的类型
                return result.结果类.失败方法("未知的道具消耗类型")

            操作列表 =[{
                "表名": 表名类.激活效果表,
                "操作": 操作类.插入,
                "数据": {
                    "用户ID": self.会话.用户qq,
                    "物品名称": 道具名称
                }
            }]

        操作列表.append(self.返回道具数量更新字典(道具名称, -1))
        结果 = await db.写入方法(操作列表)

        if 结果.是否成功:
            return result.结果类.成功方法(f"{道具名称}已经生效, 持续时间是{消耗类型[1] // 60}分钟哦")
        else:
            return result.结果类.失败方法("道具生效了, 但居然没有被消耗掉, 奇怪")


