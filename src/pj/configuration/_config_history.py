from collections import namedtuple
from dataclasses import asdict
from typing import Any, Union

from dynaconf import Dynaconf
from dynaconf.utils import inspect

from .._names import ConfigFiles
from ..loggers import get_logger

logger = get_logger()

ConfigIdentity = namedtuple("ConfigIdentity", ["value", "source"])
FieldValueWithKey = namedtuple("FieldValueWithKey", ["key_name", "value"])


class _ConfigRules:
    @classmethod
    def get_valid_key(cls, key_name: str, /) -> str:
        if not isinstance(key_name, str):
            raise ValueError("key must be a string!")
        return key_name.upper()


class ConfigHistory:
    def __init__(self, setting: Dynaconf, /):
        self.setting = setting
        self._history = inspect.get_history(self.setting)

    @property
    def setting(self) -> Dynaconf:
        return self._setting

    @setting.setter
    def setting(self, value: Dynaconf):
        if not isinstance(value, Dynaconf):
            raise ValueError("settings must be a Dynaconf instance!")
        self._setting = value

    def get(self, key: str, /, default: Any = None) -> Any:
        for config in self._history[::-1]:
            try:
                return config["value"][_ConfigRules.get_valid_key(key)]
            except KeyError:
                continue
        return default

    def patch(self, key: str, /, value: Any) -> None:
        key = _ConfigRules.get_valid_key(key)
        for config in self._history[::-1]:
            try:
                config["value"][key]
            except KeyError:
                continue
            else:
                config["value"][key] = value
                return
        raise KeyError(f"Key '{key}' couldn't be found.")

    def delete(self, key: str, /) -> None:
        key = _ConfigRules.get_valid_key(key)
        _item = None
        for config in self._history:
            try:
                _item = config["value"].pop(key)
            except KeyError:
                continue
        if not _item:
            raise KeyError(f"Key '{key}' couldn't be found.")

    def items(self):
        return self._history


class InspectConfigHistory:
    def __init__(
        self,
        history_obj: Union[ConfigHistory, Dynaconf],
        /,
        config_files: ConfigFiles,
    ):
        self.history = history_obj
        self.config_files = config_files

    @property
    def history(self) -> list[dict]:
        return self._history

    @history.setter
    def history(self, value) -> None:
        if not isinstance(value, (ConfigHistory, Dynaconf)):
            raise ValueError(
                f"{self.__class__.__name__} only accepts instance of ConfigHistory or Dynaconf."
            )
        self._history = (
            value.items()
            if isinstance(value, ConfigHistory)
            else inspect.get_history(value)
        )

    @property
    def tagged_config_files(self) -> dict:
        config_identifiers: list = [config["identifier"] for config in self.history]
        return {
            str(k): v
            for k, v in asdict(self.config_files).values()
            if str(k) in config_identifiers
        }

    @tagged_config_files.setter
    def tagged_config_files(self, value) -> None:
        raise AttributeError(
            f"{self.__class__.__name__} instance cannot modify configuration history. "
            "Use ConfigHistory to modify history."
        )

    @property
    def config_data(self) -> dict:
        config_data = {}
        for config in self.history:
            for k, v in config["value"].items():
                config_data.update({k: ConfigIdentity(v, config["identifier"])})
        return config_data

    @config_data.setter
    def config_data(self, value) -> None:
        raise AttributeError(
            f"{self.__class__.__name__} instance cannot modify configuration history. "
            "Use ConfigHistory to modify history."
        )


class MinimalConfigData:
    _instance = None
    _container: dict[str, ConfigIdentity] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinimalConfigData, cls).__new__(cls)
        return cls._instance

    def __str__(self):
        return str(self._container)

    @classmethod
    def __getitem__(cls, item: str) -> ConfigIdentity:
        return cls._container[_ConfigRules.get_valid_key(item)]

    @classmethod
    def __setitem__(cls, key: str, value: ConfigIdentity):
        cls._container[_ConfigRules.get_valid_key(key)] = value

    @classmethod
    def update(cls, value: dict):
        for k, v in value.items():
            if not isinstance(v, ConfigIdentity):
                raise ValueError(
                    f"Value '{v}' for key '{k}' must be an "
                    f"instance of {ConfigIdentity.__name__}."
                )
        cls._container.update(value)

    @classmethod
    def items(cls) -> dict:
        return cls._container

    @classmethod
    def get(cls, key: str, /, default: Any = None) -> Any:
        try:
            return cls.__getitem__(key)
        except KeyError:
            return default

    @classmethod
    def get_value(cls, key: str, /, default: Any = None) -> Any:
        try:
            value, source = cls.__getitem__(key)
        except KeyError:
            return default
        else:
            return value
