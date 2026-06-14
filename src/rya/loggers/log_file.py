from functools import cache
from pathlib import Path
from typing import Generator, Optional

from properpath import P
from properpath.validators import PathValidationError, PathWriteValidator

from ..kernel import LoggerDefaults, get_logger
from ..names import AppIdentity, CacheModel, log_file_sinks
from ..pre_init import get_cached_data, update_cache

logger = get_logger()


@cache
def get_log_file_path() -> P:
    if LoggerDefaults.will_cache_log_path:
        cached_data = get_cached_data()
        if cached_data.log_file_path:
            return cached_data.log_file_path
    else:
        cached_data = None
    log_store_paths = map(lambda p: p.path, log_file_sinks)
    try:
        log_file_path = PathWriteValidator(
            log_store_paths, err_logger=logger
        ).validate()
    except PathValidationError as e:
        logger.critical(
            f"{AppIdentity.app_name} couldn't validate any "
            f"given log file paths: "
            f"{', '.join(map(str, log_store_paths))} to write logs."
        )
        raise e
    else:
        if isinstance(cached_data, CacheModel):
            cached_data.log_file_path = log_file_path
            update_cache(cached_data)
            logger.debug(
                f"Log file path '{log_file_path}' has been cached to the cache file."
            )
        return log_file_path
