#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Batch render scenes from a queue; to be called by Cmd or Zsh"""

import os
import shutil

import rec.modules.queue as mqueue


def main():
    shutil.copy(mqueue.RENDER_QUEUE, f"{mqueue.RENDER_QUEUE}~")

    queue = mqueue.readTxtQueue(mqueue.RENDER_QUEUE)

    while True:
        try:
            scene = queue.popleft().strip()
        except IndexError:  # Queue is empty
            return
        if os.path.isfile(scene):
            break
        with mqueue.FAILED_QUEUE.open("a", encoding="utf8") as f:
            f.write(scene)

    if "arnold" in os.path.basename(scene):
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
            "-noAutoloagPlugins",
            sep=",",
        )

    mqueue.updateTxtQueue(mqueue.RENDER_QUEUE, queue=queue)


if __name__ == "__main__":
    main()
