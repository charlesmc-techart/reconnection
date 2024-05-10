from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial
from typing import Any, Literal, Union

import maya.cmds as cmds
import maya.mel as mel

import rec.camera
import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj
import rec.modules.maya.ui as mui
import rec.renderSettings

WINDOW_TITLE = "Mask Exporter"
WINDOW_NAME = "maskWindow"


class _Mask:
    __slots__ = "target", "origShaderConnections"

    def __init__(self, target: mobj.DAGNode | Sequence[mobj.DAGNode]) -> None:
        self.target = target

        self.origShaderConnections: dict[str, str] = {}
        for m in cmds.ls(type="shadingEngine"):
            if shader := cmds.listConnections(f"{m}.surfaceShader", plugs=True):
                self.origShaderConnections[m] = shader[0]

    def __enter__(self) -> None:
        if self.target is mobj.ROBOT_MODEL_GEO_GRP:
            cmds.setAttr(f"{mobj.ROBOT_FACE_MODEL_GEO}.visibility", False)

        self._create("black", colorRgb=(0, 0, 0))
        self._create("white", colorRgb=(1, 1, 1), target=self.target)

    def __exit__(self, *args: Any) -> None:
        if self.target is mobj.ROBOT_MODEL_GEO_GRP:
            cmds.setAttr(f"{mobj.ROBOT_FACE_MODEL_GEO}.visibility", True)

        for k, v in self.origShaderConnections.items():
            try:
                cmds.connectAttr(v, f"{k}.surfaceShader", force=True)
            except RuntimeError:
                continue

    def _create(
        self,
        colorLabel: Literal["black"] | Literal["white"],
        colorRgb: Sequence[float],
        target: mobj.DAGNode | Sequence[mobj.DAGNode] | None = None,
    ) -> None:
        lambert = f"mask_{colorLabel}_lam"
        if not mobj.nodeExists(lambert, "lambert"):
            cmds.shadingNode("lambert", name=lambert, asShader=True)
        cmds.setAttr(f"{lambert}.color", *colorRgb, type="float3")
        cmds.setAttr(f"{lambert}.diffuse", colorRgb[0])

        if target is None:
            target = cmds.ls(type="dagNode")
        shapes = mobj.lsChildren(target, allDescendents=True, type="shape")
        for sg in frozenset(cmds.listConnections(shapes, type="shadingEngine")):
            cmds.connectAttr(
                f"{lambert}.outColor", f"{sg}.surfaceShader", force=True
            )


class _InputWindow(mui.Window):
    def __init__(self, name: str, title: str) -> None:
        super().__init__(name, title)
        self.textField: str

    def build(
        self, *, shot: fname.ShotId, callback: Callable[[Any], None]
    ) -> _InputWindow:
        super().build()

        window = cmds.window(
            self.name,
            parent=mel.eval("$gMainWindow = $gMainWindow"),
            resizeToFitChildren=True,
            sizeable=False,
            title=self.title,
            widthHeight=(342, 16),
        )
        formLayout = cmds.formLayout(parent=window)

        text = cmds.text(
            label="Please enter a label, then press enter. The file will be saved as:",
            parent=formLayout,
        )

        placeholderFilename = f"{shot.name.upper()}_<label>_ALPHA.mov"
        filenameText = cmds.text(label=placeholderFilename, parent=formLayout)

        def updateTextFilename(_) -> None:
            if label := self.getInput():
                cmds.text(
                    filenameText,
                    edit=True,
                    label=placeholderFilename.replace("<label>", label),
                )
            else:
                cmds.text(filenameText, edit=True, label=placeholderFilename)

        self.textField = cmds.textField(
            alwaysInvokeEnterCommandOnReturn=True,
            changeCommand=updateTextFilename,
            enterCommand=callback,
            parent=formLayout,
        )

        cmds.formLayout(
            formLayout,
            edit=True,
            attachControl=(
                (filenameText, "top", 7, text),
                (self.textField, "top", 7, filenameText),
            ),
            attachForm=(
                (text, "top", 7),
                (text, "left", 21),
                (text, "right", 21),
                (filenameText, "left", 21),
                (filenameText, "right", 21),
                (self.textField, "left", 21),
                (self.textField, "right", 21),
                (self.textField, "bottom", 7),
            ),
        )

        return self

    def getInput(self) -> str:
        input = cmds.textField(self.textField, query=True, text=True)
        return input.upper()


@mapp.SuspendedRedraw()
def _main(
    shot: fname.ShotId,
    geometry: mobj.DAGNode | Sequence[mobj.DAGNode],
    label: str,
) -> None:

    try:
        camera = rec.camera.getComponents(mobj.TopLevelGroup.CAMERA)
    except mobj.TopLevelGroupDoesNotExistError:
        camera = rec.camera.getComponents(mobj.TopLevelGroup.CACHE)
    if camera is None:
        raise RuntimeError("No camera in scene")
    for c in camera:
        if cmds.objectType(c, isType="camera"):
            camera = c
            break

    exportDir = fpath.findSharedDrive()
    filename = f"{shot.name}_{label}_alpha".upper()
    filePath = exportDir / filename
    import os

    resolutionWidth = cmds.getAttr("defaultResolution.width")
    resolutionHeight = cmds.getAttr("defaultResolution.height")
    with _Mask(geometry), rec.renderSettings.Playblast() as viewport:
        cmds.lookThru(viewport, camera)  # type: ignore
        cmds.playblast(
            clearCache=True,
            compression="h.264",
            # filename=filePath.as_posix(),
            filename=os.path.join("/Users/charles_mc/Desktop", filename),
            forceOverwrite=True,
            format="qt",
            percent=100,
            quality=100,
            sequenceTime=False,
            showOrnaments=False,
            viewer=False,
            widthHeight=(resolutionWidth, resolutionHeight),
        )


@mapp.logScriptEditorOutput
def exportMechanic() -> None:
    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)

    geometry = mobj.MECHANIC_MODEL_GEO_GRP
    if not mobj.nodeExists(geometry, "transform"):
        raise RuntimeError("Mechanic not in scene")

    _main(shot=shot, geometry=geometry, label="MC")


@mapp.logScriptEditorOutput
def exportRobot() -> None:
    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)

    geometry = mobj.ROBOT_MODEL_GEO_GRP
    if not mobj.nodeExists(geometry, "transform"):
        raise RuntimeError("Robot not in scene")

    _main(shot=shot, geometry=geometry, label="RB")


def exportSelected() -> None:
    shot = fname.ShotId.fromFilename(fpath.getScenePath().stem)

    geometry = mobj.lsSelectedGeometry()
    if geometry is None:
        raise mobj.NoGeometrySelectedError
    ui = _InputWindow("inputWindow", WINDOW_TITLE)

    def export(_) -> None:
        label = ui.getInput()
        _main(shot=shot, geometry=geometry, label=label)

    ui.build(shot=shot, callback=export).show()
