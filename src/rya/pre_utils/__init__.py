import logging

from .._vendor import haggis
from .._vendor.haggis.logs import add_logging_level
from ._basic_debug_mode import get_debug_mode_envvar, load_basic_debug_mode
from ._callbacks import (
    global_cli_graceful_callback,
    global_cli_result_callback,
    global_cli_super_startup_callback,
)
from ._data_list import DataObjectList
from ._exit import Exit
from ._layer_loader import LayerLoader, PublicLayerNames
from ._log_state import LogState
from ._loggers import (
    AppDebugStateName,
    AppRichHandler,
    AppRichHandlerArgs,
    DefaultLoggerName,
    LoggerMaker,
    LogItemList,
    LogMessageData,
    ResultCallbackHandler,
    app_rich_handler_args,
    get_logger,
    get_simple_logger,
    global_log_record_container,
)
from ._missing import Missing
from ._name_containers import (
    ConfigFileTuple,
    FileTuple,
    FileTupleContainer,
    LogFileTuple,
    RunEarlyList,
)
from ._utils import (
    generate_pydantic_model_from_abstract_cls,
    get_dynaconf_core_loader,
    get_local_imports,
    is_platform_unix,
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

__all__ = [
    "DataObjectList",
    "Missing",
    "is_platform_unix",
    "generate_pydantic_model_from_abstract_cls",
    "get_local_imports",
    "LayerLoader",
    "FileTupleContainer",
    "ConfigFileTuple",
    "LogFileTuple",
    "FileTuple",
    "get_dynaconf_core_loader",
    "AppDebugStateName",
    "LoggerMaker",
    "LogItemList",
    "LogMessageData",
    "ResultCallbackHandler",
    "AppRichHandlerArgs",
    "AppRichHandler",
    "get_logger",
    "get_simple_logger",
    "global_log_record_container",
    "LogState",
    "app_rich_handler_args",
    "DefaultLoggerName",
    "add_logging_level",
    "global_cli_result_callback",
    "global_cli_graceful_callback",
    "global_cli_super_startup_callback",
    "Exit",
    "load_basic_debug_mode",
    "get_debug_mode_envvar",
    "PublicLayerNames",
    "RunEarlyList",
]
