# coding=utf-8
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

T = TypeVar('T')  # 泛型，表示返回的数据类型

@dataclass
class 结果类(Generic[T]):
    """统一返回结果，包含成功/失败状态、数据和错误信息"""
    是否成功: bool
    数据信息: Optional[T] = None
    错误信息: Optional[str] = None

    @classmethod
    def 成功方法(cls, data: T) -> "结果类[T]":
        """成功时调用"""
        return cls(是否成功=True, 数据信息=data)

    @classmethod
    def 失败方法(cls, error: str) -> "结果类[T]":
        """失败时调用"""
        return cls(是否成功=False, 错误信息=error)

