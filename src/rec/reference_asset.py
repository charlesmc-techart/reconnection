from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj


def getReferenceNode(identifier: fname.RecIdentifier) -> mobj.ReferenceNode:
    """Get an asset's reference node"""
    return mobj.lsWithWildcard(identifier, type="reference")[0]


def reference(file: Path, namespace: str) -> None:
    """Reference an asset into the scene if it isn't yet"""
    try:
        getReferenceNode(namespace)
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


assignAssetFilePathToGlobalVarProc = """
proc assignAssetFilePathToGlobalVar(string $filePath, string $_) {
    global string $_passToPython = "";
    $_passToPython = $filePath;
}
"""


class NoFileSelectedError(Exception):
    def __init__(self) -> None:
        super().__init__("No file was selected")


@mapp.logScriptEditorOutput
def main() -> None | NoReturn:
    assetsDir = fpath.findSharedDrive(dir="REC/02_ASSETS")

    mel.eval(
        f'$gDefaultFileBrowserDir = "{gDriveAssetsDirPath.as_posix()}";'
        f"{assignAssetFilePathToGlobalVarProc};"
        ""
        'fileBrowser "assignAssetFilePathToGlobalVar" '
        '"Reference re:connection Asset" "Maya Scene" 0'
    )

    filePath = mel.eval("$_passToPython = $_passToPython")
    if not filePath:
        raise mapp.NoFileSelectedError

    assetFilePath = Path(assetFilePath)
    assetType = assetFilePath.stem.rsplit("rec", 1)[-1].split("_")[3]
    namespace = mobj.constructNamespace(assetFilePath.stem, assetType=assetType)
    reference(assetFilePath, namespace=namespace)
