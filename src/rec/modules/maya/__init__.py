__author__ = "Charles Mesa Cayobit"

import traceback
from collections.abc import Callable
from contextlib import ContextDecorator
from functools import partial
from pathlib import Path
from typing import Any

import maya.cmds as cmds
import maya.standalone

import rec.modules.files.paths as fpath
import rec.modules.stringEnum as strEnum

_LOGS_PATH = Path(__file__).parents[3] / "logs"


class FileType(strEnum.StringEnum):
    """File types accepted by Maya's cmds.file function"""

    ASCII = "mayaAscii"
    BINARY = "mayaBinary"
    ALEMBIC = "Alembic"


class Standalone:
    def __enter__(self) -> None:
        maya.standalone.initialize()

    def __exit__(self, *args: Any) -> None:
        maya.standalone.uninitialize()


def loadPlugin(pluginName: str) -> None:
    """Quietly load a plugin"""
    cmds.loadPlugin(pluginName, quiet=True)


class SuspendedRedraw(ContextDecorator):
    """Temporarily disable Maya from redrawing"""

    def __enter__(self) -> None:
        cmds.refresh(suspend=True)

    def __exit__(self, *args: Any) -> None:
        cmds.refresh(suspend=False)


def logScriptEditorOutput(
    func: Callable[[], Any], *, dir: Path = _LOGS_PATH
) -> Callable[[], None]:
    """Decorator for writing the script editor's output to a text file"""
    projectPath = fpath.getProjectPath()
    scenePath = fpath.getScenePath()

    module = func.__module__
    if module == "__main__":
        moduleName = "main"
    else:
        moduleName = module.rsplit(".", 1)[-1]
    funcName = func.__name__
    fullFuncName = f"{module}.{funcName}"

    filenameDate = cmds.date(format="YY-MM-DD_hh-mm-ss")
    logFilename = f"{filenameDate}.{moduleName}.log"
    logFilePath = dir / logFilename
    info = (
        f"Date: {cmds.date()}",
        f"Project: {projectPath}",
        f"Scene: {scenePath}",
        f"Called: {fullFuncName}",
    )

    printCmd = partial(print, sep="\n")
    divider = "", "#" * 80, ""

    def funcWithLogging() -> None:
        fd = cmds.cmdFileOutput(open=logFilePath.as_posix())

        printCmd(*info, *divider)
        try:
            func()
        except:
            traceback.print_exc()
            printCmd(*divider, f"{fullFuncName} raised an error")
            raise
        else:
            printCmd(
                *divider,
                f"{fullFuncName} completed",
            )
            logFilePath.rename(Path(f"{dir}/success/{logFilename}"))
        finally:
            cmds.cmdFileOutput(close=fd)

    return funcWithLogging
