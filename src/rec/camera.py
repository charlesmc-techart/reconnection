"""Export the shot camera"""

from __future__ import annotations

__author__ = "Charles Mesa Cayobit"

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import NoReturn

import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj

_SUBPROCESS_SCRIPT_FILENAME = "export_mayaBinary.py"
_SUBPROCESS_SCRIPT_PATH = Path(__file__).with_name(_SUBPROCESS_SCRIPT_FILENAME)


def getComponents(
    cameraGrp: mobj.TopLevelGroup,
) -> tuple[mobj.DAGNode, ...] | None | NoReturn:
    """Get all components of a shot camera: transform and shape nodes

    If the camera uses a camera and aim, get the lookAt and locator nodes, too.
    """

    try:
        camera = mobj.lsChildren(cameraGrp, allDescendents=True, type="camera")
    except ValueError as e:
        groupName = "_____CAMERA_____"
        raise mobj.TopLevelGroupDoesNotExistError(groupName) from e
    try:
        camera = camera[0]
    except TypeError:
        return None

    cmds.setAttr(f"{camera}.renderable", True)
    xform: mobj.DAGNode = mobj.getParent(camera)  # type:ignore

    try:
        lookAt = cmds.listConnections(camera, type="lookAt")[0]
    except TypeError:
        return xform, camera

    target = f"{lookAt}.target[0].targetParentMatrix"
    locator = cmds.listConnections(target)[0]
    locatorShape = mobj.lsChildren(locator, shapes=True)[0]
    return lookAt, xform, camera, locator, locatorShape


def _exportMayaAsciiThenBinary(
    nodes: Sequence[mobj.DGNode], binaryFilePath: Path
) -> None:
    """Export the nodes to a temporary ASCII file before a binary one

    The nodes exported to an ASCII file in a temporary directory. Then, another
    instance of Maya is opened to export the nodes into a binary file.
    """

    prefix = f"{fname.SHOW}_"
    asciiFilename = f"{prefix}temp{fname.FileExt.MAYA_ASCII}"
    with TemporaryDirectory(prefix=prefix) as tempDir:
        asciiFilePath = Path(tempDir) / asciiFilename

        mobj.export(nodes, filePath=asciiFilePath, fileType=mapp.FileType.ASCII)

        mayapy = os.path.join(os.environ["MAYA_LOCATION"], "bin", "mayapy")
        args = (
            mayapy,
            _SUBPROCESS_SCRIPT_PATH,
            asciiFilePath,
            binaryFilePath,
            *nodes,
        )
        results = subprocess.run(args, capture_output=True, text=True)
    print(
        "",
        "stdout:",
        results.stdout,
        "",
        "stderr:",
        results.stderr,
        sep="\n",
    )


def export(cameraNodes: Sequence[mobj.DAGNode], filePath: Path) -> None:
    """If unknown nodes are present, temporarily export to an ASCII file"""

    if mobj.lsUnknown():
        _exportMayaAsciiThenBinary(cameraNodes, binaryFilePath=filePath)
        return
    mobj.export(cameraNodes, filePath=filePath, fileType=mapp.FileType.BINARY)
