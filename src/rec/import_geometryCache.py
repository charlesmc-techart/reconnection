import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp


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


# FIXME: make importing from test folder separate from main
@mapp.logScriptEditorOutput
def main() -> None:
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
