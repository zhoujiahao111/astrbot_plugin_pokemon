from pydantic import RootModel, Field, ValidationError

class 违禁词数据模型(RootModel):
    root: list[str] = Field(..., min_length=1)

    @classmethod
    def 检查元素是否为字符串(cls, v):
        if not isinstance(v, list):
            raise ValueError('违禁词数据必须是列表')

        for item in v:
            if not isinstance(item, str):
                raise ValueError('违禁词列表中的元素必须是字符串')
        return v


class 违禁词管理器:
    _数据: 违禁词数据模型
    _违禁词列表: list[str]

    def __init__(self, 原始数据):
        try:
            self._数据 = 违禁词数据模型.model_validate(原始数据)
            self._违禁词列表 = self._数据.root
        except ValidationError as e:
            print(f"错误：提供的违禁词数据格式不正确。\n{e}")
            raise

    def 文本是否通过审核(self, 待检查文本: str) -> bool:
        """检查文本是否包含任何违禁词 返回True是通过审核"""
        return not any(违禁词 in 待检查文本 for 违禁词 in self._违禁词列表)