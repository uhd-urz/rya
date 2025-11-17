from .pre_utils import DebugMode, LayerLoader, get_logger

__app_name = LayerLoader._self_app_name = LayerLoader._app_name = "rya"
LayerLoader.logger = get_logger()
DebugMode(__app_name).load(reload=True)

__all__ = []
