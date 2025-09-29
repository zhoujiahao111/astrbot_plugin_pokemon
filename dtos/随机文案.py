# coding=utf-8
import json
import random
from pydantic import  ValidationError, field_validator, RootModel

class 随机文案数据模型(RootModel[dict[str, list[str]]]):
    @field_validator('*', mode='after')
    @classmethod
    def 列表不能为空(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("文案列表不能为空")
        return value

# 2. 创建随机文案管理器
class 随机文案管理器:
    _数据: dict[str, list[str]]

    def __init__(self, 原始数据):
        try:
            已验证模型 = 随机文案数据模型.model_validate(原始数据)
            self._数据 = 已验证模型.root
        except ValidationError as e:
            print(f"错误：提供的随机文案数据格式不正确。\n{e}")
            raise

    def 获取随机文案(self, 识别码: str, 变量字典: dict = None) -> str:
        if 变量字典 is None:
            变量字典 = {}

        # 根据识别码查找对应的文案列表
        文案模板列表 = self._数据.get(识别码)

        if not 文案模板列表:
            return f"错误：未找到识别码 '{识别码}' 对应的文案。"

        选中模板 = random.choice(文案模板列表)

        try:
            return 选中模板.format(**变量字典)
        except KeyError as e:
            return f"错误：填充文案 '{识别码}' 时缺少变量：{e}"