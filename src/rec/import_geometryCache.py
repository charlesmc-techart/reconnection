import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya.app as mapp


# FIXME: make importing from test folder separate from main
@mapp.logScriptEditorOutput
def main() -> None:
    gDriveShotDir = fpath.getShotPath(
        fname.ShotID.getFromFilename(mapp.getScenePath().stem),
        parentDir=fpath.getSharedDrive(),
    )
    shotCachesDirPath = gDriveShotDir / fpath.CACHE_DIR
    shotCachesDirPath = mapp.getScenePath().parents[1] / "cache"

    cmds.workspace(fileRule=("cacheFile", shotCachesDirPath))

    # global proc doImportCacheArgList( int $version, string $args[] )
    #    $version == 0:
    #        $args[] = none
    doImportCacheArgListCmd = "doImportCacheArgList 0 {}"
    mel.eval(doImportCacheArgListCmd)
