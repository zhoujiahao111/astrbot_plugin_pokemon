# coding=utf-8
import random
from datetime import datetime
from ..models.session import 会话类
from ..dtos import 天气管理器
from ..utils import text_utils

class 天气类:
    def __init__(self, 会话: 会话类):
        self.会话 = 会话
        self.月份: str = 返回月份方法()
        self.天气间隔回合 = self.会话.天气间隔回合

        self.天气信息模型 = None
        self.下一次抽取天气回合 = None

    def 获取并更新天气方法(self, 回合: int) -> tuple[str, dict]:
        # 当没有天气信息或到了该切换天气的回合时
        if self.天气信息模型 is None or 回合 >= self.下一次抽取天气回合:
            月份到季节 = {
                "1": "冬季", "2": "冬季", "3": "春季", "4": "春季", "5": "春季",
                "6": "夏季", "7": "夏季", "8": "夏季", "9": "秋季", "10": "秋季",
                "11": "秋季", "12": "冬季"
            }

            # 1. 调用方法获取天气结果对象
            天气结果对象 = self.会话.json管理器.天气.随机抽取并生成天气(
                月份到季节.get(self.月份, "春季")
            )

            self.天气信息模型 = 天气结果对象.model_dump()

            # 3. 使用更新后的 self.天气信息字典 来设置下一次抽取回合
            self.下一次抽取天气回合 = self.天气信息模型['持续回合'] + self.天气间隔回合 + 回合

            # 4. 使用 self.天气信息字典 来构建返回的文案字典
            return "天气", {
                '月份': self.月份,
                '天气名称': self.天气信息模型['名称'],
                '天气描述': self.天气信息模型['描述'],
                '持续回合': self.天气信息模型['持续回合']
            }

        # 根据当前回合判断是生效期还是间歇期
        生效期结束回合 = self.下一次抽取天气回合 - self.天气间隔回合

        if 回合 < 生效期结束回合:
            # 天气生效期，什么都不做，因为 self.天气信息字典 已经是正确的状态
            return "", {}
        else:
            # 处于天气间歇期
            # 5. 在间歇期，也要更新 天气信息字典 为不带效果的默认值
            self.天气信息模型 = self.间歇期天气方法()

            return "天气_间歇期", {
                '间歇文案': self.天气信息模型["描述"],
                '持续回合': self.下一次抽取天气回合 - 回合
            }

    def 间歇期天气方法(self):
        return {
            "名称": "平稳",
            "持续回合": self.天气间隔回合,
            "描述": self.会话.json管理器.随机文案.获取随机文案("天气_间歇期", {"持续回合": self.天气间隔回合}),
            "属性倍率": {}  # 间歇期没有属性影响
        }

def 返回月份方法() -> str:
    return str(datetime.now().month)
