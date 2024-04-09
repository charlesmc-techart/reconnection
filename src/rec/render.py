#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy

import os
import shutil
import subprocess
import sys
from pathlib import Path

import rec.modules.queue as mqueue

_SCRIPTS_DIR = Path(__file__).parents[1]
_RENDER_QUEUE = _SCRIPTS_DIR / "__render_queue.txt"


def renderFlair(scene: str) -> None: ...


def renderArnold(scene: str) -> None:
    mayaPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
    if mayaPath not in sys.path:
        sys.path.insert(0, mayaPath)

    args = ("Render", "-renderer", "arnold", scene)
    results = subprocess.run(args, capture_output=True, text=True)
    print(results)


# @mapp.logScriptEditorOutput
def main():
    # Backup the queue
    shutil.copy(_RENDER_QUEUE, f"{_RENDER_QUEUE}.bak")

    queue = mqueue.readTxtQueue(_RENDER_QUEUE)

    while queue:
        scene = queue.popleft()

        print(f"Rendering: {scene!r}")
        renderArnold(scene=scene)

        mqueue.updateTxtQueue(_RENDER_QUEUE, queue=queue)


if __name__ == "__main__":
    main()
