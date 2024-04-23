from __future__ import annotations

__author__ = "Charles Mesa Cayobit"

from collections.abc import Iterator
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel

import rec.modules.files.names as fname


def setDefaultFileBrowserDir(dir: Path) -> None:
    """The Maya file browser will open to this directory"""
    mel.eval(f'$gDefaultFileBrowserDir = "{dir.as_posix()}"')


class NoFileSelectedError(Exception):
    """No file was chosen from the Maya file browser"""

    def __init__(self) -> None:
        super().__init__("No file was selected")


class ProgressWindow:
    """A window with a prgress bar"""

    _instances: dict[str, ProgressWindow] = {}

    __slots__ = (
        "_name",
        "_title",
        "name",
        "title",
        "text",
        "progressBar",
        "tasks",
        "tasksDone",
    )

    def __new__(cls, name: str, title: str) -> ProgressWindow:
        """Only create one instance for each title"""
        if title not in cls._instances:
            cls._instances[title] = super().__new__(cls)
        return cls._instances[title]

    def __init__(self, name: str, title: str) -> None:
        self._name = name
        self._title = title

        self.name = f"{fname.SHOW}_{name}"
        self.title = f"{fname.SHOW_FULL_TITLE} {title}"
        self.text: str
        self.progressBar: str
        self.tasks: Iterator[str]
        self.tasksDone = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._name!r}, {self._title!r})"

    def build(self) -> ProgressWindow:
        if cmds.window(self.name, exists=True):
            cmds.deleteUI(self.name, window=True)
        window = cmds.window(
            self.name,
            parent=mel.eval("$gMainWindow = $gMainWindow"),
            resizeToFitChildren=True,
            sizeable=False,
            title=self.title,
            widthHeight=(512, 16),
        )
        formLayout = cmds.formLayout(parent=window)
        self.text = cmds.text(parent=formLayout)
        self.progressBar = cmds.progressBar(parent=formLayout)
        cmds.formLayout(
            formLayout,
            edit=True,
            attachControl=((self.progressBar, "top", 7, self.text)),
            attachForm=(
                (self.text, "top", 7),
                (self.text, "left", 7),
                (self.text, "right", 7),
                (self.progressBar, "left", 7),
                (self.progressBar, "right", 7),
                (self.progressBar, "bottom", 7),
            ),
        )

        return self

    def initialize(self, *tasks: str) -> ProgressWindow:
        cmds.progressBar(self.progressBar, edit=True, maxValue=len(tasks))
        self.tasks = iter(tasks)

        return self

    def update(self) -> ProgressWindow:
        def update(currentTask: str) -> None:
            print(currentTask, end="\n")
            cmds.text(self.text, edit=True, label=currentTask)
            cmds.progressBar(
                self.progressBar, edit=True, progress=self.tasksDone
            )

        try:
            currentTask = next(self.tasks)
        except StopIteration:
            currentTask = "Complete!"
            update(currentTask)
        else:
            update(currentTask)
            self.tasksDone += 1

        return self

    def show(self) -> ProgressWindow:
        cmds.showWindow(self.name)

        return self

    def close(self) -> None:
        cmds.deleteUI(self.name)
