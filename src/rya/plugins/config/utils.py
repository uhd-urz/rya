import re
import typing
from enum import StrEnum
from typing import Generic

from dynaconf import LazySettings
from dynaconf.utils import inspect
from pydantic import BaseModel, Secret
from pydantic.fields import FieldInfo

from .exceptions import ConfigDisplayFilterNotSupportedError
from .models import ConfigDescriptionModel, ConfigDisplayFilters, ConfigDisplayIncludes


class ConfigDisplayFilterDefaults(StrEnum):
    default_key = "all"


def _is_field_secret(
    field_info: FieldInfo, config_description: ConfigDescriptionModel | None
) -> bool:
    config_description_contains_secret: bool = False
    if config_description is not None:
        config_description_contains_secret = config_description.contains_secrets
    if (
        typing.get_origin(field_info.annotation) == Secret
        or config_description_contains_secret is True
    ):
        return True
    return False


def _is_value_from_dynaconf_env(
    dynaconf_settings: LazySettings, /, field_name: str
) -> bool:
    history = get_dynaconf_settings_history(
        dynaconf_settings, field_name=field_name, default=None
    )
    if not history:
        return False
    actual_value_history = history[-1]
    match actual_value_history.get("value"):
        # See dynaconf interpolation: https://www.dynaconf.com/dynamic/?h=%40format#format-token
        # Environment variable approved characters regex: ([a-zA-Z_]+[a-zA-Z0-9_]*)
        # https://stackoverflow.com/a/2821201/7696241
        case str(s) if re.match(
            r"@format.+{env\[([a-zA-Z_]+[a-zA-Z0-9_]*)]}",
            s.strip(),
            re.IGNORECASE,
        ) or re.match(
            r"@jinja.+{{env[\[.]'?([a-zA-Z_]+[a-zA-Z0-9_]*)'?]?}}",
            s.strip(),
            re.IGNORECASE,
        ):
            return True
    return False


def partial_mask_secret(
    secret: str,
    min_hidden_char_count: int = 18,
    max_reveal_char_count: int = 5,
) -> str:
    mask_char = "*"
    breaking_char_limit = 18
    if min_hidden_char_count > breaking_char_limit:
        breaking_char_limit = min_hidden_char_count
    mask_char_repeat_count = 10
    if (expose := abs(breaking_char_limit - len(secret)) // 2) > 0:
        if expose > max_reveal_char_count:
            expose = max_reveal_char_count
    return f"{secret[:expose]}{mask_char * mask_char_repeat_count}{secret[: -expose - 1 : -1][::-1]}"


def get_dynaconf_settings_history[AnyDefault](
    dynaconf_settings: LazySettings, /, *, field_name: str, default: AnyDefault
) -> dict | AnyDefault:
    try:
        history = inspect.get_history(dynaconf_settings, key=field_name)
    except inspect.KeyNotFoundError:
        # Very likely that the full settings have not been loaded yet.
        return default
    else:
        return history


_UserOptionsType = typing.TypeVar(
    "_UserOptionsType", ConfigDisplayFilters, ConfigDisplayIncludes
)


class _MultiOptionsParserParams(BaseModel, Generic[_UserOptionsType]):
    separator: str
    default_dict: dict
    base_model_type: type[_UserOptionsType]
    identifier: str


def _parse_config_disp_user_multi_options(
    options: str,
    /,
    _parser_params: _MultiOptionsParserParams[_UserOptionsType],
) -> _UserOptionsType:
    struct_options = map(
        lambda s: s.lower(),
        options.strip().split(_parser_params.separator),
    )
    options_flag: dict[str, bool] = {**_parser_params.default_dict}
    for option in struct_options:
        if option not in _parser_params.base_model_type.model_fields.keys():
            raise ConfigDisplayFilterNotSupportedError(
                f"{_parser_params.identifier.capitalize()} '{option}' is not supported. "
                f"Valid options are: "
                f"{', '.join(_parser_params.base_model_type.model_fields.keys())}."
            )
        options_flag[option] = True
    return _parser_params.base_model_type(**options_flag)
