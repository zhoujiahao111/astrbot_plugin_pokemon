# coding=utf-8
from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from .base import Base

if TYPE_CHECKING:
    from .user import 用户表

class 用户物品表(Base):
    __tablename__ = '用户物品表'

    用户ID = Column(Integer, ForeignKey('用户表.用户ID', ondelete='CASCADE'), primary_key=True)
    物品名称 = Column(Text, primary_key=True)
    数量 = Column(Integer, nullable=False, default=1)

    # 关系定义
    用户 = relationship("用户表", back_populates="物品列表")