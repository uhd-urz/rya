import logging
import platform
from collections.abc import Callable
from typing import ClassVar, Optional

import typer
from pydantic import BaseModel, ConfigDict

from ..core_validators import Exit
from ..loggers import get_logger
from ..names import AppIdentity
from ..plugins.commons import Typer
from ..utils import PythonVersionCheckFailed, add_message, get_external_python_version
from ._plugin_handler import ExternalPluginHandler, InternalPluginHandler, PluginInfo

logger = get_logger()


def disable_plugin(
    main_app: Typer,
    /,
    *,
    plugin_name: str,
    err_msg: str,
    panel_name: str,
    short_reason: Optional[str] = None,
):
    add_message(err_msg, logging.WARNING)
    for i, registered_app in enumerate(main_app.registered_groups):
        if plugin_name == registered_app.typer_instance.info.name:
            main_app.registered_groups.pop(i)
            break
    help_message = (
        f"🚫️ Disabled{' due to ' + short_reason if short_reason is not None else ''}. "
        f"See `--help` or log file to know more."
    )

    @main_app.command(
        name=plugin_name,
        rich_help_panel=panel_name,
        help=help_message,
    )
    def name_conflict_error():
        logger.error(err_msg)
        raise Exit(1)


class PluginLoader(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _internal_plugins_loaded: ClassVar[bool] = False
    _external_plugins_loaded: ClassVar[bool] = False
    loading_errors: ClassVar[bool] = False
    reserved_plugin_names: ClassVar[list[str]] = ["version", AppIdentity.app_name]
    loaded_internal_plugins: ClassVar[dict[str, typer.Typer]] = {}
    loaded_external_plugins: ClassVar[dict[str, PluginInfo]] = {}
    commands_to_skip_cli_startup: ClassVar[list] = []
    typer_app: typer.Typer
    internal_plugins_panel_name: str
    external_plugins_panel_name: str

    def add_internal_plugins(self, callback: Callable) -> None:
        if PluginLoader._internal_plugins_loaded is True:
            logger.debug(
                f"{AppIdentity.app_name} internal plugins were loaded once. "
                f"It will not be loaded again "
                f"unless 'PluginLoader._internal_plugins_loaded' is reset to False."
            )
            return
        logger.debug(f"{AppIdentity.app_name} will load internal plugins.")
        for inter_app_obj in InternalPluginHandler.get_typer_apps():
            if inter_app_obj is not None:
                app_name = inter_app_obj.info.name
                PluginLoader.loaded_internal_plugins[app_name] = inter_app_obj
                PluginLoader.commands_to_skip_cli_startup.append(
                    inter_app_obj.info.name
                )
                self.typer_app.add_typer(
                    inter_app_obj,
                    rich_help_panel=self.internal_plugins_panel_name,
                    callback=callback,
                )

    def add_external_plugins(
        self, callback: Callable, result_callback: Callable
    ) -> None:
        if PluginLoader._external_plugins_loaded is True:
            logger.debug(
                f"{AppIdentity.app_name} external plugins were loaded once. "
                f"It will not be loaded again "
                f"unless 'PluginLoader._external_plugins_loaded' is reset to False."
            )
            return
        logger.debug(f"{AppIdentity.app_name} will load external plugins.")
        for plugin_info in ExternalPluginHandler.get_typer_apps(
            PluginLoader.loading_errors
        ):
            if plugin_info is not None:
                ext_app_obj, _path, _venv, _proj_dir = plugin_info
            else:
                continue
            if ext_app_obj is not None:
                original_name: str = ext_app_obj.info.name
                ext_app_name: str = original_name.lower()
                if ext_app_name in PluginLoader.loaded_external_plugins:
                    error_message = (
                        f"Plugin name '{original_name}' from {_path} conflicts with an "
                        f"existing third-party plugin from "
                        f"{PluginLoader.loaded_external_plugins[ext_app_name].path}. "
                        f"Please rename the plugin."
                    )
                    error_message += (
                        " Note, plugin names are case-insensitive."
                        if original_name != ext_app_name
                        else ""
                    )
                    disable_plugin(
                        self.typer_app,
                        plugin_name=ext_app_name,
                        err_msg=error_message,
                        panel_name=self.external_plugins_panel_name,
                        short_reason="naming conflict",
                    )
                elif ext_app_name in PluginLoader.loaded_internal_plugins:
                    error_message = (
                        f"Plugin name '{original_name}' from {_path} "
                        f"conflicts with an "
                        f"existing built-in plugin name. "
                        f"Please rename the plugin."
                    )
                    error_message += (
                        " Note, plugin names are case-insensitive."
                        if original_name != ext_app_name
                        else ""
                    )
                    disable_plugin(
                        self.typer_app,
                        plugin_name=ext_app_name,
                        err_msg=error_message,
                        panel_name=self.internal_plugins_panel_name,
                        short_reason="naming conflict",
                    )
                elif ext_app_name in PluginLoader.reserved_plugin_names:
                    error_message = (
                        f"Plugin name '{original_name}' from {_path} "
                        f"conflicts with a reserved name. "
                        f"Please rename the plugin."
                    )
                    error_message += (
                        " Note, plugin names are case-insensitive."
                        if original_name != ext_app_name
                        else ""
                    )
                    disable_plugin(
                        self.typer_app,
                        plugin_name=ext_app_name,
                        err_msg=error_message,
                        panel_name=self.external_plugins_panel_name,
                        short_reason="naming conflict",
                    )
                else:
                    if _venv is not None:
                        try:
                            external_plugin_python_version = (
                                get_external_python_version(venv_dir=_venv)[:2]
                            )
                        except PythonVersionCheckFailed as e:
                            error_message = (
                                f"Plugin name '{original_name}' from {_path} uses "
                                f"virtual environment "
                                f"{_venv} whose own Python version could not "
                                f"be determined for the following reason: "
                                f"{e}. Plugin will be disabled."
                            )
                            disable_plugin(
                                self.typer_app,
                                plugin_name=ext_app_name,
                                err_msg=error_message,
                                panel_name=self.external_plugins_panel_name,
                                short_reason="undetermined .venv Python version",
                            )
                            continue
                        else:
                            if external_plugin_python_version != (
                                own_python_version := platform.python_version_tuple()[
                                    :2
                                ]
                            ):
                                error_message = (
                                    f"Plugin name '{original_name}' from {_path} "
                                    f"uses virtual environment "
                                    f"{_venv} whose Python version (major and minor) "
                                    f"'{'.'.join(external_plugin_python_version)}' "
                                    f"does not match {AppIdentity.app_name}'s own Python version "
                                    f"'{'.'.join(own_python_version)}'. "
                                    f"Plugin will be disabled."
                                )
                                disable_plugin(
                                    self.typer_app,
                                    plugin_name=ext_app_name,
                                    err_msg=error_message,
                                    panel_name=self.external_plugins_panel_name,
                                    short_reason=".venv Python version conflict",
                                )
                                continue
                    PluginLoader.loaded_external_plugins[ext_app_name] = PluginInfo(
                        ext_app_obj, _path, _venv, _proj_dir
                    )
                    PluginLoader.commands_to_skip_cli_startup.append(ext_app_name)
                    self.typer_app.add_typer(
                        ext_app_obj,
                        rich_help_panel=self.external_plugins_panel_name,
                        callback=callback,
                        result_callback=result_callback,
                    )
