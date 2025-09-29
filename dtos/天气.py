import random
from pydantic import BaseModel, Field, model_validator, ValidationError


class 天气详情(BaseModel):
    """
    定义单个天气类型的详细信息模型。
    """
    名称: str
    描述: str
    概率: float = Field(gt=0, le=1)  # 概率必须大于0且小于等于1
    持续: tuple[int, int]
    属性倍率: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode='after')
    def 校验持续回合(self) -> '天气详情':
        """校验持续元组的起始值不大于结束值。"""
        start, end = self.持续
        if start > end:
            raise ValueError(f"天气的持续时间范围不正确，起始({start})不能大于结束({end})")
        return self


class 季节天气集(BaseModel):
    """
    定义包含所有季节天气信息的顶层模型。
    使用字典来存储季节，使其更具扩展性。
    """
    seasons: dict[str, list[天气详情]]

    @model_validator(mode='after')
    def 校验季节天气非空(self) -> '季节天气集':
        """
        校验规则：
        1. 必须至少定义一个季节。
        2. 每个已定义的季节内部必须有大于0个天气。
        """
        if not self.seasons:
            raise ValueError("天气数据不能为空，必须至少定义一个季节")
        for season, weathers in self.seasons.items():
            if not weathers:
                raise ValueError(f"季节 '{season}' 的天气列表不能为空")
        return self


class 生成天气结果(BaseModel):
    """
    定义随机生成天气后的标准输出格式。
    """
    名称: str
    描述: str
    持续回合: int
    属性倍率: dict[str, float]


class 天气管理器:
    def __init__(self, 原始天气数据: dict):
        try:
            self._数据 = 季节天气集.model_validate({"seasons": 原始天气数据})
        except ValidationError as e:
            print(f"天气数据格式错误: {e}")
            raise

    def 随机抽取并生成天气(self, 季节: str) -> 生成天气结果:
        季节天气列表 = self._数据.seasons.get(季节)

        # 如果季节不存在或该季节没有配置任何天气，则返回一个默认的“晴天”
        if not 季节天气列表:
            return 生成天气结果(
                名称="晴天",
                描述=f"季节 '{季节}' 未配置任何特殊天气。",
                持续回合=1,
                属性倍率={}
            )

        权值 = [天气.概率 for 天气 in 季节天气列表]

        if sum(权值) <= 0:
            return 生成天气结果(
                名称="晴天",
                描述=f"季节 '{季节}' 的所有天气概率总和为0。",
                持续回合=1,
                属性倍率={}
            )

        抽中的天气 = random.choices(季节天气列表, weights=权值, k=1)[0]

        区间 = 抽中的天气.持续
        持续回合 = random.randint(区间[0], 区间[1])

        return 生成天气结果(
            名称=抽中的天气.名称,
            持续回合=持续回合,
            描述=抽中的天气.描述,
            属性倍率=抽中的天气.属性倍率.copy()
        )
