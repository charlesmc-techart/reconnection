from __future__ import annotations

from enum import Enum


class StringEnum(str, Enum):
    """Enum that also behaves like a string"""

    def __str__(self) -> str:
        return f"{self.value}"
