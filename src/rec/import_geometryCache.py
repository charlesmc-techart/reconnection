from __future__ import annotations

from functools import partial
from typing import NoReturn

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp
import rec.modules.maya.objects as mobj


class GeometryCacheComponents:
    """Group of nodes that comprise a geometry cache"""

    __slots__ = "_origCacheFile", "cacheFile"

    def __new__(
        cls, cacheFile: mobj.DGNode
    ) -> GeometryCacheComponents | NoReturn:
        """Don't create an instance if not provided a cacheFile node"""
        if cmds.objectType(cacheFile, isType="cacheFile"):
            return super().__new__(cls)
        raise TypeError(f"{cacheFile} must be a cacheFile node")

    def __init__(self, cacheFile: mobj.DGNode) -> None:
        self._origCacheFile = cacheFile
        self.cacheFile = cacheFile

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

    def rename(self, identifier: fname.Identifier) -> None:
        nameBase = f"{identifier}_{self.meshPart}"
        self.cacheFile = cmds.rename(self.cacheFile, nameBase + "_cache")
        cmds.rename(self.historySwitch, nameBase + "_historySwitch")


def assetize(assetName: fname.AssetName, namespace: str) -> None:
    """Contain the geometry cache network in an asset

    Also, expose the cacheFile node's cache directory and filename attributes.
    """
    cacheFileNodes = mobj.lsWithWildcard(assetName, type="cacheFile")
    componentNodes = []
    for i, c in enumerate(cacheFileNodes):
        components = GeometryCacheComponents(c)
        components.rename(assetName)

        cacheFileNodes[i] = components.cacheFile
        componentNodes.extend((components.cacheFile, components.historySwitch))

    container = cmds.createNode("container", name=namespace + "_container")
    containerCmd = partial(cmds.container, container, edit=True)

    containerCmd(addNode=componentNodes, force=True)
    cmds.setAttr(container + ".blackBox", True)
    cmds.setAttr(container + ".viewMode", 0)

    cacheFileNode0, *cacheFileNodes = cacheFileNodes
    containerCmd(publishAndBind=(cacheFileNode0 + ".cachePath", "folder"))
    containerCmd(publishAndBind=(cacheFileNode0 + ".cacheName", "filename"))

    for c in cacheFileNodes:
        cmds.connectAttr(cacheFileNode0 + ".cachePath", c + ".cachePath")
        cmds.connectAttr(cacheFileNode0 + ".cacheName", c + ".cacheName")


# FIXME: make importing from test folder separate from main
@mapp.logScriptEditorOutput
def main() -> None:
    """Call the MEL procedure that opens the UI for importing a geometry cache"""
    if not mobj.lsSelectedGeometry():
        raise mobj.NoGeometrySelectedError

    shot = fname.ShotID.fromFilename(mapp.getScenePath().stem)
    shotPath = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
    cachesDir = shotPath / fpath.CACHES_DIR
    # cachesDir = mapp.getScenePath().parents[1] / "cache"

    cmds.workspace(fileRule=("cacheFile", cachesDir))
    mapp.setDefaultFileBrowserDir(cachesDir)

    # global proc doImportCacheArgList( int $version, string $args[] )
    #    $version == 0:
    #        $args[] = none
    mel.eval("doImportCacheArgList 0 {}")

    # Assetize network
    assetType = fname.AssetType.CACHE
    assetNamePattern = f"{shot.full}_*_{assetType}_v???"
    try:
        cacheFileNode = cmds.ls(assetNamePattern + "Cache1")[0]
    except IndexError:
        raise mapp.NoFileSelectedError
    cacheFilename = cmds.getAttr(cacheFileNode + ".cacheName")
    assetize(
        cacheFilename.split("_", 3)[2],  # From: `rec_seq###_name_cache_v###`
        mobj.constructNamespace(cacheFilename, assetType=assetType),
    )
