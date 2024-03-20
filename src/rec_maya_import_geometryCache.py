import rec.import_geometryCache as import_geometryCache


def onMayaDroppedPythonFile(_) -> None:
    import_geometryCache.main()
