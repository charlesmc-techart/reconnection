#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Batch render a Maya scene from the queue; to be called by Cmd or Zsh"""

import os
import shutil
from pathlib import Path

import rec.modules.queue as mqueue


_SCRIPTS_DIR = Path(__file__).parents[1]

RENDER_QUEUE = _SCRIPTS_DIR / "__render_queue.txt"
FAILED_TO_RENDER = _SCRIPTS_DIR / "__render_queue_failed.csv"


def main():
    shutil.copy(RENDER_QUEUE, f"{RENDER_QUEUE}~")

    queue = mqueue.readTxtQueue(RENDER_QUEUE)
    while True:
        try:
            scene = queue.popleft().strip()
        except IndexError:  # Queue is empty
            return
        if os.path.isfile(scene):
            scene = Path(scene)
            break
        with FAILED_TO_RENDER.open("a", encoding="utf8") as f:
            f.write(f"{scene}")

    if "arnold" in scene.stem:
        print(
            os.path.join(os.environ["MAYA_LOCATION"], "bin", "Render"),
            "-renderer",
            "arnold",
            "-ai:aerr",
            "true",
            "-ai:alf",
            "true",
            scene,
            sep=",",
        )
    else:
        print(
            os.path.join(os.environ["MAYA_LOCATION"], "bin", "mayabatch"),
            "-file",
            scene,
            "-command",
            'python(""Import flair_batch"")',
            "-noAutoloadPlugins",
            sep=",",
        )

    mqueue.updateTxtQueue(RENDER_QUEUE, queue=queue)


if __name__ == "__main__":
    main()
