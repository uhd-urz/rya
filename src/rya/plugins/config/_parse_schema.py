from typing import Any

from dynaconf import LazySettings
from pydantic.experimental.missing_sentinel import MISSING
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from ...config import AllConfigModelsType, AppConfig, FieldsConfigType
from ...config._names import PluginDefinitions as Pdf
from ._names import (
    ConfDescDefinition,
)
from .exceptions import (
    UnexpectedConfDescTypeError,
    UnknownConfigDisplayFilterError,
)
from .models import ConfigDescriptionModel, ConfigDisplayFilters, ConfigDisplayValues
from .utils import _is_field_secret, _is_value_from_dynaconf_env, partial_mask_secret


def flatten_config_schema(config_model: AllConfigModelsType) -> dict[str, FieldInfo]:
    def _get_val_by_field_name(fields: FieldsConfigType | dict, origin_key: str | None):
        flattened_data: dict[str, FieldInfo] = {}
        for field_name, field_val in fields.items():
            flattened_data[f"{f'{origin_key}.' if origin_key else ''}{field_name}"] = (
                field_val["field_info"]
            )
        return flattened_data

    all_flattened_data: dict[str, FieldInfo] = {}
    all_flattened_data.update(
        _get_val_by_field_name(
            config_model.get("main", {}).get("fields", {}),
            None,
        )
    )
    for plugin_name, plugin_config_model_val in config_model.get("plugins", {}).items():
        all_flattened_data.update(
            _get_val_by_field_name(
                plugin_config_model_val.get("fields", {}),
                f"{Pdf.config_section_name}.{plugin_name}",
            )
        )
    return all_flattened_data


def _can_pass_conf_display_filter(
    dynaconf_settings: LazySettings,
    *,
    field_name: str,
    field_value: Any,
    field_info: FieldInfo,
    config_description: ConfigDescriptionModel | None,
    filter_: ConfigDisplayFilters,
) -> bool:
    match filter_:
        case ConfigDisplayFilters(mod=False, secret=False, env=False):
            return True
        case ConfigDisplayFilters(mod=True, secret=False, env=False):
            if field_value != field_info.default:
                return True
            return False
        case ConfigDisplayFilters(mod=False, secret=True, env=False):
            if _is_field_secret(
                field_info,
                config_description,
            ):
                return True
            return False
        case ConfigDisplayFilters(mod=True, secret=True, env=False):
            if _is_field_secret(
                field_info,
                config_description,
            ):
                # Here even for secrets, field_value is a string and not a pydantic Secret!
                # That's because we fetch the value directly from dynaconf.
                if field_value != field_info.default:
                    return True
            return False
        case ConfigDisplayFilters(mod=False, secret=False, env=True):
            if _is_value_from_dynaconf_env(
                dynaconf_settings,
                field_name=field_name,
            ):
                return True
            return False
        case ConfigDisplayFilters(mod=True, secret=False, env=True):
            if _is_value_from_dynaconf_env(
                dynaconf_settings,
                field_name=field_name,
            ):
                if field_value != field_info.default:
                    return True
            return False
        case ConfigDisplayFilters(mod=False, secret=True, env=True):
            if _is_value_from_dynaconf_env(
                dynaconf_settings,
                field_name=field_name,
            ):
                if _is_field_secret(
                    field_info,
                    config_description,
                ):
                    return True
            return False
        case ConfigDisplayFilters(mod=True, secret=True, env=True):
            if _is_value_from_dynaconf_env(
                dynaconf_settings,
                field_name=field_name,
            ):
                if _is_field_secret(
                    field_info,
                    config_description,
                ):
                    if field_value != field_info.default:
                        return True
            return False
        case _:
            raise UnknownConfigDisplayFilterError(
                f"An unexpected {filter_} instance was passed."
            )


def _get_field_config_result(
    field_name: str,
    field_info: FieldInfo,
    *,
    filters: ConfigDisplayFilters,
    reload: bool = False,
) -> ConfigDisplayValues | None:
    def _default_or_missing(_field_info: FieldInfo) -> Any:
        if _field_info.default is PydanticUndefined:
            return MISSING
        return _field_info.default

    field_value = (dynaconf_settings := AppConfig.get_settings(reload=reload)).get(
        field_name, _default_or_missing(field_info)
    )
    match field_info.json_schema_extra:
        case dict():
            match config_description := field_info.json_schema_extra.get(
                ConfDescDefinition.conf_desc_key, MISSING
            ):
                case ConfigDescriptionModel():
                    # noinspection PyInconsistentReturns
                    # A false positive. All return cases are already handled.
                    match config_description.title:
                        case str():
                            if _can_pass_conf_display_filter(
                                dynaconf_settings,
                                field_name=field_name,
                                field_value=field_value,
                                field_info=field_info,
                                config_description=config_description,
                                filter_=filters,
                            ):
                                if _is_field_secret(field_info, config_description):
                                    return ConfigDisplayValues(
                                        key=field_name,
                                        title=config_description.title,
                                        value=partial_mask_secret(
                                            field_value,
                                            max_reveal_char_count=ConfDescDefinition.max_reveal_masked_secret,
                                        ),
                                        description=config_description.description,
                                    )
                                return ConfigDisplayValues(
                                    key=field_name,
                                    title=config_description.title,
                                    value=field_value,
                                    description=config_description.description,
                                )
                            return None
                        case None:
                            return None
                case MISSING.__class__():
                    return None
                case _:
                    raise UnexpectedConfDescTypeError(
                        f"{ConfDescDefinition.conf_desc_key} is found in 'json_schema_extra', "
                        f"but it is not of type {ConfigDescriptionModel.__name__}, but of "
                        f"type {type(config_description)} with value {config_description}. "
                    )
        case _:
            if _can_pass_conf_display_filter(
                dynaconf_settings,
                field_name=field_name,
                field_value=field_value,
                field_info=field_info,
                config_description=None,
                filter_=filters,
            ):
                if _is_field_secret(field_info, config_description=None):
                    return ConfigDisplayValues(
                        key=field_name,
                        value=partial_mask_secret(
                            field_value,
                            max_reveal_char_count=ConfDescDefinition.max_reveal_masked_secret,
                        ),
                    )
                return ConfigDisplayValues(key=field_name, value=field_value)
            return None
