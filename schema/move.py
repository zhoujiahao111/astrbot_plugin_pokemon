from __future__ import annotations
from typing import TYPE_CHECKING
# coding=utf-8
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from .base import Base

if TYPE_CHECKING:
    from .pokemon_orm import 宝可梦表


class 招式表(Base):
    __tablename__ = '招式表'

    宝可梦ID = Column(Integer, ForeignKey('宝可梦表.主键ID', ondelete='CASCADE'), primary_key=True)
    招式名称 = Column(Text, primary_key=True)

    # 关系定义
    宝可梦 = relationship("宝可梦表", back_populates="招式列表")