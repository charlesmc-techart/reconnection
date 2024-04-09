#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Export Mechanic geometry caches"""

import shutil
from pathlib import Path

import maya.cmds as cmds
import maya.standalone

maya.standalone.initialize()

import rec.export_cachesCamera as ecc
import rec.export_geometryCache as egc
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.files.queue as fqueue
import rec.modules.maya.objects as mobj

_SCRIPTS_DIR = Path(__file__).parents[1]
_EXPORT_QUEUE = _SCRIPTS_DIR / "__cache_queue.txt"


def main() -> None:
    # Backup the queue
    shutil.copy(_EXPORT_QUEUE, f"{_EXPORT_QUEUE}.bak")

    queue = fqueue.readTxtQueue(_EXPORT_QUEUE)

    while queue:
        scene = Path(queue.popleft())

        shot = fname.ShotID.fromFilename(scene.stem)
        shotDir = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
        cachesDir = shotDir / fpath.CACHES_DIR

        mechanicFilename = egc.constructFilename(
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
        ecc.exportGeometryCache(
            mobj.MECHANIC_MODEL_GEO_GRP,
            dir=cachesDir,
            filename=mechanicFilename,
        )

        fqueue.updateTxtQueue(_EXPORT_QUEUE, queue=queue)


if __name__ == "__main__":
    main()

maya.standalone.uninitialize()
