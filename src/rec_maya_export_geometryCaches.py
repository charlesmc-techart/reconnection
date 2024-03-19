import rec.export_geometryCaches as export_geometryCaches


def onMayaDroppedPythonFile(_) -> None:
    export_geometryCaches.main()
