from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path
from typing import NoReturn, Optional

import rec.modules.files.names as fname

_DRIVE = "G"
ASSETS_DIR = "REC/02_ASSETS"
_POST_PRODUCTION_DIR = "REC_POST"
CACHE_DIR = Path("LIGHT", "cache")


def filterShotFiles(shot: fname.ShotID, dir: Path) -> tuple[Path, ...]:
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


def getLatestVersionAsset(
    assetValidator: fname.AssetValidator, files: Iterable[Path]
) -> Optional[Path]:
    """Get the file path to the asset's latest version"""
    file = None
    for file in filter(assetValidator, files):
        continue
    return file


class DirecetoryNotFoundOnGoogleSharedDriveError(FileNotFoundError):
    """Provided directory could not be found on the Google shared drive"""

    def __init__(self, dir: Path | str) -> None:
        super().__init__(
            f"The directory, {dir}, could not be found on a Google Shared Drive"
        )


def getSharedDrive(
    *, drive: str = _DRIVE, dir: str = _POST_PRODUCTION_DIR
) -> Path | NoReturn:
    """Get the path to re:connection's Google shared drive

    By default, it gets the post-production shared drive.
    """
    if sys.platform == "win32":
        path = Path(f"{drive}:", "Shared drives", dir)
        if path.is_dir():
            return path.resolve()
        raise DirecetoryNotFoundOnGoogleSharedDriveError(dir)
    else:
        macGDrivePathPattern = "Library/CloudStorage/GoogleDrive*/Shared drives"
        for path in Path.home().glob(f"{macGDrivePathPattern}/{dir}"):
            if path.is_dir():
                return path.resolve()
        raise DirecetoryNotFoundOnGoogleSharedDriveError(dir)


def getModelPath(assetName: fname.AssetName, parentDir: Path) -> Path:
    """Get the path to the model's master file"""
    assetType = fname.AssetType.MODEL
    filenamePattern = f"rec_asset_{assetName}_{assetType}_*.*_MASTER.m?"
    dir = Path(parentDir, f"{assetName}".upper(), f"{assetType}".upper())
    dir = next(dir.glob("*.*")).joinpath("MAYA", "scenes")
    return next(dir.glob(filenamePattern)).resolve()


def getShotPath(shot: fname.ShotID, parentDir: Path) -> Path | NoReturn:
    """Get the path to the specific shot directory"""

    def findDir(identifier: str, parentDir: Path) -> Path:
        for d in parentDir.iterdir():
            if d.is_dir() and d.stem.endswith(identifier):
                return d
        raise DirecetoryNotFoundOnGoogleSharedDriveError(parentDir)

    sequenceDir = findDir(shot.sequence.upper(), parentDir)
    return findDir(shot.number, sequenceDir)
