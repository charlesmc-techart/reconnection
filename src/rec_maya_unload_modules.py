import rec.unload_modules


def onMayaDroppedPythonFile(_) -> None:
    rec.unload_modules.main()
