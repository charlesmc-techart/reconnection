from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import maya.cmds as cmds
import maya.mel as mel

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
    """Call the MEL procedure for exporting a geometry cache"""
    cmds.workspace(fileRule=("fileCache", dir.as_posix()))

    # global proc stirng[] doCreateGeometryCache( int $version, string $args[] )
    #     $version == 1:
    #         $args[0] =  time range mode:
    #             time range mode = 0 : use $args[1] and $args[2] as start-end
    #             time range mode = 1 : use render globals
    #             time range mode = 2 : use timeline
    #          $args[1] = start frame (if time range mode == 0)
    #          $args[2] = end frame (if time range mode == 0)

    #     $version == 2:
    #          $args[3] = cache file distribution, either "OneFile"
    #                     or "OneFilePerFrame"
    #          $args[4] = 0/1, whether to refresh during caching
    #          $args[5] = directory for cache files, if "", then use project
    #                     data dir
    #          $args[6] = 0/1, whether to create a cache per geometry
    #          $args[7] = name of cache file. An empty string can be used to
    #                     specify that an auto-generated name is acceptable.
    #          $args[8] = 0/1, whether the specified cache name is to be used
    #                     as a prefix

    #     $version == 3:
    #          $args[9] = action to perform: "add", "replace", "merge",
    #                     "mergeDelete" or "export"
    #         $args[10] = force save even if it overwrites existing files
    #         $args[11] = simulation rate, the rate at which the cloth
    #                     simulation is forced to run
    #         $args[12] = sample mulitplier, the rate at which samples are
    #                     written, as a multiple of simulation rate.

    #     $version == 4:
    #         $args[13] = 0/1, whether modifications should be inherited
    #                     from the cache about to be replaced. Valid
    #                     only when $action == "replace".
    #         $args[14] = 0/1, whether to store doubles as floats

    #     $version == 5:
    #         $args[15] = name of cache format

    #     $version == 6:
    #         $args[16] = 0/1, whether to export in local or world space
    doCreateGeometryCacheCmd = (
        f'doCreateGeometryCache 6 {{"2", "1", "10", "OneFile", "0", '
        f'"{dir.as_posix()}", "0", "{filename}", "0", "export", '
        '"1", "1", "1", "0", "0", "mcx", "1"}'
    )
    with mobj.TemporarySelection(geometry):
        mel.eval(doCreateGeometryCacheCmd)


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
