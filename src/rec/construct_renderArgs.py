#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Construct the args needed to batch render with Cmd or Zsh"""

import os
import shutil
from pathlib import Path
from argparse import ArgumentParser

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
            exit(1)  # Break out of the while loop in Cmd / Zsh
        if os.path.isfile(scene):
            scene = Path(scene)
            break
        with FAILED_TO_RENDER.open("a", encoding="utf8") as f:
            f.write(f"{scene}")

    # mayaPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
    mayaPath = "/Applications/Autodesk/maya2023/Maya.app/Contents/bin"
    if "arnold" in scene.stem:
        args = (
            os.path.join(mayaPath, "Render"),
            "-renderer",
            "arnold",
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
            "-command",
            'python(""Import flair_batch"")',
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
