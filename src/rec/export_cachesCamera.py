from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import NoReturn, Optional

import maya.cmds as cmds

import rec.export_geometryCache as ogcs
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui

_EXPORT_MAYA_BINARY_SCRIPT = "export_mayaBinary.py"


def exportGeometryCache(
    geometryGrp: mobj.DAGNode, dir: Path, filename: str
) -> None:
    geometry = mobj.lsChildren(geometryGrp)
    ogcs.exportGeometryCache(geometry, dir=dir, filename=filename)


def exportAlembicCache(geometry: mobj.DAGNode, filePath: Path) -> None:
    mapp.loadPlugin("AbcExport")
    cmds.workspace(fileRule=("alembicCache", filePath.parent.as_posix()))

    startTime = cmds.playbackOptions(query=True, animationStartTime=True)
    endTime = cmds.playbackOptions(query=True, animationEndTime=True)
    args = (
        f'-file "{filePath.as_posix()}" -root {geometry} '
        f"-frameRange {startTime} {endTime} -worldSpace"
    )
    cmds.AbcExport(jobArg=args)


# TODO: fix type annotation
def getCameraComponents(
    cameraGrp: mobj.TopLevelGroup,
) -> Optional[tuple[mobj.DAGNode, ...]] | NoReturn:
    try:
        camera = mobj.lsChildren(cameraGrp, allDescendents=True, type="camera")
    except ValueError as e:
        raise mobj.TopLevelGroupDoesNotExistError("_____CAMERA_____") from e
    try:
        camera = camera[0]
    except TypeError:
        return None

    cmds.setAttr(camera + ".renderable", True)
    xform = mobj.getParent(camera)

    try:
        lookAt = cmds.listConnections(camera, type="lookAt")[0]
    except TypeError:
        return xform, camera

    target = lookAt + ".target[0].targetParentMatrix"
    locator = cmds.listConnections(target)[0]
    locatorShape = mobj.lsChildren(locator, shapes=True)[0]
    return lookAt, xform, camera, locator, locatorShape


def exportMayaAsciiThenBinary(
    nodes: Sequence[mobj.DGNode], filePath: Path
) -> None:
    prefix = fname.SHOW + "_"
    with TemporaryDirectory(prefix=prefix) as tempDir:
        tempFilePath = Path(tempDir) / f"{prefix}temp{fname.FileExt.MAYA_ASCII}"

        mobj.exportNodes(
            nodes, filePath=tempFilePath, fileType=mapp.FileType.ASCII
        )

        mayaBinPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
        if mayaBinPath not in sys.path:
            sys.path.append(mayaBinPath)
        scriptPath = Path(__file__).resolve()
        scriptPath = scriptPath.with_name(_EXPORT_MAYA_BINARY_SCRIPT)

        results = subprocess.run(
            ("mayapy", scriptPath, tempFilePath, filePath, *nodes),
            capture_output=True,
            text=True,
        )
        print(results.stderr)


def exportCamera(cameraNodes: Sequence[mobj.DAGNode], filePath: Path) -> None:
    if mobj.lsUnknown():
        exportMayaAsciiThenBinary(cameraNodes, filePath=filePath)
    else:
        mobj.exportNodes(
            cameraNodes, filePath=filePath, fileType=mapp.FileType.BINARY
        )


def buildWindow(outputPath: Path) -> mui.ProgressWindow:
    ui = mui.ProgressWindow("progressWindow", "Cache & Camera Exporter")

    def defineTask(product: str) -> str:
        return f"Exporting {product} to:\n{outputPath}"

    ui.build().initialize(
        defineTask("Mechanic geometry cache"),
        defineTask("Robot geometry cache"),
        defineTask("Robot face alembic cache"),
        defineTask("camera"),
    ).update()

    return ui


# FIXME: make exporting to test folder separate from main
@mapp.SuspendedRedraw()
@mapp.logScriptEditorOutput
def main() -> None:
    shot = fname.ShotID.getFromFilename(mapp.getScenePath().stem)
    gDriveShotDir = fpath.getShotPath(shot, parentDir=fpath.getSharedDrive())
    shotCachesDirPath = gDriveShotDir / fpath.CACHE_DIR
    # shotCachesDirPath = mapp.getScenePath().parents[1] / "cache"

    constructFilenameCmd = partial(
        ogcs.constructFilename,
        dir=shotCachesDirPath,
        shot=shot,
    )
    exportGeometryCacheCmd = partial(exportGeometryCache, dir=shotCachesDirPath)

    ui = buildWindow(shotCachesDirPath).show()

    mechanicRigGeoGrp = mobj.MECHANIC_RIG_GEO_GRP
    if cmds.objExists(mechanicRigGeoGrp):
        mechanicFilename = constructFilenameCmd(
            assetName=fname.AssetName.MECHANIC,
            assetType=fname.AssetType.CACHE,
        )
        exportGeometryCacheCmd(mechanicRigGeoGrp, filename=mechanicFilename)
    ui.update()

    robotRigGeoGrp = mobj.ROBOT_RIG_GEO_GRP
    if cmds.objExists(robotRigGeoGrp):
        robotFilename = constructFilenameCmd(
            assetName=fname.AssetName.ROBOT,
            assetType=fname.AssetType.CACHE,
        )
        exportGeometryCacheCmd(robotRigGeoGrp, filename=robotFilename)
    ui.update()

    robotFaceRigGeoGrp = mobj.ROBOT_FACE_RIG_GEO
    if cmds.objExists(robotFaceRigGeoGrp):
        robotFaceFilename = constructFilenameCmd(
            assetName=fname.AssetName.ROBOT_FACE,
            assetType=fname.AssetType.CACHE,
        )
        exportAlembicCache(
            robotFaceRigGeoGrp,
            filePath=shotCachesDirPath
            / (robotFaceFilename + fname.FileExt.ALEMBIC),
        )
    ui.update()

    if cameraNodes := getCameraComponents(mobj.TopLevelGroup.CAMERA):
        cameraFilename = constructFilenameCmd(assetType=fname.AssetType.CAMERA)
        exportCamera(
            cameraNodes,
            filePath=shotCachesDirPath
            / (cameraFilename + fname.FileExt.MAYA_BINARY),
        )
    ui.close()
