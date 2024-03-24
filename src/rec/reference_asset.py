from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj


def getReferenceNode(identifier: fname.RecIdentifier) -> mobj.ReferenceNode:
    """Get an asset's reference node"""
    return mobj.lsWithWildcard(identifier, type="reference")[0]


def reference(filePath: Path, namespace: str) -> None:
    """Reference an asset into the scene if it isn't yet"""
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
            filePath.as_posix(),
            ignoreVersion=True,
            loadReferenceDepth="all",
            mergeNamespacesOnClash=True,
            namespace=namespace,
            reference=True,
            type=fileType,
        )


assignAssetFilePathToGlobalVarProc = """
proc assignAssetFilePathToGlobalVar(string $filePath, string $_) {
    global string $passToPython;
    $passToPython = $filePath;
}
"""


@mapp.logScriptEditorOutput
def main() -> None:
    gDriveAssetsDirPath = fpath.getSharedDrive(dir="REC/02_ASSETS")


    mel.eval(
        f'$gDefaultFileBrowserDir = "{gDriveAssetsDirPath.as_posix()}";'
        f"{assignAssetFilePathToGlobalVarProc};"
        ""
        'fileBrowser "assignAssetFilePathToGlobalVar" '
        '"Reference re:connection Asset" "Maya Scene" 0'
    )
    assetFilePath = Path(mel.eval("$passToPython = $passToPython"))
    assetType = assetFilePath.stem.rsplit("rec", 1)[-1].split("_")[3]
    namespace = mobj.constructNamespace(assetFilePath.stem, assetType=assetType)
    reference(assetFilePath, namespace=namespace)
