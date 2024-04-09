"""Reference the character 3D models, geometry and Alembic caches, and camera"""

from __future__ import annotations

from functools import partial
from pathlib import Path

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel

import rec.import_geometryCache as igc
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui
import rec.reference_asset as ras
import rec.reference_character as rch
import rec.unload_reference as urf


def findLatestVersionFile(
    dir: Path,
    shot: fname.ShotID,
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
        files=fpath.findShotFiles(shot, dir=dir),
    )


# TODO: Python warning or something more meaningful?
def unloadReferencedCharacter(assetName: fname.NameIdentifier) -> None:
    """Unload a referenced asset"""
    try:
        referenceNode = ras.getReferenceNode(
            f"{assetName}_{fname.AssetType.RIG}"
        )
    except IndexError as e:
        cmds.warning(e)
        return

    urf.unloadReference(referenceNode)


def importGeometryCache(
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

    igc.assetize(assetName, namespace=namespace)


def replaceRigWithCachedModel(
    assetName: fname.NameIdentifier,
    model: Path,
    cache: Path,
    geometryGrp: mobj.DAGNode,
) -> None:
    """Unload a referenced rig, reference just the model, then apply a cache"""
    unloadReferencedCharacter(assetName)
    namespace = mobj.constructNamespace(cache.stem, fname.AssetType.CACHE)
    rch.referenceCharacter(
        model,
        namespace=namespace,
        geometry=geometryGrp,
    )

    try:
        container = mobj.lsWithWildcard(namespace, type="container")[0]
    except IndexError:
        importGeometryCache(
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
    shot = fname.ShotID.fromFilename(fpath.getScenePath().stem)
    shotDir = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
    cachesDir = shotDir / fpath.CACHES_DIR
    # cachesDir = fpath.getScenePath().parents[1] / "cache"

    findLatestVersionFileCmd = partial(
        findLatestVersionFile, cachesDir, shot=shot
    )

    ui = buildWindow(cachesDir).show()

    mechanicName = fname.AssetName.MECHANIC
    if mechanicCache := findLatestVersionFileCmd(
        assetName=mechanicName, assetType=fname.AssetType.CACHE
    ):
        replaceRigWithCachedModel(
            mechanicName,
            model=rch.getModelPathCmd(mechanicName),
            cache=mechanicCache,
            geometryGrp=mobj.MECHANIC_MODEL_GEO_GRP,
        )
    ui.update()

    robotName = fname.AssetName.ROBOT
    if robotCache := findLatestVersionFileCmd(
        assetName=robotName, assetType=fname.AssetType.CACHE
    ):
        replaceRigWithCachedModel(
            robotName,
            model=rch.getModelPathCmd(robotName),
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
        rch.referenceCharacter(
            robotFaceCache,
            namespace=robotFaceNamespace,
            geometry=mobj.ROBOT_FACE_MODEL_GEO,
        )
    ui.update()

    if cameraFile := findLatestVersionFileCmd(assetType=fname.AssetType.CAMERA):
        cameraNamespace = mobj.constructNamespace(
            cameraFile.stem, assetType=fname.AssetType.CAMERA
        )
        ras.reference(file=cameraFile, namespace=cameraNamespace)

        cameras = cmds.ls(f"{cameraNamespace}:*", transforms=True, long=True)
        for c in (c for c in cameras if c.count("|") == 1):
            rch.parent(c, mobj.TopLevelGroup.CAMERA)
    ui.update().close()
