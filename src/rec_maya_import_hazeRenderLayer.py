import rec.import_hazeRenderLayer as import_hazeRenderLayer


def onMayaDroppedPythonFile(_) -> None:
    import_hazeRenderLayer.main()
