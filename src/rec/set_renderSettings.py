from functools import partial

import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp


def globals() -> None:
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
def flair() -> None:
    """Set Flair render settings"""
    shotName = fname.ShotID.fromFilename(fpath.getScenePath().stem).name
    cmds.setAttr(
        "flailGlobals._sequenceName",
        f"{shotName.upper()}.<####>",
        type="string",
    )
    for attribute, value in (
        ("_taa", True),
        ("_renderScale", 1),
        #
        ("_bundleAOVs", True),  # FIXME: set bundle AOVs in EXR to True
        ("_eachLight", True),  # FIXME: set render each light to True
        ("_format", ".exr"),  # FIXME: set format to EXR
    ):
        try:
            cmds.setAttr(f"flairGlobals.{attribute}", value)
        except Exception as e:
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
    )
    cmds.flair(target=targets)  # set render targets


def arnold(renderFilename: str) -> None:
    """Set Arnold render settings"""
    setStrAttr = partial(cmds.setAttr, type="string")
    setStrAttr("defaultRenderGlobals.currentRenderer", "arnold")
    setStrAttr("defaultRenderGlobals.imageFilePrefix", renderFilename)

    da = "defaultArnold"
    setStrAttr(f"{da}Driver.aiTranslator", "exr", type="string")
    cmds.setAttr(f"{da}Driver.mergeAOVs", True)

    daro = f"{da}RenderOptions"
    for attribute, value in (
        ("AA", 1),
        ("GIDiffuse", 1),
        ("GISpecular", 0),
        ("GITransmission", 0),
        ("GISss", 0),
        ("GIVolume", 1),
    ):
        cmds.setAttr(f"{daro}.{attribute}Samples", value)
    cmds.setAttr(f"{daro}.GIVolumeDepth", 1)
