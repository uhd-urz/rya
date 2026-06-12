import re
import typing
from enum import StrEnum

from dynaconf import LazySettings
from dynaconf.utils import inspect
from pydantic import Secret
from pydantic.fields import FieldInfo

from rya.plugins.config.exceptions import ConfigDisplayFilterNotSupportedError

from .models import ConfigDescriptionModel, ConfigDisplayFilters


class ConfigDisplayFilterDefaults(StrEnum):
    default_key = "all"
    separator = " "


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
    try:
        history = inspect.get_history(dynaconf_settings, key=field_name)
    except inspect.KeyNotFoundError:
        # Very likely that the full settings have not been loaded yet.
        return False
    else:
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
                r"@jinja.+{{env[[.]'?([a-zA-Z_]+[a-zA-Z0-9_]*)'?]?}}",
                s.strip(),
                re.IGNORECASE,
            ):
                return True
        return False


def partial_mask_secret(secret: str, max_reveal_char_count: int = 5) -> str:
    mask_char = "*"
    breaking_char_limit = 18
    minimum_mask_char = 10
    if (expose := abs(breaking_char_limit - len(secret)) // 2) > 0:
        if expose > max_reveal_char_count:
            expose = max_reveal_char_count
    return f"{secret[:expose]}{mask_char * minimum_mask_char}{secret[: -expose - 1 : -1][::-1]}"


def _parse_config_disp_user_multi_options(options: str) -> ConfigDisplayFilters:
    struct_options = map(
        lambda s: s.lower(),
        options.strip().split(ConfigDisplayFilterDefaults.separator),
    )
    options_flag: dict[str, bool] = {ConfigDisplayFilterDefaults.default_key: True}
    for option in struct_options:
        if option not in ConfigDisplayFilters.model_fields.keys():
            raise ConfigDisplayFilterNotSupportedError(
                f"Filter '{option}' is not supported. Valid filters are: "
                f"{', '.join(ConfigDisplayFilters.model_fields.keys())}."
            )
        options_flag[option] = True
    return ConfigDisplayFilters(**options_flag)
