# coding=utf-8
from pydantic import BaseModel, ValidationError, Field

class 招式(BaseModel):
    属性: str = Field(..., description="招式的属性，例如：一般、火、水等")
    分类: str = Field(..., description="招式的分类，例如：物理、特殊、变化")
    威力: int = Field(..., description="招式的威力数值", ge=0)
    命中: int = Field(..., description="招式的命中数值", ge=0, le=100)
    PP: int = Field(..., description="招式的PP值", ge=0)


class 招式管理器:
    def __init__(self, 原始数据):
        try:
            # 使用字典推导式和 Pydantic 模型进行数据校验和转换
            self._数据: dict[str, 招式] = {
                招式名称: 招式.model_validate(招式详情)
                for 招式名称, 招式详情 in 原始数据.items()
            }
        except ValidationError as e:
            print(f"错误：提供的招式数据格式不正确。\n{e}")
            raise

    def 添加招式(self, 名称: str, 招式数据: 招式):
        pass

    def 获取招式(self, 名称: str) -> 招式:
        pass

    def 更新招式(self, 名称: str, 更新数据: 招式):
        pass

    def 删除招式(self, 名称: str):
        pass
