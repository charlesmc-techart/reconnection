from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path
from typing import NoReturn, Optional

import maya.cmds as cmds

import rec.modules.files.names as fname

_DRIVE = "G"
ASSETS_DIR = "REC/02_ASSETS"
_POST_PRODUCTION_DIR = "REC_POST"
CACHES_DIR = Path("LIGHT", "cache")


def getProjectPath() -> Path:
    """Get the path to the current project"""
    return Path(cmds.workspace(query=True, fullname=True))


def getScenePath() -> Path:
    """Get the path to the current scene

    If the scene is blank and unsaved, it gets the path to the current project,
    including the untitled file.
    """
    if path := cmds.file(query=True, sceneName=True):
        path = Path(path)
    else:
        path = getProjectPath() / "untitled"
    return path.resolve()


def findShotFiles(shot: fname.ShotID, dir: Path) -> tuple[Path, ...]:
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
) -> Optional[Path]:
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
    *, drive: str = _DRIVE, dir: str = _POST_PRODUCTION_DIR
) -> Path | NoReturn:
    """Get the path to re:connection's Google shared drive

    By default, it gets the post-production shared drive.
    """
    if sys.platform == "win32":
        path = Path(f"{drive}:", "Shared drives", dir)
        if path.is_dir():
            return path.resolve()
        raise DirectoryNotFoundError(path)
    else:
        pathPattern = "Library/CloudStorage/GoogleDrive*/Shared drives"
        for path in Path.home().glob(f"{pathPattern}/{dir}"):
            if path.is_dir():
                return path.resolve()
        raise DirectoryNotFoundError(f"~/{pathPattern}/{dir}")


def findModelPath(assetName: fname.NameIdentifier, parentDir: Path) -> Path:
    """Get the path to the model's master file"""
    assetType = fname.AssetType.MODEL
    filenamePattern = f"rec_asset_{assetName}_{assetType}_*.*_MASTER.m?"
    dir = Path(parentDir, f"{assetName}".upper(), f"{assetType}".upper())
    dir = next(dir.glob("*.*")).joinpath("MAYA", "scenes")
    return next(dir.glob(filenamePattern)).resolve()


def findShotPath(shot: fname.ShotID, parentDir: Path) -> Path | NoReturn:
    """Get the path to the specific shot directory"""

    def findDir(identifier: str, parentDir: Path) -> Path:
        for d in parentDir.iterdir():
            if d.is_dir() and d.stem.endswith(identifier):
                return d
        raise DirectoryNotFoundError(parentDir / ("*" + identifier))

    sequenceDir = findDir(shot.sequence.upper(), parentDir)
    return findDir(shot.number, sequenceDir)
