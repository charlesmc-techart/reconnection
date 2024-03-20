from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui


def constructFilename(
    dir: Path,
    shot: fname.ShotID,
    assetType: fname.AssetType,
    assetName: Optional[fname.AssetName | str] = None,
) -> str:
    filenameBase = fname.constructFilenameBase(
        shot, assetName=assetName, assetType=assetType
    )
    assetValidator = fname.constructAssetValidator(
        filenameBase, assetName=assetName, assetType=assetType
    )
    versionSuffix = fname.constructVersionSuffix(
        assetValidator,
        files=fpath.filterShotFiles(shot, dir=dir),
    )
    return f"{filenameBase}_{versionSuffix}"


def exportGeometryCache(
    geometry: mobj.DAGNode | Sequence[mobj.DAGNode], dir: Path, filename: str
) -> None:
    with mobj.TemporarySelection(geometry):
        mobj.exportGeometryCache(dir, fileName=filename)


def getNodeNameBase(node: mobj.DAGNode) -> str:
    return node.rsplit(":", 1)[-1].rsplit("_", 1)[0]


def buildWindow(*objects: str, outputPath: Path) -> mui.ProgressWindow:
    ui = mui.ProgressWindow("progressWindow", "Geometry Cache Exporter")

    def defineTask(product: str) -> str:
        name = getNodeNameBase(product)
        return f"Exporting {name} geometry cache to:\n{outputPath}"

    ui.build().initialize(*[defineTask(o) for o in objects]).update()

    return ui


# FIXME: make exporting to test folder separate from main
@mapp.SuspendedRedraw()
@mapp.logScriptEditorOutput
def main() -> None:
    shot = fname.ShotID.getFromFilename(mapp.getScenePath().stem)
    gDriveShotDir = fpath.getShotPath(shot, parentDir=fpath.getSharedDrive())
    shotCachesDirPath = gDriveShotDir / fpath.CACHE_DIR
    shotCachesDirPath = mapp.getScenePath().parents[1] / "cache"

    # TODO: test if this actually filters xforms with just mesh shapes
    objects = [
        o
        for o in cmds.ls(selection=True, transforms=True)
        if cmds.listRelatives(o, type="mesh")
    ]
    if not objects:
        raise ValueError("No geometry is selected")

    ui = buildWindow(*objects, outputPath=shotCachesDirPath).show()

    for o in objects:
        nameBase = getNodeNameBase(o)
        filename = constructFilename(
            shotCachesDirPath,
            shot=shot,
            assetName=nameBase,
            assetType=fname.AssetType.CACHE,
        )
        exportGeometryCache(o, dir=shotCachesDirPath, filename=filename)
        ui.update()
    ui.close()
