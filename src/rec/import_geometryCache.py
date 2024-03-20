from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import Any, NoReturn, Optional

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj


def lsWithWildcard(
    identifier: fname.RecIdentifier, **kwargs: Optional[Any]
) -> mobj.DGNode:
    return cmds.ls(f"*{identifier}*", **kwargs)


def constructNamespace(filename: str, assetType: fname.AssetType) -> str:
    cutoff = filename.index(f"{assetType}") + len(assetType)
    return filename[:cutoff]


class GeometryCacheComponents:
    __slots__ = ("_origCacheFile", "cacheFile")

    def __new__(
        cls, cacheFileNode: mobj.DGNode
    ) -> GeometryCacheComponents | NoReturn:
        if cmds.objectType(cacheFileNode, isType="cacheFile"):
            return super().__new__(cls)
        raise TypeError(f"{cacheFileNode!r} must be a cacheFile node")

    def __init__(self, cacheFileNode: mobj.DGNode) -> None:
        self._origCacheFile = cacheFileNode
        self.cacheFile = cacheFileNode

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._origCacheFile!r})"

    @property
    def historySwitch(self) -> mobj.DGNode:
        return cmds.listConnections(self.cacheFile, type="historySwitch")[0]

    @property
    def mesh(self) -> mobj.ShapeNode:
        return cmds.listConnections(self.historySwitch, type="mesh")[0]

    @property
    def meshPart(self) -> str:
        return self.mesh.rsplit(":", 1)[-1].rsplit("_", 1)[0]

    def renameComponents(self, identifier: fname.RecIdentifier) -> None:
        nameBase = f"{identifier}_{self.meshPart}"
        self.cacheFile = cmds.rename(self.cacheFile, nameBase + "_cache")
        cmds.rename(self.historySwitch, nameBase + "_historySwitch")


def assetizeGeometryCacheComponents(
    assetName: fname.AssetName, namespace: str
) -> None:
    geometryCacheComponents = []
    for cacheFileNode in lsWithWildcard(assetName, type="cacheFile"):
        components = GeometryCacheComponents(cacheFileNode)
        components.renameComponents(assetName)

        geometryCacheComponents.extend(
            (components.cacheFile, components.historySwitch)
        )

    asset = cmds.createNode("container", name=namespace + "_container")
    containerCmd = partial(cmds.container, asset, edit=True)
    containerCmd(addNode=geometryCacheComponents, force=True)
    cmds.setAttr(asset + ".blackBox", True)
    cmds.setAttr(asset + ".viewMode", 0)

    firstCacheFileNode = None
    isCacheFileNode = partial(cmds.objectType, isType="cacheFile")
    for n in filter(isCacheFileNode, geometryCacheComponents):
        if firstCacheFileNode is None:
            firstCacheFileNode = n
            containerCmd(publishAndBind=(n + ".cachePath", "folder"))
            containerCmd(publishAndBind=(n + ".cacheName", "filename"))
            continue
        cmds.connectAttr(firstCacheFileNode + ".cachePath", n + ".cachePath")
        cmds.connectAttr(firstCacheFileNode + ".cacheName", n + ".cacheName")


# FIXME: make importing from test folder separate from main
@mapp.logScriptEditorOutput
def main() -> None:
    if not mobj.lsSelectedGeometry():
        raise mobj.NoGeometrySelectedError

    shot = fname.ShotID.getFromFilename(mapp.getScenePath().stem)
    gDriveShotDir = fpath.getShotPath(shot, parentDir=fpath.getSharedDrive())
    shotCachesDirPath = gDriveShotDir / fpath.CACHE_DIR
    shotCachesDirPath = mapp.getScenePath().parents[1] / "cache"

    cmds.workspace(fileRule=("cacheFile", shotCachesDirPath))

    # global proc doImportCacheArgList( int $version, string $args[] )
    #    $version == 0:
    #        $args[] = none
    doImportCacheArgListCmd = "doImportCacheArgList 0 {}"
    mel.eval(doImportCacheArgListCmd)

    assetType = fname.AssetType.CACHE
    cacheFileNodeNamePattern = f"{shot.full}_*_{assetType}_v???"
    cacheFilename = cmds.getAttr(
        cmds.ls(cacheFileNodeNamePattern + "Cache1")[0] + ".cacheName"
    )
    assetName = cacheFilename.split("_", 3)[2]

    assetizeGeometryCacheComponents(
        assetName, constructNamespace(cacheFilename, assetType=assetType)
    )
