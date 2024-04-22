from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.maya as mapp
import rec.modules.stringEnum as strEnum

DGNode = DAGNode = ShapeNode = str
ReferenceNode = DGNode


class TopLevelGroup(strEnum.StringEnum):
    """Patterns for top-level groups parented under the world"""

    CHARACTER = "::_*CHARACTER*_"
    CAMERA = "::_*CAMERA*_"


class TopLevelGroupDoesNotExistError(Exception):
    def __init__(self, groupName: DAGNode) -> None:
        super().__init__(f"Top-level group does not exist: '{groupName}'")


MECHANIC_MODEL_GEO_GRP = "::mechanic_grp"
MECHANIC_RIG_ROOT = "::MECHANIC"
MECHANIC_RIG_GEO_GRP = f"{MECHANIC_RIG_ROOT}|::geo_grp|{MECHANIC_MODEL_GEO_GRP}"

ROBOT_MODEL_GEO_GRP = "::GEO"
ROBOT_RIG_ROOT = "::ROBOT"
ROBOT_RIG_GEO_GRP = f"{ROBOT_RIG_ROOT}|::geo_grp|{ROBOT_MODEL_GEO_GRP}"

ROBOT_FACE_MODEL_GEO = "::face_doNotTouch_MASH_ReproMesh"
ROBOT_FACE_RIG_GEO = f"{ROBOT_RIG_ROOT}|::face_rig_grp|::face_MASH_grp|::face_MASH_geos_grp|{ROBOT_FACE_MODEL_GEO}"


class TemporarySelection:
    __slots__ = "selection"

    def __init__(self, selection: DGNode | Sequence[DGNode]) -> None:
        self.selection = selection

    def __enter__(self) -> None:
        cmds.undoInfo(stateWithoutFlush=False)
        cmds.select(self.selection, replace=True)

    def __exit__(self, *args: Any) -> None:
        cmds.select(clear=True)
        cmds.undoInfo(stateWithoutFlush=True)


def lsSelectedGeometry() -> list[DAGNode]:
    return [
        s
        for s in cmds.ls(selection=True, transforms=True)
        if cmds.listRelatives(s, shapes=True, noIntermediate=True, type="mesh")
    ]


class NoGeometrySelectedError(Exception):
    def __init__(self) -> None:
        super().__init__("No geometry selected")


def lsChildren(
    nodes: DAGNode | Sequence[DAGNode], **kwargs: Any
) -> list[DAGNode]:
    return cmds.listRelatives(nodes, path=True, **kwargs)


def getParent(node: DAGNode) -> DAGNode | None:
    try:
        return lsChildren(node, parent=True)[0]
    except TypeError:
        return None


def lsUnknown() -> list[DGNode]:
    return cmds.ls(type="unknown")


def export(
    nodes: Sequence[DGNode], filePath: Path, fileType: mapp.FileType
) -> None:
    with TemporarySelection(nodes):
        cmds.file(
            filePath.as_posix(),
            exportSelectedStrict=True,
            force=True,
            options="v=0",
            type=fileType,
        )


def lsWithWildcard(identifier: fname.Identifier, **kwargs: Any) -> list[DGNode]:
    """Find a node using wildcards"""
    return cmds.ls(f"*{identifier}*", **kwargs)


def constructNamespace(filename: str, assetType: fname.TypeIdentifier) -> str:
    """Construct a namespace based an asset's filename and type"""
    cutoff = filename.index(assetType) + len(assetType)
    return filename[:cutoff]
