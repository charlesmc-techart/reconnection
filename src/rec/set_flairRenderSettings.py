import maya.cmds as cmds

import rec.modules.files.names as fname
import rec.modules.files.paths as fpath
import rec.modules.maya as mapp


@mapp.logScriptEditorOutput
def main() -> None:
    shot = fname.ShotID.fromFilename(fpath.getScenePath().stem)

    fg = "flairGlobals"
    try:  # cmds.flair()  # FIXME: set name
        cmds.setAttr(f"{fg}._sequenceName", f"{shot.name.upper()}.<####>")
    except Exception as e:
        cmds.warning(e)

    try:  # cmds.flair()  # FIXME: set quality to TAA
        cmds.setAttr(f"{fg}._taa", True)
    except Exception as e:
        cmds.warning(e)

    cmds.flair(alpha=2)  # set alphat to Premult

    try:  # cmds.flair()  # FIXME: set format to EXR
        cmds.setAttr(f"{fg}._format", ".exr")
    except Exception as e:
        cmds.warning(e)

    targets = (
        "cryptomatte",
        "albedo",
        "lighting",
        "specular",
        "shadows",
        "ambientOcclusionTarget",
        "bloomTarget",
    )
    cmds.flair(target=targets)

    try:  # cmds.flair()  # FIXME: set render scale to 100%
        cmds.setAttr(f"{fg}._renderScale", 1)
    except Exception as e:
        cmds.warning(e)

    try:  # cmds.flair()  # FIXME: set render each light to True
        cmds.setAttr(f"{fg}._eachLight", True)
    except Exception as e:
        cmds.warning(e)

    try:  # cmds.flair()  # FIXME: set bundle AOVs in EXR to True
        cmds.setAttr(f"{fg}._bundleAOVs", True)
    except Exception as e:
        cmds.warning(e)
