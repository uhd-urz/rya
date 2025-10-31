from typing import Optional

from ..pre_utils import (
    AppRichHandler,
    LoggerDefaults,
    LoggerMaker,
    ResultCallbackHandler,
    app_rich_handler_args,
)
from .handlers.file import AppFileHandler, AppFileHandlerArgs
from .log_file import get_log_file_path

logger_maker = LoggerMaker()
app_file_handler_args = AppFileHandlerArgs(filename=get_log_file_path())


@logger_maker.register_logger_caller()
def get_main_logger(name: Optional[str] = None):
    if name is None:
        name = LoggerDefaults.logger_name
    logger = logger_maker.get_registered_logger(get_main_logger.__name__, name=name)
    if logger is None:
        # The handlers (especially the file_handler) must be instantiated before
        # logger_maker.create_singleton_logger is called. This is to avoid logger_maker
        # registering a logger instance first.
        file_handler = AppFileHandler(app_file_handler_args)
        stdout_handler = AppRichHandler(app_rich_handler_args)
        result_callback_handler = ResultCallbackHandler()
        logger = logger_maker.create_singleton_logger(
            get_main_logger.__name__, name=name, register=True
        )
        logger.addHandler(stdout_handler)
        logger.addHandler(file_handler)
        logger.addHandler(result_callback_handler)
        # The level and formatter are set already in respective handlers
    return logger


@logger_maker.register_logger_caller()
def get_file_logger(name: Optional[str] = None):
    if name is None:
        name = LoggerDefaults.logger_name
    logger = logger_maker.get_registered_logger(get_file_logger.__name__, name=name)
    if logger is None:
        # The handlers (especially the file_handler) must be instantiated before
        # logger_maker.create_singleton_logger is called. This is to avoid logger_maker
        # registering a logger instance first.
        file_handler = AppFileHandler(app_file_handler_args)
        logger = logger_maker.create_singleton_logger(
            get_file_logger.__name__, name=name
        )
        logger.addHandler(file_handler)
    return logger
