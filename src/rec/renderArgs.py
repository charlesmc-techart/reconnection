#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Construct the args needed to batch render with Cmd or Zsh"""

__author__ = "Charles Mesa Cayobit"

import os
import shutil
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parents[1]
sys.path.insert(0, f"{_SCRIPTS_DIR}")

import rec.modules.files.paths as fpath
import rec.modules.queue as mqueue

ARGS_FILE = _SCRIPTS_DIR / "__render_args.cmd"

RENDER_QUEUE = _SCRIPTS_DIR / "__render_queue.txt"
FAILED_TO_RENDER = _SCRIPTS_DIR / "__render_failed.txt"


def main() -> None:
    shutil.copy(RENDER_QUEUE, f"{RENDER_QUEUE}~")

    queue = mqueue.readTxt(RENDER_QUEUE)
    while True:
        try:
            scene = queue.popleft().strip()
        except IndexError:  # Queue is empty
            sys.exit(1)  # Break out of the while loop in Cmd / Zsh
        if os.path.isfile(scene):
            scene = Path(scene)
            break
        mqueue.updateTxt(RENDER_QUEUE, queue=queue)
        with FAILED_TO_RENDER.open("a", encoding="utf8") as f:
            print(scene, file=f)

    mayaPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
    if "arnold" in scene.stem:
        args = (
            f'"{os.path.join(mayaPath, "Render")}"',
            "-renderer",
            "arnold",
            "-proj",
            f'"{fpath.findSharedDrive().as_posix()}"',
            "-ai:threads",
            "-1",
            "-ai:aerr",
            "true",
            "-ai:alf",
            "true",
            f'"{scene}"',
        )
    else:
        args = (
            f'"{os.path.join(mayaPath, "mayabatch")}"',
            "-file",
            f'"{scene}"',
            "-proj",
            f'"{fpath.findSharedDrive().as_posix()}"',
            "-command",
            '"python(\\"import rec.renderFlair\\")"',
            "-noAutoloadPlugins",
        )
    with ARGS_FILE.open("w", encoding="utf-8") as f:
        print(*args, file=f)

    mqueue.updateTxt(RENDER_QUEUE, queue=queue)


if __name__ == "__main__":
    main()
