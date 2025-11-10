from sys import argv
from typing import Callable, Optional

import click
from click import Context
from pydantic import BaseModel

from ..config import AppConfig

# noinspection PyProtectedMember
from ..config._model_handler import NoConfigModelRegistrationFound
from ..loggers import get_logger
from ..names import run_early_list
from ..plugins.commons import Typer
from ..pre_utils import ResultCallbackHandler, global_log_record_container
from ._plugin_handler import ext_plugin_def
from ._plugin_loader import PluginLoader
from ._venv_state_manager import switch_venv_state

logger = get_logger()


def validate_configuration() -> BaseModel:
    validated_config = AppConfig.validate(errors="ignore", reload=True)
    if AppConfig.exceptions:
        for exc in AppConfig.exceptions:
            if not isinstance(exc, NoConfigModelRegistrationFound):
                logger.debug(
                    "Not all configuration models were validated successfully. "
                    "An incomplete or configuration model was used."
                )
                break
        else:
            logger.debug(
                "The registered configuration models were validated successfully, "
                "but not all plugins or main app registered configuration models."
            )
    else:
        logger.debug("All configuration models were validated successfully.")
    return validated_config


def load_plugins(
    plugin_loader: PluginLoader,
    cli_startup_for_plugins: Callable,
    cli_cleanup_for_third_party_plugins: Callable,
) -> None:
    plugin_loader.add_internal_plugins(callback=cli_startup_for_plugins)
    PluginLoader._internal_plugins_loaded = True
    if ext_plugin_def.dir is None:
        logger.debug(
            f"{ext_plugin_def.__class__.__name__} attribute 'dir' is None. "
            f"Loading {ext_plugin_def.name} plugins will be skipped."
        )
        return
    plugin_loader.add_external_plugins(
        callback=cli_startup_for_plugins,
        result_callback=cli_cleanup_for_third_party_plugins,
    )
    PluginLoader._external_plugins_loaded = True


def should_skip_cli_startup(
    typer_app: Typer,
    click_context: Optional[Context] = None,
) -> tuple[bool, Optional[str]]:
    try:
        running_command_name = argv[-1]
    except IndexError:
        return False, None
    else:
        if len(argv) == 2 and running_command_name in getattr(
            typer_app, "commands_skip_cli_startup", []
        ):
            return True, running_command_name
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


def call_run_early_list() -> None:
    if run_early_list:
        logger.debug("run_early_list is non-empty. Early validation will be performed.")
        early_validated_config = validate_configuration()
        for func in run_early_list:
            func(early_validated_config)


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
