#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy

import os
import shutil
import subprocess
import traceback
from collections import deque
from functools import partial
from pathlib import Path

import rec.modules.queue as mqueue

_SCRIPTS_DIR = Path(__file__).parents[1]
_RENDER_QUEUE = _SCRIPTS_DIR / "__render_queue.txt"
_FAILED_QUEUE = _SCRIPTS_DIR / "__render_queue_failed.csv"


runCmd = partial(subprocess.run, capture_output=True, text=True)


def renderFlair(scene: str) -> None:
    args = (
        "mayabatch",
        "-file",
        scene,
        "-command",
        'python(""Import flair_batch"") -noAutoloagPlugins',
    )
    results = runCmd(args)
    print(results)


def renderArnold(scene: str) -> None:
    args = ("Render", "-renderer", "arnold", scene)
    results = runCmd(args)
    print(results)


# @mapp.logScriptEditorOutput
def main():
    mayaPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
    os.environ["PATH"] += f"{os.pathsep}{mayaPath}"

    # Backup the queue
    shutil.copy(_RENDER_QUEUE, f"{_RENDER_QUEUE}~")

    queue = mqueue.readTxtQueue(_RENDER_QUEUE)
    failedQueue: deque[tuple[str, str]] = deque()

    while queue:
        scene = queue.popleft().strip()

        print(f"Rendering: {scene!r}")
        try:
            if "arnold" in os.path.basename(scene):
                renderArnold(scene=scene)
            else:
                renderFlair(scene=scene)
        except Exception as e:
            failedQueue.append((scene, f"{e}"))
            mqueue.updateCsvQueue(_FAILED_QUEUE, queue=failedQueue)  # type: ignore

        mqueue.updateTxtQueue(_RENDER_QUEUE, queue=queue)


if __name__ == "__main__":
    main()
