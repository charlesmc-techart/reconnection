from __future__ import annotations

from enum import Enum
from typing import NoReturn


class StringEnum(Enum):
    def __str__(self) -> str:
        return f"{self.value}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return f"{self}" == other
        return super().__eq__(other)

    def __len__(self) -> int:
        return len(f"{self}")

    def __radd__(self, other: object) -> str | NoReturn:
        if isinstance(other, str):
            return other + f"{self}"
        raise NotImplementedError
