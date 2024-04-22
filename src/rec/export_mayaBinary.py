import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

import maya.cmds as cmds

sys.path.append(f"{Path(__file__).parents[1]}")

import rec.modules.maya as mapp
import rec.modules.maya.objects as mobj


def main(maPath: Path, mbPath: Path, nodes: Sequence[mobj.DGNode]) -> None:
    cmds.file(maPath.as_posix(), open=True)
    mobj.export(nodes, filePath=mbPath, fileType=mapp.FileType.BINARY)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("maPath", type=Path)
    parser.add_argument("mbPath", type=Path)
    parser.add_argument("nodes", nargs="+")
    args = parser.parse_args()

    with mapp.Standalone():
        main(args.maPath, args.mbPath, args.nodes)
