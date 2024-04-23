"""Set render settings"""

__author__ = "Charles Mesa Cayobit"

import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp


def setGlobals() -> None:
    """Set global render settings"""
    drg = "defaultRenderGlobals"
    for attribute, value in (
        ("animation", True),
        ("putFrameBeforeExt", True),
        ("periodInExt", 1),
        ("modifyExtension", True),
        ("startExtension", 1),
        ("byExtension", 1),
    ):
        cmds.setAttr(f"{drg}.{attribute}", value)

    try:
        cache = cmds.ls(type="cacheFile")[0]
    except IndexError:
        cmds.warning("No geometry cache applied in the scene.")
        return

    startFrame = cmds.getAttr(f"{cache}.originalStart")
    cmds.playbackOptions(minTime=startFrame, animationStartTime=startFrame)
    cmds.setAttr(f"{drg}.startFrame", startFrame)

    endFrame = cmds.getAttr(f"{cache}.originalEnd")
    cmds.playbackOptions(maxTime=endFrame, animationEndTime=endFrame)
    cmds.setAttr(f"{drg}.endFrame", endFrame)


@mapp.logScriptEditorOutput
def setFlair() -> None:
    """Set Flair render settings"""
    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)
    renderDrive = fpath.findSharedDrive(dir=fpath.RENDER_GDRIVE)
    shotDir = fpath.findShotPath(shot, parentDir=renderDrive)

    cmds.setAttr(
        "flairGlobals._sequenceName",
        f"{shot.name.upper()}.<####>",
        type="string",
    )
    for attribute, value in (
        ("_taa", True),
        ("_renderScale", 1),
        #
        ("_bundleAOVs", True),  # FIXME: set bundle AOVs in EXR to True
        ("_eachLight", True),  # FIXME: set render each light to True
    ):
        try:
            cmds.setAttr(f"flairGlobals.{attribute}", value)
        except RuntimeError as e:
            cmds.warning(e)

    cmds.flair(alpha=2)  # set alpha to Premult

    targets = (
        "cryptomatte",
        "albedo",
        "lighting",
        "specular",
        "shadows",
        "ambientOcclusionTarget",
        "bloomTarget",
        "outputTarget",
    )
    cmds.flair(target=targets)  # set render targets


def setArnold(renderFilename: str) -> None:
    """Set Arnold render settings"""
    cmds.setAttr(
        "defaultRenderGlobals.currentRenderer", "arnold", type="string"
    )
    cmds.setAttr(
        "defaultRenderGlobals.imageFilePrefix", renderFilename, type="string"
    )

    cmds.setAttr("defaultArnoldDriver.aiTranslator", "exr", type="string")
    cmds.setAttr("defaultArnoldDriver.mergeAOVs", True)

    for attribute, value in (
        ("AA", 1),
        ("GIDiffuse", 1),
        ("GISpecular", 0),
        ("GITransmission", 0),
        ("GISss", 0),
        ("GIVolume", 1),
    ):
        cmds.setAttr(f"defaultArnoldRenderOptions.{attribute}Samples", value)
    cmds.setAttr("defaultArnoldRenderOptions.GIVolumeDepth", 1)
