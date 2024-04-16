from collections.abc import Sequence
from pathlib import Path
from typing import Any

import rec.modules.maya.objects as mobj

# General

def about(version: bool) -> str: ...
def container(
    node: mobj.DGNode,
    edit: bool = False,
    addNode: Sequence[str] | None = None,
    force: bool = False,
    publishAndBind: Sequence[str] | None = None,
) -> str: ...
def ls(
    node: mobj.DGNode | Sequence[mobj.DGNode] | None = None,
    long: bool = False,
    orderedSelection: bool = False,
    selection: bool = False,
    transforms: bool = False,
    type: str | None = None,
) -> list[str]: ...
def parent(child: mobj.DAGNode, parent: mobj.DAGNode) -> list[str]: ...
def rename(node: mobj.DGNode, name: str) -> str: ...
def xform(
    node: mobj.DAGNode, matrix: Sequence[float] | None = None
) -> None: ...

# Attributes

def connectAttr(
    attribute1: str, attribute2: str, force: bool = False
) -> str: ...
def createNode(node: mobj.DGNode, name: str | None = None) -> str: ...
def getAttr(attribute: str) -> Any: ...
def listConnections(
    node: mobj.DGNode | Sequence[mobj.DGNode], type: str | None = None
) -> list[str]: ...
def listRelatives(
    node: mobj.DAGNode | Sequence[mobj.DAGNode] | None = None,
    allDescendents: bool = False,
    noIntermediate: bool = False,
    path: bool = False,
    shapes: bool = False,
    type: str | None = None,
) -> list[str]: ...
def objExists(node: mobj.DGNode) -> bool: ...
def objectType(node: mobj.DGNode, isType: str) -> bool: ...
def setAttr(attribute: str, value: Any, type: str | None = None) -> None: ...

# Selection

def select(
    node: mobj.DGNode | Sequence[mobj.DGNode] | None = None,
    clear: bool = False,
    replace: bool = False,
) -> None: ...

# Language

# Scripting

def deleteUI(name: str | Sequence[str], window: bool = False) -> None: ...
def refresh(suspend: bool) -> None: ...

# Animation

def playbackOptions(
    query: bool = False,
    animationStartTime: bool = False,
    animationEndTime: bool = False,
    maxTime: float | None = None,
    minTime: float | None = None,
) -> float: ...

# Rendering

def shadingNode(node: mobj.DGNode, asShader: bool, name: str) -> str: ...

# System

# Files

def cmdFileOutput(close: int | None = None, open: str | None = None) -> int: ...
def file(
    path: str | Path | None = None,
    query: bool = False,
    exportSelectedStrict: bool = False,
    force: bool = False,
    ignoreVersion: bool = False,
    loadReferenceDepth: str | None = None,
    mergeNamespacesOnClash: bool = False,
    namespace: str | None = None,
    open: bool = False,
    options: str = "v=0;p=17",
    reference: bool = False,
    rename: str | None = None,
    save: bool = False,
    sceneName: bool = False,
    type: str | bool | None = None,
    unloadReference: str | None = None,
) -> str: ...
def referenceQuery(
    object: mobj.DGNode | Sequence[mobj.DGNode], filename: bool = False
) -> str: ...
def workspace(
    query: bool = False,
    fileRule: Sequence[str | Path] | None = None,
    fullName: bool = False,
) -> str: ...

# Plug-ins

def loadPlugin(name: str, quiet: bool) -> None: ...

# Utilities

def date(format: str = "") -> str: ...
def undoInfo(stateWithoutFlush: bool) -> None: ...
def warning(warning: object) -> None: ...

# Windows

def window(
    name: str,
    exists: bool = False,
    parent: str | None = None,
    resizeToFitChildren: bool = False,
    sizeable: bool = False,
    title: str = "",
    widthHeight: Sequence[int] | None = None,
) -> str: ...
def showWindow(name: str) -> None: ...

# Panels

def hyperShade(assign: str) -> str: ...

# Controls

def progressBar(
    name: str = "",
    edit: bool = False,
    maxValue: int = 100,
    parent: str | None = None,
    progress: int = 0,
) -> str: ...
def text(
    name: str | None = None,
    edit: bool = False,
    label: str | None = None,
    parent: str | None = None,
) -> str: ...

# Layouts

def formLayout(
    name: str = "",
    edit: bool = False,
    attachControl: Sequence[Any] | None = None,
    attachForm: Sequence[Sequence[str | int]] | None = None,
    parent: str | None = None,
) -> str: ...
def shelfLayout(name: str, exists: bool = False) -> str: ...

###
def AbcExport(jobArg: str) -> None: ...
def flair(
    alpha: int | None = None, target: Sequence[str] | None = None
) -> None: ...
