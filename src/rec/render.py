#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy

import csv
import os
import shutil
import subprocess
import sys
from collections import deque
from functools import partial
from pathlib import Path
from time import sleep

_SCRIPTS_DIR = Path(__file__).parents[1]
_RENDER_QUEUE = _SCRIPTS_DIR / "render_queue.txt"

_openQueueCmd = partial(_RENDER_QUEUE.open, encoding="utf-8")
_readQueueCmd = partial(_openQueueCmd, "r")
_writeQueueCmd = partial(_openQueueCmd, "w")


def readTxtQueue() -> deque[str]:
    with _readQueueCmd() as f:
        return deque(f)


def updateTxtQueue(queue: deque[str]) -> None:
    with _writeQueueCmd() as f:
        f.writelines(queue)


def readCsvQueue() -> deque[list[str]]:
    with _readQueueCmd() as f:
        reader = csv.reader(f)
        return deque(reader)


def updateCsvQueue(queue: deque[list[str]]) -> None:
    with _writeQueueCmd() as f:
        writer = csv.writer(f)
        writer.writerows(queue)


def renderFlair(scene: Path) -> None: ...


def renderArnold(scene: Path) -> None:
    mayaPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
    if mayaPath not in sys.path:
        sys.path.insert(0, mayaPath)

    args = ("Render", scene)
    results = subprocess.run(args, capture_output=True, text=True)
    print(results)


# @mapp.logScriptEditorOutput
def main():
    # Backup the queue
    shutil.copy(_RENDER_QUEUE, f"{_RENDER_QUEUE}.bak")

    queue = readTxtQueue()

    while queue:
        filePath = queue.popleft()

        try:
            print(f"{filePath!r}")
        except Exception:
            raise

        updateTxtQueue(queue)

        sleep(0.5)


if __name__ == "__main__":
    main()
