"""Export or import character geometry caches, Robot face alembic cache,
and camera"""

from __future__ import annotations

__author__ = "Charles Mesa Cayobit"

from functools import partial
from pathlib import Path

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel

import rec.camera
import rec.geometryCache
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui
import rec.reference

################################################################################
# Export
################################################################################


def exportGeometryCache(
    geometryGrp: mobj.DAGNode, dir: Path, filename: str
) -> None:
    """Export a geometry cache for all geometry under a group"""

    geometry = mobj.lsChildren(geometryGrp)
    rec.geometryCache.export(geometry, dir=dir, filename=filename)


def _exportAlembicCache(geometry: mobj.DAGNode, filePath: Path) -> None:
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


def _buildWindow_e(outputPath: Path) -> mui.ProgressWindow:
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
def export() -> None:
    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)
    shotDir = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
    cachesDir = shotDir / fpath.CACHES_DIR
    # cachesDir = fpath.getScenePath().parents[1] / "cache"

    constructFilenameCmd = partial(
        rec.geometryCache.constructFilename,
        dir=cachesDir,
        shot=shot,
    )
    exportGeometryCacheCmd = partial(exportGeometryCache, dir=cachesDir)

    ui = _buildWindow_e(cachesDir).show()

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
        _exportAlembicCache(
            robotFaceRigGeoGrp,
            filePath=cachesDir / f"{robotFaceFilename}{fname.FileExt.ALEMBIC}",
        )
    ui.update()

    if cameraNodes := rec.camera.getComponents(mobj.TopLevelGroup.CAMERA):
        cameraFilename = constructFilenameCmd(assetType=fname.AssetType.CAMERA)
        rec.camera.export(
            cameraNodes,
            filePath=cachesDir / f"{cameraFilename}{fname.FileExt.MAYA_BINARY}",
        )
    ui.update().close()


################################################################################
# Import
################################################################################


def _findLatestVersionFile(
    dir: Path,
    shot: fname.ShotId,
    assetType: fname.TypeIdentifier,
    assetName: fname.NameIdentifier | None = None,
) -> Path | None:
    """Get the file path to the asset's latest version"""

    filenameBase = fname.constructFilenameBase(
        shot, assetName=assetName, assetType=assetType
    )
    validator = fname.constructValidator(
        filenameBase, assetName=assetName, assetType=assetType
    )
    return fpath.findLatestVersionAsset(
        validator,
        files=fpath.findShotFiles(shot, directory=dir),
    )


# TODO: Python warning or something more meaningful?
def _unloadReferencedCharacter(assetName: fname.NameIdentifier) -> None:
    """Unload a referenced asset"""

    referenceNode = rec.reference.findNode(f"{assetName}_{fname.AssetType.RIG}")
    if referenceNode is not None:
        rec.reference.unload(referenceNode)
        return

    cmds.warning(f"No reference node for: {assetName}")


def _importGeometryCache(
    geometryGrp: mobj.DAGNode,
    file: Path,
    assetName: fname.NameIdentifier,
    namespace: str,
) -> None:
    """Call the MEL procedure for importing a geometry cache"""

    geometry = mobj.lsChildren(geometryGrp)

    cmds.workspace(fileRule=("fileCache", file.parent.as_posix()))

    doImportCacheFileCmd = f'doImportCacheFile "{file.as_posix()}" "" {{}} {{}}'
    with mobj.TemporarySelection(geometry):
        mel.eval(doImportCacheFileCmd)

    rec.geometryCache.assetize(assetName, namespace=namespace)


def _replaceRigWithCachedModel(
    assetName: fname.NameIdentifier,
    model: Path,
    cache: Path,
    geometryGrp: mobj.DAGNode,
) -> None:
    """Unload a referenced rig, reference just the model, then apply a cache"""

    _unloadReferencedCharacter(assetName)
    namespace = mobj.constructNamespace(cache.stem, fname.AssetType.CACHE)
    rec.reference.character(
        model,
        namespace=namespace,
        geometry=geometryGrp,
    )

    try:
        container = mobj.lsWithWildcard(namespace, type="container")[0]
    except IndexError:
        _importGeometryCache(
            geometryGrp,
            assetName=assetName,
            file=cache,
            namespace=namespace,
        )
    else:
        cmds.setAttr(f"{container}.filename", cache.stem, type="string")

    # The cache saved world space positions, so get rid of geometry's xforms
    for c in mobj.lsChildren(geometryGrp):
        cmds.xform(c, matrix=om.MMatrix())


def _buildWindow_i(outputPath: Path) -> mui.ProgressWindow:
    ui = mui.ProgressWindow("progressWindow", "Cache & Camera Importer")

    def defineTask(product: str) -> str:
        return f"Referencing {product} from:\n{outputPath}"

    ui.build().initialize(
        defineTask("Mechanic model and applying geometry cache"),
        defineTask("Robot model and applying geometry cache"),
        defineTask("Robot face alembic cache"),
        defineTask("shot camera"),
    ).update()

    return ui


# FIXME: make importing from test folder separate from main
@mapp.SuspendedRedraw()
@mapp.logScriptEditorOutput
def import_() -> None:
    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)
    shotDir = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
    cachesDir = shotDir / fpath.CACHES_DIR
    # cachesDir = fpath.getScenePath().parents[1] / "cache"

    findLatestVersionFileCmd = partial(
        _findLatestVersionFile, cachesDir, shot=shot
    )

    ui = _buildWindow_i(cachesDir).show()

    mechanicName = fname.AssetName.MECHANIC
    if mechanicCache := findLatestVersionFileCmd(
        assetName=mechanicName, assetType=fname.AssetType.CACHE
    ):
        _replaceRigWithCachedModel(
            mechanicName,
            model=rec.reference.getModelPathCmd(mechanicName),
            cache=mechanicCache,
            geometryGrp=mobj.MECHANIC_MODEL_GEO_GRP,
        )
    ui.update()

    robotName = fname.AssetName.ROBOT
    if robotCache := findLatestVersionFileCmd(
        assetName=robotName, assetType=fname.AssetType.CACHE
    ):
        _replaceRigWithCachedModel(
            robotName,
            model=rec.reference.getModelPathCmd(robotName),
            cache=robotCache,
            geometryGrp=mobj.ROBOT_MODEL_GEO_GRP,
        )
    ui.update()

    if robotFaceCache := findLatestVersionFileCmd(
        assetName=fname.AssetName.ROBOT_FACE,
        assetType=fname.AssetType.CACHE,
    ):
        mapp.loadPlugin("AbcImport")
        robotFaceNamespace = mobj.constructNamespace(
            robotFaceCache.stem, assetType=fname.AssetType.CACHE
        )
        rec.reference.character(
            robotFaceCache,
            namespace=robotFaceNamespace,
            geometry=mobj.ROBOT_FACE_MODEL_GEO,
        )
    ui.update()

    if cameraFile := findLatestVersionFileCmd(assetType=fname.AssetType.CAMERA):
        cameraNamespace = mobj.constructNamespace(
            cameraFile.stem, assetType=fname.AssetType.CAMERA
        )
        rec.reference.load(file=cameraFile, namespace=cameraNamespace)

        cameras = cmds.ls(f"{cameraNamespace}:*", transforms=True, long=True)
        for c in (c for c in cameras if c.count("|") == 1):
            rec.reference.parent(c, mobj.TopLevelGroup.CAMERA)
    ui.update().close()
