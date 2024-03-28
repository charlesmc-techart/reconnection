"""Unload the selected referenced assets"""

from pathlib import Path

import maya.cmds as cmds

import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj


class NoReferenceNodeSelectedError(Exception):
    def __init__(self) -> None:
        super().__init__("No reference node selected")


def unloadReference(referenceNode: mobj.ReferenceNode) -> None:
    """Unload a reference"""
    file = Path(cmds.referenceQuery(referenceNode, filename=True))
    cmds.file(file.as_posix(), unloadReference=referenceNode)


@mapp.logScriptEditorOutput
def main() -> None:
    selection = cmds.ls(selection=True, type="reference")
    if not selection:
        raise NoReferenceNodeSelectedError

    for s in selection:
        unloadReference(s)
