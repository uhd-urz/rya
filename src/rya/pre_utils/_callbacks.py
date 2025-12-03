from typing import Callable, Optional

from ._data_list import DataObjectList
from ._loggers import get_logger

logger = get_logger()


class CallbackList(DataObjectList[Callable]):
    def __init__(self, items: Optional[list[Callable]] = None):
        super().__init__(items, run_before=self.check_duplicates)

    @staticmethod
    def check_duplicates(items: list[Callable], value: Callable) -> None:
        if value in items:
            raise ValueError(
                f"Callable already exists in {CallbackList.__name__}({items})."
            )


class _Callback:
    def __init__(self, instance_name: str, /):
        self.instance_name = instance_name
        self._callbacks: CallbackList = CallbackList()
        self.in_a_call = False

    def add_callback(self, func: Callable) -> None:
        self._callbacks.append(func)

    def remove_callback(self, func: Callable) -> None:
        self._callbacks.remove(func)

    def call_callbacks(self) -> None:
        if not self.in_a_call:
            if self._callbacks:
                logger.debug(
                    f"Calling '{self.instance_name}' registered functions: "
                    f"{', '.join(map(str, self._callbacks))}"
                )
                for func in self._callbacks:
                    self.in_a_call = True
                    func()
                self._callbacks.clear()

    def get_callbacks(self) -> CallbackList:
        return self._callbacks


global_cli_result_callback = _Callback("global_cli_result_callback")
global_cli_super_startup_callback = _Callback("global_cli_super_startup_callback")
global_cli_graceful_callback = _Callback("global_cli_graceful_callback")
