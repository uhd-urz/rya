__all__ = [
    "LogMessageTuple",
    "get_simple_logger",
    "STDERRBaseHandlerMaker",
    "get_logger",
    "BaseHandlerMaker",
    "LoggerMaker",
    "add_logging_level",
    "get_app_version",
    "NoException",
    "GlobalCLIResultCallback",
    "GlobalCLISuperStartupCallback",
    "ResultCallbackHandler",
    "GlobalLogRecordContainer",
    "GlobalCLIGracefulCallback",
    "LogItemList",
    "PatternNotFoundError",
    "Missing",
    "get_logger",
]
import logging

from .._vendor import haggis
from .._vendor.haggis.logs import add_logging_level
from ._loggers import (
    BaseHandlerMaker,
    GlobalLogRecordContainer,
    get_logger,
    LoggerMaker,
    LogItemList,
    LogMessageTuple,
    ResultCallbackHandler,
    STDERRBaseHandlerMaker,
    get_logger,
    get_simple_logger,
)
from ._missing import Missing
from ._utils import (
    GlobalCLIGracefulCallback,
    GlobalCLIResultCallback,
    GlobalCLISuperStartupCallback,
    NoException,
    PatternNotFoundError,
    get_app_version,
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
