"""Import or update the re:connection custom shelf"""

import os
import sys
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.maya as mapp

_SCRIPTS_DIR = Path(__file__).parents[1]
_SHELF_NAME = "reconnection"
_SHELF_FILE = _SCRIPTS_DIR.joinpath("rec", "data", f"shelf_{_SHELF_NAME}.mel")


@mapp.logScriptEditorOutput
def main() -> None:
    if f"{_SCRIPTS_DIR}" not in sys.path:
        sys.path.insert(0, f"{_SCRIPTS_DIR}")

    if cmds.shelfLayout(_SHELF_NAME, exists=True):
        mel.eval(f'deleteShelfTab "{_SHELF_NAME}"')
    mel.eval(f'loadNewShelf "{_SHELF_FILE.as_posix()}"')

    mayaVersion = cmds.about(version=True)
    envDir = Path(os.environ["MAYA_APP_DIR"], mayaVersion, "Maya.env")
    pathSeparator = ";" if cmds.about(ntOS=True) else ":"
    try:
        file = envDir.open("r+", encoding="utf-8")
    except FileNotFoundError:
        envDir.write_text(f"PYTHONPATH={_SCRIPTS_DIR}", encoding="utf-8")
        return
    for line in file:
        if f"{_SCRIPTS_DIR}" in line:
            return
        elif line.startswith("PYTHONPATH"):
            file.write(f"{pathSeparator}{_SCRIPTS_DIR}")
            return
    file.write(f"\nPYTHONPATH={_SCRIPTS_DIR}")
    file.close()
