from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, TextIO


@dataclass
class CurrentJob:
    __slots__ = "id", "file", "start_time", "end_time"

    id: int
    file: str = ""
    start_time: str = ""
    end_time: str = ""

    @property
    def forJSON(self) -> dict[str, int | str]:
        return {
            "ID": self.id,
            "File": self.file,
            "Start Time": self.start_time,
            "End Time": self.end_time,
        }

    @property
    def forTSV(self) -> list[int | str]:
        return [self.id, self.file, self.start_time, self.end_time]


class FileHandler(ABC):
    def __init__(self, file: TextIO) -> None:
        self.file = file

    @abstractmethod
    def read(self) -> Any: ...
    @abstractmethod
    def write(self, info: Any) -> Any: ...


class TextFileHandler(FileHandler):
    def read(self) -> list[str]:
        return self.file.readlines()

    def write(self, info: Sequence[Any]) -> None:
        self.file.writelines(info)

    def overwrite(self, info: Sequence[Any]) -> None:
        self.file.seek(0)
        self.file.truncate()
        self.write(info)
        self.file.truncate()


class JSONHandler(FileHandler):
    def read(self) -> dict[str, Any]:
        try:
            return json.load(self.file)
        except json.decoder.JSONDecodeError:
            return {}

    def write(self, info: dict[str, Any]) -> None:
        json.dump(info, self.file, indent=2)

    def overwrite(self, info: dict[str, Any]) -> None:
        self.file.seek(0)
        self.file.truncate()
        self.write(info)
        self.file.truncate()


class CSVHandler(FileHandler):
    # def read(self) -> None:
    #     raise NotImplementedError

    def write(self, info: Sequence[Any]) -> None:
        writer = csv.writer(self.file, csv.excel_tab)
        writer.writerow(info)

    # def overwrite(self, info: Sequence[Any]) -> None:
    #     self.file.seek(0)
    #     self.file.truncate()
    #     self.write(info)
    #     self.file.truncate()


def remove_from_queue(
    queued_items: MutableSequence[str], job: CurrentJob
) -> tuple[MutableSequence[str], CurrentJob]:
    try:
        job.file = queued_items.pop(0).strip()
    except IndexError:
        raise RuntimeError("Queue is empty!")
    return queued_items, job


def add_job(current_jobs: dict, job: CurrentJob) -> tuple[dict, CurrentJob]:
    current_jobs[job.id] = job.forJSON
    return current_jobs, job


def remove_job(current_jobs: dict, job: CurrentJob) -> tuple[dict, CurrentJob]:
    current_jobs.pop(job.id)
    return current_jobs, job


def process(
    file_path: Path,
    file_handler: Callable[[TextIO], FileHandler],
    job: CurrentJob,
    action: Callable,
):
    with open(file_path, "r+", encoding="utf-8") as f:
        handler = file_handler(f)

        queued_files = handler.read()
        queued_files, job = action(queued_files, job)

        handler.write(queued_files)

        return job


def log(
    file_path: Path,
    mode: str,
    file_handler: Callable[[TextIO], FileHandler],
    info: Any,
):
    with open(file_path, "a", encoding="utf-8") as f:
        handler = file_handler(f)

        handler.write(info)

import os
import sys


def main():
    if sys.platform != 'win32':
        return

    _scriptsDir = os.path.join(
        'G:',
        'Shared drives',
        'REC_POST',
        'REC_SCRIPTS.lnk'
    )
    if not os.path.exists(_scriptsDir):
        raise FileNotFoundError(f"Direcotry {_scriptsDir} does not exist")
    elif _scriptsDir not in sys.path:
        sys.path.insert(0, _scriptsDir)

if __name__ == '__main__':
    main()