"""Export or import a geometry cache for the selected objects"""

from __future__ import annotations

__author__ = "Charles Mesa Cayobit"

from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import NoReturn

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui

################################################################################
# Export
################################################################################


def constructFilename(
    dir: Path,
    shot: fname.ShotId,
    assetType: fname.TypeIdentifier,
    assetName: fname.NameIdentifier | None = None,
) -> str:
    """Construct a filename, formatted 'rec_seq###_name_type_v###"""
    filenameBase = fname.constructFilenameBase(
        shot, assetName=assetName, assetType=assetType
    )
    validator = fname.constructValidator(
        filenameBase, assetName=assetName, assetType=assetType
    )
    versionSuffix = fname.constructVersionSuffix(
        validator,
        files=fpath.findShotFiles(shot, dir=dir),
    )
    return f"{filenameBase}_{versionSuffix}"


def export(
    geometry: mobj.DAGNode | Sequence[mobj.DAGNode], dir: Path, filename: str
) -> None:
    """Call the MEL procedure for exporting a geometry cache"""
    cmds.workspace(fileRule=("fileCache", dir.as_posix()))

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
        f'"{dir.as_posix()}", "0", "{filename}", "0", "export", '
        '"1", "1", "1", "0", "0", "mcx", "1"}'
    )
    with mobj.TemporarySelection(geometry):
        mel.eval(doCreateGeometryCacheCmd)


def _getNodeNameBase(node: mobj.DAGNode) -> str:
    """From a node name 'namespace:node_name_type', get 'node_name'"""
    return node.rsplit(":", 1)[-1].rsplit("_", 1)[0]


def _buildWindow(*objects: str, outputPath: Path) -> mui.ProgressWindow:
    ui = mui.ProgressWindow("progressWindow", "Geometry Cache Exporter")

    def defineTask(product: str) -> str:
        name = _getNodeNameBase(product)
        return f"Exporting {name} geometry cache to:\n{outputPath}"

    ui.build().initialize(*[defineTask(o) for o in objects]).update()

    return ui


# FIXME: make exporting to test folder separate from main
@mapp.SuspendedRedraw()
@mapp.logScriptEditorOutput
def exportSelected() -> None:
    geometry = mobj.lsSelectedGeometry()
    if geometry is None:
        raise mobj.NoGeometrySelectedError

    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)
    shotDir = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
    cachesDir = shotDir / fpath.CACHES_DIR
    # cachesDir = fpath.getScenePath().parents[1] / "cache"

    ui = _buildWindow(*geometry, outputPath=cachesDir).show()

    assetName = _getNodeNameBase(geometry[0])
    filename = constructFilename(
        cachesDir,
        shot=shot,
        assetName=assetName,
        assetType=fname.AssetType.CACHE,
    )
    export(geometry, dir=cachesDir, filename=filename)
    ui.update().close()


################################################################################
# Import
################################################################################


class _GeometryCacheComponents:
    """Group of nodes that comprise a geometry cache"""

    __slots__ = "_origCacheFile", "cacheFile"

    def __new__(
        cls, cacheFile: mobj.DGNode
    ) -> _GeometryCacheComponents | NoReturn:
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
        self.cacheFile = cmds.rename(self.cacheFile, f"{nameBase}_cache")
        cmds.rename(self.historySwitch, f"{nameBase}_historySwitch")


def assetize(assetName: fname.NameIdentifier, namespace: str) -> None:
    """Contain the geometry cache network in an asset

    Also, expose the cacheFile node's cache directory and filename attributes.
    """
    cacheFileNodes = mobj.lsWithWildcard(assetName, type="cacheFile")
    componentNodes: list[mobj.DGNode] = []
    for i, c in enumerate(cacheFileNodes):
        components = _GeometryCacheComponents(c)
        components.rename(assetName)

        cacheFileNodes[i] = components.cacheFile
        componentNodes += components.cacheFile, components.historySwitch

    container = cmds.createNode("container", name=f"{namespace}_container")
    containerCmd = partial(cmds.container, container, edit=True)

    containerCmd(addNode=componentNodes, force=True)
    cmds.setAttr(f"{container}.blackBox", True)
    cmds.setAttr(f"{container}.viewMode", 0)

    cacheFileNode0, *cacheFileNodes = cacheFileNodes
    containerCmd(publishAndBind=(f"{cacheFileNode0}.cachePath", "folder"))
    containerCmd(publishAndBind=(f"{cacheFileNode0}.cacheName", "filename"))

    for c in cacheFileNodes:
        cmds.connectAttr(f"{cacheFileNode0}.cachePath", f"{c}.cachePath")
        cmds.connectAttr(f"{cacheFileNode0}.cacheName", f"{c}.cacheName")


# FIXME: make importing from test folder separate from main
@mapp.logScriptEditorOutput
def importSelected() -> None:
    if mobj.lsSelectedGeometry() is None:
        raise mobj.NoGeometrySelectedError

    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)
    shotPath = fpath.findShotPath(shot, parentDir=fpath.findSharedDrive())
    cachesDir = shotPath / fpath.CACHES_DIR
    # cachesDir = fpath.getScenePath().parents[1] / "cache"

    cmds.workspace(fileRule=("cacheFile", cachesDir))
    mui.setDefaultFileBrowserDir(cachesDir)

    # global proc doImportCacheArgList( int $version, string $args[] )
    #    $version == 0:
    #        $args[] = none
    mel.eval("doImportCacheArgList 0 {}")

    # Assetize network
    assetType = fname.AssetType.CACHE
    assetNamePattern = f"{shot.full}_*_{assetType}_v???"
    try:
        cacheFileNode = cmds.ls(f"{assetNamePattern}Cache1")[0]
    except IndexError:
        raise mui.NoFileSelectedError

    cacheFilename = cmds.getAttr(f"{cacheFileNode}.cacheName")
    assetize(
        # Formatted: 'rec_seq###_name_cache_v###'
        cacheFilename.split("_", 3)[2],
        mobj.constructNamespace(cacheFilename, assetType=assetType),
    )
