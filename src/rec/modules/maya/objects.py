from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import Any, Optional

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj
import rec.modules.stringEnum as strEnum

DGNode = DAGNode = ShapeNode = str
ReferenceNode = DGNode


class TopLevelGroup(strEnum.StringEnum):
    CHARACTER = "::_*CHARACTER*_"
    CAMERA = "::_*CAMERA*_"


class TopLevelGroupDoesNotExistError(Exception):
    def __init__(self, groupName: TopLevelGroup | DAGNode) -> None:
        super().__init__(f"The top-level group, {groupName}, does not exist")


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

    def __exit__(self, *args) -> None:
        cmds.select(clear=True)
        cmds.undoInfo(stateWithoutFlush=True)


def lsChildren(
    nodes: DAGNode | Sequence[DAGNode], **kwargs: Optional[Any]
) -> list[DAGNode]:
    return cmds.listRelatives(nodes, path=True, **kwargs)


def getParent(node: DAGNode) -> Optional[DAGNode]:
    try:
        return lsChildren(node, parent=True)[0]
    except TypeError:
        return None


def lsUnknown() -> list[DGNode]:
    return cmds.ls(type="unknown")


def exportNodes(
    nodes: Sequence[DGNode], filePath: Path, fileType: mapp.FileType
) -> None:
    with mobj.TemporarySelection(nodes):
        cmds.file(
            filePath.as_posix(),
            exportSelectedStrict=True,
            force=True,
            options="v=0",
            type=fileType,
        )
