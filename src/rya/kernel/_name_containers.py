from collections.abc import Callable
from typing import Optional, Sequence

from properpath import P
from pydantic import BaseModel

from ._data_list import DataObjectList


class FileModel(BaseModel):
    path: P
    name: str


class FileModelContainer(DataObjectList[FileModel]):
    def __init__(self, items: Optional[Sequence[FileModel]] = None) -> None:
        super().__init__(items, run_before=self.check_duplicates)

    @staticmethod
    def check_duplicates(items: list[FileModel], value: FileModel) -> None:
        for item in items:
            if item.name == value.name:
                raise ValueError(f"Name '{item.name}' already exists in {item}.")
            if item.path == value.path:
                raise ValueError(f"Path '{item.path}' already exists in {item}.")

    def remove_by_name(self, name: str) -> None:
        for file_tuple in self.data:
            if file_tuple.name == name:
                self.remove(file_tuple)
                return
        raise ValueError(f"Name '{name}' not found in data.")


class ConfigFileModel(FileModel):
    target_platforms: tuple[str, ...] | None = None


class FallbackLogFileModel(FileModel):
    target_platforms: tuple[str, ...] | None = None


class LogFileModel(FileModel):
    fallback_paths: Sequence[FallbackLogFileModel] = []


class RunEarlyList(DataObjectList[Callable]): ...
