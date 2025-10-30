import inspect
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import ClassVar, Generator, Iterable, Optional

from properpath import P

from ._utils import get_local_imports


class LayerLoader:
    _bootstrap_mode: ClassVar[bool] = False
    _root_installation_dir: ClassVar[None | P | Path] = None
    _current_layer_name: ClassVar[str] = "pre_utils"
    _app_name: ClassVar[Optional[str]] = None
    _self_app_name: ClassVar[Optional[str]] = None
    logger = logging.getLogger(__name__)

    @classmethod
    def enable_bootstrap_mode(cls, root_installation_dir: P | Path, app_name: str):
        cls._bootstrap_mode = True
        if not isinstance(root_installation_dir, Path):
            raise TypeError("root_installation_dir must be an instance of Path.")
        if not isinstance(app_name, str):
            raise TypeError("app_name must be an instance of str.")
        cls._root_installation_dir = root_installation_dir
        cls._app_name = app_name

    @classmethod
    def disable_bootstrap_mode(cls):
        cls._bootstrap_mode = False

    @classmethod
    def is_bootstrap_mode(cls) -> bool:
        return cls._bootstrap_mode

    @staticmethod
    def _filter_object_item(object_item: tuple[str, type[object]]) -> bool:
        name, object_ = object_item
        if inspect.isfunction(object_):
            return False
        if object_ is LayerLoader or isinstance(object_, LayerLoader):
            return False
        if name == "__app_name":
            return False
        return True

    @classmethod
    def get_self_imported_objects(
        cls, globals_: dict, /
    ) -> Generator[tuple[str, type[object]], None, None]:
        imports = get_local_imports(globals_)
        for package_name, objects in imports.items():
            if package_name.startswith(f"{cls._self_app_name}."):
                yield from filter(cls._filter_object_item, objects.items())

    @classmethod
    def _load_module(cls, layer_name: str) -> ModuleType:
        module_name = __package__.replace(cls._self_app_name, cls._app_name).replace(
            cls._current_layer_name, layer_name
        )
        imported_module = sys.modules.get(module_name) or sys.modules.get(
            f"src.{module_name}"
        )
        return imported_module

    @classmethod
    def load_layers(cls, globals_: dict, /, layer_names: Iterable[str]) -> None:
        if isinstance(layer_names, str) or not isinstance(layer_names, Iterable):
            raise TypeError("layer_names must be an iterable of strings.")
        for layer_name in layer_names:
            layer = cls._load_module(layer_name)
            for object_name, object_ in cls.get_self_imported_objects(globals_):
                try:
                    attr = getattr(layer, object_name)
                except AttributeError:
                    continue
                else:
                    globals_[object_name] = attr
                    cls.logger.debug(
                        f"Attribute'{object_name}' is overloaded "
                        f"from layer '{layer_name}'."
                    )
