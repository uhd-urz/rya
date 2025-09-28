from typing import Any, Iterable, Optional, Tuple

from .._names import KEY_DEVELOPMENT_MODE
from ..core_validators import Exit, Validate, ValidationError
from ..loggers import get_logger
from ..utils import Missing, PreventiveWarning, get_sub_package_name
from ._config_history import (
    ConfigIdentity,
    FieldValueWithKey,
    minimal_config_data
)
from .config import FALLBACK_SOURCE_NAME, history, settings
from .validators import MainConfigurationValidator

logger = get_logger()


class PatchConfigHistory:
    def __init__(self, configuration_fields: list[FieldValueWithKey]):
        self.configuration_fields = configuration_fields
        self.config_data = minimal_config_data
        self.settings = settings

    @property
    def configuration_fields(self):
        return self._configuration_fields

    @configuration_fields.setter
    def configuration_fields(self, value):
        if not isinstance(value, Iterable) or isinstance(value, str):
            raise ValueError(
                f"Value must be an iterable of {FieldValueWithKey.__name__} namedtuple."
            )
        for tuple_ in value:
            if not isinstance(tuple_, FieldValueWithKey):
                raise ValueError(
                    f"'Value {tuple_}' is not a {FieldValueWithKey.__name__} namedtuple."
                )
        self._configuration_fields = value

    def _modify_history(self, key_name: str, value: str) -> None:
        _val, _src = self.config_data[key_name]
        self.config_data[key_name] = ConfigIdentity(value, _src)
        if value != _val:
            try:
                history.delete(key_name)
            except KeyError:
                ...
            self.config_data[key_name] = ConfigIdentity(
                value, FALLBACK_SOURCE_NAME
            )

    def apply(self) -> None:
        for key_name, value in self.configuration_fields:
            self._modify_history(key_name, value)


def validate_configuration(limited_to: Optional[list]) -> None:
    try:
        validated_fields: list = Validate(
            MainConfigurationValidator(limited_to=limited_to)
        ).get()
    except ValidationError:
        raise Exit(1)
    else:
        if limited_to is not None:
            for validator in limited_to:
                validator.ALREADY_VALIDATED = True
        if validated_fields:
            patch_settings = PatchConfigHistory(validated_fields)
            patch_settings.apply()


def reinitiate_config(
    ignore_essential_validation: bool = False, ignore_already_validated: bool = True
) -> None:
    limited_to: Optional[list]
    limited_to = []
    if not ignore_essential_validation:
        if ignore_already_validated:
            for validator in MainConfigurationValidator.ALL_VALIDATORS:
                if validator.ALREADY_VALIDATED is False:
                    limited_to.append(validator)
        else:
            limited_to = None
        validate_configuration(limited_to)
    else:
        if ignore_already_validated:
            for validator in MainConfigurationValidator.NON_ESSENTIAL_VALIDATORS:
                if validator.ALREADY_VALIDATED is False:
                    limited_to.append(validator)
        else:
            limited_to = MainConfigurationValidator.NON_ESSENTIAL_VALIDATORS
        validate_configuration(limited_to)


def preventive_missing_warning(field: Tuple[str, Any], /) -> None:
    configuration_sub_package_name = get_sub_package_name(__package__)
    if not isinstance(field, Iterable) and not isinstance(field, str):
        raise TypeError(
            f"{preventive_missing_warning.__name__} only accepts an iterable of key-value pair."
        )
    try:
        key, value = field
        # value can be an API token, so it must not be exposed to STDOUT
    except ValueError as e:
        raise ValueError(
            "Only a pair of configuration key and its value in an "
            f"iterable can be passed to {preventive_missing_warning.__name__}."
        ) from e
    if isinstance(value, Missing):
        key = key.lower()
        raise PreventiveWarning(
            f"Value for '{key}' from configuration file is missing. "
            f"This is not necessarily a critical error but a future operation might fail. "
            f"If '{key}' is supposed to fallback to a default value or if you want to "
            f"get a more precise error message, make sure to run function "
            f"'{reinitiate_config.__name__}()' (can be imported with "
            f"'from {configuration_sub_package_name} import {reinitiate_config.__name__}') "
            f"before running anything else. You could also just define a valid value for '{key}' "
            f"in configuration file. This warning may also be shown because '{KEY_DEVELOPMENT_MODE.lower()}' "
            f"is set to '{True}' in configuration file. In most cases, just running "
            f"'{reinitiate_config.__name__}()' should fix this issue."
        )
