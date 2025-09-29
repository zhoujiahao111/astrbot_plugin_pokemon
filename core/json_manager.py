from typing import TYPE_CHECKING
from ..utils import text_utils

from ..dtos import *


class json管理器:
    _对象 = None
    _已初始化 = False

    def __new__(cls, *args, **kwargs):
        if not cls._对象:
            cls._对象 = super().__new__(cls)
        return cls._对象

    def __init__(self):
        if self._已初始化:
            return

        self._初始伙伴 = None
        self._道具 = None
        self._宝可梦图鉴 = None
        self._升级需求经验值 = None
        self._天气 = None
        self._性格 = None
        self._招式 = None
        self._违禁词 = None
        self._随机文案 = None
        self._已初始化 = True

    @property
    def 初始伙伴(self) -> "伙伴管理器":
        if self._初始伙伴 is None:
            self._初始伙伴 = 伙伴管理器(text_utils.读取json方法("初始伙伴"))

        return self._初始伙伴

    @property
    def 道具(self) -> "道具管理器":
        if self._道具 is None:
            self._道具 = 道具管理器(text_utils.读取json方法("道具"))

        return self._道具

    @property
    def 宝可梦图鉴(self) -> "宝可梦图鉴管理器":
        if self._宝可梦图鉴 is None:
            self._宝可梦图鉴 = 宝可梦图鉴管理器(text_utils.读取json方法("宝可梦图鉴"))

        return self._宝可梦图鉴

    @property
    def 升级需求经验值(self) -> "升级需求经验值管理器":
        if self._升级需求经验值 is None:
            self._升级需求经验值 = 升级需求经验值管理器(text_utils.读取json方法("升级需求经验值"))

        return self._升级需求经验值

    @property
    def 天气(self) -> "天气管理器":
        if self._天气 is None:
            self._天气 = 天气管理器(text_utils.读取json方法("天气"))

        return self._天气

    @property
    def 性格(self) -> "性格管理器":
        if self._性格 is None:
            self._性格 = 性格管理器(text_utils.读取json方法("性格"))

        return self._性格

    @property
    def 招式(self) -> "招式管理器":
        if self._招式 is None:
            self._招式 = 招式管理器(text_utils.读取json方法("招式"))

        return self._招式

    @property
    def 违禁词(self) -> "违禁词管理器":
        if self._违禁词 is None:
            self._违禁词 = 违禁词管理器(text_utils.读取json方法("违禁词"))

        return self._违禁词

    @property
    def 随机文案(self) -> "随机文案管理器":
        if self._随机文案 is None:
            self._随机文案 = 随机文案管理器(text_utils.读取json方法("随机文案"))

        return self._随机文案
