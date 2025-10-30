# coding=utf-8
from ..utils import validators
from ..core.json_manager import json管理器
class 会话类:
    def __init__(self, json管理器: json管理器, 配置, 事件, **初始数据):
        """
        初始化Session对象
        """
        self.json管理器: json管理器 = json管理器

        # self.用户qq = validators.验证用户qq方法(事件.get_sender_id())
        self.用户qq = 10003
        self.用户昵称 = 事件.get_sender_name()
        self.机器人qq = 事件.get_self_id()

        # 配置项
        self.初始最大队伍上限 = 配置.get("default_max_team", 3)
        self.缓存超时时长 = 配置.get("cache_max_timeout", 120)
        self.最大回合数 = 配置.get("max_round", 120)
        self.天气间隔回合 = 配置.get("weather_interval", 3)
        self.是否生成战场图 = 配置.get("generate_battlefield", True)
        self.是否立即发送第一张战场图 = 配置.get("send_battlefield_immediately", False)
        self.是否生成mega与极巨化图 = 配置.get("generate_mega_dynamax_battlefield", True)
        self.初始金钱数 = 配置.get("initial_money", 300)
        self.战斗奖励倍率修正 = 配置.get("battle_reward_multiplier_modifier", 1.0)
        self.商店聊天记录商品数量 = 配置.get("shop_chatlog_item_count", 20)

        self.事件记录 = 事件

        self.更新(**初始数据)

    def 更新(self, **新数据):
        """更新或添加新的数据"""
        self.__dict__.update(新数据)

        for 键, 值 in 新数据.items():
            setattr(self, 键, 值)
        return self

    def 获取(self, 键, 默认值=None):
        """获取指定键的值"""
        return self.__dict__.get(键, 默认值)

    def 删除(self, *键列表):
        """删除一个或多个键值对"""
        for 键 in 键列表:
            self.__dict__.pop(键, None)

    def 存在(self, 键):
        """检查键是否存在"""
        return 键 in self.__dict__

    def 清空(self):
        """清空所有数据"""
        self.__dict__.clear()

    def 转字典(self):
        """转换为字典"""
        return self.__dict__.copy()

    def 键列表(self):
        """获取所有键"""
        return list(self.__dict__.keys())

    def 值列表(self):
        """获取所有值"""
        return list(self.__dict__.values())

    def 键值对列表(self):
        """获取所有键值对"""
        return list(self.__dict__.items())