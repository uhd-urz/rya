from properpath import ProperPath

from ._core_init import get_logger
from ._core_utils import LayerLoader
from .names import AppIdentity

LayerLoader.logger = ProperPath.default_err_logger = get_logger()
LayerLoader._self_app_name = LayerLoader._app_name = AppIdentity.app_name

__all__ = ["AppIdentity"]
