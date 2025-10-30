import logging

from .._core_init import Exit, LogState
from ..configuration import DynaConfArgs, get_dynaconf_settings
from ..loggers import get_logger

logger = get_logger()


def get_debug_mode() -> str:
    return get_dynaconf_settings(
        DynaConfArgs(
            core_loaders=[], settings_files=[], loaders=["dynaconf.loaders.env_loader"]
        )
    ).get("DEBUG", "o")


def load_debug_mode() -> None:
    match debug_mode := get_debug_mode():
        case "f":
            Exit.SYSTEM_EXIT = False
            LogState.switch_state(logging.DEBUG)
        case "o":
            Exit.SYSTEM_EXIT = True
            LogState.switch_state(logging.INFO)
        case _:
            envvar_prefix = DynaConfArgs.model_fields["envvar_prefix"].default
            logger.warning(
                f"Invalid environment variable value '{debug_mode}' for "
                f"'{envvar_prefix}_DEBUG'."
            )
