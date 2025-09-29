from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    RootModel,
    model_validator,
)

class 伙伴模型(BaseModel):
    索引: int = Field(..., ge=0, description="索引必须是大于等于0的整数")
    名称: str = Field(..., min_length=1, description="名称不能为空")


class 伙伴数据模型(RootModel[dict[str, list[伙伴模型]]]):
    @model_validator(mode='after')
    def 校验自定义规则(self) -> '伙伴数据模型':
        数据字典 = self.root
        if not 数据字典:
            raise ValueError("JSON数据不能为空字典")
        for 键名, 伙伴列表 in 数据字典.items():
            if not 伙伴列表:
                raise ValueError(f"键 '{键名}' 对应的列表不能为空")
            索引集合 = set()
            for 伙伴 in 伙伴列表:
                if 伙伴.索引 in 索引集合:
                    raise ValueError(f"在 '{键名}' 中发现重复的索引: {伙伴.索引}")
                索引集合.add(伙伴.索引)
        return self


class 伙伴管理器:
    """
    用于管理伙伴数据并提供统一接口的会话类。
    """
    _数据: 伙伴数据模型

    def __init__(self, 原始数据: dict[str, list[dict]]):
        """
        初始化管理器，并对传入的原始数据进行校验。
        """
        try:
            self._数据 = 伙伴数据模型.model_validate(原始数据)
        except ValidationError as e:
            print(f"错误：提供的伙伴数据格式不正确。\n{e}")
            raise

    def __iter__(self):
        return iter(self._数据.root.values())

    def 获取所有组合名称(self) -> list[str]:
        return list(self._数据.root.keys())

    def 根据名称获取伙伴列表(self, 组合名称: str) -> list[伙伴模型]:
        return self._数据.root.get(组合名称)

    def 根据索引获取组合名称(self, 选择: int) -> str:
        组合列表 = self.获取所有组合名称()
        if 1 <= 选择 <= len(组合列表):
            # 将用户习惯的 1开始的序号转换为 0开始的索引
            return 组合列表[选择 - 1]
        return None

