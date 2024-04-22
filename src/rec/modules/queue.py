import csv
from collections import deque
from collections.abc import Sequence
from pathlib import Path


def readTxt(file: Path) -> deque[str]:
    with file.open("r", encoding="utf-8") as f:
        return deque(f)


def updateTxt(file: Path, queue: deque[str]) -> None:
    with file.open("w", encoding="utf-8") as f:
        f.writelines(queue)


def readCsv(file: Path) -> deque[list[str]]:
    with file.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return deque(reader)


def updateCsv(file: Path, queue: deque[Sequence[str]]) -> None:
    with file.open("w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(queue)
