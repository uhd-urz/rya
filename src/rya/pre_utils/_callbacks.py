from typing import Callable, Optional

from ._loggers import get_logger

logger = get_logger()


class _Callback:
    def __init__(self, instance_name: str, /):
        self._callbacks: Optional[list[Callable]] = None
        self.instance_name = instance_name
        self.in_a_call = False

    def _invalid_callback_type_exception(self):
        ValueError(
            f"_result_callbacks private attribute of class "
            f"{self.__name__} was expected to be None or a list of "
            f"callables. But it is of type '{type(self._callbacks)}'."
        )

    def add_callback(self, func: Callable) -> None:
        if self._callbacks is None:
            self._callbacks = []
        if not isinstance(self._callbacks, list):
            raise self._invalid_callback_type_exception()
        if callable(func):
            if func not in self._callbacks:
                self._callbacks.append(func)
                return
            return
        raise TypeError("result_callback function must be a callable!")

    def remove_callback(self, func: Callable) -> None:
        if isinstance(self._callbacks, list):
            self._callbacks.remove(func)
            return
        raise self._invalid_callback_type_exception()

    def call_callbacks(self) -> None:
        if not self.in_a_call:
            if self._callbacks is not None:
                if not isinstance(self._callbacks, list):
                    raise self._invalid_callback_type_exception()
                logger.debug(
                    f"Calling {self.instance_name} registered functions: "
                    f"{', '.join(map(str, self._callbacks))}"
                )
                for func in self._callbacks:
                    if not callable(func):
                        raise RuntimeError(
                            f"result_callback function must be a callable! "
                            f"But '{func}' is of type '{type(func)}' instead."
                        )
                    self.in_a_call = True
                    func()
                self._callbacks.clear()
                self._callbacks = None
        return None

    def get_callbacks(self) -> Optional[list[Callable]]:
        return self._callbacks


global_cli_result_callback = _Callback("global_cli_result_callback")
global_cli_super_startup_callback = _Callback("global_cli_super_startup_callback")
global_cli_graceful_callback = _Callback("global_cli_graceful_callback")
