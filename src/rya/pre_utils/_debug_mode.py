from typing import Callable, ClassVar

from dynaconf import Dynaconf

from ._debug_builtins import BuiltInDebugModeShortcuts
from ._logger_state import LoggerState
from ._logger_state_utils import LoggerStateTuple
from ._loggers import LoggerDefaults, get_logger

logger = get_logger()


def get_debug_mode_envvar(envvar_prefix: str, reload: bool = False) -> str:
    settings = Dynaconf(
        core_loaders=[],
        settings_files=[],
        envvar_prefix=envvar_prefix,
    )
    if reload is True:
        settings.reload()
    return settings.get(
        LoggerDefaults.debug_envvar_suffix, BuiltInDebugModeShortcuts.reset.name
    )


class DebugMode:
    _registered_shortcuts: ClassVar[dict[str, Callable]] = {}

    def __init__(self, envvar_prefix: str) -> None:
        self.envvar_prefix = envvar_prefix

    @classmethod
    def add_shortcut(cls, name: str, action: Callable | LoggerStateTuple) -> None:
        if name in cls._registered_shortcuts:
            raise ValueError(f"Debug mode shortcut '{name}' already exists.")
        if not isinstance(action, (Callable, LoggerStateTuple)):
            raise TypeError(
                f"Argument 'action' for debug mode shortcut "
                f"'{name}' must be a callable or a {LoggerStateTuple.__name__}."
            )
        cls._registered_shortcuts[name] = action

    def load(self, reload: bool = False, verbose: bool = True, **kwargs) -> None:
        debug_mode = get_debug_mode_envvar(self.envvar_prefix, reload)
        match registered_sc_log_state_tuple := DebugMode._registered_shortcuts.get(
            debug_mode
        ):
            case func if callable(func):
                func(reload=reload, verbose=verbose, **kwargs)
            case LoggerStateTuple():
                LoggerState.switch_package_state(
                    registered_sc_log_state_tuple, verbose=verbose
                )
            case None:
                logger.warning(
                    f"Environment variable value '{debug_mode}' for "
                    f"'{self.envvar_prefix}_{LoggerDefaults.debug_envvar_suffix}' "
                    f"is not recognized. Debug mode will not be updated."
                )
            case _:
                logger.warning(
                    f"Invalid value '{registered_sc_log_state_tuple}' of type "
                    f"'{type(registered_sc_log_state_tuple)}' "
                    f"found for registered shortcut debug mode '{debug_mode}' for "
                    f"'{self.envvar_prefix}_{LoggerDefaults.debug_envvar_suffix}'. "
                    f"This is an unexpected error. "
                    f"Debug mode will not be updated."
                )


DebugMode.add_shortcut(**BuiltInDebugModeShortcuts.all.model_dump())
DebugMode.add_shortcut(**BuiltInDebugModeShortcuts.core.model_dump())
DebugMode.add_shortcut(**BuiltInDebugModeShortcuts.reset.model_dump())
