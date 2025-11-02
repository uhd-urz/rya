from ..loggers import get_logger
from ..names import AppIdentity
from ..pre_utils import LayerLoader
from .app import app

LayerLoader._self_app_name = LayerLoader._app_name = AppIdentity.app_name
LayerLoader.logger = get_logger()

from ._cli_handler import initiate_cli_startup  # noqa: E402

initiate_cli_startup(app)
app(prog_name=AppIdentity.app_name)
