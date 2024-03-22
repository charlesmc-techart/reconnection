from collections.abc import Callable
from pathlib import Path
from typing import Any

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

def wrapAsRunTimeCommand(func: Callable[[Any], Any]) -> None:
    

melProcedures = """
proc referenceAssetCallback(string $filePath, string $fileType) {
    string $getAssetTypeCmd, $constructNamespaceCmd, $namespace;

    $getAssetTypeCmd = ".rsplit('/', 1)[-1].split('rec')[-1].split('_', 4)[3]";
    $fileType = `python ("'" + $filePath + "'" + $getAssetTypeCmd)`;

    $constructNamespaceCmd = "mobj.constructNamespace";
    $constructNamespaceCmd += "(Path('" + $filePath + "').stem, '" + $fileType + "')";
    $namespace = `python $constructNamespaceCmd`;

    python ("reference(Path('" + $filePath + "'), '" + $namespace + "')");
}


proc referenceAsset(string $dir, string $func) {
    $gDefaultFileBrowserDir = $dir;
    fileBrowser $func "Reference re:connection Asset" "Maya Scene" 0;
}
"""


@mapp.logScriptEditorOutput
def main() -> None:
    gDriveAssetsDirPath = fpath.getSharedDrive(dir="REC/02_ASSETS")

    mel.eval(melProcedures)
    mel.eval(
        f'referenceAsset "{gDriveAssetsDirPath.as_posix()}" "referenceAssetCallback"'
    )
