"""Reference a 3D asset from the ASSETS directory"""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui


def getReferenceNode(identifier: fname.Identifier) -> mobj.ReferenceNode:
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


# Assign the file path returned by 'fileBrowser' to a MEL global variable
assignAssetFilePathToGlobalVarProc = """
proc assignAssetFilePathToGlobalVar(string $filePath, string $_) {
    global string $_passToPython = "";
    $_passToPython = $filePath;
}
"""


@mapp.logScriptEditorOutput
def main() -> None | NoReturn:
    assetsDir = fpath.findSharedDrive(dir="REC/02_ASSETS")

    mui.setDefaultFileBrowserDir(assetsDir)
    mel.eval(
        f"{assignAssetFilePathToGlobalVarProc};"
        'fileBrowser "assignAssetFilePathToGlobalVar" '
        '"Reference re:connection Asset" "Maya Scene" 0'
    )

    filePath = mel.eval("$_passToPython = $_passToPython")
    if not filePath:
        raise mui.NoFileSelectedError

    filePath = Path(filePath)
    filename = filePath.stem  # Formatted: 'rec_asset_name_type_v###'
    assetType = filename.rsplit("rec", 1)[-1].split("_")[3]
    namespace = mobj.constructNamespace(filename, assetType=assetType)
    reference(filePath, namespace=namespace)
