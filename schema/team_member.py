from __future__ import annotations
from typing import TYPE_CHECKING

# coding=utf-8
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .base import Base

if TYPE_CHECKING:
    from .team import 队伍信息表
    from .pokemon_orm import 宝可梦表

class 队伍成员表(Base):
    __tablename__ = '队伍成员表'

    队伍ID = Column(Integer, ForeignKey('队伍信息表.队伍ID', ondelete='CASCADE'), primary_key=True)
    宝可梦ID = Column(Integer, ForeignKey('宝可梦表.主键ID', ondelete='CASCADE'), nullable=False, unique=True)
    位置索引 = Column(Integer, nullable=False, primary_key=True)

    # 关系定义
    队伍 = relationship("队伍信息表", back_populates="成员列表")
    宝可梦 = relationship("宝可梦表")
