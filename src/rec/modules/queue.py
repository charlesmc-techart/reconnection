import csv
from collections import deque
from pathlib import Path


def readTxtQueue(file: Path) -> deque[str]:
    with file.open("r", encoding="utf-8") as f:
        return deque(f)


def updateTxtQueue(file: Path, queue: deque[str]) -> None:
    with file.open("w", encoding="utf-8") as f:
        f.writelines(queue)


def readCsvQueue(file: Path) -> deque[list[str]]:
    with file.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return deque(reader)


def updateCsvQueue(file: Path, queue: deque[list[str]]) -> None:
    with file.open("w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(queue)
