from sys import argv
from typing import Callable, Optional

import click
from click import Context

from ..loggers import get_logger
from ..pre_utils import ResultCallbackHandler, global_log_record_container
from ._plugin_loader import PluginLoader
from ._venv_state_manager import switch_venv_state

logger = get_logger()


def load_plugins(
    plugin_loader: PluginLoader,
    cli_startup_for_plugins: Callable,
    cli_cleanup_for_third_party_plugins: Callable,
) -> None:
    should_skip, command = should_skip_cli_startup(plugin_loader)
    if not is_run_with_help_arg():
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


def should_skip_cli_startup(
    plugin_loader: PluginLoader,
    click_context: Optional[Context] = None,
) -> tuple[bool, Optional[str]]:
    if is_run_with_help_arg(click_context):
        return True, None
    try:
        running_command_name = argv[-1]
    except IndexError:
        return False, None
    else:
        if click_context is not None:
            is_no_arg_is_help = getattr(
                click_context.command,
                "no_args_is_help",
                False,
            )
            invoked_subcommand = click_context.invoked_subcommand
            if invoked_subcommand is None and is_no_arg_is_help is True:
                return True, invoked_subcommand
            else:
                return False, None
        else:
            if len(argv) == 2 and running_command_name in getattr(
                plugin_loader.typer_app,
                "commands_skip_cli_startup",
                [],
            ):
                return True, running_command_name
            return False, None


def is_run_with_help_arg(click_context: Optional[Context] = None) -> bool:
    if click_context is None:
        return "--help" in argv
    return any(help_arg in argv for help_arg in click_context.help_option_names)


def check_result_callback_log_container() -> None:
    if (
        ResultCallbackHandler.is_store_okay()
        and ResultCallbackHandler.get_client_count() == 0
    ):
        global_log_record_container.data.clear()
        ResultCallbackHandler.disable_store_okay()


def cli_switch_venv_state(state: bool, /) -> None:
    ctx = click.get_current_context()
    try:
        venv_dir, project_dir = (
            PluginLoader.loaded_external_plugins[ctx.command.name].venv,
            PluginLoader.loaded_external_plugins[ctx.command.name].project_dir,
        )
    except KeyError:
        pass
    else:
        if venv_dir is not None:
            switch_venv_state(state, venv_dir, project_dir)


def cli_cleanup_for_external_plugins(*args, **kwargs) -> None:
    cli_switch_venv_state(False)
