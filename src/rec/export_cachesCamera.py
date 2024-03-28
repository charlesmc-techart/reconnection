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

import rec.export_geometryCache as ogc
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui

_SUBPROCESS_SCRIPT_FILENAME = "export_mayaBinary.py"
_SUBPROCESS_SCRIPT_PATH = Path(__file__).with_name(_SUBPROCESS_SCRIPT_FILENAME)


def exportGeometryCache(
    geometryGrp: mobj.DAGNode, dir: Path, filename: str
) -> None:
    """Export a geometry cache for all geometry under a group"""
    geometry = mobj.lsChildren(geometryGrp)
    ogc.export(geometry, dir=dir, filename=filename)


def exportAlembicCache(geometry: mobj.DAGNode, filePath: Path) -> None:
    """Export an Alembic cache"""
    mapp.loadPlugin("AbcExport")
    cmds.workspace(fileRule=("alembicCache", filePath.parent.as_posix()))

    startTime = cmds.playbackOptions(query=True, animationStartTime=True)
    endTime = cmds.playbackOptions(query=True, animationEndTime=True)
    args = (
        f'-file "{filePath.as_posix()}" -root {geometry} '
        f"-frameRange {startTime} {endTime} -worldSpace"
    )
    cmds.AbcExport(jobArg=args)


def getCameraComponents(
    cameraGrp: mobj.TopLevelGroup,
) -> Optional[tuple[mobj.DAGNode, ...]] | NoReturn:
    """Get all components of a shot camera: transform and shape nodes

    If the camera uses a camera and aim, get the lookAt and locator nodes, too.
    """
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


# TODO: do I need a subprocess at all? Check other maya executables in bin
# TODO: check if TemporaryDirectories have methods similar to TemporaryFiles
# TODO: use maya.cmds module to get MAYA_LOCATION instead of os.environ?
def exportMayaAsciiThenBinary(
    nodes: Sequence[mobj.DGNode], filePath: Path
) -> None:
    """Export the nodes to a temporary ASCII file before a binary one

    The nodes exported to an ASCII file in a temporary directory. Then, another
    instance of Maya is opened to export the nodes into a binary file.
    """
    prefix = fname.SHOW + "_"
    asciiFilename = f"{prefix}temp{fname.FileExt.MAYA_ASCII}"
    with TemporaryDirectory(prefix=prefix) as tempDir:
        asciiFilePath = Path(tempDir) / asciiFilename

        mobj.export(nodes, filePath=asciiFilePath, fileType=mapp.FileType.ASCII)

        mayaPath = os.path.join(os.environ["MAYA_LOCATION"], "bin")
        if mayaPath not in sys.path:
            sys.path.append(mayaPath)

        results = subprocess.run(
            (
                "mayapy",
                _SUBPROCESS_SCRIPT_PATH,
                asciiFilePath,
                filePath,
                *nodes,
            ),
            capture_output=True,
            text=True,
        )
    print(results.stderr)


def exportCamera(cameraNodes: Sequence[mobj.DAGNode], filePath: Path) -> None:
    """If unknown nodes are present, temporarily export to an ASCII file"""
    if mobj.lsUnknown():
        exportMayaAsciiThenBinary(cameraNodes, filePath=filePath)
        return

    mobj.export(cameraNodes, filePath=filePath, fileType=mapp.FileType.BINARY)


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
    shot = fname.ShotID.fromFilename(fpath.getScenePath().stem)
    shotDir = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
    cachesDir = shotDir / fpath.CACHES_DIR
    # cachesDir = fpath.getScenePath().parents[1] / "cache"

    constructFilenameCmd = partial(
        ogc.constructFilename,
        dir=cachesDir,
        shot=shot,
    )
    exportGeometryCacheCmd = partial(exportGeometryCache, dir=cachesDir)

    ui = buildWindow(cachesDir).show()

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
            filePath=cachesDir / (robotFaceFilename + fname.FileExt.ALEMBIC),
        )
    ui.update()

    if cameraNodes := getCameraComponents(mobj.TopLevelGroup.CAMERA):
        cameraFilename = constructFilenameCmd(assetType=fname.AssetType.CAMERA)
        exportCamera(
            cameraNodes,
            filePath=cachesDir / (cameraFilename + fname.FileExt.MAYA_BINARY),
        )
    ui.update().close()
