#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Import or export Mechanic geometry caches"""

import shutil
from pathlib import Path

import maya.cmds as cmds

import rec.geometryCache
import rec.geometryCachesCamera
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.queue as mqueue

_SCRIPTS_DIR = Path(__file__).parents[1]
_EXPORT_QUEUE = _SCRIPTS_DIR / "__cache_queue.txt"


def main() -> None:
    # Backup the queue
    shutil.copy(_EXPORT_QUEUE, f"{_EXPORT_QUEUE}~")

    queue = mqueue.readTxt(_EXPORT_QUEUE)

    while queue:
        scene = Path(queue.popleft())

        shot = fname.ShotId.fromFilename(scene.stem)
        shotDir = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
        cachesDir = shotDir / fpath.CACHES_DIR

        mechanicFilename = rec.geometryCache.constructFilename(
            dir=cachesDir,
            shot=shot,
            assetName=fname.AssetName.MECHANIC,
            assetType=fname.AssetType.CACHE,
        )

        print(
            "",
            f"Exporting {shot} Mechanic geometry cache to:",
            cachesDir,
            "",
            sep="\n",
        )

        cmds.file(scene, open=True)
        rec.geometryCachesCamera.exportGeometryCache(
            mobj.MECHANIC_MODEL_GEO_GRP,
            dir=cachesDir,
            filename=mechanicFilename,
        )

        mqueue.updateTxt(_EXPORT_QUEUE, queue=queue)


if __name__ == "__main__":
    with mapp.Standalone():
        main()
