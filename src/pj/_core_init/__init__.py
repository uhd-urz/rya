__all__ = [
    "LogMessageData",
    "get_simple_logger",
    "AppRichHandler",
    "get_logger",
    "LoggerMaker",
    "add_logging_level",
    "get_app_version",
    "global_cli_result_callback",
    "global_cli_super_startup_callback",
    "ResultCallbackHandler",
    "global_log_record_container",
    "global_cli_graceful_callback",
    "LogItemList",
    "PatternNotFoundError",
    "get_logger",
    "get_cached_data",
    "update_cache",
    "LogState",
    "Exit",
    "BaseExit",
    "app_rich_handler_args",
    "AppRichHandlerArgs",
]
import logging

from .._vendor import haggis
from .._vendor.haggis.logs import add_logging_level
from ._exit import BaseExit, Exit
from ._log_state import LogState
from ._loggers import (
    AppRichHandler,
    AppRichHandlerArgs,
    LoggerMaker,
    LogItemList,
    LogMessageData,
    ResultCallbackHandler,
    get_logger,
    get_simple_logger,
    global_log_record_container,
)
from ._loggers.base import app_rich_handler_args
from ._utils import (
    PatternNotFoundError,
    get_app_version,
    get_cached_data,
    global_cli_graceful_callback,
    global_cli_result_callback,
    global_cli_super_startup_callback,
    update_cache,
)

haggis.logs.logging = logging

try:
    # Python 3.13 deprecated _acquireLock, _releaseLock
    # Based on https://github.com/celery/billiard/issues/403, commit 81cc942
    logging._acquireLock, logging._releaseLock = (
        logging._prepareFork,
        logging._afterFork,
    )
except AttributeError:
    ...
