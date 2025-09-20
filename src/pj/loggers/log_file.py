from dataclasses import asdict
from pathlib import Path

from .._core_init import get_logger
from .._names import APP_NAME, log_files
from ..core_validators import (
    CriticalValidationError,
    PathWriteValidator,
    Validate,
    ValidationError,
)
from ..path import ProperPath

logger = get_logger()

log_store_paths: list[Path | ProperPath]
log_store_paths = [file for file, _ in asdict(log_files).values()]
validate_path = Validate(PathWriteValidator(log_store_paths))
try:
    LOG_FILE_PATH = validate_path.get()
except ValidationError as e:
    logger.critical(
        f"{APP_NAME} couldn't validate fallback path "
        f"{log_store_paths[-1]} to write logs! This is a "
        f"critical error. {APP_NAME} will not run!"
    )
    raise CriticalValidationError from e
