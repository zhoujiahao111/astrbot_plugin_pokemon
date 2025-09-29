# coding=utf-8
from ..services import pokemon_services
from ..models import result, increment,  session
from ..dtos import 宝可梦图鉴管理器, 宝可梦模型, 种族值模型

class 宝可梦类:
    def __init__(
        self,
        会话: session.会话类,
        宝可梦数据字典: dict,
        宝可梦图鉴信息: 宝可梦模型 | None,
        招式列表: list[dict]
    ):
        self.会话 = 会话

        # 使用下划线前缀表示这些是内部数据，外部不应直接访问
        self._宝可梦数据 = 宝可梦数据字典
        self._图鉴信息 = 宝可梦图鉴信息
        if self._图鉴信息 is None:
            raise ValueError("宝可梦图鉴信息似乎不包含此编号, 读取失败了")

        self._招式列表 = 招式列表

        self.等级: int = pokemon_services.返回宝可梦等级方法(self.会话, self.经验, self.成长速度)

        # self.升级所需经验值: int = self.会话.json管理器.升级需求经验值.获取经验值(self.等级+1, self.成长速度) - 当前经验值

        self.当前属性字典: dict = self.返回宝可梦当前属性方法()
        self.当前生命值 = self.当前属性字典["HP"]

        self.是否濒死: bool = False
        self.mega是否开启: bool = False
        self.极巨化是否开启: bool = False

        # [{"名称": {数据}}]
        self.招式列表 = 招式列表

    @property
    def 主键ID(self) -> int:
        return self._宝可梦数据["主键ID"]

    @property
    def 用户ID(self) -> int:
        return self._宝可梦数据["用户ID"]

    @property
    def 昵称(self) -> str:
        return self._宝可梦数据["昵称"]

    @property
    def 经验(self) -> int:
        return self._宝可梦数据["经验"]

    @property
    def 天赋(self) -> int:
        return self._宝可梦数据["天赋"]

    @property
    def 性格(self) -> str:
        return self._宝可梦数据["性格"]

    @property
    def 性别(self) -> str:
        return self._宝可梦数据["性别"]

    @property
    def 心情(self) -> int:
        return self._宝可梦数据["心情"]

    @property
    def 注册日期(self) -> str:
        return self._宝可梦数据["注册日期"]

    @property
    def 编号(self) -> int:
        # 修正了原始代码中重复定义的问题，通常以图鉴为准
        return self._图鉴信息.编号

    @property
    def 默认名称(self) -> str:
        return self._图鉴信息.名称

    @property
    def 贴图(self) -> str:
        return self._图鉴信息.贴图

    @property
    def 宝可梦属性列表(self) -> list:
        return self._图鉴信息.宝可梦属性

    @property
    def 宝可梦分类(self) -> str:
        return self._图鉴信息.宝可梦分类

    @property
    def 身高(self) -> str:
        return self._图鉴信息.身高

    @property
    def 体重(self) -> str:
        return self._图鉴信息.体重

    @property
    def 种族值模型(self) -> 种族值模型:
        return self._图鉴信息.种族值字典

    @property
    def 升级可学会招式列表(self) -> list:
        return self._图鉴信息.升级可学会招式列表

    @property
    def mega贴图名称(self) -> str | None:
        return self._图鉴信息.mega

    @property
    def 极巨化贴图名称(self) -> str | None:
        return self._图鉴信息.极巨化

    @property
    def 简介(self) -> str:
        return self._图鉴信息.简介

    @property
    def 进化信息字典(self) -> dict:
        return self._图鉴信息.进化信息

    @property
    def 天赋描述(self) -> str:
        return pokemon_services.返回天赋值对应描述文本(self.天赋)

    @property
    def 天赋值加成倍率(self) -> float:
        # 依赖于动态数据 self.天赋
        return pokemon_services.返回天赋值对应倍率(self.天赋)

    @property
    def 战胜经验值(self) -> int:
        return self._图鉴信息.战胜经验值

    @property
    def 成长速度(self) -> str:
        return self._图鉴信息.成长速度

    def 承受伤害方法(self, 伤害值: int):
        self.当前生命值 -= 伤害值

        if self.当前生命值 <= 0:
            self.当前生命值 = 0
            self.是否濒死 = True

    def 返回宝可梦当前属性方法(self) -> dict:
        """基于等级, 天赋值, 性格和种族值动态计算出属性"""
        HP = ((self.种族值模型.HP * 2 + self.天赋值加成倍率) * self.等级 / 100) + self.等级 + 10

        属性字典 = {
            "HP": int(HP)
        }

        # 迭代种族值模型中除HP外的其他五个属性
        for 属性 in ["攻击", "防御", "特攻", "特防", "速度"]:
            # 使用 getattr 安全地获取属性值
            种族值 = getattr(self.种族值模型, 属性)

            值 = (
                (((种族值 * 2 + self.天赋值加成倍率) * self.等级 / 100) + 5)
                * self.会话.json管理器.性格.获取属性数值(self.性格, 属性)
            )

            属性字典[属性] = int(值)

        return 属性字典

    def 提取画战斗图所需数据(self) -> dict:
        return {
            "当前属性字典": self.当前属性字典,
            "极巨化贴图名称": self.极巨化贴图名称,
            "mega贴图名称": self.mega贴图名称,
            "贴图": self.贴图,
            "当前生命值": self.当前生命值,
            "招式名称列表": [list(字典.keys())[0] for 字典 in self.招式列表]
        }

    def 返回宝可梦数据字典(self) -> dict:
        return {
            "主键ID": self.主键ID,
            "用户ID": self.用户ID,
            "编号": self.编号,
            "昵称": self.昵称,
            "经验": self.经验,
            "天赋": self.天赋,
            "性格": self.性格,
            "性别": self.性别,
            "心情": self.心情,
            "注册日期": self.注册日期,
        }

    def 执行mega进化(self):
        self.mega是否开启 = True
        self.当前生命值 = int(self.当前生命值 * 1.3)

        for i in self.当前属性字典.keys():
            self.当前属性字典[i] = int(self.当前属性字典[i] * 1.3)

    def 执行极巨化(self):
        self.极巨化是否开启 = True
        self.当前属性字典["HP"] *= 2.5
        self.当前生命值 *= 2.5

    def 终止极巨化(self):
        self.极巨化是否开启 = False
        self.当前属性字典["HP"] //= 2.5
        self.当前生命值 //= 2.5

