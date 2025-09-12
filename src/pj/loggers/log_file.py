import os
from pathlib import Path

from .._core_init import get_logger
from .._names import (
    APP_NAME,
    ENV_XDG_DATA_HOME,
    FALLBACK_DIR,
    LOG_DIR_ROOT,
    LOG_FILE_NAME,
)
from ..core_validators import (
    CriticalValidationError,
    PathValidator,
    Validate,
    ValidationError,
)
from ..path import ProperPath

logger = get_logger()

log_store_paths: list[Path | ProperPath]
log_store_paths = [LOG_DIR_ROOT / LOG_FILE_NAME]
if _XDG_DATA_HOME := os.getenv(ENV_XDG_DATA_HOME):
    log_store_paths.append(ProperPath(_XDG_DATA_HOME) / APP_NAME / LOG_FILE_NAME)
log_store_paths.append(FALLBACK_LOG_PATH := (FALLBACK_DIR / LOG_FILE_NAME))
validate_path = Validate(PathValidator(log_store_paths, err_logger=logger))

try:
    LOG_FILE_PATH = validate_path.get()
except ValidationError as e:
    logger.critical(
        f"{APP_NAME} couldn't validate fallback path {FALLBACK_LOG_PATH} "
        f"to write logs! This is a critical error. "
        f"{APP_NAME} will not run!"
    )
    raise CriticalValidationError from e
