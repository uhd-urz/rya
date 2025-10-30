from functools import partial
from sys import argv
from typing import Optional

import click
import typer
from properpath import P
from typing_extensions import Annotated

from ..config import AppConfig
from ..core_validators import Exit
from ..loggers import (
    ResultCallbackHandler,
    get_logger,
    global_log_record_container,
)
from ..names import AppIdentity, config_file_sources
from ..plugins.commons import Typer

# noinspection PyProtectedMember
from ..plugins.commons._names import TyperArgs, TyperGlobalOptions, TyperRichPanelNames
from ..pre_utils import ConfigFileTuple
from ..styles import (
    print_typer_error,
    rich_format_help_with_callback,
)
from ..utils import (
    global_cli_graceful_callback,
    global_cli_result_callback,
    global_cli_super_startup_callback,
    messages_list,
)
from ._debug_mode import load_debug_mode
from ._message_panel import messages_panel
from ._plugin_loader import PluginLoader
from ._venv_state_manager import switch_venv_state
from .doc import MainAppCLIDoc

logger = get_logger()

load_debug_mode()


def result_callback_wrapper(_, **kwargs):
    should_skip, _ = should_skip_cli_startup()
    if should_skip:
        return
    user_result_callback()
    ctx = click.get_current_context()
    if ctx.command.name != ctx.invoked_subcommand:
        if argv[-1] != (ARG_TO_SKIP := "--help") or ARG_TO_SKIP not in argv:
            if global_cli_result_callback.get_callbacks():
                logger.debug(
                    f"Running {__package__} controlled callback with "
                    f"Typer result callback: "
                    f"{global_cli_result_callback.instance_name}"
                )
                global_cli_result_callback.call_callbacks()


typer_args = TyperArgs()
user_result_callback = typer_args.result_callback or (lambda: None)
user_callback = typer_args.callback or (lambda: None)
typer_args.result_callback = result_callback_wrapper
app = Typer(**typer_args.model_dump())
panel_names = TyperRichPanelNames()
plugin_loader = PluginLoader(
    typer_app=app,
    internal_plugins_panel_name=panel_names.internal_plugins,
    external_plugins_panel_name=panel_names.external_plugins,
)
typer_global_options = TyperGlobalOptions()


@app.callback(invoke_without_command=True)
def cli_startup(
    config_file: Annotated[
        Optional[str],
        typer.Option(
            typer_global_options.config_file[0],
            typer_global_options.config_file[1],
            help=MainAppCLIDoc.cli_startup,
            show_default=False,
            rich_help_panel=panel_names.callback,
        ),
    ] = None,
) -> None:
    should_skip, _ = should_skip_cli_startup()
    if should_skip:
        return
    user_callback()
    # GlobalCLICallback is run before configuration validation
    if global_cli_super_startup_callback.get_callbacks():
        logger.debug(
            f"Running {__package__} controlled callback before anything else: "
            f"{global_cli_super_startup_callback.instance_name}"
        )
        global_cli_super_startup_callback.call_callbacks()

    def show_aggressive_log_message():
        for log_data in messages_list:
            message, level, logger_, is_aggressive = log_data
            if is_aggressive is True:
                logger.log(level, message) if logger_ is None else logger_.log(
                    level, message
                )

    if config_file is not None:
        try:
            cli_config_file = P(config_file)
        except (ValueError, TypeError) as conf_val_exc:
            print_typer_error(str(conf_val_exc))
            raise Exit(1)
        else:
            config_file_tuple = ConfigFileTuple(
                path=cli_config_file,
                name="CLI --config-file",
            )
            if config_file_tuple not in config_file_sources:
                config_file_sources.append(config_file_tuple)
            AppConfig.dynaconf_args.settings_files.append(str(cli_config_file))
    ctx = click.get_current_context()
    if ctx.command.name != (calling_sub_command_name := ctx.invoked_subcommand):
        if argv[-1] != (arg_to_skip := "--help") or arg_to_skip not in argv:
            # If an external plugin adds a new config file to dynaconf_args,
            # it will not be validated.
            if AppConfig.validated is None:
                AppConfig.validate(errors="ignore")
            show_aggressive_log_message()
            if global_cli_graceful_callback.get_callbacks():
                logger.debug(
                    f"Running {__package__} controlled callback "
                    f"after configuration validation: "
                    f"{global_cli_graceful_callback.instance_name}"
                )
                global_cli_graceful_callback.call_callbacks()
        else:
            return
    if calling_sub_command_name is None:
        # This is where we know that the app is run as is
        if no_arg_cmd := getattr(plugin_loader.typer_app, "no_arg_command", None):
            no_arg_cmd()


def check_result_callback_log_container():
    if (
        ResultCallbackHandler.is_store_okay()
        and ResultCallbackHandler.get_client_count() == 0
    ):
        global_log_record_container.data.clear()
        ResultCallbackHandler.is_store_okay = lambda: False


def cli_switch_venv_state(state: bool, /) -> None:
    try:
        venv_dir = PluginLoader.loaded_external_plugins[
            click.get_current_context().command.name
        ].venv
        project_dir = PluginLoader.loaded_external_plugins[
            click.get_current_context().command.name
        ].project_dir
    except KeyError:
        ...
    else:
        if venv_dir is not None:
            switch_venv_state(state, venv_dir, project_dir)


def cli_startup_for_plugins(
    config_file: Annotated[
        Optional[str],
        typer.Option(
            "--config-file",
            "--C",
            help=MainAppCLIDoc.cli_startup,
            show_default=False,
            rich_help_panel=panel_names.callback,
        ),
    ] = None,
) -> None:
    cli_switch_venv_state(True)
    if config_file is not None:
        print_typer_error(
            f"--config-file/--C can only be passed after "
            f"the main program name '{AppIdentity.app_name}', "
            f"and not after a plugin name."
        )
        raise Exit(1)
    # Calling cli_startup again here would call cli_startup
    # again before loading each plugin. This is necessary because
    # whatever modifications/additions a plugin made,
    # cli_startup would need to consider them again. E.g., adding a
    # callback to global_cli_graceful_callback.
    cli_startup()


def cli_cleanup_for_third_party_plugins(*args, **kwargs):
    cli_switch_venv_state(False)


def should_skip_cli_startup() -> tuple[bool, Optional[str]]:
    try:
        if len(argv) == 2 and (running_command := argv[-1]) in getattr(
            plugin_loader.typer_app, "commands_skip_cli_startup", []
        ):
            return True, running_command
    except IndexError:
        return False, None
    return False, None


def load_plugins():
    should_skip, command = should_skip_cli_startup()
    if should_skip:
        logger.debug(f"Command '{command}' will skip any plugin loading.")
        return
    plugin_loader.add_internal_plugins(callback=cli_startup_for_plugins)
    PluginLoader._internal_plugins_loaded = True
    plugin_loader.add_external_plugins(
        callback=cli_startup_for_plugins,
        result_callback=cli_cleanup_for_third_party_plugins,
    )
    PluginLoader._external_plugins_loaded = True


# cli_startup is passed here because --help doesn't trigger cli_startup
typer.rich_utils.rich_format_help = partial(
    rich_format_help_with_callback,
    result_callback=(cli_startup, messages_panel),
)

# Must be run after all plugins are loaded as they are given
# a chance to modify ResultCallbackHandler.is_store_okay
load_plugins()
check_result_callback_log_container()
