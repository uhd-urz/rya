import logging
from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from ._loggers import get_logger

logger = get_logger()


class LoggerStateFlags(StrEnum):
    ALL = "__all_packages__"


class LoggerUpdateRel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    logger: logging.Logger = logger
    old: type[logging.Handler]
    new: type[logging.Handler]


class LoggerStateTuple(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    package_name: str | Literal["__all_packages__"]
    level: Optional[int]
    logger_update_rel: Optional[LoggerUpdateRel] = None


def _get_logger_handler(logger_update_rel: LoggerUpdateRel, /) -> logging.Handler:
    for handler in logger_update_rel.logger.handlers:
        if isinstance(handler, logger_update_rel.new):
            if type(handler) is not logger_update_rel.new:
                logger.debug(
                    f"Logging handler {handler} is found but not it is not a "
                    f"direct instance of type {logger_update_rel.new.__name__}."
                )
            return handler
    raise RuntimeError(
        f"A handler instance of class {logger_update_rel.new.__name__} was "
        f"expected to exist in {logger} handlers, but "
        f"it wasn't found."
    )
