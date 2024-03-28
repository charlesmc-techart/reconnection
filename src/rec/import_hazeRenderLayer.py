from pathlib import Path

import maya.app.renderSetup.model.renderSetup as renderSetup
import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj

_ARNOLD_RENDER_OPTIONS = {
    "AASamples": 1,
    "GIDiffuseSamples": 1,
    "GISpecularSamples": 0,
    "GITransmissionSamples": 0,
    "GISssSamples": 0,
    "GIVolumeSamples": 1,
    "GIVolumeDepth": 1,
}

_TEMPLATE_DIR = Path(__file__).with_name("data")
_TEMPLATE = _TEMPLATE_DIR / "renderLayer_haze.json"
_LAYER_NAME = "HAZE"


def createAiNode(node: mobj.DGNode) -> mobj.DGNode:
    if not (
        cmds.objExists(f"::{node}")
        and cmds.objectType(f"::{node}", isType=node)
    ):
        node = cmds.shadingNode(node, asShader=True, name=node)
    return node


@mapp.logScriptEditorOutput
def main() -> None:
    # Create aiLambert and aiAtmosphereVolume
    mapp.loadPlugin("mtoa")
    createAiNode("aiLambert")
    atmosphere = createAiNode("aiAtmosphereVolume")
    cmds.connectAttr(
        f"{atmosphere}.message",
        "defaultArnoldRenderOptions.atmosphere",
        force=True,
    )

    # Set Arnold settings
    for k, v in _ARNOLD_RENDER_OPTIONS.items():
        cmds.setAttr(f"defaultArnoldRenderOptions.{k}", v)

    try:
        cache = cmds.ls(type="cacheFile")[0]
    except IndexError:
        pass  # Don't set the frame range
    else:
        startFrame = cmds.getAttr(cache + ".originalStart")
        cmds.playbackOptions(minTime=startFrame, animationStartTime=startFrame)
        cmds.setAttr("defaultRenderGlobals.startFrame", startFrame)

        endFrame = cmds.getAttr(cache + ".originalEnd")
        cmds.playbackOptions(maxTime=endFrame, animationEndTime=endFrame)
        cmds.setAttr("defaultRenderGlobals.endFrame", endFrame)

    # Import HAZE render layer
    rs = renderSetup.instance()
    rs.importAllFromFile(_TEMPLATE, renderSetup.DECODE_AND_MERGE, None)
    layer = rs.getRenderLayer(_LAYER_NAME)
    rs.switchToLayer(layer)
    cmds.setAttr("defaultRenderLayer.renderable", False)

    # Save scene as new file
    # Construct filename base
    scene = fpath.getScenePath()
    sceneName = scene.stem
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
    shot = fname.ShotID.fromFilename(sceneName)
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
