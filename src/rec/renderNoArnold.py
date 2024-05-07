#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Batch render using Flair"""

__author__ = "Charles Mesa Cayobit"

import os
import shutil
import subprocess
import sys
from functools import partial
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parents[1]
sys.path.insert(0, f"{_SCRIPTS_DIR}")

import rec.modules.files.paths as fpath
import rec.modules.queue as mqueue

RENDER_QUEUE = _SCRIPTS_DIR / "__render_queue.txt"
FAILED_TO_RENDER = _SCRIPTS_DIR / "__render_failed.txt"

MAYA_PATH = os.path.join(os.environ["MAYA_LOCATION"], "bin", "mayabatch")


def render(scene: Path) -> None:
    args = (
        MAYA_PATH,
        "-file",
        scene.as_posix(),
        "-proj",
        fpath.findSharedDrive().as_posix(),
        "-command",
        'python("import rec.renderFlair")',
        "-noAutoloadPlugins",
    )
    subprocess.run(args, stdout=sys.stdout, stderr=sys.stderr)


def main() -> None:
    border = partial(print, "", "#" * 80, "", sep="\n")
    border()

    shutil.copy(RENDER_QUEUE, f"{RENDER_QUEUE}~")

    print("Starting render...", "", sep="\n")

    queue = mqueue.readTxt(RENDER_QUEUE)
    while queue:
        scene = queue.popleft().strip()
        if os.path.isfile(scene):
            render(Path(scene))
        else:
            with FAILED_TO_RENDER.open("a", encoding="utf8") as f:
                print(scene, file=f)

        mqueue.updateTxt(RENDER_QUEUE, queue=queue)

    print("", "Render done!", sep="\n")
    border()


if __name__ == "__main__":
    main()
