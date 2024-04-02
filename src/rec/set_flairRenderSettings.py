import maya.cmds as cmds

import rec.modules.maya as mapp


@mapp.logScriptEditorOutput
def main() -> None:
    cmds.flair()  # FIXME: set name

    cmds.flair()  # FIXME: set quality to TAA
    cmds.flair(alpha=2)
    cmds.flair()  # FIXME: set format to EXR

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

    cmds.flair()  # FIXME: set render scale to 100%

    cmds.flair()  # FIXME: set render each light to True
    cmds.flair()  # FIXME: set bundle AOVs in EXR to True
