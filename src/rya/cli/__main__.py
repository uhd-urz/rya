from ..pre_init import get_logger
from ..pre_utils import LayerLoader
from ..names import AppIdentity

LayerLoader._self_app_name = LayerLoader._app_name = AppIdentity.app_name
LayerLoader.logger = get_logger()

from .app import app  # noqa: E402

app(prog_name=AppIdentity.app_name)
