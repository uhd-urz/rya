from typing import TypedDict

from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING

from ..loggers import get_logger
from ._names import PluginDefinitions as Pdf
from ._pydantic_parser import FieldsConfigType, get_pydantic_nested_model_fields

logger = get_logger()


class _PluginConfigType(TypedDict, total=False):
    model: type[BaseModel]
    fields: FieldsConfigType


_PluginsConfigType = dict[str, _PluginConfigType]


class _AllModelsType(TypedDict, total=False):
    main: _PluginConfigType
    plugins: _PluginsConfigType


class NoConfigModelRegistrationFound(KeyError): ...


class ConfigMaker:
    _main_config_model: _PluginConfigType = {}
    _plugins_config_model: _PluginsConfigType = {}
    # Pycharm interprets the union type as if the assigned value must also be of a union type!

    @classmethod
    def get_plugin_model(cls, plugin_name: str) -> _PluginConfigType:
        try:
            return cls._plugins_config_model[plugin_name]
        except KeyError as e:
            raise NoConfigModelRegistrationFound(
                f"Plugin '{plugin_name}' is not registered. "
                f"Make sure the model has 'plugin_name' class attribute set."
            ) from e

    @classmethod
    def get_main_model(cls) -> _PluginConfigType:
        if not cls._main_config_model:
            raise NoConfigModelRegistrationFound(
                f"No main configuration model registered to {cls.__name__}."
            )
        return cls._main_config_model

    @classmethod
    def get_plugins_models(cls) -> _PluginsConfigType:
        if not cls._plugins_config_model:
            raise NoConfigModelRegistrationFound(
                f"No plugin model is registered to {cls.__name__}."
            )
        return cls._plugins_config_model

    @classmethod
    def get_all_models(cls) -> _AllModelsType:
        return {"main": cls._main_config_model, "plugins": cls._plugins_config_model}

    @staticmethod
    def _check_reserved_names(config_model: type[BaseModel]) -> None:
        if (
            Pdf.config_section_name in config_model.model_fields
            or Pdf.config_section_name in config_model.__class_vars__
        ):
            raise ValueError(
                f"The name '{Pdf.config_section_name}' is reserved. "
                f"Main model '{config_model}' cannot have '{Pdf.config_section_name}' as "
                f"a field or a class attribute. Use 'plugin_name' class attribute "
                f"to add a plugin model."
            )

    @classmethod
    def _register_plugin_model(
        cls,
        plugin_name: str,
        config_model: type[BaseModel],
        *,
        force_reregister: bool = False,
    ) -> None:
        if cls._plugins_config_model.get(plugin_name) and not force_reregister:
            logger.warning(
                f"Plugin model '{config_model}' for plugin '{plugin_name}' "
                f"is already registered. Re-registration will not be considered. "
                f"Pass 'force_reregister = True' to force re-registration."
            )
            return
        if force_reregister:
            logger.debug(
                f"Re-registering plugin '{plugin_name}' configuration model {config_model}."
            )
        cls._plugins_config_model[plugin_name] = {
            "model": config_model,
            "fields": get_pydantic_nested_model_fields(config_model),
        }

    @classmethod
    def _register_main_model(
        cls, config_model: type[BaseModel], *, force_reregister: bool = False
    ) -> None:
        if cls._main_config_model and not force_reregister:
            logger.warning(
                f"Main model '{config_model}' for is already registered. "
                f"Re-registration will not be considered. Pass 'force_reregister = True' "
                f"to force re-registration."
            )
            return
        if force_reregister:
            logger.debug(f"Re-registering main configuration model {config_model}.")
        cls._main_config_model = {
            "model": config_model,
            "fields": get_pydantic_nested_model_fields(config_model),
        }

    @classmethod
    def add_model(
        cls, config_model: type[BaseModel], /, *, force_reregister: bool = False
    ) -> None:
        if not issubclass(config_model, BaseModel):
            raise ValueError(
                f"Model '{config_model}' must be a subclass of Pydantic BaseModel."
            )
        cls._check_reserved_names(config_model)
        if Pdf.cls_attr_name in config_model.__class_vars__:
            if not isinstance(
                plugin_name := getattr(config_model, Pdf.cls_attr_name, MISSING),
                str,
            ):
                raise ValueError(
                    f"Model '{config_model}' has '{Pdf.cls_attr_name}' class attribute. "
                    f"This indicates that the model is a plugin-specific "
                    f"configuration model. plugin_name can only be a string, given "
                    f"value '{plugin_name}' of type {type(plugin_name)}"
                )
            cls._register_plugin_model(
                plugin_name,
                config_model,
                force_reregister=force_reregister,
            )
            return
        cls._register_main_model(
            config_model,
            force_reregister=force_reregister,
        )
