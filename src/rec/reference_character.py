from __future__ import annotations

from functools import partial
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj
import rec.reference_asset as iras


def parent(child: mobj.DAGNode, parent: mobj.DAGNode) -> None:
    """Parent a node if it isn't parented to anything"""
    if mobj.getParent(child):
        return

    try:
        cmds.parent(child, parent)
    except ValueError as e:
        cmds.warning(e)


def referenceCharacter(
    file: Path,
    namespace: str,
    geometry: mobj.DAGNode,
    characterGrp: mobj.TopLevelGroup = mobj.TopLevelGroup.CHARACTER,
) -> None:
    """Reference a or a component of a character"""
    iras.reference(file, namespace=namespace)

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
def referenceMechanicModel() -> None:
    file = getModelPathCmd(fname.AssetName.MECHANIC)
    namespace = _constructNamespaceCmd(file.stem)
    referenceCharacter(
        file,
        namespace=namespace,
        geometry=mobj.MECHANIC_MODEL_GEO_GRP,
    )


@mapp.logScriptEditorOutput
def referenceRobotModel() -> None:
    file = getModelPathCmd(fname.AssetName.ROBOT)
    namespace = _constructNamespaceCmd(file.stem)
    referenceCharacter(
        file,
        namespace=namespace,
        geometry=mobj.MECHANIC_MODEL_GEO_GRP,
    )


def main() -> None:
    referenceMechanicModel()
    referenceRobotModel()
