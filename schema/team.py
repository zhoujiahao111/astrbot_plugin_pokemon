from __future__ import annotations

# coding=utf-8
from sqlalchemy import (
    Column,
    Integer,
    TIMESTAMP,
    UniqueConstraint,
    Index,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from .base import Base

if TYPE_CHECKING:  # 仅在类型检查时导入
    from .team_member import 队伍成员表
    from .user import 用户表 # 添加导入

class 队伍信息表(Base):
    __tablename__ = '队伍信息表'
    __table_args__ = (
        UniqueConstraint('用户ID', '队伍序号'),
        Index('idx_team_owner', '用户ID'),
    )

    队伍ID = Column(Integer, primary_key=True, autoincrement=True)
    用户ID = Column(Integer, ForeignKey('用户表.用户ID', ondelete='CASCADE'), nullable=False)
    队伍序号 = Column(Integer, nullable=False)
    队伍名称 = Column(Text, nullable=False, default='新队伍')
    注册日期 = Column(TIMESTAMP, default=func.now())

    成员列表 = relationship("队伍成员表", back_populates="队伍", cascade="all, delete-orphan")
    用户 = relationship("用户表", back_populates="队伍列表", foreign_keys=[用户ID])