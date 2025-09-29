# coding=utf-8

class 增量类:
    """
    一个数据类，用于表示数据库字段的原子性增/减操作。
    在 '通用更新方法' 中使用此类的实例，可以生成如 '字段 = 字段 + ?' 的 SQL。
    """

    def __init__(self, 用户输入: int | float, 上限: int | float = None, 下限: int | float = None):
        if not isinstance(用户输入, (int, float)):
            raise TypeError("Increment value 必须是数字。")
        self.值 = 用户输入
        self.上限 = 上限
        self.下限 = 下限
