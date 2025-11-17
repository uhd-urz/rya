from typing import Optional

import click
import typer
from properpath import P
from typing_extensions import Annotated

from ..config import AppConfig, ConfigMaker

# noinspection PyProtectedMember
from ..core_validators import Exit
from ..loggers import get_logger
from ..names import AppIdentity, config_file_sources, run_early_list
from ..plugins.commons import Typer

# noinspection PyProtectedMember
from ..plugins.commons._names import (
    TyperGlobalOptions,
    TyperRichPanelNames,
)
from ..pre_utils import ConfigFileTuple, DebugMode
from ..styles import (
    print_typer_error,
)
from ..utils import (
    global_cli_graceful_callback,
    global_cli_super_startup_callback,
    messages_list,
)
from ._app_util import user_callback
from ._cli_handler_utils import (
    call_run_early_list,
    check_result_callback_log_container,
    cli_cleanup_for_external_plugins,
    cli_switch_venv_state,
    is_run_with_help_arg,
    load_plugins,
    should_skip_cli_startup,
    validate_configuration,
)
from ._click_help import apply_click_typer_help_patch
from ._message_panel import messages_panel
from ._plugin_loader import PluginLoader
from .doc import MainAppCLIDoc

logger = get_logger()


def initiate_cli_startup(app: Typer):
    DebugMode(AppIdentity.app_name).load(reload=True, verbose=False)
    # noinspection PyPep8Naming
    CLIConfigFileType = Annotated[
        Optional[str],
        typer.Option(
            TyperGlobalOptions.config_file[0],
            TyperGlobalOptions.config_file[1],
            help=MainAppCLIDoc.config_file,
            show_default=False,
            rich_help_panel=TyperRichPanelNames.callback,
        ),
    ]

    @app.callback(invoke_without_command=True)
    def cli_startup(config_file: CLIConfigFileType = None) -> None:
        ctx = click.get_current_context()
        should_skip, _ = should_skip_cli_startup(app, ctx)  # ctx is not None here
        if is_run_with_help_arg(ctx) or should_skip:
            return
        global_options = {"global_options": {"config_file": config_file}}
        user_callback(**global_options)
        # GlobalCLICallback is run before configuration validation
        logger.debug("Running global callbacks at the CLI startup.")
        global_cli_super_startup_callback.call_callbacks()

        def show_aggressive_log_message():
            for log_data in messages_list:
                message, level, logger_, is_aggressive = log_data
                if is_aggressive is True:
                    logger.log(level, message) if logger_ is None else logger_.log(
                        level, message
                    )

        cli_config_file_name: str = "CLI --config-file"
        if config_file is not None:
            try:
                cli_config_file = P(config_file)
            except (ValueError, TypeError) as conf_val_exc:
                print_typer_error(str(conf_val_exc))
                raise Exit(1)
            else:
                cli_config_file = cli_config_file.absolute()
                config_file_tuple = ConfigFileTuple(
                    path=cli_config_file,
                    name=cli_config_file_name,
                )
                if config_file_tuple not in config_file_sources:
                    config_file_sources.append(config_file_tuple)
                AppConfig.dynaconf_args.settings_files.append(str(cli_config_file))
                logger.debug(
                    f"The following config files will be used: "
                    f"{', '.join(AppConfig.dynaconf_args.settings_files)}"
                )
        # If an external/internal plugin adds a new config file to dynaconf_args,
        # it will not be validated (i.e., validation is only performed once).
        # Internal plugins should rely on a fixed number of config files added
        # in the names/ layer. External plugins should perform the
        # validation themselves.
        calling_sub_command_name = ctx.invoked_subcommand
        if (
            AppConfig.validated is None
            or len(ConfigMaker.get_all_models()) > 1
            or config_file is not None
        ):
            if run_early_list:
                logger.debug(
                    "run_early_list is not empty. run_early_list functions did "
                    "not get the latest validated configuration model."
                )
            validate_configuration()
        show_aggressive_log_message()
        logger.debug("Running global callbacks after configuration validation.")
        global_cli_graceful_callback.call_callbacks()
        if calling_sub_command_name is None:
            # This is where we know that the app is run with no sub-commands or options
            if no_arg_cmd := getattr(app, "no_arg_command", None):
                no_arg_cmd(**global_options)

    Typer.add_cli_help_callback(cli_startup)

    def cli_startup_for_plugins(config_file: CLIConfigFileType = None) -> None:
        cli_switch_venv_state(True)
        if config_file is not None:
            print_typer_error(
                f"{'/'.join(TyperGlobalOptions.config_file)} can only be "
                f"passed after the main program name "
                f"'{AppIdentity.app_name}', and not after a plugin name."
            )
            raise Exit(1)
        # Calling cli_startup again here would call cli_startup
        # again before loading each plugin. This is necessary because
        # whatever modifications/additions a plugin made,
        # cli_startup would need to consider them again. E.g., adding a
        # callback to global_cli_graceful_callback.
        cli_startup()

    _should_skip, _command = should_skip_cli_startup(app)
    if _should_skip:
        logger.debug(
            f"Command '{_command}' will skip Click-Typer help patch, "
            f"calling run_early_list, loading plugins, and checking result "
            f"callback log container."
        )
        return
    apply_click_typer_help_patch(app, messages_panel)
    call_run_early_list()
    load_plugins(
        PluginLoader(
            typer_app=app,
            internal_plugins_panel_name=TyperRichPanelNames.internal_plugins,
            external_plugins_panel_name=TyperRichPanelNames.external_plugins,
        ),
        cli_startup_for_plugins,
        cli_cleanup_for_external_plugins,
    )
    # Must be run after all plugins are loaded as they are given
    # a chance to modify ResultCallbackHandler.is_store_okay
    check_result_callback_log_container()
