import os
import sys
from functools import partial

import maya.cmds as cmds


def main() -> None:
    printBorder = partial(print, "#" * 80, end="\n\n")
    printIndented = partial(print, "")
    printNoPythonPath = partial(printIndented, "No PYTHONPATH variable")
    getEnv = os.environ.get
    joinPath = os.path.join

    print()
    printBorder()
    print("sys.path:")
    for p in sys.path:
        printIndented(p)

    print()
    print("PYTHONPATH:")
    pythonPath = getEnv("PYTHONPATH", [])
    if pythonPath:
        for p in pythonPath.split(":"):
            printIndented(p)
    else:
        printNoPythonPath()

    print()
    print("MAYA_ENV_PATH:")
    printIndented(getEnv("MAYA_ENV_PATH", None))

    print()
    print("MAYA_APP_DIR:")
    mayaAppDir = os.environ["MAYA_APP_DIR"]
    maya2023AppDir = joinPath(mayaAppDir, cmds.about(version=True))

    splitter = ";" if cmds.about(ntOS=True) else ":"

    def printMayaEnv(dir: str) -> None:
        print()
        print(f"Maya.env in {dir}:")
        if "Maya.env" in os.listdir(dir):
            with open(joinPath(dir, "Maya.env")) as f:
                for line in f:
                    if line.startswith("PYTHONPATH"):
                        printIndented("PYTHONPATH:")
                        for p in line[11:].split(splitter):
                            printIndented("", p)
                        return
                printNoPythonPath()
                return
        printIndented("No Maya.env")

    printMayaEnv(maya2023AppDir)
    printMayaEnv(mayaAppDir)

    print()
    printBorder()


def onMayaDroppedPythonFile(_):
    main()


if __name__ == "__main__":
    main()
