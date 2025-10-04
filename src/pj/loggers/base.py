import logging
from typing import Optional

from .._core_init import (
    LoggerMaker,
    ResultCallbackHandler,
    STDERRBaseHandlerMaker,
)
from .._names import AppIdentity
from .handlers.file import FileHandlerMaker
from .log_file import LOG_FILE_PATH

logger_maker = LoggerMaker()


@logger_maker.register_logger_caller()
def get_main_logger(name: Optional[str] = None):
    if name is None:
        name = AppIdentity.app_name
    logger = logger_maker.get_registered_logger(get_main_logger.__name__, name=name)
    if logger is None:
        logger = logger_maker.create_singleton_logger(
            get_main_logger.__name__, name=name
        )
        file_handler = FileHandlerMaker(LOG_FILE_PATH).handler
        logger.addHandler(file_handler)
        stdout_handler = STDERRBaseHandlerMaker().handler
        logger.addHandler(stdout_handler)
        result_callback_handler = ResultCallbackHandler()
        result_callback_handler.setLevel(logging.INFO)
        logger.addHandler(result_callback_handler)
    return logger


@logger_maker.register_logger_caller()
def get_file_logger(name: Optional[str] = None):
    if name is None:
        name = AppIdentity.app_name
    logger = logger_maker.get_registered_logger(get_file_logger.__name__, name=name)
    if logger is None:
        logger = logger_maker.create_singleton_logger(
            get_file_logger.__name__, name=name
        )
        file_handler = FileHandlerMaker(LOG_FILE_PATH).handler
        logger.addHandler(file_handler)
    return logger
