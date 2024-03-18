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


def lsWithWildcard(
    identifier: fname.RecIdentifier, **kwargs: Optional[Any]
) -> mobj.DGNode:
    return cmds.ls(f"*{identifier}*", **kwargs)


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


def exportGeometryCache(dir: Path, fileName: str) -> None:
    """Call the MEL procedure for exporting a geometry cache"""
    # global proc stirng[] doCreateGeometryCache( int $version, string $args[] )
    #     $version == 1:
    #         $args[0] =  time range mode:
    #             time range mode = 0 : use $args[1] and $args[2] as start-end
    #             time range mode = 1 : use render globals
    #             time range mode = 2 : use timeline
    #          $args[1] = start frame (if time range mode == 0)
    #          $args[2] = end frame (if time range mode == 0)

    #     $version == 2:
    #          $args[3] = cache file distribution, either "OneFile"
    #                     or "OneFilePerFrame"
    #          $args[4] = 0/1, whether to refresh during caching
    #          $args[5] = directory for cache files, if "", then use project
    #                     data dir
    #          $args[6] = 0/1, whether to create a cache per geometry
    #          $args[7] = name of cache file. An empty string can be used to
    #                     specify that an auto-generated name is acceptable.
    #          $args[8] = 0/1, whether the specified cache name is to be used
    #                     as a prefix

    #     $version == 3:
    #          $args[9] = action to perform: "add", "replace", "merge",
    #                     "mergeDelete" or "export"
    #         $args[10] = force save even if it overwrites existing files
    #         $args[11] = simulation rate, the rate at which the cloth
    #                     simulation is forced to run
    #         $args[12] = sample mulitplier, the rate at which samples are
    #                     written, as a multiple of simulation rate.

    #     $version == 4:
    #         $args[13] = 0/1, whether modifications should be inherited
    #                     from the cache about to be replaced. Valid
    #                     only when $action == "replace".
    #         $args[14] = 0/1, whether to store doubles as floats

    #     $version == 5:
    #         $args[15] = name of cache format

    #     $version == 6:
    #         $args[16] = 0/1, whether to export in local or world space
    doCreateGeometryCacheCmd = (
        f'doCreateGeometryCache 6 {{"2", "1", "10", "OneFile", "0", '
        f'"{dir.as_posix()}", "0", "{fileName}", "0", "export", '
        '"1", "1", "1", "0", "0", "mcx", "1"}'
    )
    mel.eval(doCreateGeometryCacheCmd)


def importGeometryCache(
    filePath: Path, assetName: fname.AssetName, namespace: str
) -> None:
    doImportCacheFileCmd = (
        f'doImportCacheFile "{filePath.as_posix()}" "" {{}} {{}}'
    )
    mel.eval(doImportCacheFileCmd)

    cacheFileAndHistoryNodes = []
    for cacheFileNode in lsWithWildcard(assetName, type="cacheFile"):
        historySwitch = cmds.listConnections(
            cacheFileNode, type="historySwitch"
        )[0]
        mesh = cmds.listConnections(historySwitch, type="shape")[0]
        meshPart = mesh.rsplit(":", 1)[-1].rsplit("_", 1)[0]

        cacheFileNewName = cmds.rename(
            cacheFileNode, f"{assetName}_{meshPart}_cache"
        )
        historySwitchNewName = cmds.rename(
            historySwitch, f"{assetName}_{meshPart}_historySwitch"
        )
        cacheFileAndHistoryNodes.extend(
            (cacheFileNewName, historySwitchNewName)
        )

    asset = cmds.createNode("container", name=namespace + "_container")
    containerCmd = partial(cmds.container, asset, edit=True)
    containerCmd(addNode=cacheFileAndHistoryNodes, force=True)
    cmds.setAttr(asset + ".blackBox", True)
    cmds.setAttr(asset + ".viewMode", 0)

    firstCacheFileNode = None
    isCacheFileNode = partial(cmds.objectType, isType="cacheFile")
    for n in filter(isCacheFileNode, cacheFileAndHistoryNodes):
        if firstCacheFileNode is None:
            firstCacheFileNode = n
            containerCmd(publishAndBind=(n + ".cachePath", "folder"))
            containerCmd(publishAndBind=(n + ".cacheName", "filename"))
            continue
        cmds.connectAttr(firstCacheFileNode + ".cachePath", n + ".cachePath")
        cmds.connectAttr(firstCacheFileNode + ".cacheName", n + ".cacheName")
