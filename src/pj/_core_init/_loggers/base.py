import logging
from dataclasses import dataclass
from functools import update_wrapper
from typing import Optional

from ..._names import AppIdentity
from .handlers.stderr import STDERRBaseHandlerMaker


@dataclass
class LogMessageTuple:
    message: str
    level: int = logging.NOTSET
    logger: Optional[logging.Logger] = None
    is_aggressive: bool = False


class LoggerMaker:
    _logger_wrapper_callers: dict[str, type] = {}
    _logger_objects: dict[str, dict[str, logging.Logger]] = {}

    @classmethod
    def get_registered_wrapper_class(cls, name: str) -> Optional[type]:
        return cls._logger_wrapper_callers.get(name)

    @classmethod
    def get_registered_logger(
        cls, logger_caller_name: str, *, name: str
    ) -> Optional[logging.Logger]:
        return cls._logger_objects.get(logger_caller_name, {}).get(name)

    @classmethod
    def registered_logger_items(cls):
        return cls._logger_objects.items()

    @classmethod
    def register_logger_caller(cls):
        def decorator(caller):
            update_wrapper(wrapper=decorator, wrapped=caller)
            if cls._logger_wrapper_callers.get(caller.__name__) is None:
                cls._logger_wrapper_callers[caller.__name__] = caller
            return cls._logger_wrapper_callers[caller.__name__]

        return decorator

    @classmethod
    def remove_registered_logger_caller(cls, name: str) -> None:
        if cls._logger_wrapper_callers.get(name) is not None:
            cls._logger_wrapper_callers.pop(name)

    @classmethod
    def remove_registered_singleton_logger(cls, name: str) -> None:
        if cls._logger_objects.get(name) is not None:
            cls._logger_objects.pop(name)

    @classmethod
    def create_singleton_logger(
        cls, logger_caller_name: str, *, name: str, level: int = logging.DEBUG
    ):
        try:
            cls._logger_objects[logger_caller_name]
        except KeyError:
            cls._logger_objects[logger_caller_name] = {}
        try:
            cls._logger_objects[logger_caller_name][name]
        except KeyError:
            logger = logging.Logger(name)
            logger.setLevel(level)
            cls._logger_objects[logger_caller_name][name] = logger
        return cls._logger_objects[logger_caller_name][name]


logger_maker = LoggerMaker()


@logger_maker.register_logger_caller()
def get_simple_logger(name: Optional[str] = None) -> logging.Logger:
    if name is None:
        name = AppIdentity.app_name
    logger = logger_maker.get_registered_logger(get_simple_logger.__name__, name=name)
    if logger is None:
        logger = logger_maker.create_singleton_logger(
            get_simple_logger.__name__, name=name
        )
        stdout_handler = STDERRBaseHandlerMaker().handler
        logger.addHandler(stdout_handler)
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    main_logger = logger_maker.get_registered_wrapper_class("get_main_logger")
    if main_logger is not None:
        return main_logger(name)
    return get_simple_logger(name)
