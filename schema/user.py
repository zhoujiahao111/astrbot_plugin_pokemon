from __future__ import annotations
# coding=utf-8
from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import TYPE_CHECKING
from .base import Base  # 导入共享的 Base

# TYPE_CHECKING 块用于类型提示，避免运行时循环导入
if TYPE_CHECKING:
    from .pokemon_orm import 宝可梦表
    from .user_item import 用户物品表
    from .activation_effect import 激活效果表
    from .team import 队伍信息表

class 用户表(Base):
    __tablename__ = '用户表'

    用户ID = Column(Integer, primary_key=True)
    群ID = Column(BigInteger, nullable=False, default=0)
    金钱 = Column(Integer, nullable=False, default=0)
    当前队伍ID = Column(Integer, ForeignKey('队伍信息表.队伍ID', ondelete='SET NULL'))
    注册日期 = Column(DateTime, default=datetime.now)

    # 当一个用户被删除时，与该用户关联的所有宝可梦也应被删除。
    宝可梦列表 = relationship("宝可梦表", back_populates="主人", cascade="all, delete-orphan")

    # 当一个用户被删除时，其所有物品记录也应被删除。
    物品列表 = relationship("用户物品表", back_populates="用户", cascade="all, delete-orphan")

    # 当一个用户被删除时，其所有激活效果记录也应被删除。
    激活效果列表 = relationship(
        "激活效果表",
        back_populates="用户",
        cascade="all, delete-orphan"
    )

    # 当一个用户被删除时，其创建的所有队伍都应被删除。
    # ondelete='CASCADE' 在数据库层面处理，而 cascade="all, delete-orphan" 在ORM层面处理。
    队伍列表 = relationship(
        "队伍信息表",
        back_populates="用户",
        foreign_keys="[队伍信息表.用户ID]",
        cascade="all, delete-orphan"
    )

    # 这只是一个视图，用于方便地获取当前队伍，不需要 cascade。
    当前队伍 = relationship("队伍信息表", foreign_keys=[当前队伍ID])