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
    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH,
    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS,
    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME,
    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH,
    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH,
    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME,
    EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR,
    EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME,
    DynaConfArgs,
    get_dynaconf_core_loader,
    get_dynaconf_settings,
)
from ..configuration.config import (
    EXTERNAL_LOCAL_PLUGIN_DIR,
    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_EXT,
    EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME,
    INTERNAL_PLUGIN_DIRECTORY_NAME,
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME,
    INTERNAL_PLUGIN_TYPER_APP_VAR_NAME,
    ROOT_INSTALLATION_DIR,
)
from ..core_validators import Validate, ValidationError, Validator
from ..loggers import get_logger
from ..plugins import __PACKAGE_IDENTIFIER__ as plugins_sub_plugin_name
from ..utils import add_message
from ._venv_state_manager import switch_venv_state

logger = get_logger()
PluginInfo = namedtuple("PluginInfo", ["plugin_app", "path", "venv", "project_dir"])


class InternalPluginHandler:
    @classmethod
    def get_plugin_locations(cls) -> List[Tuple[str, Path]]:
        _paths = []
        for path in (ROOT_INSTALLATION_DIR / INTERNAL_PLUGIN_DIRECTORY_NAME).iterdir():
            if path.is_dir():
                if (path / INTERNAL_PLUGIN_TYPER_APP_FILE_NAME).exists():
                    _paths.append((path.name, path))
        return _paths

    @classmethod
    def get_typer_apps(cls) -> Generator[typer.Typer | None, None, None]:
        for plugin_name, path in cls.get_plugin_locations():
            spec = importlib.util.spec_from_file_location(
                plugin_name,
                path / INTERNAL_PLUGIN_TYPER_APP_FILE_NAME,
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            module.__package__ = f"{plugins_sub_plugin_name}.{plugin_name}"  # Python will find module relative to __package__ path,
            # without this module.__package__ change Python will throw an ImportError.
            spec.loader.exec_module(module)
            try:
                yield getattr(module, INTERNAL_PLUGIN_TYPER_APP_VAR_NAME)
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
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS: None,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH: None,
            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME: None,
        }

        if self.location.is_dir():
            actual_cwd = Path.cwd()
            os.chdir(self.location)

            if (
                plugin_metadata_file := (
                    self.location / EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME
                )
            ).exists():
                parsed_metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS] = (
                    True
                )
                plugin_settings_args = DynaConfArgs(
                    settings_files=[str(plugin_metadata_file)],
                    core_loaders=list(
                        get_dynaconf_core_loader(
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_EXT
                        )
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
                        CLI_SCRIPT_PATH = plugin_settings[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                        ]
                    except KeyError:
                        if (
                            external_local_plugin_typer_app_file := (
                                self.location
                                / EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME
                            )
                        ).exists():
                            parsed_metadata[
                                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                            ] = external_local_plugin_typer_app_file
                        else:
                            raise ValidationError(
                                f"{self.location} has the plugin metadata file, but no "
                                f"'{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH}' path is "
                                f"defined inside. No "
                                f"{EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME} script is found as well."
                            )
                    else:
                        try:
                            CLI_SCRIPT_PATH = P(CLI_SCRIPT_PATH)
                        except (TypeError, ValueError):
                            raise ValidationError(
                                f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH}' "
                                f"exists in {plugin_metadata_file}, but its assigned "
                                f"value '{CLI_SCRIPT_PATH}' is invalid."
                            )
                        else:
                            if CLI_SCRIPT_PATH.exists():
                                parsed_metadata[
                                    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                                ] = CLI_SCRIPT_PATH.absolute()
                            else:
                                raise ValidationError(
                                    f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH}' "
                                    f"exists in {plugin_metadata_file}, but the path "
                                    f"'{CLI_SCRIPT_PATH}' does not exist."
                                )
                    try:
                        VENV_PATH = plugin_settings[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                        ]
                    except KeyError:
                        VENV_PATH = parsed_metadata[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                        ] = None
                    else:
                        try:
                            VENV_PATH = P(VENV_PATH)
                        except (TypeError, ValueError):
                            raise ValidationError(
                                f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH}' "
                                f"exists in {plugin_metadata_file}, but its assigned "
                                f"value '{VENV_PATH}' is invalid."
                            )
                        else:
                            if VENV_PATH.exists():
                                parsed_metadata[
                                    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                                ] = VENV_PATH.absolute()
                            else:
                                raise ValidationError(
                                    f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH}' "
                                    f"exists in {plugin_metadata_file}, but the path "
                                    f"'{VENV_PATH}' does not exist."
                                )
                    try:
                        PROJECT_PATH = plugin_settings[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                        ]
                    except KeyError:
                        PROJECT_PATH = parsed_metadata[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                        ] = parsed_metadata[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                        ].parent
                    else:
                        try:
                            PROJECT_PATH = P(PROJECT_PATH)
                        except (TypeError, ValueError):
                            raise ValidationError(
                                f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH}' "
                                f"exists in {plugin_metadata_file}, but its assigned "
                                f"value '{PROJECT_PATH}' is invalid."
                            )
                        else:
                            if PROJECT_PATH.exists():
                                parsed_metadata[
                                    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                                ] = PROJECT_PATH.absolute()
                            else:
                                raise ValidationError(
                                    f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH}' "
                                    f"exists in {plugin_metadata_file}, but the path "
                                    f"'{PROJECT_PATH}' does not exist."
                                )
                    try:
                        PLUGIN_NAME = plugin_settings[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                        ]
                    except KeyError:
                        PLUGIN_NAME = parsed_metadata[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                        ] = self.location.name
                    else:
                        if self.location.name != PLUGIN_NAME:
                            raise ValidationError(
                                f"Key '{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME}' "
                                f"exists in {plugin_metadata_file}, but it must be the same "
                                f"name as the directory name the metadata file is in."
                            )
                        parsed_metadata[
                            EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                        ] = PLUGIN_NAME
            else:
                parsed_metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS] = (
                    False
                )
                if (
                    external_local_plugin_typer_app_file := (
                        self.location / EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME
                    )
                ).exists():
                    parsed_metadata[
                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
                    ] = external_local_plugin_typer_app_file
                    parsed_metadata[
                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
                    ] = self.location
                    PLUGIN_NAME = self.location.name
                    parsed_metadata[
                        EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
                    ] = PLUGIN_NAME
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
            for p in EXTERNAL_LOCAL_PLUGIN_DIR.iterdir()
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
                    metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR] = path
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
            plugin_name: str = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME
            ]
            cli_script: Path = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH
            ]
            plugin_root_dir: Path = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR
            ]
            project_dir: Path = metadata[
                EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH
            ]
            if metadata[EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS] is False:
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
                            module, EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME
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
                venv_dir: Path = metadata[
                    EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH
                ]
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
                                    module, EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME
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
                                module, EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME
                            )
                        except AttributeError:
                            yield
                        else:
                            typer_app.info.name = plugin_name
                            yield PluginInfo(
                                typer_app, plugin_root_dir, None, project_dir
                            )
