from ..loggers import get_logger
from ..names import AppIdentity
from ..pre_utils import LayerLoader

LayerLoader._self_app_name = LayerLoader._app_name = AppIdentity.app_name
LayerLoader.logger = get_logger()

from .app import app  # noqa: E402

app(prog_name=AppIdentity.app_name)
