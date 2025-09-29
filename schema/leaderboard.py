# coding=utf-8
import datetime
from sqlalchemy import (
    Column,
    Integer,
)
from .base import Base

class 排行榜表(Base):
    __tablename__ = '排行榜表'

    用户ID = Column(Integer, primary_key=True)
    积分 = Column(Integer, nullable=False, default=0)
    最高战斗分 = Column(Integer, nullable=False, default=0)