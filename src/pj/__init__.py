from properpath import ProperPath

from ._core_init import get_logger
from ._names import APP_BRAND_NAME, APP_NAME

ProperPath.default_err_logger = get_logger()

__all__ = ["APP_NAME", "APP_BRAND_NAME"]
