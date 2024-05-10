"""Set render settings"""

from __future__ import annotations

__author__ = "Charles Mesa Cayobit"

from typing import ClassVar

import maya.cmds as cmds
import maya.mel as mel

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


class setPlayblast:
    """Temporarily set playblast settings"""

    modelEditorOptions: ClassVar[dict[str, bool | str]] = {
        "allObjects": False,
        "displayAppearance": "smoothShaded",
        "displayLights": "flat",
        "displayTextures": False,
        "grid": False,
        "headsUpDisplay": False,
        "manipulators": False,
        "polymeshes": True,
        "useDefaultMaterial": False,
        "selectionHiliteDisplay": False,
        "shadows": False,
        "wireframeOnShaded": False,
        "xray": False,
    }
    hardwareRenderGlobalsOptions: ClassVar[dict[str, bool]] = {
        "ssaoEnable": False,
        "motionBlurEnable": False,
        "multiSampleEnable": True,
    }

    def __init__(self) -> None:
        self.viewport: str = cmds.playblast(activeEditor=True)

        self.origModelEditorOptions: dict[str, bool | str] = {}
        for k in self.modelEditorOptions:
            if k == "allObjects":
                self.origModelEditorOptions[k] = True
            else:
                self.origModelEditorOptions[k] = cmds.modelEditor(
                    self.viewport, query=True, **{k: True}
                )

        self.origHardwareRenderGlobalsOptions: dict[str, bool] = {
            k: cmds.getAttr(f"hardwareRenderingGlobals.{k}")
            for k in self.hardwareRenderGlobalsOptions
        }
        self.origGradient: bool = cmds.displayPref(
            query=True, displayGradient=True
        )
        self.origBg = cmds.displayRGBColor("background", query=True)

    def __enter__(self) -> str:
        cmds.modelEditor(self.viewport, edit=True, **self.modelEditorOptions)
        for k, v in self.hardwareRenderGlobalsOptions.items():
            cmds.setAttr(f"hardwareRenderingGlobals.{k}", v)
        cmds.displayPref(displayGradient=False)
        cmds.displayRGBColor("background", 0, 0, 0)

        return self.viewport

    def __exit__(self, *args) -> None:
        cmds.modelEditor(
            self.viewport, edit=True, **self.origModelEditorOptions
        )
        for k, v in self.origHardwareRenderGlobalsOptions.items():
            cmds.setAttr(f"hardwareRenderingGlobals.{k}", v)
        cmds.displayPref(displayGradient=self.origGradient)
        cmds.displayRGBColor("background", *self.origBg)

        mel.eval("rebuildShowMenu")


@mapp.logScriptEditorOutput
def setFlair() -> None:
    """Set Flair render settings"""
    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)
    renderDrive = fpath.findSharedDrive(dir=fpath.RENDER_GDRIVE)
    shotDir = fpath.findShotPath(shot, parentDir=renderDrive) / "IMAGES"

    for attribute, value in (
        ("_sequenceDir", shotDir.as_posix()),
        ("_sequenceName", f"{shot.name.upper()}.<###>"),
    ):
        try:
            cmds.setAttr(f"flairGlobals.{attribute}", value, type="string")
        except RuntimeError as e:
            cmds.warning(e)

    for attribute, value in (("_taa", True), ("_renderScale", 1)):
        try:
            cmds.setAttr(f"flairGlobals.{attribute}", value)
        except RuntimeError as e:
            cmds.warning(e)

    cmds.flair(alpha=2)  # set alpha to Premult

    cmds.flair(target=("outputTarget",))  # set render targets


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
