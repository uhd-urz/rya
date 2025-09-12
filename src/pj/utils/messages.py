import logging
from collections import UserList
from typing import Generic, Optional, Self, TypeVar

from ..loggers import LogMessageTuple

T = TypeVar("T")


class DataObjectList(UserList, Generic[T]):
    def __init__(self, *tuples: list[T]) -> None:
        super().__init__(tuple_ for tuple_ in tuples)

    @property
    def _last_item(self):
        return self.__value

    @_last_item.setter
    def _last_item(self, value: T) -> None:
        self.__value = value

    def __setitem__(self, index: int, tuple_: T) -> None:
        self.data[index] = self._last_item = tuple_

    def append(self, tuple_: T) -> None:
        self._last_item = tuple_
        self.data.append(self._last_item)

    def insert(self, index, tuple_: T) -> None:
        self._last_item = tuple_
        self.data.insert(index, self._last_item)


class MessagesList(DataObjectList[LogMessageTuple]):
    _instance = None

    @property
    def _last_item(self) -> LogMessageTuple:
        return self.__value

    @_last_item.setter
    def _last_item(self, value: LogMessageTuple) -> None:
        if not isinstance(value, LogMessageTuple):
            raise TypeError(
                f"{self.__class__.__name__} only accepts "
                f"'{LogMessageTuple.__name__}' as values."
            )
        self.__value = value

    def __setitem__(self, index: int, tuple_: LogMessageTuple) -> None:
        self.data[index] = self._last_item = tuple_

    def append(self, tuple_: LogMessageTuple) -> None:
        self._last_item = tuple_
        self.data.append(self._last_item)

    def insert(self, index, tuple_: LogMessageTuple) -> None:
        self._last_item = tuple_
        self.data.insert(index, self._last_item)

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


def add_message(
    message: str,
    level: int = logging.INFO,
    logger: Optional[logging.Logger] = None,
    is_aggressive: bool = False,
) -> None:
    important_messages = MessagesList()
    important_messages.append(LogMessageTuple(message, level, logger, is_aggressive))
