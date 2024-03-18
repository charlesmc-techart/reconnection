from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import partial
from pathlib import Path
from typing import Optional, Union

import rec.modules.stringEnum as strEnum

SHOW = "rec"
SHOW_FULL_TITLE = "re:connection"

_VERSION_INDICATOR = "v"


class ReConnectionFilenameError(Exception):
    """File does not adhere to re:connection's filename protocol"""

    def __init__(self, filename: str) -> None:
        message = (
            f"The current scene's filename, {filename}, must contain "
            "'rec_seq###' for the script to work properly."
        )
        super().__init__(message)


class ShotID:
    __slots__ = "name", "sequence", "number", "full"

    def __init__(self, name: str) -> None:
        self.name = name
        self.sequence = name[:3]
        self.number = name[3:]
        self.full = f"{SHOW}_{name}"

    def __str__(self) -> str:
        return f"{self.name}"

    @classmethod
    def getFromFilename(cls, filename: str) -> ShotID:
        affix = SHOW + "_"
        if affix not in filename:
            raise ReConnectionFilenameError(filename)
        name = filename.split(affix, 1)[-1][:6]
        try:
            int(name[3:])
        except ValueError as e:
            raise ReConnectionFilenameError(filename) from e

        return cls(name)


class AssetName(strEnum.StringEnum):
    MECHANIC = "mechanic"
    ROBOT = "robot"
    ROBOT_FACE = "robotFace"
    ARNOLD = "arnold"


class AssetType(strEnum.StringEnum):
    MODEL = "model"
    RIG = "rig"
    CACHE = "cache"
    LIGHTS = "lights"
    CAMERA = "cam"


def constructFilenameBase(
    shotName: ShotID, assetName: Optional[AssetName], assetType: AssetType
) -> str:
    if assetName:
        return f"{shotName.full}_{assetName}_{assetType}"
    else:
        return f"{shotName.full}_{assetType}"


class FileExt(strEnum.StringEnum):
    MAYA_ASCII = ".ma"
    MAYA_BINARY = ".mb"
    MAYA_CACHE = ".mcx"
    ALEMBIC = ".abc"
    XML = ".xml"
    PYTHON = ".py"


RecIdentifier = Union[ShotID, AssetName, AssetType, str]


def inFilename(identifier: RecIdentifier, file: Path) -> bool:
    return f"{identifier}" in file.stem


AssetValidator = Callable[[Path], bool]


def constructAssetValidator(
    filenameBase: str,
    assetType: AssetType,
    assetName: Optional[AssetName],
) -> AssetValidator:
    def isFileWithExt(file: Path, fileExt: FileExt) -> bool:
        return file.suffix == f"{fileExt}"

    def isFileWithExts(file: Path, fileExts: Iterable[FileExt]) -> bool:
        isFileWithExtsCmd = partial(isFileWithExt, file)
        return any(map(isFileWithExtsCmd, fileExts))

    if assetType != AssetType.CACHE:
        fileExtValidator = partial(
            isFileWithExts,
            fileExts=(FileExt.MAYA_BINARY, FileExt.MAYA_ASCII),
        )
    elif assetName != AssetName.ROBOT_FACE:
        fileExtValidator = partial(
            isFileWithExts,
            fileExts=(FileExt.MAYA_CACHE, FileExt.XML),
        )
    else:
        fileExtValidator = partial(isFileWithExt, fileExt=FileExt.ALEMBIC)
    return lambda f: inFilename(filenameBase, file=f) and fileExtValidator(f)


def constructVersionSuffix(
    assetValidator: AssetValidator,
    files: Iterable[Path],
    versionIndicator: str = _VERSION_INDICATOR,
) -> str:
    filenames = {f.stem for f in files if assetValidator(f)}
    try:
        filename = sorted(filenames)[-1]
    except IndexError:
        version = 0
    else:
        version = int(filename.rsplit(versionIndicator, 1)[-1])

    return versionIndicator + f"{version + 1}".zfill(3)
