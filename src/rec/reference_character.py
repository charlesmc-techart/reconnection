from __future__ import annotations

from functools import partial
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.objects as mobj
import rec.reference_asset as iras


def parent(
    node: mobj.DAGNode, parent: mobj.DAGNode | mobj.TopLevelGroup
) -> None:
    """Parent a node if it isn't parented to anything"""
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
    characterGrp: mobj.TopLevelGroup = mobj.TopLevelGroup.CHARACTER,
) -> None:
    """Reference a or a component of a character"""
    iras.reference(filePath, namespace=namespace)

    with mobj.TemporarySelection(geometry):
        mel.eval("UnlockNormals")

    parent(geometry, parent=characterGrp)


getModelPathCmd = partial(
    fpath.getModelPath, parentDir=fpath.getSharedDrive(dir=fpath.ASSETS_DIR)
)
constructNamespaceCmd = partial(
    mobj.constructNamespace, assetType=fname.AssetType.MODEL
)


def referenceMechanicModel() -> None:
    modelFilePath = getModelPathCmd(fname.AssetName.MECHANIC)
    namespace = constructNamespaceCmd(modelFilePath.stem)
    referenceCharacter(
        modelFilePath,
        namespace=namespace,
        geometry=mobj.MECHANIC_MODEL_GEO_GRP,
    )


def referenceRobotModel() -> None:
    modelFilePath = getModelPathCmd(fname.AssetName.ROBOT)
    namespace = constructNamespaceCmd(modelFilePath.stem)
    referenceCharacter(
        modelFilePath,
        namespace=namespace,
        geometry=mobj.MECHANIC_MODEL_GEO_GRP,
    )


def main() -> None:
    referenceMechanicModel()
    referenceRobotModel()
