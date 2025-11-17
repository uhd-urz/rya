import logging
from dataclasses import dataclass
from typing import Callable, ClassVar

from pydantic import BaseModel

from ._exit import Exit
from ._logger_state import LoggerState


# noinspection PyUnusedLocal
def _star_debug_mode_sc(reload: bool = False, verbose: bool = True, **kwargs) -> None:
    Exit.SYSTEM_EXIT = False
    if reload is True:
        LoggerState._last_int_state = None
    LoggerState.switch_int_state(logging.DEBUG, verbose=verbose)
    LoggerState.switch_package_state(
        logging.DEBUG, package_name=None, update_stderr_handler=True, verbose=verbose
    )


# noinspection PyUnusedLocal
def _core_debug_mode_sc(reload: bool = False, verbose: bool = True, **kwargs) -> None:
    Exit.SYSTEM_EXIT = False
    if reload is True:
        LoggerState._last_int_state = None
    LoggerState.switch_int_state(logging.DEBUG, verbose=verbose)


# noinspection PyUnusedLocal
def _o_debug_mode_sc(**kwargs) -> None:
    Exit.SYSTEM_EXIT = True
    LoggerState.reset_states()


class _CallableSc(BaseModel, validate_assignment=True):
    name: str
    action: Callable


@dataclass
class BuiltInDebugModeShortcuts:
    all: ClassVar[_CallableSc] = _CallableSc(name="*", action=_star_debug_mode_sc)
    core: ClassVar[_CallableSc] = _CallableSc(name="c", action=_core_debug_mode_sc)
    reset: ClassVar[_CallableSc] = _CallableSc(name="o", action=_o_debug_mode_sc)
