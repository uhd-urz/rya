from typing import Callable, ClassVar, Iterable

from dynaconf import Dynaconf
from pydantic import BaseModel

from ._debug_builtins import BuiltInDebugModeShortcuts
from ._logger_state import LoggerState
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


class DebugModeTuple(BaseModel):
    level: int
    packages: str | None | Iterable[str]
    update_stderr_handler: bool = True


class DebugMode:
    _registered_shortcuts: ClassVar[dict[str, Callable]] = {}

    def __init__(self, envvar_prefix: str) -> None:
        self.envvar_prefix = envvar_prefix

    @classmethod
    def add_shortcut(cls, name: str, action: Callable | DebugModeTuple) -> None:
        if name in cls._registered_shortcuts:
            raise ValueError(f"Debug mode shortcut '{name}' already exists.")
        if not isinstance(action, (Callable, DebugModeTuple)):
            raise TypeError(
                f"Argument 'action' for debug mode shortcut "
                f"'{name}' must be a callable or a {DebugModeTuple.__name__}."
            )
        cls._registered_shortcuts[name] = action

    def load(self, reload: bool = False, verbose: bool = True, **kwargs) -> None:
        debug_mode = get_debug_mode_envvar(self.envvar_prefix, reload)
        match registered_sc := DebugMode._registered_shortcuts.get(debug_mode):
            case func if callable(func):
                func(reload=reload, verbose=verbose, **kwargs)
            case DebugModeTuple():
                if isinstance(registered_sc.packages, Iterable) and not isinstance(
                    registered_sc.packages, str
                ):
                    for package_name in registered_sc.packages:
                        LoggerState.switch_package_state(
                            registered_sc.level,
                            package_name,
                            update_stderr_handler=registered_sc.update_stderr_handler,
                            verbose=verbose,
                        )
                else:
                    LoggerState.switch_package_state(
                        **registered_sc.model_dump(),
                        verbose=verbose,
                    )
            case None:
                logger.warning(
                    f"Environment variable value '{debug_mode}' for "
                    f"'{self.envvar_prefix}_{LoggerDefaults.debug_envvar_suffix}' "
                    f"is not recognized. Debug mode will not be updated."
                )
            case _:
                logger.warning(
                    f"Invalid value '{registered_sc}' of type '{type(registered_sc)}' "
                    f"found for registered shortcut debug mode '{debug_mode}' for "
                    f"'{self.envvar_prefix}_{LoggerDefaults.debug_envvar_suffix}'. "
                    f"This is an unexpected error. l"
                    f"Debug mode will not be updated."
                )


DebugMode.add_shortcut(**BuiltInDebugModeShortcuts.all.model_dump())
DebugMode.add_shortcut(**BuiltInDebugModeShortcuts.core.model_dump())
DebugMode.add_shortcut(**BuiltInDebugModeShortcuts.reset.model_dump())
