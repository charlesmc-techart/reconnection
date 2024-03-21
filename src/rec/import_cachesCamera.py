from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Optional

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel

import rec.import_geometryCache as igcs
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui


def getLatestVersionAsset(
    dir: Path,
    shot: fname.ShotID,
    assetType: fname.AssetType,
    assetName: Optional[fname.AssetName] = None,
) -> Optional[Path]:
    filenameBase = fname.constructFilenameBase(
        shot, assetName=assetName, assetType=assetType
    )
    assetValidator = fname.constructAssetValidator(
        filenameBase, assetName=assetName, assetType=assetType
    )
    return fpath.getLatestVersionAsset(
        assetValidator,
        files=fpath.filterShotFiles(shot, dir=dir),
    )


def getReferenceNode(identifier: fname.RecIdentifier) -> mobj.ReferenceNode:
    return igcs.lsWithWildcard(identifier, type="reference")[0]


def reference(filePath: Path, namespace: str) -> None:
    try:
        getReferenceNode(namespace)
    except IndexError:
        fileExt = filePath.suffix
        if fileExt == fname.FileExt.MAYA_BINARY:
            fileType = mapp.FileType.BINARY
        elif fileExt == fname.FileExt.MAYA_ASCII:
            fileType = mapp.FileType.ASCII
        else:
            fileType = mapp.FileType.ALEMBIC

        cmds.file(
            filePath.resolve().as_posix(),
            ignoreVersion=True,
            loadReferenceDepth="all",
            mergeNamespacesOnClash=True,
            namespace=namespace,
            reference=True,
            type=fileType,
        )


def parent(
    node: mobj.DAGNode, parent: mobj.DAGNode | mobj.TopLevelGroup
) -> None:
    if mobj.getParent(node):
        return

    try:
        cmds.parent(node, parent)
    except ValueError as e:
        cmds.warning(e)


def referenceCharacter(
    filePath: Path,
    namespace: str,
    geometry: mobj.DAGNode,
    characterGrp: mobj.TopLevelGroup,
) -> None:
    reference(filePath=filePath, namespace=namespace)

    with mobj.TemporarySelection(geometry):
        mel.eval("UnlockNormals")

    parent(geometry, parent=characterGrp)


# TODO: Python warning or something more meaningful?
def unloadReference(assetName: fname.AssetName) -> None:
    try:
        referenceNode = getReferenceNode(f"{assetName}_{fname.AssetType.RIG}")
    except IndexError as e:
        cmds.warning(e)
        return

    filePath = Path(cmds.referenceQuery(referenceNode, filename=True))
    cmds.file(filePath.as_posix(), unloadReference=referenceNode)


def importGeometryCache(
    geometryGrp: mobj.DAGNode,
    filePath: Path,
    assetName: fname.AssetName,
    namespace: str,
) -> None:
    geometry = mobj.lsChildren(geometryGrp)

    cmds.workspace(fileRule=("fileCache", filePath.parent.as_posix()))

    doImportCacheFileCmd = (
        f'doImportCacheFile "{filePath.as_posix()}" "" {{}} {{}}'
    )
    with mobj.TemporarySelection(geometry):
        mel.eval(doImportCacheFileCmd)

    igcs.assetize(assetName, namespace=namespace)


def replaceRigWithCachedModel(
    assetName: fname.AssetName,
    modelFilePath: Path,
    cacheFilePath: Path,
    geometryGrp: mobj.DAGNode,
    characterGrp: mobj.TopLevelGroup,
) -> None:
    unloadReference(assetName)
    namespace = igcs.constructNamespace(
        cacheFilePath.stem, fname.AssetType.CACHE
    )
    referenceCharacter(
        modelFilePath,
        namespace=namespace,
        geometry=geometryGrp,
        characterGrp=characterGrp,
    )

    try:
        container = igcs.lsWithWildcard(namespace, type="container")[0]
    except IndexError:
        importGeometryCache(
            geometryGrp,
            assetName=assetName,
            filePath=cacheFilePath,
            namespace=namespace,
        )
    else:
        cmds.setAttr(container + ".filename", cacheFilePath.stem, type="string")

    # The cache saved world space positions, so get rid of geometry's xforms
    for c in mobj.lsChildren(geometryGrp):
        cmds.xform(c, matrix=om.MMatrix())


def buildWindow(outputPath: Path) -> mui.ProgressWindow:
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
def main() -> None:
    shot = fname.ShotID.getFromFilename(mapp.getScenePath().stem)
    gDriveShotDir = fpath.getShotPath(shot, parentDir=fpath.getSharedDrive())
    shotCachesDirPath = gDriveShotDir / fpath.CACHE_DIR
    # shotCachesDirPath = mapp.getScenePath().parents[1] / "cache"

    getLatestVersionAssetCmd = partial(
        getLatestVersionAsset, shotCachesDirPath, shot=shot
    )

    characterGrp = mobj.TopLevelGroup.CHARACTER
    gDriveAssetsDirPath = fpath.getSharedDrive(dir="REC/02_ASSETS")
    replaceRigWithCachedModelCmd = partial(
        replaceRigWithCachedModel, characterGrp=characterGrp
    )

    ui = buildWindow(shotCachesDirPath).show()

    mechanicName = fname.AssetName.MECHANIC
    if mechanicCache := getLatestVersionAssetCmd(
        assetName=mechanicName, assetType=fname.AssetType.CACHE
    ):
        mechanicModel = fpath.getModelPath(
            mechanicName, parentDir=gDriveAssetsDirPath
        )
        replaceRigWithCachedModelCmd(
            mechanicName,
            modelFilePath=mechanicModel,
            cacheFilePath=mechanicCache,
            geometryGrp=mobj.MECHANIC_MODEL_GEO_GRP,
        )
    ui.update()

    robotName = fname.AssetName.ROBOT
    if robotCache := getLatestVersionAssetCmd(
        assetName=robotName, assetType=fname.AssetType.CACHE
    ):
        robotModel = fpath.getModelPath(
            robotName, parentDir=gDriveAssetsDirPath
        )
        replaceRigWithCachedModelCmd(
            robotName,
            modelFilePath=robotModel,
            cacheFilePath=robotCache,
            geometryGrp=mobj.ROBOT_MODEL_GEO_GRP,
        )
    ui.update()

    if robotFaceCache := getLatestVersionAssetCmd(
        assetName=fname.AssetName.ROBOT_FACE,
        assetType=fname.AssetType.CACHE,
    ):
        mapp.loadPlugin("AbcImport")
        robotFaceNamespace = igcs.constructNamespace(
            robotFaceCache.stem, assetType=fname.AssetType.CACHE
        )
        referenceCharacter(
            robotFaceCache,
            namespace=robotFaceNamespace,
            geometry=mobj.ROBOT_FACE_MODEL_GEO,
            characterGrp=characterGrp,
        )
    ui.update()

    if cameraFile := getLatestVersionAssetCmd(assetType=fname.AssetType.CAMERA):
        cameraNamespace = igcs.constructNamespace(
            cameraFile.stem, assetType=fname.AssetType.CAMERA
        )
        reference(filePath=cameraFile, namespace=cameraNamespace)

        cameras = cmds.ls(cameraNamespace + ":*", transforms=True, long=True)
        for c in (c for c in cameras if c.count("|") == 1):
            parent(c, mobj.TopLevelGroup.CAMERA)
    ui.close()
