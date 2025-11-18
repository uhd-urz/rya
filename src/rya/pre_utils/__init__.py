import logging

from .._vendor import haggis
from .._vendor.haggis.logs import add_logging_level
from ._callbacks import (
    global_cli_graceful_callback,
    global_cli_result_callback,
    global_cli_super_startup_callback,
)
from ._data_list import DataObjectList
from ._debug_builtins import BuiltInDebugModeShortcuts
from ._debug_mode import DebugMode, get_debug_mode_envvar
from ._exit import Exit
from ._layer_loader import LayerLoader, PublicLayerNames
from ._logger_state import LoggerState
from ._logger_state_utils import LoggerStateFlags, LoggerStateTuple, LoggerUpdateRel
from ._loggers import (
    AppRichHandler,
    AppRichHandlerArgs,
    LoggerDefaults,
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
    SafeCWD,
    detected_click_feedback,
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
    "LoggerDefaults",
    "LoggerMaker",
    "LogItemList",
    "LogMessageData",
    "ResultCallbackHandler",
    "AppRichHandlerArgs",
    "AppRichHandler",
    "get_logger",
    "get_simple_logger",
    "global_log_record_container",
    "LoggerState",
    "app_rich_handler_args",
    "add_logging_level",
    "global_cli_result_callback",
    "global_cli_graceful_callback",
    "global_cli_super_startup_callback",
    "Exit",
    "get_debug_mode_envvar",
    "PublicLayerNames",
    "RunEarlyList",
    "detected_click_feedback",
    "SafeCWD",
    "BuiltInDebugModeShortcuts",
    "DebugMode",
    "LoggerStateTuple",
    "LoggerUpdateRel",
    "LoggerStateFlags",
]
