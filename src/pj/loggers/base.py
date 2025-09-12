import logging

from .._core_init import (
    LoggerMaker,
    ResultCallbackHandler,
    STDERRBaseHandlerMaker,
)
from .handlers.file import FileHandlerMaker
from .log_file import LOG_FILE_PATH

logger_maker = LoggerMaker()


@logger_maker.register_logger_caller()
def get_main_logger():
    logger = logger_maker.get_registered_logger(
        get_main_logger.__name__,
    )
    if logger is None:
        logger = logger_maker.create_singleton_logger(
            name=get_main_logger.__name__,
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
def get_file_logger():
    logger = logger_maker.get_registered_logger(
        get_file_logger.__name__,
    )
    if logger is None:
        logger = logger_maker.create_singleton_logger(
            name=get_file_logger.__name__,
        )
        file_handler = FileHandlerMaker(LOG_FILE_PATH).handler
        logger.addHandler(file_handler)
    return logger
