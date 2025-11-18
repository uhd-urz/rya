import json
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from csv import DictWriter
from io import StringIO
from typing import Any, Optional, Self

import yaml
from pydantic import BaseModel

from ..names import AppIdentity
from ..pre_utils import generate_pydantic_model_from_abstract_cls


class BaseFormat(ABC):
    _registry: dict[str, dict[str, type[Self]]] = {AppIdentity.app_name: {}}
    _names: dict[str, list[str]] = {AppIdentity.app_name: []}
    _conventions: dict[str, tuple[str]] = {AppIdentity.app_name: []}

    # noinspection PyTypeChecker
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        attrs_cls = generate_pydantic_model_from_abstract_cls(
            BaseFormat, exclude=("__call__",)
        )
        attrs_cls(**cls.__dict__)
        if cls.identifier not in cls._registry:
            cls._registry[cls.identifier] = {}
            cls._registry[cls.identifier].update(cls._registry[AppIdentity.app_name])
        if cls.identifier not in cls._names:
            cls._names[cls.identifier] = []
            cls._names[cls.identifier] += cls._names[AppIdentity.app_name]
        if cls.identifier not in cls._conventions:
            cls._conventions[cls.identifier] = []
            cls._conventions[cls.identifier] += cls._conventions[AppIdentity.app_name]
        if cls.name is None:
            if cls.identifier == AppIdentity.app_name:
                raise ValueError(
                    f"Attribute 'name' cannot be None for when identifier "
                    f"is {AppIdentity.app_name} as it will "
                    f"remove {AppIdentity.app_name} built-in formats."
                )
            existing_cls = cls._registry[cls.identifier].pop(cls.pattern)
            try:
                cls._names[cls.identifier].remove(existing_cls.name)
                cls._conventions[cls.identifier].remove(existing_cls.conventions)
            except ValueError as e:
                raise KeyError(
                    f"Attribute 'name' is None, which will remove "
                    f"{cls!r} as a formatter, "
                    f"but class {cls!r} was never registered before!"
                ) from e
        else:
            cls._registry[cls.identifier][cls.pattern] = cls
            if cls.name not in cls._names[cls.identifier]:
                cls._names[cls.identifier].append(cls.name)
            if cls.conventions not in cls._conventions[cls.identifier]:
                cls._conventions[cls.identifier].append(cls.conventions)

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
    def identifier(self) -> Optional[str]: ...

    @classmethod
    def supported_formatters(
        cls, identifier: Optional[str] = None
    ) -> dict[str, dict[str, type[Self]]] | dict[str, type[Self]]:
        if identifier is None:
            return cls._registry
        return cls._registry[identifier]

    @classmethod
    def supported_formatter_names(
        cls, identifier: Optional[str] = None
    ) -> dict[str, list[str]] | list[str]:
        if identifier is None:
            return cls._names
        return cls._names[identifier]

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
    identifier: str = AppIdentity.app_name

    def __call__(self, data: Any) -> str:
        return json.dumps(
            data, indent=2, ensure_ascii=False
        )  # ensure_ascii==False allows unicode


class YAMLFormat(BaseFormat):
    name: str = "yaml"
    conventions: tuple[str] = ("yml", "yaml")
    pattern: str = r"^ya?ml$"
    identifier: str = AppIdentity.app_name

    def __call__(self, data: Any) -> str:
        return yaml.dump(data, indent=2, allow_unicode=True, sort_keys=False)


class CSVFormat(BaseFormat):
    name: str = "csv"
    conventions: tuple[str] = (name,)
    pattern: str = r"^csv$"
    identifier: str = AppIdentity.app_name

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
    identifier: str = AppIdentity.app_name

    def __call__(self, data: Any) -> str:
        return str(data)


class _FormatInstantiator(BaseModel):
    language: str
    identifier: str

    def __call__(self) -> BaseFormat:
        try:
            supported_formatters = BaseFormat.supported_formatters()[self.identifier]
        except KeyError as e:
            raise KeyError(
                f"Plugin '{self.identifier}' not found in registered "
                f"{BaseFormat.supported_formatters.__name__} dictionary!"
            ) from e
        for pattern, formatter in supported_formatters.items():
            if re.match(rf"{pattern or ''}", self.language, flags=re.IGNORECASE):
                return formatter
        raise FormatError(
            f"'{self.language}' isn't a supported language format! "
            f"Supported formats for plugin '{self.identifier}' are: "
            f"{BaseFormat.supported_formatter_names(self.identifier)}."
        )


def get_formatter(language: str, /, *, identifier: str) -> BaseFormat:
    return _FormatInstantiator(language=language, identifier=identifier)()
