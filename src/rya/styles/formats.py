import json
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from csv import DictWriter
from io import StringIO
from typing import Any, Optional, Self, Union

import yaml

from .._core_utils import generate_pydantic_model_from_abstract_cls
from ..names import AppIdentity


class BaseFormat(ABC):
    _registry: dict[str, dict[str, type[Self]]] = {AppIdentity.app_name: {}}
    _names: dict[str, list[str]] = {AppIdentity.app_name: []}
    _conventions: dict[str, list[str]] = {AppIdentity.app_name: []}

    # noinspection PyTypeChecker
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        attrs_cls = generate_pydantic_model_from_abstract_cls(
            BaseFormat, exclude=("__call__",)
        )
        attrs_cls(**cls.__dict__)
        if cls.plugin_name not in cls._registry:
            cls._registry[cls.plugin_name] = {}
            cls._registry[cls.plugin_name].update(cls._registry[AppIdentity.app_name])
        if cls.plugin_name not in cls._names:
            cls._names[cls.plugin_name] = []
            cls._names[cls.plugin_name] += cls._names[AppIdentity.app_name]
        if cls.plugin_name not in cls._conventions:
            cls._conventions[cls.plugin_name] = []
            cls._conventions[cls.plugin_name] += cls._conventions[AppIdentity.app_name]
        if cls.name is None:
            if cls.plugin_name == AppIdentity.app_name:
                raise ValueError(
                    f"Attribute 'name' cannot be None for when plugin_name "
                    f"is {AppIdentity.app_name} as it will "
                    f"remove {AppIdentity.app_name} built-in formats."
                )
            existing_cls = cls._registry[cls.plugin_name].pop(cls.pattern)
            try:
                cls._names[cls.plugin_name].remove(existing_cls.name)
                cls._conventions[cls.plugin_name].remove(existing_cls.conventions)
            except ValueError as e:
                raise KeyError(
                    f"Attribute 'name' is None, which will remove "
                    f"{cls!r} as a formatter, "
                    f"but class {cls!r} was never registered before!"
                ) from e
        else:
            cls._registry[cls.plugin_name][cls.pattern] = cls
            if cls.name not in cls._names[cls.plugin_name]:
                cls._names[cls.plugin_name].append(cls.name)
            if cls.conventions not in cls._conventions[cls.plugin_name]:
                cls._conventions[cls.plugin_name].append(cls.conventions)

    @property
    @abstractmethod
    def name(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def conventions(self) -> Optional[tuple[str, ...]]:
        return self.name

    @conventions.setter
    def conventions(self, value): ...

    @property
    @abstractmethod
    def plugin_name(self) -> Optional[str]: ...

    @classmethod
    def supported_formatters(
        cls, plugin_name: Optional[str] = None
    ) -> dict[str, dict[str, type[Self]]] | dict[str, type[Self]]:
        if plugin_name is None:
            return cls._registry
        return cls._registry[plugin_name]

    @classmethod
    def supported_formatter_names(
        cls, plugin_name: Optional[str] = None
    ) -> dict[str, list[str]] | list[str]:
        if plugin_name is None:
            return cls._names
        return cls._names[plugin_name]

    @property
    @abstractmethod
    def pattern(self) -> str: ...

    @abstractmethod
    def __call__(self, data: Any): ...


class FormatError(Exception): ...


class JSONFormat(BaseFormat):
    name: str = "json"
    conventions: tuple[str] = (name,)
    pattern: str = r"^json$"
    plugin_name: str = AppIdentity.app_name

    def __call__(self, data: Any) -> str:
        return json.dumps(
            data, indent=2, ensure_ascii=False
        )  # ensure_ascii==False allows unicode


class YAMLFormat(BaseFormat):
    name: str = "yaml"
    conventions: tuple[str] = ("yml", "yaml")
    pattern: str = r"^ya?ml$"
    plugin_name: str = AppIdentity.app_name

    def __call__(self, data: Any) -> str:
        return yaml.dump(data, indent=2, allow_unicode=True, sort_keys=False)


class CSVFormat(BaseFormat):
    name: str = "csv"
    conventions: tuple[str] = (name,)
    pattern: str = r"^csv$"
    plugin_name: str = AppIdentity.app_name

    def __call__(self, data: Any) -> str:
        with StringIO() as csv_buffer:
            writer: DictWriter = DictWriter(csv_buffer, fieldnames=[])
            if isinstance(data, dict):
                writer.fieldnames = data.keys()
                writer.writeheader()
                writer.writerow(data)
                csv_as_string = csv_buffer.getvalue()
            elif isinstance(data, Iterable):
                for item in data:
                    if not isinstance(item, dict):
                        raise FormatError(
                            "Only dictionaries or iterables of dictionaries can be formatted to CSV."
                        )
                    if not writer.fieldnames:
                        writer.fieldnames = item.keys()
                        writer.writeheader()
                    if len(item.items()) > len(writer.fieldnames):
                        raise FormatError(
                            "Iterable of dictionary contains insistent length of key items."
                        )
                    writer.writerow(item)
                csv_as_string = csv_buffer.getvalue()
        return csv_as_string


class TXTFormat(BaseFormat):
    name: str = "txt"
    conventions: tuple[str] = ("txt",)
    pattern: str = r"^txt|text|plaintext$"
    plugin_name: str = AppIdentity.app_name

    def __call__(self, data: Any) -> str:
        return str(data)


class FormatInstantiator:
    def __init__(self, language: str, *, plugin_name: str):
        self.plugin_name = plugin_name
        self._register = language

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @plugin_name.setter
    def plugin_name(self, value):
        if not isinstance(value, str):
            raise ValueError(f"{value} must be an instance of str.")
        self._plugin_name = value

    @property
    def _register(self):
        raise AttributeError(
            "'_register' isn't meant to be called directly! "
            "Use attributes 'name' and 'formatter'."
        )

    @_register.setter
    def _register(self, value):
        try:
            supported_formatters = BaseFormat.supported_formatters()[self.plugin_name]
        except KeyError as e:
            raise KeyError(
                f"Plugin '{self.plugin_name}' not found "
                f"in registered supported_formatters dictionary!"
            ) from e
        for pattern, formatter in supported_formatters.items():
            if re.match(rf"{pattern or ''}", value, flags=re.IGNORECASE):
                self.name: str = formatter.name
                self.conventions: Union[str, Iterable[str]] = formatter.conventions
                self.formatter: type[BaseFormat] = formatter
                return
        raise FormatError(
            f"'{value}' isn't a supported language format! "
            f"Supported formats are: "
            f"{BaseFormat.supported_formatter_names(self.plugin_name)}."
        )


def get_formatter(language: str, /, *, plugin_name: str) -> BaseFormat:
    lang = FormatInstantiator(language, plugin_name=plugin_name)
    return lang.formatter()
