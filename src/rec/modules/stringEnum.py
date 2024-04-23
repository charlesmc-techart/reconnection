from __future__ import annotations

__author__ = "Charles Mesa Cayobit"

from enum import Enum


class StringEnum(str, Enum):
    """Enum that also behaves like a string"""

    def __str__(self) -> str:
        return f"{self.value}"
