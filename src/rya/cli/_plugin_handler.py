import importlib.util
import logging
import os
import sys
from collections import namedtuple
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

import typer
from dynaconf.vendor.ruamel.yaml.scanner import ScannerError
from dynaconf.vendor.tomllib import TOMLDecodeError
from properpath import P

from ..configuration import (
    DynaConfArgs,
    ExternalPluginLoaderDefinitions,
    ExternalPluginMetadataDefinitions,
    InternalPluginLoaderDefinitions,
    get_dynaconf_core_loader,
    get_dynaconf_settings,
)
from ..core_validators import Validate, ValidationError, Validator
from ..loggers import get_logger
from ..plugins import __PACKAGE_IDENTIFIER__ as PLUGIN_PACKAGE
from ..utils import add_message
from ._venv_state_manager import switch_venv_state

logger = get_logger()
PluginInfo = namedtuple("PluginInfo", ["plugin_app", "path", "venv", "project_dir"])
int_plugin_def = InternalPluginLoaderDefinitions()
ext_plugin_def = ExternalPluginLoaderDefinitions()
ext_plugin_meta = ExternalPluginMetadataDefinitions()


class InternalPluginHandler:
    @classmethod
    def get_plugin_locations(cls) -> List[Tuple[str, Path]]:
        _paths = []
        for path in (
            int_plugin_def.root_installation_dir / int_plugin_def.directory_name
        ).iterdir():
            if path.is_dir():
                if (path / int_plugin_def.typer_app_file_name).exists():
                    _paths.append((path.name, path))
        return _paths

    @classmethod
    def get_typer_apps(cls) -> Generator[typer.Typer | None, None, None]:
        for plugin_name, path in cls.get_plugin_locations():
            spec = importlib.util.spec_from_file_location(
                plugin_name,
                path / int_plugin_def.typer_app_file_name,
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            module.__package__ = f"{PLUGIN_PACKAGE}.{plugin_name}"
            # Python will find the module relative to the __package__ path,
            # without this module.__package__ modification, Python will throw an ImportError.
            spec.loader.exec_module(module)
            try:
                yield getattr(module, int_plugin_def.typer_app_var_name)
            except AttributeError:
                yield None


class ExternalPluginLocationValidator(Validator):
    def __init__(self, location: Union[str, Path, P], /):
        self.location = location

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if not isinstance(value, P):
            try:
                value = P(value)
            except ValueError as e:
                raise ValueError(
                    f"'location' attribute for class {self.__class__.__class__} "
                    f"is invalid."
                ) from e
        self._location = value

    def validate(self):
        parsed_metadata: dict = {
            ext_plugin_meta.file_exists: None,
            ext_plugin_meta.cli_script_path: None,
            ext_plugin_meta.plugin_name: None,
        }

        if self.location.is_dir():
            actual_cwd = Path.cwd()
            os.chdir(self.location)

            if (
                plugin_metadata_file := (self.location / ext_plugin_def.file_name)
            ).exists():
                parsed_metadata[ext_plugin_meta.file_exists] = True
                plugin_settings_args = DynaConfArgs(
                    settings_files=[str(plugin_metadata_file)],
                    core_loaders=list(
                        get_dynaconf_core_loader(ext_plugin_def.file_ext)
                    ),
                )
                plugin_settings = get_dynaconf_settings(plugin_settings_args)
                try:
                    plugin_settings.reload()
                except (ScannerError, TOMLDecodeError) as e:
                    raise ValidationError(
                        f"Plugin metadata file {plugin_metadata_file} exists, "
                        f"but it couldn't be parsed. Exception details: {e}"
                    )
                else:
                    try:
                        cli_script_path = plugin_settings[
                            ext_plugin_meta.cli_script_path
                        ]
                    except KeyError:
                        if (
                            typer_app_file := (
                                self.location / ext_plugin_def.typer_app_file_name
                            )
                        ).exists():
                            parsed_metadata[ext_plugin_meta.cli_script_path] = (
                                typer_app_file
                            )
                        else:
                            raise ValidationError(
                                f"{self.location} has the plugin metadata file, but no "
                                f"'{ext_plugin_meta.cli_script_path}' path is "
                                f"defined inside. No "
                                f"{ext_plugin_def.typer_app_file_name} script is found as well."
                            )
                    else:
                        try:
                            cli_script_path = P(cli_script_path)
                        except (TypeError, ValueError):
                            raise ValidationError(
                                f"Key '{ext_plugin_meta.cli_script_path}' "
                                f"exists in {plugin_metadata_file}, but its assigned "
                                f"value '{cli_script_path}' is invalid."
                            )
                        else:
                            if cli_script_path.exists():
                                parsed_metadata[ext_plugin_meta.cli_script_path] = (
                                    cli_script_path.absolute()
                                )
                            else:
                                raise ValidationError(
                                    f"Key '{ext_plugin_meta.cli_script_path}' "
                                    f"exists in {plugin_metadata_file}, but the path "
                                    f"'{cli_script_path}' does not exist."
                                )
                    try:
                        venv_path = plugin_settings[ext_plugin_meta.venv_path]
                    except KeyError:
                        parsed_metadata[ext_plugin_meta.venv_path] = None
                    else:
                        try:
                            venv_path = P(venv_path)
                        except (TypeError, ValueError):
                            raise ValidationError(
                                f"Key '{ext_plugin_meta.venv_path}' "
                                f"exists in {plugin_metadata_file}, but its assigned "
                                f"value '{venv_path}' is invalid."
                            )
                        else:
                            if venv_path.exists():
                                parsed_metadata[ext_plugin_meta.venv_path] = (
                                    venv_path.absolute()
                                )
                            else:
                                raise ValidationError(
                                    f"Key '{ext_plugin_meta.venv_path}' "
                                    f"exists in {plugin_metadata_file}, but the path "
                                    f"'{venv_path}' does not exist."
                                )
                    try:
                        project_path = plugin_settings[ext_plugin_meta.project_path]
                    except KeyError:
                        parsed_metadata[ext_plugin_meta.project_path] = parsed_metadata[
                            ext_plugin_meta.cli_script_path
                        ].parent
                    else:
                        try:
                            project_path = P(project_path)
                        except (TypeError, ValueError):
                            raise ValidationError(
                                f"Key '{ext_plugin_meta.project_path}' "
                                f"exists in {plugin_metadata_file}, but its assigned "
                                f"value '{project_path}' is invalid."
                            )
                        else:
                            if project_path.exists():
                                parsed_metadata[ext_plugin_meta.project_path] = (
                                    project_path.absolute()
                                )
                            else:
                                raise ValidationError(
                                    f"Key '{ext_plugin_meta.project_path}' "
                                    f"exists in {plugin_metadata_file}, but the path "
                                    f"'{project_path}' does not exist."
                                )
                    try:
                        plugin_name = plugin_settings[ext_plugin_meta.plugin_name]
                    except KeyError:
                        parsed_metadata[ext_plugin_meta.plugin_name] = (
                            self.location.name
                        )
                    else:
                        if self.location.name != plugin_name:
                            raise ValidationError(
                                f"Key '{ext_plugin_meta.plugin_name}' "
                                f"exists in {plugin_metadata_file}, but it must be the same "
                                f"name as the directory name the metadata file is in."
                            )
                        parsed_metadata[ext_plugin_meta.plugin_name] = plugin_name
            else:
                parsed_metadata[ext_plugin_meta.file_exists] = False
                if (
                    typer_app_file := (
                        self.location / ext_plugin_def.typer_app_file_name
                    )
                ).exists():
                    parsed_metadata[ext_plugin_meta.cli_script_path] = typer_app_file
                    parsed_metadata[ext_plugin_meta.project_path] = self.location
                    plugin_name = self.location.name
                    parsed_metadata[ext_plugin_meta.plugin_name] = plugin_name
                else:
                    raise ValueError(
                        f"{self.location} is not a proper plugin directory."
                    )
            os.chdir(actual_cwd)
        else:
            raise ValueError(f"{self.location} is not a directory.")
        return parsed_metadata


class ExternalPluginHandler:
    @staticmethod
    def get_plugin_metadata(
        loading_errors: bool = False,
    ) -> Generator[Optional[dict], None, None]:
        plugin_paths: list[P] = [
            p
            for p in ext_plugin_def.dir.iterdir()
            if not p.name.startswith(".") and p.kind == "dir"
        ]
        try:
            for path in sorted(plugin_paths, key=lambda x: str(x).lower()):
                try:
                    metadata = Validate(ExternalPluginLocationValidator(path)).get()
                except ValidationError as e:
                    logger.debug(str(e))
                    if loading_errors is True:
                        raise e
                    add_message(str(e))
                    continue
                except ValueError as e:
                    logger.debug(str(e))
                    if loading_errors is True:
                        raise e
                    continue
                else:
                    metadata[ext_plugin_meta.plugin_root_dir] = path
                    yield metadata
        except FileNotFoundError:
            yield None

    @staticmethod
    def load_plugin(plugin_name: str, cli_script: Path, project_dir: Path):
        spec = importlib.util.spec_from_file_location(
            plugin_name, cli_script, submodule_search_locations=[str(project_dir)]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        module.__package__ = plugin_name
        # Python will find a module relative to the __package__ path,
        # without this module.__package__ change Python will throw an ImportError.
        spec.loader.exec_module(module)
        return module

    @classmethod
    def get_typer_apps(
        cls, loading_errors: bool = False
    ) -> Generator[Optional[PluginInfo], None, None]:
        for metadata in cls.get_plugin_metadata(loading_errors):
            if metadata is None:
                break
            plugin_name: str = metadata[ext_plugin_meta.plugin_name]
            cli_script: Path = metadata[ext_plugin_meta.cli_script_path]
            plugin_root_dir: Path = metadata[ext_plugin_meta.plugin_root_dir]
            project_dir: Path = metadata[ext_plugin_meta.project_path]
            if metadata[ext_plugin_meta.file_exists] is False:
                try:
                    module = cls.load_plugin(plugin_name, cli_script, project_dir)
                except (Exception, BaseException) as e:
                    if loading_errors is True:
                        raise e
                    message: str = (
                        f"An exception occurred while trying to load a local "
                        f"plugin '{plugin_name}' in path {cli_script}. "
                        f"Plugin '{plugin_name}' will be ignored. "
                        f'Exception details: "{e.__class__.__name__}: {e}"'
                    )
                    add_message(message, logging.WARNING)
                    yield
                else:
                    try:
                        typer_app: typer.Typer = getattr(
                            module,
                            ext_plugin_def.typer_app_var_name,
                        )
                    except AttributeError:
                        yield
                    else:
                        typer_app.info.name = plugin_name
                        yield PluginInfo(
                            typer_app,
                            plugin_root_dir,
                            None,
                            project_dir,
                        )
            else:
                venv_dir: Path = metadata[ext_plugin_meta.venv_path]
                if venv_dir is not None:
                    try:
                        switch_venv_state(True, venv_dir, project_dir)
                    except (ValueError, RuntimeError) as e:
                        message: str = (
                            f"An exception occurred while trying to load a local "
                            f"plugin '{plugin_name}' with virtual environment {venv_dir} "
                            f"in path {cli_script}. "
                            f"Plugin '{plugin_name}' will be ignored. "
                            f'Exception details: "{e.__class__.__name__}: {e}"'
                        )
                        add_message(message, logging.WARNING)
                        yield
                    else:
                        try:
                            module = cls.load_plugin(
                                plugin_name, cli_script, project_dir
                            )
                        except (Exception, BaseException) as e:
                            if loading_errors is True:
                                raise e
                            message: str = (
                                f"An exception occurred while trying to load a local "
                                f"plugin '{plugin_name}' with virtual environment {venv_dir} "
                                f"in path {cli_script}. "
                                f"Plugin '{plugin_name}' will be ignored. "
                                f'Exception details: "{e.__class__.__name__}: {e}"'
                            )
                            add_message(message, logging.WARNING)
                            yield
                        else:
                            try:
                                typer_app: typer.Typer = getattr(
                                    module,
                                    ext_plugin_def.typer_app_var_name,
                                )
                            except AttributeError:
                                yield
                            else:
                                switch_venv_state(False, venv_dir, project_dir)
                                typer_app.info.name = plugin_name
                                yield PluginInfo(
                                    typer_app, plugin_root_dir, venv_dir, project_dir
                                )
                else:
                    try:
                        module = cls.load_plugin(plugin_name, cli_script, project_dir)
                    except (Exception, BaseException) as e:
                        # Catching all exceptions here is meant for protecting
                        # the main app from failing from external plugins.
                        if loading_errors is True:
                            raise e
                        message: str = (
                            f"An exception occurred while trying to load a local "
                            f"plugin '{plugin_name}' in path {cli_script}. "
                            f"Plugin '{plugin_name}' will be ignored. "
                            f'Exception details: "{e.__class__.__name__}: {e}"'
                        )
                        add_message(message, logging.WARNING)
                        yield
                    else:
                        try:
                            typer_app: typer.Typer = getattr(
                                module,
                                ext_plugin_def.typer_app_var_name,
                            )
                        except AttributeError:
                            yield
                        else:
                            typer_app.info.name = plugin_name
                            yield PluginInfo(
                                typer_app, plugin_root_dir, None, project_dir
                            )
