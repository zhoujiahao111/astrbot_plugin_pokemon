from __future__ import annotations
from typing import Iterator

class 空招式类(list[dict]):
    """任何访问都立即抛异常，防止误用。"""
    def __getitem__(self, index: int) -> dict:
        raise RuntimeError("此处不允许读取招式数据, 请检查调用代码")

    def __iter__(self) -> Iterator[dict]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def __bool__(self) -> bool:
        return False
