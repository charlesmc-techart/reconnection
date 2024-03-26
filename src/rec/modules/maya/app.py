import traceback
from collections.abc import Callable
from contextlib import ContextDecorator
from functools import partial
from pathlib import Path
from typing import Any

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.stringEnum as strEnum

_LOGS_PATH = Path(__file__).parents[3] / "logs"


class FileType(strEnum.StringEnum):
    """File types accepted by Maya's cmds.file function"""

    ASCII = "mayaAscii"
    BINARY = "mayaBinary"
    ALEMBIC = "Alembic"


def getScenePath() -> Path:
    """Get the path to the current scene

    If the scene is blank and unsaved, it gets the path to the current project,
    including the untitled file.
    """
    if path := cmds.file(query=True, sceneName=True):
        path = Path(path)
    else:
        path = Path(cmds.workspace(query=True, fullName=True), "untitled")
    return path.resolve()


def loadPlugin(pluginName: str) -> None:
    """Quietly load a plugin"""
    cmds.loadPlugin(pluginName, quiet=True)


class SuspendedRedraw(ContextDecorator):
    """Temporarily disable Maya from redrawing"""

    def __enter__(self) -> None:
        cmds.refresh(suspend=True)

    def __exit__(self, *args) -> None:
        cmds.refresh(suspend=False)


def logScriptEditorOutput(
    func: Callable[[], Any], *, dir: Path = _LOGS_PATH
) -> Callable[[], None]:
    """Decorator for writing the script editor's output to a text file"""
    projectPath = Path(cmds.workspace(query=True, fullName=True)).resolve()
    scenePath = getScenePath()
    sceneFilename = scenePath.stem

    module = func.__module__
    if module == "__main__":
        moduleName = "main"
    else:
        moduleName = module.rsplit(".", 1)[-1]
    funcName = func.__name__
    fullFuncName = f"{module}.{funcName}"

    date = cmds.date(format="YYMMDD.hhmmss")
    logFilenameBase = f"{date}.{moduleName}.{funcName}.{sceneFilename}"
    logFilePath = dir / (logFilenameBase + ".log")
    info = (
        f"Date: {cmds.date()}",
        f"Project: {projectPath}",
        f"Scene: {scenePath}",
        f"Called: {fullFuncName}",
    )

    printCmd = partial(print, sep="\n")
    divider = "", "#" * 80, ""
    printCmd(*info, *divider)

    def funcWithLogging() -> None:
        fd = cmds.cmdFileOutput(open=logFilePath.as_posix())

        try:
            func()
        except:
            traceback.print_exc()
            printCmd(*divider, f"{fullFuncName} executed unsuccessfully")
            raise
        else:
            printCmd(
                *divider,
                f"{fullFuncName} executed successfully",
            )
        finally:
            cmds.cmdFileOutput(close=fd)

    return funcWithLogging


class NoFileSelectedError(Exception):
    def __init__(self) -> None:
        super().__init__("No file was selected")


def setDefaultFileBrowserDir(dir: Path) -> None:
    mel.eval(f'$gDefaultFileBrowserDir = "{dir.as_posix()}"')
