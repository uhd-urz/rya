from functools import cache
from pathlib import Path
from typing import Generator

from properpath import P

from ..core_validators import (
    PathWriteValidator,
    Validate,
    ValidationError,
)
from ..names import AppIdentity, log_file_sinks
from ..pre_init import get_cached_data, update_cache
from ..pre_utils import get_logger

logger = get_logger()


@cache
def get_log_file_path() -> P:
    cached_data = get_cached_data()
    if cached_data.log_file_path:
        return cached_data.log_file_path
    log_store_paths: Generator[Path | P]
    log_store_paths = (log_file_tuple.path for log_file_tuple in log_file_sinks)
    validate_path = Validate(PathWriteValidator(log_store_paths, err_logger=logger))
    try:
        log_file_path = validate_path.get()
    except ValidationError as e:
        logger.critical(
            f"{AppIdentity.app_name} couldn't validate any given log file paths: "
            f"{', '.join(map(str, log_store_paths))} to write logs."
        )
        raise e
    else:
        cached_data.log_file_path = log_file_path
        update_cache(cached_data)
        return log_file_path
