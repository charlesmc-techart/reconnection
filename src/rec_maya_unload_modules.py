import rec.unload_modules as unload_modules


def onMayaDroppedPythonFile(_) -> None:
    unload_modules.main()
