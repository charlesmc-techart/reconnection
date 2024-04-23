__author__ = "Charles Mesa Cayobit"

import rec.import_shelf


def onMayaDroppedPythonFile(_) -> None:
    rec.import_shelf.main()
