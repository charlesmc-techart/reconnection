#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Construct the args needed to batch render with Cmd or Zsh"""

import os
import shutil
import sys
from argparse import ArgumentParser
from pathlib import Path

import rec.modules.queue as mqueue

_SCRIPTS_DIR = Path(__file__).parents[1]

RENDER_QUEUE = _SCRIPTS_DIR / "__render_queue.txt"
FAILED_TO_RENDER = _SCRIPTS_DIR / "__render_queue_failed.csv"


def main(scriptFile: Path) -> None:
    shutil.copy(RENDER_QUEUE, f"{RENDER_QUEUE}~")

    queue = mqueue.readTxtQueue(RENDER_QUEUE)
    while True:
        try:
            scene = queue.popleft().strip()
        except IndexError:  # Queue is empty
            sys.exit(1)  # Break out of the while loop in Cmd / Zsh
        if os.path.isfile(scene):
            scene = Path(scene)
            break
        mqueue.updateTxtQueue(RENDER_QUEUE, queue=queue)
        with FAILED_TO_RENDER.open("a", encoding="utf8") as f:
            print(scene, file=f)

    mayaPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
    if "arnold" in scene.stem:
        args = (
            os.path.join(mayaPath, "Render"),
            "-renderer",
            "arnold",
            # "-proj",
            # "",
            "-ai:threads",
            "-1",
            "-ai:aerr",
            "true",
            "-ai:alf",
            "true",
            scene,
        )
    else:
        args = (
            os.path.join(mayaPath, "mayabatch"),
            "-file",
            scene,
            # "-proj",
            # "",
            "-command",
            '"python(\\"Import flair_batch\\")"',
            "-noAutoloadPlugins",
        )
    with scriptFile.open("w", encoding="utf-8") as f:
        print(*args, file=f)

    mqueue.updateTxtQueue(RENDER_QUEUE, queue=queue)


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="re:connection Batch Render Args Constructor", description=__doc__
    )
    parser.add_argument(
        "file", type=Path, help="path to script file the shell will execute"
    )
    args = parser.parse_args()
    main(args.file)
