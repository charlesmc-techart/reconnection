from __future__ import annotations

__author__ = "Charles Mesa Cayobit"

import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import NoReturn

import maya.cmds as cmds

import rec.modules.files.names as fname

_DRIVE = "G"
MAIN_GDRIVE = "REC"
POST_PRODUCTION_GDRIVE = "REC_POST"
RENDER_GDRIVE = "REC_RENDER"

ASSETS_DIR = os.path.join(MAIN_GDRIVE, "02_ASSETS")
CACHES_DIR = os.path.join("LIGHT", "cache")


def getProjectPath() -> Path:
    """Get the path to the current project"""
    return Path(cmds.workspace(query=True, fullName=True))


def getScenePath() -> Path:
    """Get the path to the current scene

    If the scene is blank and unsaved, it gets the path to the current project,
    including the untitled file.
    """
    if path := cmds.file(query=True, sceneName=True):
        path = Path(path)
    else:
        path = getProjectPath() / "untitled"
    return path


def findShotFiles(shot: fname.ShotId, dir: Path) -> tuple[Path, ...]:
    """Filter shot files in the provided directory

    The internal list is sorted so the last item is the latest version,
    then it is returned as a tuple.
    """
    files = [
        f
        for f in dir.iterdir()
        if f.is_file() and fname.inFilename(shot, file=f)
    ]
    files.sort()
    return tuple(files)


def findLatestVersionAsset(
    validator: fname.Validator, files: Iterable[Path]
) -> Path | None:
    """Get the file path to the asset's latest version"""
    file = None
    for file in filter(validator, files):
        continue
    return file


class DirectoryNotFoundError(FileNotFoundError):
    """Provided directory could not be found on the Google shared drive"""

    def __init__(self, dir: Path | str) -> None:
        super().__init__(f"Directory not found: '{dir}'")


def findSharedDrive(
    *, drive: str = _DRIVE, dir: str = POST_PRODUCTION_GDRIVE
) -> Path | NoReturn:
    """Get the path to re:connection's Google shared drive

    By default, it gets the post-production shared drive.
    """
    if sys.platform == "win32":
        path = Path(f"{drive}:", "Shared drives", dir)
        if path.is_dir():
            return path
        raise DirectoryNotFoundError(path)
    else:
        pathPattern = "Library/CloudStorage/GoogleDrive*/Shared drives"
        for path in Path.home().glob(f"{pathPattern}/{dir}"):
            if path.is_dir():
                return path
        raise DirectoryNotFoundError(f"~/{pathPattern}/{dir}")


# TODO: cleaner way to do this?
def findModelPath(assetName: fname.NameIdentifier, parentDir: Path) -> Path:
    """Get the path to the model's master file"""
    assetType = fname.AssetType.MODEL
    filePathPattern = os.path.join(
        f"{assetName}".upper(),
        f"{assetType}".upper(),
        "*.*",
        "MAYA",
        "scenes",
        f"rec_asset_{assetName}_{assetType}_*.*_MASTER.m?",
    )
    for path in parentDir.glob(filePathPattern):
        if path.is_file():
            return path
    raise FileNotFoundError(parentDir / filePathPattern)


def findShotPath(shot: fname.ShotId, parentDir: Path) -> Path | NoReturn:
    """Get the path to the specific shot directory"""

    def findDir(identifier: str, parentDir: Path) -> Path:
        for d in parentDir.iterdir():
            if d.is_dir() and d.stem.endswith(identifier):
                return d
        raise DirectoryNotFoundError(parentDir / f"*{identifier}")

    sequenceDir = findDir(shot.sequence.upper(), parentDir)
    return findDir(shot.number, sequenceDir)
