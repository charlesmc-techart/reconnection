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
) -> list[mobj.DGNode]:
    """Find a node using wildcards"""
    return cmds.ls(f"*{identifier}*", **kwargs)


def constructNamespace(filename: str, assetType: fname.AssetType) -> str:
    """Construct a namespace based an asset's filename and type"""
    cutoff = filename.index(f"{assetType}") + len(assetType)
    return filename[:cutoff]


class GeometryCacheComponents:
    """Group of nodes that comprise a geometry cache"""

    __slots__ = ("_origCacheFile", "cacheFile")

    def __new__(
        cls, cacheFileNode: mobj.DGNode
    ) -> GeometryCacheComponents | NoReturn:
        """Don't create an instance if not provided a cacheFile node"""
        if cmds.objectType(cacheFileNode, isType="cacheFile"):
            return super().__new__(cls)
        raise TypeError(f"{cacheFileNode} must be a cacheFile node")

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

    def rename(self, identifier: fname.RecIdentifier) -> None:
        nameBase = f"{identifier}_{self.meshPart}"
        self.cacheFile = cmds.rename(self.cacheFile, nameBase + "_cache")
        cmds.rename(self.historySwitch, nameBase + "_historySwitch")


class GeometryCacheNetwork:
    def __init__(self, components: Sequence[GeometryCacheComponents]) -> None:
        self.components = components
        self.cacheFiles = [c.cacheFile for c in components]
        self.historySwitches = [c.historySwitch for c in components]

    def assetize(self, identifier: fname.RecIdentifier) -> None:
        asset = cmds.createNode("container", name=f"{identifier}_container")
        containerCmd = partial(cmds.container, asset, edit=True)
        containerCmd(addNode=self.cacheFiles + self.historySwitches, force=True)
        cmds.setAttr(asset + ".blackBox", True)
        cmds.setAttr(asset + ".viewMode", 0)

        firstCacheFileNode = self.cacheFiles[0]
        containerCmd(
            publishAndBind=(firstCacheFileNode + ".cachePath", "folder")
        )
        containerCmd(
            publishAndBind=(firstCacheFileNode + ".cacheName", "filename")
        )
        for n in self.cacheFiles[1:]:
            cmds.connectAttr(
                firstCacheFileNode + ".cachePath", n + ".cachePath"
            )
            cmds.connectAttr(
                firstCacheFileNode + ".cacheName", n + ".cacheName"
            )


def assetize(assetName: fname.AssetName, namespace: str) -> None:
    """Contain the geometry cache network in an asset

    Also, expose the cacheFile node's cache directory and filename attributes.
    """
    cacheFileNodes = lsWithWildcard(assetName, type="cacheFile")
    componentNodes = []
    for i, c in enumerate(cacheFileNodes):
        components = GeometryCacheComponents(c)
        components.rename(assetName)

        cacheFileNodes[i] = components.cacheFile
        componentNodes.extend((components.cacheFile, components.historySwitch))

    asset = cmds.createNode("container", name=namespace + "_container")
    containerCmd = partial(cmds.container, asset, edit=True)

    containerCmd(addNode=componentNodes, force=True)
    cmds.setAttr(asset + ".blackBox", True)
    cmds.setAttr(asset + ".viewMode", 0)

    cacheFileNode0, *cacheFileNodes = cacheFileNodes
    containerCmd(publishAndBind=(cacheFileNode0 + ".cachePath", "folder"))
    containerCmd(publishAndBind=(cacheFileNode0 + ".cacheName", "filename"))

    for c in cacheFileNodes:
        cmds.connectAttr(cacheFileNode0 + ".cachePath", c + ".cachePath")
        cmds.connectAttr(cacheFileNode0 + ".cacheName", c + ".cacheName")


# FIXME: make importing from test folder separate from main
@mapp.SuspendedRedraw()
@mapp.logScriptEditorOutput
def main() -> None:
    """Call the MEL procedure that opens the UI for importing a geometry cache"""
    if not mobj.lsSelectedGeometry():
        raise mobj.NoGeometrySelectedError

    shot = fname.ShotID.getFromFilename(mapp.getScenePath().stem)
    gDriveShotDir = fpath.getShotPath(shot, parentDir=fpath.getSharedDrive())
    shotCachesDirPath = gDriveShotDir / fpath.CACHE_DIR
    # shotCachesDirPath = mapp.getScenePath().parents[1] / "cache"

    cmds.workspace(fileRule=("cacheFile", shotCachesDirPath))

    # global proc doImportCacheArgList( int $version, string $args[] )
    #    $version == 0:
    #        $args[] = none
    doImportCacheArgListCmd = "doImportCacheArgList 0 {}"
    mel.eval(doImportCacheArgListCmd)

    # Assetize network
    assetType = fname.AssetType.CACHE
    cacheFileNodeNamePattern = f"{shot.full}_*_{assetType}_v???"
    cacheFilename = cmds.getAttr(
        cmds.ls(cacheFileNodeNamePattern + "Cache1")[0] + ".cacheName"
    )
    assetName = cacheFilename.split("_", 3)[2]

    assetize(assetName, constructNamespace(cacheFilename, assetType=assetType))
