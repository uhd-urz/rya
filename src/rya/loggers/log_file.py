from functools import cache

from properpath import P
from properpath.validators import PathValidationError, PathWriteValidator
from pydantic import ValidationError
from pydantic.experimental.missing_sentinel import MISSING

from ..kernel import LoggerDefaults, get_logger
from ..names import AppIdentity, CacheModel, app_locations
from ..pre_init import get_cached_data, update_meta_cache

logger = get_logger()


class LogFileNotGivenError(ValidationError): ...


@cache
def get_log_file_path() -> P:
    if app_locations.log_file is None:
        raise LogFileNotGivenError(
            f"No log file path was provided to {app_locations.__class__} instance."
        )
    if LoggerDefaults.will_cache_log_path:
        cached_data = get_cached_data()
        if getattr(cached_data.app_meta, "log_file_path", MISSING) is not MISSING:
            return cached_data.app_meta.log_file_path
    else:
        cached_data = None
    log_paths = (
        file.path
        for file in (
            app_locations.log_file,
            *app_locations.log_file.fallback_paths,
        )
    )
    try:
        log_file_path = PathWriteValidator(log_paths, err_logger=logger).validate()
    except PathValidationError as e:
        logger.critical(
            f"{AppIdentity.app_name} couldn't validate any "
            f"given log file paths: "
            f"{', '.join(map(str, log_paths))} to write logs."
        )
        raise e
    else:
        if isinstance(cached_data, CacheModel):
            update_meta_cache(cached_data, log_file_path=log_file_path)
            logger.debug(
                f"Log file path '{log_file_path}' has been cached to the cache file."
            )
        return log_file_path
