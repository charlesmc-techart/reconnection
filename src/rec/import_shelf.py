import os
import sys
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel

_SHELF_NAME = "reconnection"
_SHELF_DIR = f"data/shelf_{_SHELF_NAME}.mel"


def main() -> None:
    scriptsDir = Path(__file__).resolve().parent
    if f"{scriptsDir}" not in sys.path:
        sys.path.insert(0, f"{scriptsDir}")

    shelfFile = scriptsDir / _SHELF_DIR
    try:
        mel.eval(f'deleteShelfTab "{_SHELF_NAME}"')
    except RuntimeError as e:
        raise
    finally:
        mel.eval(f'loadNewShelf "{shelfFile.as_posix()}"')

    mayaVersion = cmds.about(version=True)
    envDir = Path(os.environ["MAYA_APP_DIR"], mayaVersion, "Maya.env")
    pathSeparator = ";" if cmds.about(ntOS=True) else ":"
    try:
        file = envDir.open("r+", encoding="utf-8")
    except FileNotFoundError:
        envDir.write_text(f"PYTHONPATH={scriptsDir}", encoding="utf-8")
        return
    for line in file:
        if f"{scriptsDir}" in line:
            return
        elif line.startswith("PYTHONPATH"):
            file.write(f"{pathSeparator}{scriptsDir}")
            return
    file.write(f"\nPYTHONPATH={scriptsDir}")
    file.close()
