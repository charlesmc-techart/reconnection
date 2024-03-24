from pathlib import Path

import maya.cmds as cmds


class NoReferenceNodeSelectedError(Exception):
    def __init__(self) -> None:
        super().__init__("No reference node is selected")


def unloadReference(referenceNode) -> None:
    filePath = Path(cmds.referenceQuery(referenceNode, filename=True))
    cmds.file(filePath.as_posix(), unloadReference=referenceNode)


def main() -> None:
    selection = cmds.ls(selection=True, type="reference")
    if not selection:
        raise NoReferenceNodeSelectedError

    for s in selection:
        unloadReference(s)
