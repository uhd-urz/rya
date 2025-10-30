import inspect
import sys
from abc import ABC
from enum import StrEnum
from types import ModuleType
from typing import Callable, Optional, get_type_hints

from pydantic import BaseModel, create_model

LocalImportsType = dict[str, dict[str, type[object] | Callable | ModuleType]]


def is_platform_unix() -> bool:
    return sys.platform in ("linux", "darwin")


def generate_pydantic_model_from_abstract_cls(
    abs_cls: type[ABC], /, exclude: Optional[tuple[str]] = None
) -> type[BaseModel]:
    exclude = exclude or ()
    abs_fields: dict[str, tuple[type, ...]] = {}
    abs_methods = [_ for _ in abs_cls.__abstractmethods__ if _ not in exclude]
    for abs_method_name in abs_methods:
        abs_cls_attribute = getattr(abs_cls, abs_method_name)
        if isinstance(abs_cls_attribute, property):
            abs_cls_attribute = abs_cls_attribute.fget
        attribute_return_type = get_type_hints(abs_cls_attribute).get("return")
        if attribute_return_type is None:
            raise ValueError(
                f"Abstract class {abs_cls}'s abstract method '{abs_method_name}' "
                f"must have a return type annotation."
            )
        # noinspection PyTypeChecker
        abs_fields[abs_method_name] = (attribute_return_type, ...)
    return create_model(f"{abs_cls.__name__}Attrs", **abs_fields)


def get_local_imports(
    globals_: dict, /, include_modules: Optional[list[type[object] | ModuleType]] = None
) -> LocalImportsType:
    include_modules = include_modules or []
    local_imports: LocalImportsType = {}

    for name, obj in globals_.items():
        module = inspect.getmodule(obj)
        if module is not None:
            if (
                module.__name__ != __name__
                and not module.__name__.startswith("__")
                and not inspect.isbuiltin(obj)
                and module.__name__ != "builtins"
            ):
                try:
                    local_imports[module.__name__]
                except KeyError:
                    local_imports[module.__name__] = {}
                if inspect.ismodule(obj):
                    if obj in include_modules:
                        local_imports[module.__name__][name] = obj
                    continue
                local_imports[module.__name__][name] = obj
    return local_imports


def get_dynaconf_core_loader(
    config_file_extension: str,
) -> tuple[str]:
    class SupportedDynaconfCoreLoaders(StrEnum):
        YAML = "YAML"
        YML = "YAML"
        TOML = "TOML"
        JSON = "JSON"
        INI = "INI"

    supported_core_loaders = SupportedDynaconfCoreLoaders.__members__
    for e in supported_core_loaders:
        if e == config_file_extension.upper():
            return (str(supported_core_loaders[e]),)
    raise ValueError(
        f"Unsupported config file extension: '{config_file_extension}'. "
        f"Supported configuration extensions are: "
        f"{', '.join(supported_core_loaders)}."
    )
