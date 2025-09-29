# coding=utf-8
from pydantic import BaseModel, PositiveInt, Field, field_validator, ValidationError
import bisect
from pydantic import ValidationError

class 需求经验值(BaseModel):
    最快: PositiveInt
    快: PositiveInt
    较快: PositiveInt
    较慢: PositiveInt
    慢: PositiveInt
    最慢: PositiveInt

class 升级需求(BaseModel):
    """
    表示单次升级所需的数据结构。
    """
    升级至: PositiveInt = Field(..., description="升级到的目标等级")
    需求经验值: 需求经验值


class 升级数据(BaseModel):
    """
    根模型，用于容纳整个升级数据列表并执行高级校验。
    """
    数据: list[升级需求] = Field(..., min_length=1, description="升级需求记录列表")

    @field_validator('数据')
    @classmethod
    def 校验升级等级的连续性和唯一性(cls, 升级列表: list[升级需求]) -> list[升级需求]:
        """
        校验所有升级记录中的目标等级是否唯一且连续。
        """
        if not 升级列表:
            return 升级列表

        # 提取所有 "升级至" 的等级
        levels = [item.升级至 for item in 升级列表]

        # 校验: "升级至" 的值不可重复
        if len(levels) != len(set(levels)):
            raise ValueError('校验失败: “升级至”的值包含重复项。')

        # 校验: "升级至" 的值必须从2开始且连续
        sorted_levels = sorted(levels)
        # 假设等级从1升到2开始
        expected_levels = list(range(2, sorted_levels[-1] + 1))
        if sorted_levels != expected_levels:
            raise ValueError(f'校验失败: “升级至”的值不连续。期望是 {expected_levels}，实际是 {sorted_levels}。')

        return 升级列表


class 升级需求经验值管理器:
    """
    管理和查询宝可梦升级所需的经验值数据。
    """

    def __init__(self, 原始升级数据: list[dict]):
        try:
            # 1. 使用Pydantic模型验证和解析数据
            validated_data = 升级数据.model_validate({'数据': 原始升级数据})

            # 2. 初始化内部数据结构
            # _等级查找表: 通过等级快速查找到对应的经验值对象
            self._等级查找表: dict[int, 需求经验值] = {}

            # 获取所有成长速度的名称，如 ['最快', '快', ...]
            growth_speeds = list(需求经验值.model_fields.keys())

            # _排序经验列表: 按成长速度分类，存储排序好的 (等级, 经验值) 元组列表，用于快速查找
            self._排序经验列表: dict[str, list[tuple[int, int]]] = {
                speed: [] for speed in growth_speeds
            }

            # 3. 填充数据
            for item in validated_data.数据:
                self._等级查找表[item.升级至] = item.需求经验值
                for speed in growth_speeds:
                    exp_value = getattr(item.需求经验值, speed)
                    self._排序经验列表[speed].append((item.升级至, exp_value))

            # 4. 对每个成长速度的经验值列表按经验值进行排序，用于后续的二分查找
            for speed in self._排序经验列表:
                self._排序经验列表[speed].sort(key=lambda x: x[1])

        except ValidationError as e:
            # 将Pydantic的校验错误重新包装成更通用的ValueError，方便上层统一处理
            raise ValueError(f"升级数据校验失败: {e}") from e

    def 获取经验值(self, 等级: int, 成长速度: str) ->int:
        """
        根据等级和成长速度，获取达到该等级所需的总经验值。
        """
        if 等级 < 2:
            return 0

        exp_data = self._等级查找表.get(等级)

        if not exp_data:
            return None

        return getattr(exp_data, 成长速度, None)

    def 获取最大等级(self) -> int:
        """
        返回数据中定义的最大等级。
        """
        if not self._等级查找表:
            return 1  # 如果没有数据，默认最大等级为1
        return max(self._等级查找表.keys())

    def 根据经验值获取等级(self, 经验: int, 成长速度: str) -> int:
        """
        根据当前经验值和成长速度，返回对应的当前等级。
        """
        # 验证成长速度是否存在
        if 成长速度 not in self._排序经验列表:
            valid_speeds = ", ".join(self._排序经验列表.keys())
            raise ValueError(f"无效的成长速度: '{成长速度}'。有效值为: {valid_speeds}")

        经验值列表 = self._排序经验列表[成长速度]

        # 如果经验值列表为空，则返回初始等级1
        if not 经验值列表:
            return 1

        # 提取所有升级所需的经验阈值
        经验阈值 = [item[1] for item in 经验值列表]

        idx = bisect.bisect_right(经验阈值, 经验)

        if idx == 0:
            # 当前经验值小于第一个升级门槛
            return 1
        else:
            return 经验值列表[idx - 1][0]

    def 获取到达等级所需经验(self, 目标等级: int, 成长速度: str) -> int:
        if 目标等级 <= 1:
            return 0

        所需经验的对应等级 = 目标等级

        return self.获取经验值(所需经验的对应等级, 成长速度)