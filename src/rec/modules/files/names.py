from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import partial
from pathlib import Path
from typing import Union

import rec.modules.stringEnum as strEnum

SHOW = "rec"
SHOW_FULL_TITLE = "re:connection"


class InvalidFilenameError(ValueError):
    """File does not adhere to re:connection's filename protocol"""


class ShotId:
    """Shot identifier used in asset filenames, formatted 'rec_seq###'"""

    __slots__ = "name", "sequence", "number", "full"

    def __new__(cls, name: str) -> ShotId:
        try:
            int(name[3:])
        except ValueError as e:
            message = f"Name {name!r} must match pattern: 'seq###'"
            raise InvalidFilenameError(message) from e
        return super().__new__(cls)

    def __init__(self, name: str) -> None:
        self.name = name
        self.sequence = name[:3]
        self.number = name[3:6]
        self.full = f"{SHOW}_{name}"

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"

    @classmethod
    def fromFilename(cls, filename: str, affix: str = f"{SHOW}_") -> ShotId:
        if affix not in filename:
            message = f"Filename {filename!r} must match pattern: 'rec_seq###'"
            raise InvalidFilenameError(message)
        name = filename.split(affix, 1)[-1][:6]
        return cls(name)


class AssetName(strEnum.StringEnum):
    """Name identifiers used in asset filenames"""

    MECHANIC = "mechanic"
    ROBOT = "robot"
    ROBOT_FACE = "robotFace"
    ARNOLD = "arnold"


class AssetType(strEnum.StringEnum):
    """Type identifiers used in asset filenames"""

    MODEL = "model"
    RIG = "rig"
    CACHE = "cache"
    LIGHTS = "lights"
    CAMERA = "cam"


NameIdentifier = Union[AssetName, str]
TypeIdentifier = Union[AssetType, str]


def constructFilenameBase(
    shot: ShotId, assetName: NameIdentifier | None, assetType: TypeIdentifier
) -> str:
    """Construct a filename base, formatted 'rec_seq###_name_type'"""
    if assetName:
        return f"{shot.full}_{assetName}_{assetType}"
    else:
        return f"{shot.full}_{assetType}"


class FileExt(strEnum.StringEnum):
    """File extensions used in asset files"""

    MAYA_ASCII = ".ma"
    MAYA_BINARY = ".mb"
    MAYA_CACHE = ".mcx"
    ALEMBIC = ".abc"
    XML = ".xml"
    PYTHON = ".py"


Identifier = Union[ShotId, NameIdentifier, TypeIdentifier]


def inFilename(identifier: Identifier, file: Path) -> bool:
    """Check if an identifier is the filename"""
    return f"{identifier}" in file.stem


Validator = Callable[[Path], bool]


def hasExtension(file: Path, fileExt: FileExt) -> bool:
    return file.suffix == fileExt


def hasAnyEtension(file: Path, fileExts: set[FileExt]) -> bool:
    return file.suffix in fileExts


def constructValidator(
    filenameBase: str,
    assetName: NameIdentifier | None,
    assetType: TypeIdentifier,
) -> Validator:
    """Construct a validator used for filtering assets"""
    if assetType != AssetType.CACHE:
        fileExtValidator = partial(
            hasAnyEtension,
            fileExts={FileExt.MAYA_BINARY, FileExt.MAYA_ASCII},
        )
    elif assetName != AssetName.ROBOT_FACE:
        fileExtValidator = partial(
            hasAnyEtension,
            fileExts={FileExt.MAYA_CACHE, FileExt.XML},
        )
    else:
        fileExtValidator = partial(hasExtension, fileExt=FileExt.ALEMBIC)
    return lambda f: inFilename(filenameBase, file=f) and fileExtValidator(f)


def constructVersionSuffix(
    validator: Validator, files: Iterable[Path], versionIndicator: str = "v"
) -> str:
    """Construct a filename version, formatted 'v###'"""
    filenames = {f.stem for f in files if validator(f)}
    try:
        filename = sorted(filenames)[-1]
    except IndexError:
        version = 0
    else:
        version = int(filename.rsplit(versionIndicator, 1)[-1])
    return f"{versionIndicator}{f'{version + 1}'.zfill(3)}"
