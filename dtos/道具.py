from ..models.enums import 效果类型类
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    RootModel,
    model_validator,
)

class 使用规则模型(BaseModel):
    """校验'使用规则'字段的内部结构"""
    可主动使用: bool
    消耗方式: str = Field(..., min_length=1)
    允许多次使用: bool


class 效果模型(BaseModel):
    """校验'效果列表'中每个元素的内部结构"""
    效果类型: 效果类型类
    效果参数: dict


class 道具模型(BaseModel):
    """用于描述单个物品信息的基础模型"""
    # 基础属性校验，字符串不能为空，价格必须大于等于0
    标识ID: str = Field(..., min_length=1)
    名称: str = Field(..., min_length=1)
    贴图: str = Field(..., min_length=1)
    描述: str = Field(..., min_length=1)
    价格: int = Field(..., ge=0)
    能否重复购买: bool
    量词: str = Field(default="个")

    # 嵌套结构校验，使用上面定义的模型
    使用规则: 使用规则模型
    效果列表: list[效果模型] = Field(..., min_length=1)  # 效果列表不能为空


class 道具数据模型(RootModel[list[道具模型]]):
    """
    用于校验整个物品JSON数据 (根类型是一个列表) 的根模型。
    """

    @model_validator(mode='after')
    def 校验标识ID唯一性(self) -> '道具数据模型':
        """在所有物品都通过基础校验后，检查整个列表中是否存在重复的'标识ID'"""
        ID集合 = set()
        for 物品 in self.root:
            if 物品.标识ID in ID集合:
                raise ValueError(f"发现重复的'标识ID': {物品.标识ID}")
            ID集合.add(物品.标识ID)
        return self

class 道具管理器:
    _数据: 道具数据模型
    _物品索引: dict[str, 道具模型]

    def __init__(self, 原始数据):
        try:
            self._数据 = 道具数据模型.model_validate(原始数据)
            self._物品索引 = {物品.标识ID: 物品 for 物品 in self._数据.root}
            self._物品名称索引 = {物品.名称: 物品 for 物品 in self._数据.root}
        except ValidationError as e:
            print(f"错误：提供的物品数据格式不正确。\n{e}")
            raise

    def 根据ID获取物品(self, 标识ID: str) -> 道具模型:
        return self._物品索引.get(标识ID)

    def 获取所有物品(self) -> list[道具模型]:
        return self._数据.root

    def 获取所有物品ID(self) -> list[str]:
        return list(self._物品索引.keys())

    def 获取所有物品名称(self) -> list[str]:
        return [物品.名称 for 物品 in self._数据.root]

    def 根据索引获取物品(self, 索引: int) -> 道具模型 | None:
        if 0 <= 索引 < len(self._数据.root):
            return self._数据.root[索引]
        return None

    def 返回用户物品列表(self, 待处理列表: list[dict]) -> list[dict]:
        用户物品列表 = []
        for i in 待处理列表:
            名称 = i.get("物品名称")
            数量 = i.get("数量")

            # 通过名称索引直接查找物品对象
            物品对象 = self._物品名称索引.get(名称)

            # 如果找不到任何一个物品，则按原逻辑返回空列表
            if not 物品对象:
                return []

            # 将 pydantic 模型对象转换为字典
            信息 = 物品对象.model_dump()
            信息["数量"] = int(数量)

            用户物品列表.append(信息)

        return 用户物品列表

    def 根据名称获取物品(self, 名称: str) -> 道具模型:
        """
        根据道具的名称，返回对应的 Pydantic 道具模型对象, 找不到返回 None
        """
        return self._物品名称索引.get(名称)