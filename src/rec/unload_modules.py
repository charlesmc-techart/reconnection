"""Unload the re:connection Python modules"""

import sys

import rec.modules.files.names as fname


def main() -> None:
    module = fname.SHOW
    while True:
        try:
            for m in sys.modules:
                if m.startswith(module) or m.startswith(f"_{module}"):
                    del sys.modules[m]
        except RuntimeError:
            continue
        else:
            break
