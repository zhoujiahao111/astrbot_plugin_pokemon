# coding=utf-8
from pydantic import BaseModel, field_validator, ValidationError
import random

class 性格模型(BaseModel):
    """
    用于校验性格数据结构的 Pydantic 模型。
    确保每个属性修正值都是大于0小于2的数值。
    """
    data: dict[str, dict[str, float | int]]

    @field_validator('data')
    @classmethod
    def validate_modifiers(cls, v: dict[str, dict[str, float | int]]) -> dict[str, dict[str, float | int]]:
        """校验每个属性修正值都在 (0, 2) 范围内"""
        for trait, modifiers in v.items():
            if not isinstance(modifiers, dict):
                 raise ValueError(f"性格 '{trait}' 的值必须是一个字典")
            for attr, value in modifiers.items():
                if not isinstance(value, (float, int)):
                    raise ValueError(f"性格 '{trait}' 的属性 '{attr}' 的值 '{value}' 必须是数值")
                if not (0 < value < 2):
                    raise ValueError(f"性格 '{trait}' 的属性 '{attr}' 的值 {value} 不在 (0, 2) 范围内")
        return v


class 性格管理器:
    """
    用于管理和操作性格数据。
    """
    _性格数据: dict[str, dict[str, float | int]]

    def __init__(self, data: dict[str, dict[str, float | int]]):
        try:
            # 使用 Pydantic 模型进行数据校验和解析
            validated_model = 性格模型(data=data)
            self._性格数据 = validated_model.data
        except ValidationError as e:
            print(f"数据校验失败: {e}")
            raise

    def 随机返回一个性格名称(self) -> str:
        """
        从所有性格中随机返回一个性格的名称。
        """
        if not self._性格数据:
            return ""
        性格列表 = list(self._性格数据.keys())
        return random.choice(性格列表)

    def 获取属性数值(self, 性格: str, 属性: str) -> float | int:
        """
        根据指定的性格和属性，返回对应的修正数值。如果没有定义，则返回默认值 1.0
        """
        return self._性格数据.get(性格, {}).get(属性, 1.0)