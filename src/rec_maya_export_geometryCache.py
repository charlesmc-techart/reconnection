import rec.export_geometryCache as export_geometryCache


def onMayaDroppedPythonFile(_) -> None:
    export_geometryCache.main()
