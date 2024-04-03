#!/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy

import sys
import time
import uuid
from pathlib import Path

dir = f"{Path(__file__).parents[1]}"
if dir not in sys.path:
    sys.path.append(dir)

from . import _queue as rec_queue
from . import _utilities as rec_files

_DATA_DIR = Path(__file__).parents[2] / "data"
_QUEUE_PATH = Path(_DATA_DIR) / ".rec_renderQueue.txt"
_JOBS_PATH = Path(_DATA_DIR) / ".rec_renderJobs.json"
_LOGS_PATH = Path(_DATA_DIR) / ".rec_renderLog.tsv"


def main():
    id = uuid.uuid4().time_hi_version
    job = rec_queue.CurrentJob(id)
    job = rec_queue.process(
        _QUEUE_PATH,
        rec_queue.TextFileHandler,
        job,
        rec_queue.remove_from_queue,
    )

    job.start_time = rec_files.getCurrentTime()
    rec_queue.process(
        _JOBS_PATH,
        file_handler=rec_queue.JSONHandler,
        job=job,
        action=rec_queue.add_job,
    )

    time.sleep(2)

    job.end_time = rec_files.getCurrentTime()
    rec_queue.process(
        _JOBS_PATH,
        file_handler=rec_queue.JSONHandler,
        job=job,
        action=rec_queue.remove_job,
    )

    rec_queue.log(
        _LOGS_PATH, mode="a", file_handler=rec_queue.CSVHandler, info=job.forTSV
    )


main()
