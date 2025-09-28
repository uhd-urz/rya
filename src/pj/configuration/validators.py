import logging
from typing import Iterable, Optional

from dynaconf.utils.boxing import DynaBox

from ..configuration.config import CONFIG_FILE_NAME, NON_CANON_YAML_EXTENSION
from ..core_validators import (
    Validate,
    Validator,
)
from ..loggers import get_logger
from ..utils import Missing, add_message
from ._config_history import FieldValueWithKey, MinimalConfigData, minimal_config_data
from .config import (
    DEVELOPMENT_MODE_DEFAULT_VAL,
    KEY_DEVELOPMENT_MODE,
    KEY_PLUGIN_KEY_NAME,
    PLUGIN_DEFAULT_VALUE,
)

logger = get_logger()


class ConfigurationValidation:
    def __init__(self, minimal_config_data_obj: MinimalConfigData, /):
        self.config_data = minimal_config_data_obj

    @property
    def config_data(self) -> MinimalConfigData:
        return self._config_data

    @config_data.setter
    def config_data(self, value: MinimalConfigData):
        if not isinstance(value, MinimalConfigData):
            raise TypeError(
                f"Value must be an instance of {MinimalConfigData.__name__}."
            )
        self._config_data = value


class ModesWithFallbackConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args, key_name: str, fallback_value: bool):
        super().__init__(*args)
        self.key_name = key_name
        self.fallback_value = fallback_value

    def validate(self) -> bool:
        if isinstance(value := self.config_data.get_value(self.key_name), Missing):
            return self.fallback_value
        if value is None:
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            return self.fallback_value
        if not isinstance(value, bool):
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's not a boolean."
            )
            return self.fallback_value
        return value


class TimeWithFallbackConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(
        self,
        *args,
        key_name: str,
        fallback_value: Optional[float],
        allow_none: bool = False,
    ):
        super().__init__(*args)
        self.key_name = key_name
        self.fallback_value = fallback_value
        self.allow_none = allow_none

    def validate(self) -> Optional[float]:
        if isinstance(value := self.config_data.get_value(self.key_name), Missing):
            return self.fallback_value
        if value is None and not self.allow_none:
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            return self.fallback_value
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's not a float or integer{' or None' if self.allow_none else ''}."
            )
            return self.fallback_value
        return float(value)


class DiscreteWithFallbackConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(
        self,
        *args,
        key_name: str,
        fallback_value: Optional[int],
        allow_none: bool = False,
    ):
        super().__init__(*args)
        self.key_name = key_name
        self.fallback_value = fallback_value
        self.allow_none = allow_none

    def validate(self) -> Optional[int]:
        if isinstance(value := self.config_data.get_value(self.key_name), Missing):
            return self.fallback_value
        if value is None:
            if not self.allow_none:
                logger.warning(
                    f"'{self.key_name.lower()}' is detected in configuration file, "
                    f"but it's null."
                )
                return self.fallback_value
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            logger.warning(
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's not an integer{' or None' if self.allow_none else ''}."
            )
            return self.fallback_value
        return int(value)


class PluginConfigurationValidator(ConfigurationValidation, Validator):
    ALREADY_VALIDATED: bool = False
    __slots__ = ()

    def __init__(self, *args, key_name: str, fallback_value: dict):
        super().__init__(*args)
        self.key_name = key_name
        self.fallback_value = fallback_value

    def validate(self) -> dict:
        value: DynaBox = self.config_data.get_value(self.key_name)
        if isinstance(value, Missing):
            return self.fallback_value
        if value is None:
            message = (
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's null."
            )
            add_message(message, logging.WARNING, is_aggressive=True)
            return self.fallback_value
        if not isinstance(value, dict):
            message = (
                f"'{self.key_name.lower()}' is detected in configuration file, "
                f"but it's not a {NON_CANON_YAML_EXTENSION.upper()} dictionary."
            )
            add_message(message, logging.WARNING, is_aggressive=True)
            return self.fallback_value
        else:
            value: dict = value.to_dict()  # Dynaconf uses Box:
            # https://github.com/cdgriffith/Box/wiki/Converters#dictionary
            for plugin_name, plugin_config in value.copy().items():
                if not isinstance(plugin_config, dict):
                    message = (
                        f"Configuration value for plugin '{plugin_name}' "
                        f"exists in '{CONFIG_FILE_NAME}' under '{self.key_name.lower()}', "
                        f"but it's not a {NON_CANON_YAML_EXTENSION.upper()} dictionary. "
                        f"Plugin configuration for '{plugin_name}' will be ignored."
                    )
                    add_message(message, logging.WARNING, is_aggressive=True)
                    value.pop(plugin_name)
        return value


class MainConfigurationValidator(ConfigurationValidation, Validator):
    ALL_VALIDATORS: list = [
        ModesWithFallbackConfigurationValidator,
        TimeWithFallbackConfigurationValidator,
        DiscreteWithFallbackConfigurationValidator,
        PluginConfigurationValidator,
    ]
    ESSENTIAL_VALIDATORS: list = []
    NON_ESSENTIAL_VALIDATORS: list = [
        ModesWithFallbackConfigurationValidator,
        TimeWithFallbackConfigurationValidator,
        DiscreteWithFallbackConfigurationValidator,
        PluginConfigurationValidator,
    ]
    __slots__ = ()

    def __init__(
        self,
        *,
        limited_to: Optional[Iterable[type[Validator]]] = None,
    ):
        super().__init__(minimal_config_data)
        self.limited_to = limited_to

    @property
    def limited_to(self) -> list[type[Validator]]:
        return self._limited_to

    @limited_to.setter
    def limited_to(self, value):
        if value is None:
            self._limited_to = MainConfigurationValidator.ALL_VALIDATORS
        else:
            if not isinstance(value, Iterable) and isinstance(value, str):
                raise ValueError(
                    f"Value must be an iterable of {Validator.__name__} subclass."
                )
            for _ in value:
                if not issubclass(_, Validator):
                    raise ValueError(
                        f"Value must be an iterable of {Validator.__name__} subclass."
                    )
            self._limited_to = value

    def validate(self) -> list[FieldValueWithKey]:
        validated_fields: list[FieldValueWithKey] = []

        if ModesWithFallbackConfigurationValidator in self.limited_to:
            for key_name, default_value in [
                (KEY_DEVELOPMENT_MODE, DEVELOPMENT_MODE_DEFAULT_VAL),
            ]:
                value = Validate(
                    ModesWithFallbackConfigurationValidator(
                        self.config_data,
                        key_name=key_name,
                        fallback_value=default_value,
                    )
                ).get()
                # Update validated_fields after validation
                validated_fields.append(FieldValueWithKey(key_name, value))
        if PluginConfigurationValidator in self.limited_to:
            plugin = Validate(
                PluginConfigurationValidator(
                    self.config_data,
                    key_name=KEY_PLUGIN_KEY_NAME,
                    fallback_value=PLUGIN_DEFAULT_VALUE,
                )
            ).get()
            # Update validated_fields after validation
            validated_fields.append(FieldValueWithKey(KEY_PLUGIN_KEY_NAME, plugin))
        return validated_fields
