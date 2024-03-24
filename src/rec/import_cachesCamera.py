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
import rec.reference_asset as iras
import rec.reference_character as ircm


def getLatestVersionAsset(
    dir: Path,
    shot: fname.ShotID,
    assetType: fname.AssetType,
    assetName: Optional[fname.AssetName] = None,
) -> Optional[Path]:
    """Get the file path to the asset's latest version"""
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


# TODO: Python warning or something more meaningful?
def unloadReference(assetName: fname.AssetName) -> None:
    """Unload a referenced asset"""
    try:
        referenceNode = iras.getReferenceNode(
            f"{assetName}_{fname.AssetType.RIG}"
        )
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
    """Call the MEL procedure for importing a geometry cache"""
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
) -> None:
    """Unload a referenced rig, reference just the model, then apply a cache"""
    unloadReference(assetName)
    namespace = mobj.constructNamespace(
        cacheFilePath.stem, fname.AssetType.CACHE
    )
    ircm.referenceCharacter(
        modelFilePath,
        namespace=namespace,
        geometry=geometryGrp,
    )

    try:
        container = mobj.lsWithWildcard(namespace, type="container")[0]
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

    ui = buildWindow(shotCachesDirPath).show()

    mechanicName = fname.AssetName.MECHANIC
    if mechanicCache := getLatestVersionAssetCmd(
        assetName=mechanicName, assetType=fname.AssetType.CACHE
    ):
        replaceRigWithCachedModel(
            mechanicName,
            modelFilePath=ircm.getModelPathCmd(mechanicName),
            cacheFilePath=mechanicCache,
            geometryGrp=mobj.MECHANIC_MODEL_GEO_GRP,
        )
    ui.update()

    robotName = fname.AssetName.ROBOT
    if robotCache := getLatestVersionAssetCmd(
        assetName=robotName, assetType=fname.AssetType.CACHE
    ):
        replaceRigWithCachedModel(
            robotName,
            modelFilePath=ircm.getModelPathCmd(robotName),
            cacheFilePath=robotCache,
            geometryGrp=mobj.ROBOT_MODEL_GEO_GRP,
        )
    ui.update()

    if robotFaceCache := getLatestVersionAssetCmd(
        assetName=fname.AssetName.ROBOT_FACE,
        assetType=fname.AssetType.CACHE,
    ):
        mapp.loadPlugin("AbcImport")
        robotFaceNamespace = mobj.constructNamespace(
            robotFaceCache.stem, assetType=fname.AssetType.CACHE
        )
        ircm.referenceCharacter(
            robotFaceCache,
            namespace=robotFaceNamespace,
            geometry=mobj.ROBOT_FACE_MODEL_GEO,
        )
    ui.update()

    if cameraFile := getLatestVersionAssetCmd(assetType=fname.AssetType.CAMERA):
        cameraNamespace = mobj.constructNamespace(
            cameraFile.stem, assetType=fname.AssetType.CAMERA
        )
        iras.reference(filePath=cameraFile, namespace=cameraNamespace)

        cameras = cmds.ls(cameraNamespace + ":*", transforms=True, long=True)
        for c in (c for c in cameras if c.count("|") == 1):
            ircm.parent(c, mobj.TopLevelGroup.CAMERA)
    ui.update().close()
