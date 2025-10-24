import sys
from abc import ABC
from typing import Self

from ._utils import global_cli_result_callback


class BaseExit(BaseException, ABC): ...


class Exit(BaseExit):
    SYSTEM_EXIT: bool
    if (
        hasattr(sys, "ps1")
        or hasattr(sys, "ps2")
        or sys.modules.get(
            "ptpython", False
        )  # hasattr(sys, "ps1") doesn't work with ptpython.
        or sys.modules.get("bpython", False)
    ):
        SYSTEM_EXIT = False
    else:
        SYSTEM_EXIT = True

    def __new__(cls, *args, **kwargs) -> SystemExit | Self:
        global_cli_result_callback.call_callbacks()
        if cls.SYSTEM_EXIT:
            return SystemExit(*args)
        return super().__new__(cls, *args, **kwargs)  # cls == CriticalValidationError


BaseExit.register(SystemExit)
