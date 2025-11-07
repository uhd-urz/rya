from pydantic import BaseModel

from ..loggers import get_logger
from ._names import PluginDefinitions as Pdf
from ._pydantic_parser import FieldsConfigStructType, get_pydantic_nested_model_fields

logger = get_logger()
PluginConfigStructType = dict[str, type[BaseModel] | FieldsConfigStructType]
PluginsConfigStructType = dict[str, PluginConfigStructType]
MainConfigStructType = dict[str, PluginsConfigStructType | PluginConfigStructType]


class NoConfigModelRegistrationFound(KeyError): ...


class ConfigMaker:
    _basic_registry: MainConfigStructType = {}

    @classmethod
    def get_plugin_model(cls, plugin_name: str) -> PluginConfigStructType:
        try:
            return cls._basic_registry.get(Pdf.config_section_name, {})[plugin_name]
        except KeyError as e:
            raise NoConfigModelRegistrationFound(
                f"Plugin '{plugin_name}' is not registered. "
                f"Make sure the model has 'plugin_name' class attribute set."
            ) from e

    @classmethod
    def get_main_model(cls) -> PluginConfigStructType:
        try:
            return cls._basic_registry["main"]
        except KeyError as e:
            raise NoConfigModelRegistrationFound(
                f"No main configuration model registered to {cls}."
            ) from e

    @classmethod
    def get_plugins_models(cls) -> PluginsConfigStructType:
        try:
            return cls._basic_registry[Pdf.config_section_name]
        except KeyError as e:
            raise NoConfigModelRegistrationFound(
                f"No plugin model is registered to {cls}."
            ) from e

    @classmethod
    def get_all_models(cls) -> MainConfigStructType:
        return cls._basic_registry

    @staticmethod
    def _check_reserved_names(config_model: type[BaseModel]) -> None:
        if (
            Pdf.config_section_name in config_model.model_fields
            or Pdf.config_section_name in config_model.__class_vars__
        ):
            raise ValueError(
                f"The name 'plugins' is reserved. "
                f"Main model '{config_model}' cannot have 'plugins' as a field or "
                f"a class attribute. Use 'plugin_name' class attribute "
                f"to add a plugin model."
            )

    @classmethod
    def _register_plugin_model(
        cls, plugin_name: str, config_model: type[BaseModel]
    ) -> None:
        cls._basic_registry.setdefault(Pdf.config_section_name, {})
        if cls._basic_registry[Pdf.config_section_name].get(plugin_name) is not None:
            logger.debug(
                f"Plugin model '{config_model}' for plugin '{plugin_name}' "
                f"is already registered."
            )
        else:
            cls._basic_registry[Pdf.config_section_name].setdefault(
                plugin_name,
                {
                    "model": config_model,
                    "fields": get_pydantic_nested_model_fields(config_model),
                },
            )

    @classmethod
    def _register_main_model(cls, config_model: type[BaseModel]) -> None:
        if cls._basic_registry.get("main") is not None:
            logger.debug(f"Main model '{config_model}' for is already registered.")
            return
        cls._basic_registry.setdefault(
            "main",
            {
                "model": config_model,
                "fields": get_pydantic_nested_model_fields(config_model),
            },
        )

    @classmethod
    def add_model(cls, config_model: type[BaseModel], /) -> None:
        if not issubclass(config_model, BaseModel):
            raise ValueError(
                f"Model '{config_model}' must be a subclass of Pydantic BaseModel."
            )
        cls._check_reserved_names(config_model)
        for class_attr in config_model.__class_vars__:
            if class_attr == "plugin_name":
                if (plugin_name := getattr(config_model, class_attr, None)) is not None:
                    cls._register_plugin_model(plugin_name, config_model)
                else:
                    raise ValueError(
                        f"Model '{config_model}' has 'plugin_name' class attribute, "
                        "but it cannot be None."
                    )
                break
        else:
            cls._register_main_model(config_model)
