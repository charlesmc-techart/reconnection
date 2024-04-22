"""Load or unload asset references"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import NoReturn

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui

################################################################################
# General assets
################################################################################


def findNode(identifier: fname.Identifier) -> mobj.ReferenceNode:
    """Get an asset's reference node"""
    return mobj.lsWithWildcard(identifier, type="reference")[0]


def load(file: Path, namespace: str) -> None:
    """Reference an asset into the scene if it isn't yet"""
    try:
        findNode(namespace)
    except IndexError:
        fileExt = file.suffix
        if fileExt == fname.FileExt.MAYA_BINARY:
            fileType = mapp.FileType.BINARY
        elif fileExt == fname.FileExt.MAYA_ASCII:
            fileType = mapp.FileType.ASCII
        else:
            fileType = mapp.FileType.ALEMBIC

        cmds.file(
            file.as_posix(),
            ignoreVersion=True,
            loadReferenceDepth="all",
            mergeNamespacesOnClash=True,
            namespace=namespace,
            reference=True,
            type=fileType,
        )


# Assign the file path returned by 'fileBrowser' to a MEL global variable
_getFilePathProc = """
proc _getFilePath(string $filePath, string $_) {
    global string $_passToPython = "";
    $_passToPython = $filePath;
}
"""


def _getFilePath() -> str:
    mel.eval(
        f"{_getFilePathProc}; "
        'fileBrowser "_getFilePath" '
        '"Reference re:connection Asset" "Maya Scene" 0'
    )
    return mel.eval("$_passToPython = $_passToPython")


@mapp.logScriptEditorOutput
def asset() -> None | NoReturn:
    assetsDir = fpath.findSharedDrive(dir="REC/02_ASSETS")
    mui.setDefaultFileBrowserDir(assetsDir)

    filePath = _getFilePath()
    if not filePath:
        raise mui.NoFileSelectedError

    filePath = Path(filePath)
    filename = filePath.stem  # Formatted: 'rec_asset_name_type_v###'
    assetType = filename.rsplit("rec", 1)[-1].split("_")[3]
    namespace = mobj.constructNamespace(filename, assetType=assetType)
    load(filePath, namespace=namespace)


################################################################################
# Characters
################################################################################


# TODO: something more useful than a warming?
def parent(child: mobj.DAGNode, parent: mobj.DAGNode) -> None:
    """Parent a node if it isn't parented to anything"""
    if mobj.getParent(child):
        return

    try:
        cmds.parent(child, parent)
    except ValueError as e:
        cmds.warning(e)


def character(
    file: Path,
    namespace: str,
    geometry: mobj.DAGNode,
    characterGrp: mobj.TopLevelGroup = mobj.TopLevelGroup.CHARACTER,
) -> None:
    """Reference a or a component of a character"""
    load(file, namespace=namespace)

    with mobj.TemporarySelection(geometry):
        mel.eval("UnlockNormals")

    parent(geometry, parent=characterGrp)


getModelPathCmd = partial(
    fpath.findModelPath, parentDir=fpath.findSharedDrive(dir=fpath.ASSETS_DIR)
)
_constructNamespaceCmd = partial(
    mobj.constructNamespace, assetType=fname.AssetType.MODEL
)


@mapp.logScriptEditorOutput
def mechanicModel() -> None:
    file = getModelPathCmd(fname.AssetName.MECHANIC)
    namespace = _constructNamespaceCmd(file.stem)
    character(
        file,
        namespace=namespace,
        geometry=mobj.MECHANIC_MODEL_GEO_GRP,
    )


@mapp.logScriptEditorOutput
def robotModel() -> None:
    file = getModelPathCmd(fname.AssetName.ROBOT)
    namespace = _constructNamespaceCmd(file.stem)
    character(
        file,
        namespace=namespace,
        geometry=mobj.MECHANIC_MODEL_GEO_GRP,
    )


def mechanicAndRobotModels() -> None:
    mechanicModel()
    robotModel()


################################################################################
# Unload
################################################################################


class NoReferenceNodeSelectedError(Exception):
    def __init__(self) -> None:
        super().__init__("No reference node selected")


def unload(referenceNode: mobj.ReferenceNode) -> None:
    """Unload a reference"""
    file = Path(cmds.referenceQuery(referenceNode, filename=True))
    cmds.file(file.as_posix(), unloadReference=referenceNode)


@mapp.logScriptEditorOutput
def unloadSelected() -> None:
    selection = cmds.ls(selection=True, type="reference")
    if not selection:
        raise NoReferenceNodeSelectedError

    for s in selection:
        unload(s)
