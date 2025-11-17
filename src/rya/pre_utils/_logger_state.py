import logging
from collections import defaultdict
from collections.abc import Iterable
from typing import Optional

from ._loggers import AppRichHandler, LoggerMaker, app_rich_handler_args, get_logger

logger = get_logger()


class LoggerState:
    _last_int_state: Optional[int] = None
    _original_states: dict[str, dict[str, tuple[logging.Handler, int]]] = defaultdict(
        dict
    )

    @staticmethod
    def modify_int_logger_level(level: int) -> None:
        for _, loggers in LoggerMaker.registered_logger_items():
            for logger_name, logger_obj in loggers.items():
                for handler in logger_obj.handlers:
                    if handler.name not in LoggerState._original_states[logger_name]:
                        LoggerState._original_states[logger_name] = {
                            handler.name: (handler, level)
                        }
                    handler.setLevel(level)

    @staticmethod
    def modify_package_logger_level(
        level: int,
        package_name: Optional[str] = None,
        update_stderr_handler: bool = True,
    ) -> None:
        package_loggers: Iterable[logging.Logger]
        if package_name is not None:
            package_loggers: list[logging.Logger] = []
            for logger_name, logger_obj in logging.root.manager.loggerDict.items():
                if logger_name.startswith(package_name):
                    package_loggers.append(logger_obj)
        else:
            package_loggers = logging.root.manager.loggerDict.values()
        for package_logger in package_loggers:
            if isinstance(package_logger, logging.Logger):
                # The instance check is needed to avoid objects that are logging.PlaceHolder
                for handler in package_logger.handlers:
                    logger_name = package_logger.name
                    if handler.name not in LoggerState._original_states[logger_name]:
                        LoggerState._original_states[logger_name] = {
                            handler.name: (handler, level)
                        }
                    if update_stderr_handler:
                        if handler.__class__ is logging.StreamHandler:
                            package_logger.handlers.remove(handler)
                            package_logger.addHandler(
                                AppRichHandler(app_rich_handler_args)
                            )
                    handler.setLevel(level)

    @classmethod
    def switch_int_state(cls, level: int, verbose: bool = True) -> None:
        if level != cls._last_int_state:
            cls.modify_int_logger_level(level)
            if cls._last_int_state is not None:
                if verbose:
                    logger.info(
                        f"Logging level is set to {level}. "
                        f"The new value will be respected from this point on."
                    )
            cls._last_int_state = level

    @classmethod
    def switch_package_state(
        cls,
        level: int,
        package_name: Optional[str] = None,
        update_stderr_handler: bool = True,
        verbose: bool = True,
    ) -> None:
        cls.modify_package_logger_level(level, package_name, update_stderr_handler)
        if verbose:
            package_name = (
                f"package '{package_name}'"
                if package_name is not None
                else "all packages"
            )
            logger.info(f"Logging level for {package_name} is set to {level}.")

    @classmethod
    def reset_states(cls) -> None:
        for logger_name, handlers in cls._original_states.items():
            for handler, level in handlers.values():
                handler.setLevel(level)
        cls._original_states.clear()
        cls._last_int_state = None
