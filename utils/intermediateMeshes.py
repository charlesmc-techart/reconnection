"""Utilities for showing, hiding, and connecting intermediate meshes"""

from functools import partial

import maya.cmds as cmds


def revealAllItermediateMeshes() -> None:
    for s in cmds.listRelatives(allDescendents=True, type="mesh"):
        cmds.setAttr(f"{s}.intermediateObject", False)


def hideIntermediateMeshes() -> None:
    for s in cmds.ls("rec_asset_*:*_geoShape", type="mesh"):
        cmds.setAttr(f"{s}.intermediateObject", True)


def connectShapeOrigToDeformers() -> None:
    originalMesh, *deformers = cmds.ls(orderedSelection=True)

    connectAttrCmd = partial(cmds.connectAttr, force=True)
    connectAttrCmd(
        f"{originalMesh}.outMesh",
        f"{deformers[0]}.originalGeometry[0]",
    )
    connectAttrCmd(
        f"{originalMesh}.worldMesh",
        f"{deformers[0]}.input[0].inputGeometry",
    )

    for i, d in enumerate(deformers[1:]):
        connectAttrCmd(
            f"{deformers[i]}.originalGeometry[0]",
            f"{d}.originalGeometry[0]",
        )
