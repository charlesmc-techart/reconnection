#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy
"""Export Mechanic geometry caches"""

from argparse import ArgumentParser
from functools import partial
from pathlib import Path

import maya.cmds as cmds
import maya.standalone

maya.standalone.initialize()

import rec.export_cachesCamera as ecc
import rec.export_geometryCache as egc
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.objects as mobj


def main(scenePaths: list[Path]) -> None:
    sharedDrive = fpath.findSharedDrive()

    for scene in scenePaths:
        cmds.file(scene, open=True)
        shot = fname.ShotID.fromFilename(filename=scene.stem)
        shotDir = fpath.findShotPath(shot=shot, parentDir=sharedDrive)
        cachesDir = shotDir / fpath.CACHES_DIR

        constructFilenameCmd = partial(
            egc.constructFilename, dir=cachesDir, shot=shot
        )

        mechanicRigGeoGrp = mobj.MECHANIC_MODEL_GEO_GRP

        print(
            "",
            f"Exporting {shot} Mechanic geometry cache to:",
            cachesDir,
            "",
            sep="\n",
        )

        mechanicFilename = constructFilenameCmd(
            assetName=fname.AssetName.MECHANIC, assetType=fname.AssetType.CACHE
        )
        ecc.exportGeometryCache(
            mechanicRigGeoGrp, dir=cachesDir, filename=mechanicFilename
        )


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="re:connection Queued Mechanic Geometry Cache Exporter",
        description=__doc__,
    )
    parser.add_argument(
        "scenes", type=Path, nargs="+", help="paths to Maya scene files"
    )
    args = parser.parse_args()

    main(args.scenes)

maya.standalone.uninitialize()
