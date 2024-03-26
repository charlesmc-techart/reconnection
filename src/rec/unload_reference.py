from pathlib import Path

import maya.cmds as cmds


class NoReferenceNodeSelectedError(Exception):
    def __init__(self) -> None:
        super().__init__("No reference node selected")


def unloadReference(referenceNode) -> None:
    file = Path(cmds.referenceQuery(referenceNode, filename=True))
    cmds.file(file.as_posix(), unloadReference=referenceNode)


def main() -> None:
    selection = cmds.ls(selection=True, type="reference")
    if not selection:
        raise NoReferenceNodeSelectedError

    for s in selection:
        unloadReference(s)
