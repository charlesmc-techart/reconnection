from __future__ import annotations

from typing import NoReturn

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp
import rec.renderArgs


@mapp.logScriptEditorOutput
def main() -> None | NoReturn:
    scene = fpath.getScenePath()

    if fname.inFilename("untitiled", scene):
        message = f"Filename {scene.name!r} must match pattern: 'rec_seq###_description'"
        raise fname.InvalidFilenameError(message)
    elif not fname.hasAnyEtension(
        scene, fileExts={fname.FileExt.MAYA_BINARY, fname.FileExt.MAYA_ASCII}
    ):
        message = f"File {scene.name!r} is not a Maya scene"
        raise fname.InvalidFilenameError(message)

    with rec.renderArgs.RENDER_QUEUE.open("a", encoding="utf-8") as f:
        print(scene, file=f)
