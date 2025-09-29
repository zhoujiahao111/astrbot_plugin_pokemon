# coding=utf-8
import cProfile
import json
import pstats
import time

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    RootModel,
    model_validator,
)

# 此代码可能和后面的招式重复了
class 招式模型(BaseModel):
    """用于校验升级可学会招式列表中的单个招式对象"""
    等级: int = Field(..., gt=0, description="等级必须是大于0的整数")
    招式名称: str = Field(..., min_length=1, description="招式名称不能为空")

class 种族值模型(BaseModel):
    """用于校验种族值字典中的六项能力值"""
    HP: int = Field(..., ge=0)
    攻击: int = Field(..., ge=0)
    防御: int = Field(..., ge=0)
    特攻: int = Field(..., ge=0)
    特防: int = Field(..., ge=0)
    速度: int = Field(..., ge=0)


class 宝可梦模型(BaseModel):
    """用于校验单个宝可梦对象的完整结构和类型"""
    编号: int = Field(..., ge=0, description="编号必须是大于等于0的整数")
    名称: str = Field(..., min_length=1, description="名称不能为空")
    贴图: str = Field(..., min_length=1, description="贴图文件名不能为空")
    宝可梦属性: list[str]
    宝可梦分类: str
    身高: str
    体重: str
    种族值字典: 种族值模型
    mega: str | None
    极巨化: str | None
    简介: str
    进化信息: dict | list[dict] = Field(...,description="进化信息可以是单个字典或字典列表")
    战胜经验值: int
    成长速度: str
    升级可学会招式列表: list[招式模型]

class 宝可梦图鉴模型(RootModel[list[宝可梦模型]]):
    """
    根模型，代表整个JSON文件的数据结构（一个宝可梦模型的列表）。
    并在此处进行跨宝可梦的全局校验。
    """
    @model_validator(mode='after')
    def 校验自定义规则(self) -> '宝可梦图鉴模型':
        宝可梦列表 = self.root
        if not 宝可梦列表:
            raise ValueError("宝可梦图鉴数据列表不能为空")

        编号集合 = set()
        贴图集合 = set()
        for 宝可梦 in 宝可梦列表:
            # 校验编号的唯一性
            if 宝可梦.编号 in 编号集合:
                raise ValueError(f"发现重复的宝可梦编号: {宝可梦.编号} (名称: {宝可梦.名称})")
            编号集合.add(宝可梦.编号)

            # 校验贴图的唯一性
            if 宝可梦.贴图 in 贴图集合:
                raise ValueError(f"发现重复的贴图文件名: '{宝可梦.贴图}' (名称: {宝可梦.名称})")
            贴图集合.add(宝可梦.贴图)
        return self


class 宝可梦图鉴管理器:
    """
    用于管理宝可梦图鉴数据并提供统一接口的类。
    """
    _数据: 宝可梦图鉴模型
    _编号索引: dict[int, 宝可梦模型]
    _名称索引: dict[str, 宝可梦模型]
    _贴图索引: dict[str, 宝可梦模型]

    def __init__(self, 原始数据: list[dict]):
        """
        初始化图鉴管理器，并对传入的原始数据进行严格校验。
        """
        try:
            self._数据 = 宝可梦图鉴模型.model_validate(原始数据)

            # 构建索引
            self._构建索引()

        except ValidationError as e:
            print(f"错误：提供的宝可梦图鉴数据格式不正确。\n{e}")
            raise

    def _构建索引(self):
        """构建查找索引以加速查询"""
        self._编号索引 = {}
        self._名称索引 = {}
        self._贴图索引 = {}

        for 宝可梦 in self._数据.root:
            self._编号索引[宝可梦.编号] = 宝可梦
            self._名称索引[宝可梦.名称] = 宝可梦
            self._贴图索引[宝可梦.贴图] = 宝可梦

    def 根据编号获取宝可梦(self, 编号: str) -> 宝可梦模型:
        """根据编号查找并返回单个宝可梦对象（O(1)时间复杂度）"""
        return self._编号索引.get(int(编号))

    def 根据名称获取宝可梦(self, 名称: str) -> 宝可梦模型:
        """根据名称（精确匹配）查找并返回单个宝可梦对象（O(1)时间复杂度）"""
        return self._名称索引.get(名称)


    # ! 临时代码 ! 此处需要新增一批 宝可梦稀有度相关代码