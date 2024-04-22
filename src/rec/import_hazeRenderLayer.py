"""Import the haze render layer template"""

from pathlib import Path

import maya.app.renderSetup.model.renderSetup as renderSetup
import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.set_renderSettings as set_renderSettings

_TEMPLATE_DIR = Path(__file__).with_name("data")
_TEMPLATE = _TEMPLATE_DIR / "renderLayer_haze.json"
_LAYER_NAME = "HAZE"


@mapp.SuspendedRedraw()
@mapp.logScriptEditorOutput
def main() -> None:
    mapp.loadPlugin("mtoa")

    def createAiNode(node: mobj.DGNode) -> mobj.DGNode:
        if not (
            cmds.objExists(f"::{node}")
            and cmds.objectType(f"::{node}", isType=node)
        ):
            node = cmds.shadingNode(node, asShader=True, name=node)
        return node

    # Create aiLambert and aiAtmosphereVolume
    createAiNode("aiLambert")
    atmosphere = createAiNode("aiAtmosphereVolume")
    cmds.setAttr(f"{atmosphere}.density", 0.1)
    cmds.setAttr(f"{atmosphere}.samples", 10)
    cmds.connectAttr(
        f"{atmosphere}.message",
        "defaultArnoldRenderOptions.atmosphere",
        force=True,
    )

    with mobj.TemporarySelection(cmds.ls(type="dagNode")):
        cmds.hyperShade(assign="initialShadingGroup")

    # Import HAZE render layer
    rs = renderSetup.instance()
    rs.importAllFromFile(_TEMPLATE, renderSetup.DECODE_AND_MERGE, None)
    layer = rs.getRenderLayer(_LAYER_NAME)
    rs.switchToLayer(layer)
    cmds.setAttr("defaultRenderLayer.renderable", False)

    scene = fpath.getScenePath()
    sceneName = scene.stem
    shot = fname.ShotId.fromFilename(sceneName)

    # Set render settings
    set_renderSettings.globals()
    set_renderSettings.arnold(f"{shot.name}.{_LAYER_NAME}".upper())

    # Save scene as new file
    # Construct filename base
    if "arnold" in sceneName:
        filenameBase = sceneName.split("arnold")[0]
        filenameBase += "arnold"
    else:
        filenameBase, artistLastName = sceneName.rsplit(".", 1)
        artistLastName = artistLastName.split("_", 1)[0]
        filenameBase += f".{artistLastName}_arnold"

    # Construct version suffix
    validator = fname.constructValidator(
        filenameBase,
        assetName=fname.AssetName.ARNOLD,
        assetType=fname.AssetType.LIGHTS,
    )
    sceneFiles = fpath.findShotFiles(shot, dir=scene.parent)
    versionSuffix = fname.constructVersionSuffix(validator, files=sceneFiles)

    if mobj.lsUnknown():
        fileExt = scene.suffix
        fileType = cmds.file(query=True, type=True)[0]
    else:
        fileExt = fname.FileExt.MAYA_BINARY
        fileType = mapp.FileType.BINARY

    filePath = scene.with_name(f"{filenameBase}_{versionSuffix}{fileExt}")
    cmds.file(rename=filePath.as_posix())
    cmds.file(force=True, options="v=0", save=True, type=fileType)
