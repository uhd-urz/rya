from ..utils import Missing
from ._overload_history import reinitiate_config
from .config import (
    KEY_DEVELOPMENT_MODE,
    KEY_PLUGIN_KEY_NAME,
    MinimalActiveConfiguration,
)


def _development_mode_validation_switch() -> None:
    _value = MinimalActiveConfiguration().get_value(KEY_DEVELOPMENT_MODE)
    if _value is False or _value == Missing():
        reinitiate_config()


def get_development_mode(*, skip_validation: bool = False) -> bool:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_DEVELOPMENT_MODE)


def get_active_plugin_configs(*, skip_validation: bool = False) -> dict:
    if not skip_validation:
        _development_mode_validation_switch()
    return MinimalActiveConfiguration().get_value(KEY_PLUGIN_KEY_NAME)
