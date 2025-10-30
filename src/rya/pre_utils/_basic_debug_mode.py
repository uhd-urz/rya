import logging

from dynaconf import Dynaconf

# noinspection PyProtectedMember
from ._exit import Exit
from ._log_state import LogState
from ._loggers import AppDebugStateName, get_logger

logger = get_logger()


def get_debug_mode_envvar(envvar_prefix: str, reload: bool = False) -> str:
    settings = Dynaconf(
        core_loaders=[],
        settings_files=[],
        envvar_prefix=envvar_prefix,
    )
    if reload is True:
        settings.reload()
    return settings.get(AppDebugStateName.envvar_suffix, "o")


def load_basic_debug_mode(envvar_prefix: str, *, reload: bool = False) -> None:
    match debug_mode := get_debug_mode_envvar(envvar_prefix, reload):
        case "f":
            Exit.SYSTEM_EXIT = False
            if reload is True:
                LogState._last_state = None
            LogState.switch_state(logging.DEBUG)
        case "o":
            Exit.SYSTEM_EXIT = True
            LogState.switch_state(logging.INFO)
        case _:
            logger.warning(
                f"Invalid environment variable value '{debug_mode}' for "
                f"'{envvar_prefix}_{AppDebugStateName.envvar_suffix}'. "
                f"Debug mode will not be updated."
            )
