from __future__ import annotations
from typing import TYPE_CHECKING

# coding=utf-8
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
    Index,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

if TYPE_CHECKING:
    from .user import 用户表
    from .move import 招式表


class 宝可梦表(Base):
    __tablename__ = '宝可梦表'

    __table_args__ = (
        Index('idx_pokemon_owner', '用户ID'),
        UniqueConstraint('用户ID', '盒子序号', name='idx_user_warehouse_slot'),
    )

    主键ID = Column(Integer, primary_key=True, autoincrement=True)
    用户ID = Column(Integer, ForeignKey('用户表.用户ID', ondelete='CASCADE'), nullable=False)
    编号 = Column(Integer, nullable=False)
    昵称 = Column(Text)
    经验 = Column(Integer, nullable=False, default=0)
    天赋 = Column(Integer, nullable=False)
    性格 = Column(Text, nullable=False)
    性别 = Column(Text, nullable=False)
    心情 = Column(Integer, nullable=False, default=60)
    盒子序号 = Column(Integer)
    注册日期 = Column(TIMESTAMP, default=func.now())

    # 关系定义
    主人 = relationship("用户表", back_populates="宝可梦列表")
    招式列表 = relationship("招式表", back_populates="宝可梦", cascade="all, delete-orphan")
