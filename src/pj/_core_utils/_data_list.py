from collections import UserList
from types import get_original_bases
from typing import Callable, Optional, get_args, get_origin


class DataObjectList[T](UserList):
    def __init__(
        self,
        items: Optional[list[T]] = None,
        *,
        run_before: Optional[Callable[[list[T], T], None]] = None,
    ) -> None:
        super().__init__()
        self.run_before = run_before
        for item in items or ():
            self.append(item)

    def __rich_repr__(self):
        yield "data", self.data

    @property
    def _last_item(self):
        return self.__value

    @_last_item.setter
    def _last_item(self, value: T) -> None:
        for base in get_original_bases(self.__class__):
            if DataObjectList is get_origin(base):
                used_generic_type: type = get_args(base)[0]
                break
        else:
            raise TypeError(
                f"{self.__class__.__name__} must be subclassed with a valid type. "
                f"E.g., class StrList({self.__class__.__name__}[str]): ..."
            )
        if not isinstance(value, used_generic_type):
            raise TypeError(
                f"{self.__class__.__name__} only accepts "
                f"'{used_generic_type.__name__}' as values."
            )
        if self.run_before is not None:
            self.run_before(self.data, value)
        self.__value = value

    def __setitem__(self, index: int, item: T) -> None:
        self._last_item = item
        self.data[index] = item

    def append(self, item: T) -> None:
        self.insert(len(self.data), item)

    def insert(self, index, item: T) -> None:
        self._last_item = item
        self.data.insert(index, self._last_item)

    def extend(self, items: list[T]):
        for item in items:
            self.append(item)

    def __iadd__(self, items: list[T]):
        self.extend(items)
        return self
