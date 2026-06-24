import logging
from collections import defaultdict
from typing import Optional

from ._logger_state_utils import (
    LoggerStateFlags,
    LoggerStateTuple,
    _get_logger_handler,
)
from ._loggers import LoggerMaker, get_logger

logger = get_logger()


class LoggerState:
    _last_int_state: Optional[int] = None
    _original_states: dict[str, dict[Optional[str], tuple[logging.Handler, int]]] = (
        defaultdict(dict)
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
    def modify_package_logger_state(logger_state_tuple: LoggerStateTuple) -> None:
        package_loggers: list[logging.Logger | logging.PlaceHolder] = []
        logger_state_changed: bool = False
        match logger_state_tuple.package_name:
            case LoggerStateFlags.ALL:
                package_loggers = list(logging.root.manager.loggerDict.values())
            case _:
                for logger_name, logger_obj in logging.root.manager.loggerDict.items():
                    if logger_name.startswith(logger_state_tuple.package_name):
                        package_loggers.append(logger_obj)
        for package_logger in package_loggers:
            if isinstance(package_logger, logging.Logger):
                # The instance check is needed to avoid objects that are logging.PlaceHolder
                for handler in package_logger.handlers:
                    logger_name = package_logger.name
                    x_handler = handler
                    x_handler_level = handler.level
                    if logger_state_tuple.logger_update_rel is not None:
                        if type(handler) is logger_state_tuple.logger_update_rel.old:
                            package_logger.removeHandler(handler)
                            package_logger.addHandler(
                                sub_handler := _get_logger_handler(
                                    logger_state_tuple.logger_update_rel
                                )
                            )
                            logger.debug(
                                f"Handler {handler} of logger '{package_logger.name}' of package "
                                f"'{logger_state_tuple.package_name}' was removed and replaced "
                                f"with {sub_handler}."
                            )
                            x_handler = sub_handler
                            x_handler_level = sub_handler.level
                            logger_state_changed = True
                    if logger_state_tuple.level is not None:
                        x_handler.setLevel(logger_state_tuple.level)
                        logger_state_changed = True
                    if logger_state_changed:
                        # x_handler.name here is the handler name which can also be None apparently.
                        if (
                            x_handler.name
                            not in LoggerState._original_states[logger_name]
                        ):
                            LoggerState._original_states[logger_name] = {
                                x_handler.name: (x_handler, x_handler_level)
                            }

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
        logger_state_tuple: LoggerStateTuple,
        verbose: bool = True,
    ) -> None:
        cls.modify_package_logger_state(logger_state_tuple)
        if verbose:
            package_name = (
                f"package '{logger_state_tuple.package_name}'"
                if logger_state_tuple.package_name != LoggerStateFlags.ALL
                else "all packages"
            )
            logger.info(
                f"Logging state for {package_name} has been set to: "
                f"{logger_state_tuple.model_dump()}."
            )

    @classmethod
    def reset_levels(cls) -> None:
        for logger_name, handlers in cls._original_states.items():
            for handler, level in handlers.values():
                handler.setLevel(level)
        cls._original_states.clear()
        cls._last_int_state = None
