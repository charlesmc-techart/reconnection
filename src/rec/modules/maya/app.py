import traceback
from collections.abc import Callable
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any

import maya.cmds as cmds

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
    sceneFilename = scenePath.stem or "untitled"

    module = func.__module__
    if module == "__main__":
        moduleName = "main"
    else:
        moduleName = module.rsplit(".", 1)[-1]
    funcName = func.__name__

    date = cmds.date(format="YYMMDD.hhmmss")
    logFilenameBase = f"{date}.{moduleName}.{funcName}.{sceneFilename}"
    logFilePath = dir / (logFilenameBase + ".log")
    info = (
        f"Date: {cmds.date()}",
        f"Project: {projectPath}",
        f"Scene: {scenePath}",
        f"Called: {module}.{funcName}",
    )

    def funcWithLogging() -> None:
        fileDescriptor = cmds.cmdFileOutput(open=logFilePath.as_posix())

        print(*info, "", sep="\n")
        try:
            func()
        except:
            traceback.print_exc()
            raise
        finally:
            cmds.cmdFileOutput(close=fileDescriptor)

    return funcWithLogging
