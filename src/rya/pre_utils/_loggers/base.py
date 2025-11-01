import logging
from dataclasses import dataclass
from typing import Callable, ClassVar, Optional

from pydantic import BaseModel, ConfigDict

from .handlers.stderr import AppRichHandler, AppRichHandlerArgs


class LogMessageData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    message: str
    level: int = logging.NOTSET
    logger: Optional[logging.Logger] = None
    is_aggressive: bool = False


class LoggerMaker:
    _logger_wrapper_callers: dict[str, Callable] = {}
    _logger_objects: dict[str, dict[str, logging.Logger]] = {}

    @classmethod
    def get_registered_caller(cls, name: str) -> Optional[Callable]:
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
        cls,
        logger_caller_name: str,
        *,
        register: bool = False,
        name: str,
        level: int = logging.DEBUG,
    ):
        cls._logger_objects.setdefault(logger_caller_name, {})
        logger = cls._logger_objects[logger_caller_name].get(name)
        if logger is None:
            logger = logging.Logger(name)
            logger.setLevel(level)
            cls._logger_objects[logger_caller_name][name] = logger
            if register:
                logging.root.manager.loggerDict[str(name)] = logger
        return logger


app_rich_handler_args = AppRichHandlerArgs()


@LoggerMaker.register_logger_caller()
def get_simple_logger(name: Optional[str] = None) -> logging.Logger:
    if name is None:
        name = LoggerDefaults.logger_name
    logger = LoggerMaker.get_registered_logger(
        get_simple_logger.__name__,
        name=name,
    )
    if logger is None:
        logger = LoggerMaker.create_singleton_logger(
            get_simple_logger.__name__, name=name, register=True
        )
        stdout_handler = AppRichHandler(app_rich_handler_args)
        logger.addHandler(stdout_handler)
    return logger


def _get_logger(name: Optional[str] = None) -> logging.Logger:
    main_logger = LoggerMaker.get_registered_caller("get_main_logger")
    if main_logger is not None:
        return main_logger(name)
    return get_simple_logger(name)


@dataclass
class LoggerDefaults:
    debug_envvar_suffix: ClassVar[str] = "DEBUG"
    logger_name: ClassVar[str] = "app"
    logger_callable: ClassVar[Callable] = _get_logger
    will_cache_log_path: ClassVar[bool] = False


def get_logger(*args, **kwargs) -> logging.Logger:
    if not callable(LoggerDefaults.logger_callable):
        raise RuntimeError(
            f"{LoggerDefaults.__name__} attribute 'logger_callable' value "
            f"'{LoggerDefaults.logger_callable}' must be a callable that "
            f"supports passing arguments."
        )
    return LoggerDefaults.logger_callable(*args, **kwargs)
