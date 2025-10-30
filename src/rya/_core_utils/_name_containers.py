from typing import Optional

from properpath import P
from pydantic import BaseModel

from ._data_list import DataObjectList


class FileTuple(BaseModel):
    path: P
    name: str


class ConfigFileTuple(FileTuple):
    init_cmd_default: bool = False


class LogFileTuple(FileTuple): ...


class FileTupleContainer(DataObjectList[FileTuple]):
    def __init__(self, items: Optional[list[FileTuple]] = None) -> None:
        super().__init__(items, run_before=self.check_duplicates)

    @staticmethod
    def check_duplicates(items: list[FileTuple], value: FileTuple) -> None:
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
