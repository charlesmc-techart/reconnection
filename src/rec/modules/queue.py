import csv
from collections import deque
from collections.abc import Sequence
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parents[2]

RENDER_QUEUE = _SCRIPTS_DIR / "__render_queue.txt"
FAILED_QUEUE = _SCRIPTS_DIR / "__render_queue_failed.csv"


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


def updateCsvQueue(file: Path, queue: deque[Sequence[str]]) -> None:
    with file.open("w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(queue)
