from collections.abc import Callable
from types import EllipsisType
from typing import Literal, Optional

from dynaconf import Dynaconf
from dynaconf.vendor.ruamel.yaml.scanner import ScannerError

# tomllib.TOMLDecodeError will not work since dynaconf uses vendored tomllib
from dynaconf.vendor.tomllib import TOMLDecodeError
from pydantic import BaseModel, ValidationError, create_model

from ..loggers import get_logger
from ._model_handler import (
    ConfigMaker,
    NoConfigModelRegistrationFound,
    PluginConfigStructType,
    PluginsConfigStructType,
)
from ._names import DynaConfArgs
from ._names import PluginDefinitions as Pdf

logger = get_logger()


def get_dynaconf_settings(dynaconf_args_: DynaConfArgs, /) -> Dynaconf:
    return Dynaconf(**dynaconf_args_.model_dump())


class BadConfigurationFile(Exception): ...


class ConfigurationValidationError(Exception): ...


AppConfigErrorRaiseType = Literal["raise", "ignore", "ignore+"]
ExpectedConfigModelType = "Union[BaseModel, ConfigModel]"


class AppConfig:
    _dynaconf_settings: Optional[Dynaconf] = None
    dynaconf_args: DynaConfArgs = DynaConfArgs()
    validated: ExpectedConfigModelType = None
    exceptions: list[Exception] = []

    class PluginConfigModel(BaseModel): ...

    class ConfigModel(BaseModel): ...

    @classmethod
    def load_settings(cls, reload: bool = False) -> None:
        if cls._dynaconf_settings is None or reload is True:
            cls._dynaconf_settings = get_dynaconf_settings(cls.dynaconf_args)
            cls._dynaconf_settings.reload()

    @classmethod
    def get_settings(cls, reload: bool = False) -> Dynaconf:
        cls.load_settings(reload=reload)
        return cls._dynaconf_settings

    @classmethod
    def _handle_config_errors(
        cls,
        config_loader_func: Callable,
        source_name: Optional[str],
        errors: AppConfigErrorRaiseType = "raise",
    ) -> Optional[BaseModel]:
        try:
            called_loader = config_loader_func()
        except (ScannerError, TOMLDecodeError) as e:
            if errors != "ignore+":
                logger.warning(
                    f"Configuration file(s) could not be scanned. {source_name} could "
                    f"not be loaded. Exception details: {e}"
                )
            cls.exceptions.append(e)
            match errors:
                case "raise":
                    cls.exceptions.append(e)
                    raise BadConfigurationFile from e
                case "ignore" | "ignore+":
                    return None
        except ValidationError as e:
            cls.exceptions.append(e)
            if errors != "ignore+":
                logger.warning(
                    f"{source_name} validation was unsuccessful. Exception details: {e}"
                )
            match errors:
                case "raise":
                    raise e
                case "ignore" | "ignore+":
                    return None
        else:
            return called_loader

    @classmethod
    def validate(
        cls,
        errors: AppConfigErrorRaiseType = "raise",
        reload: bool = False,
    ) -> ExpectedConfigModelType:
        try:
            validated_main_model = cls.main_validate(errors=errors, reload=reload)
        except NoConfigModelRegistrationFound as e:
            cls.exceptions.append(e)
            logger.debug(str(e).replace('"', ""))
            validated_main_model = create_model(
                cls.ConfigModel.__name__, __base__=cls.ConfigModel
            )()
        try:
            validated_plugins_models = cls.plugins_validate(
                errors=errors, reload=reload
            )
        except NoConfigModelRegistrationFound as e:
            cls.exceptions.append(e)
            logger.debug(str(e).replace('"', ""))
            cls.validated = validated_main_model
            return cls.validated
        else:
            model = create_model(
                validated_main_model.__class__.__name__,
                __base__=validated_main_model.__class__,
                plugins=validated_plugins_models.__class__,
            )
            cls.validated = model(
                **validated_main_model.model_dump(), plugins=validated_plugins_models
            )
            return cls.validated

    @classmethod
    def _main_validate(
        cls,
        main_model: type[BaseModel],
        reload: bool = False,
    ) -> BaseModel:
        settings: Dynaconf = cls.get_settings(reload=reload)
        settings_data = {k.lower(): v for k, v in settings.as_dict().items()}
        settings_data.pop(Pdf.config_section_name, None)
        validated_main_model = main_model(**settings_data)
        return validated_main_model

    @classmethod
    def main_validate(
        cls,
        errors: AppConfigErrorRaiseType = "raise",
        reload: bool = False,
    ) -> BaseModel:
        main_model_data: PluginConfigStructType = ConfigMaker.get_main_model()
        main_model = main_model_data["model"]
        validated_plugin_model = cls._handle_config_errors(
            lambda: cls._main_validate(main_model, reload=reload),
            source_name=f"Main configuration model '{main_model}'",
            errors=errors,
        )
        if validated_plugin_model is None:
            return create_model(
                f"Incomplete{main_model.__name__}",
            )()
        return validated_plugin_model

    @classmethod
    def plugins_validate(
        cls,
        errors: AppConfigErrorRaiseType = "raise",
        reload: bool = False,
    ) -> BaseModel:
        plugins_models_data: PluginsConfigStructType = ConfigMaker.get_plugins_models()
        plugins_validated_models: dict[str, tuple[type[BaseModel], EllipsisType]] = {}
        plugins_validated_model_instances: dict[str, BaseModel] = {}
        plugin_model_shell: type[BaseModel] = cls.PluginConfigModel
        incomplete_model: bool = False
        for plugin_name in plugins_models_data:
            validated_plugin_model = cls._handle_config_errors(
                lambda: cls.plugin_validate(plugin_name, reload=reload),
                source_name=f"Plugin '{plugin_name}'",
                errors=errors,
            )
            if validated_plugin_model is None:
                incomplete_model = True
            else:
                plugins_validated_models[plugin_name] = (
                    validated_plugin_model.__class__,
                    ...,
                )
                plugins_validated_model_instances[plugin_name] = validated_plugin_model
        plugin_model_name = (
            f"Incomplete{cls.PluginConfigModel.__name__}"
            if incomplete_model
            else cls.PluginConfigModel.__name__
        )
        plugin_model_shell = create_model(
            plugin_model_name,
            **plugins_validated_models,
            __base__=plugin_model_shell,
        )
        return plugin_model_shell(**plugins_validated_model_instances)

    @classmethod
    def plugin_validate(
        cls,
        plugin_name: str,
        reload: bool = False,
    ) -> BaseModel:
        plugins_settings_data: dict = getattr(
            cls.get_settings(reload=reload), Pdf.config_section_name, {}
        )
        plugin_model_data = ConfigMaker.get_plugin_model(plugin_name)
        plugin_model: type[BaseModel] = plugin_model_data["model"]
        plugin_settings_user_data: dict = plugins_settings_data.get(plugin_name, {})
        validated_plugin_model = plugin_model(**plugin_settings_user_data)
        return validated_plugin_model
