from __future__ import annotations
from typing import TYPE_CHECKING
# coding=utf-8
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

if TYPE_CHECKING:
    from .user import 用户表

class 激活效果表(Base):
    __tablename__ = '激活效果表'

    __table_args__ = (
        UniqueConstraint('用户ID', '物品名称', name='_user_item_uc'),
    )

    主键ID = Column(Integer, primary_key=True, autoincrement=True)
    用户ID = Column(Integer, ForeignKey('用户表.用户ID', ondelete='CASCADE'), nullable=False)
    物品名称 = Column(Text, nullable=False)
    到期日期 = Column(TIMESTAMP, default=func.now())

    用户 = relationship("用户表", back_populates="激活效果列表")
