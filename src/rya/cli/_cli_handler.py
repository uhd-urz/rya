from typing import Optional

import click
import typer
from properpath import P
from typing_extensions import Annotated

from ..config import AppConfig

# noinspection PyProtectedMember
from ..config._model_handler import NoConfigModelRegistrationFound
from ..core_validators import Exit
from ..loggers import get_logger
from ..names import AppIdentity, config_file_sources, run_early_list
from ..plugins.commons import Typer

# noinspection PyProtectedMember
from ..plugins.commons._names import (
    TyperGlobalOptions,
    TyperRichPanelNames,
)
from ..pre_utils import ConfigFileTuple, load_basic_debug_mode
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
    check_result_callback_log_container,
    cli_cleanup_for_external_plugins,
    cli_switch_venv_state,
    is_run_with_help_arg,
    load_plugins,
    should_skip_cli_startup,
)
from ._click_help import apply_click_typer_help_patch
from ._message_panel import messages_panel
from ._plugin_loader import PluginLoader
from .doc import MainAppCLIDoc

logger = get_logger()


def initiate_cli_startup(app: Typer):
    load_basic_debug_mode(AppIdentity.app_name, reload=True)
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
        should_skip, _ = should_skip_cli_startup(app, ctx)
        if is_run_with_help_arg(ctx) or should_skip:
            return
        global_options = {"global_options": {"config_file": config_file}}
        user_callback(**global_options)
        # GlobalCLICallback is run before configuration validation
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
        if AppConfig.validated is None or config_file is not None:
            if run_early_list:
                logger.debug(
                    f"run_early_list is not empty, but a file with "
                    f"'{cli_config_file_name}' was passed. "
                    f"run_early_list functions did not get the latest "
                    f"validated configuration model."
                )
            AppConfig.validate(errors="ignore", reload=True)
            if AppConfig.exceptions:
                for exc in AppConfig.exceptions:
                    if not isinstance(exc, NoConfigModelRegistrationFound):
                        logger.debug(
                            "Not all configuration models were validated successfully. "
                            "An incomplete or configuration model was used."
                        )
                        break
            else:
                logger.debug("All configuration models were validated successfully.")
        show_aggressive_log_message()
        logger.debug(
            f"Running '{__package__}' controlled callback "
            f"after configuration validation: "
            f"{global_cli_graceful_callback.instance_name}"
        )
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

    apply_click_typer_help_patch(app, messages_panel)

    if run_early_list:
        logger.debug("run_early_list is non-empty. Early validation will be performed.")
        early_validated_config = AppConfig.validate(errors="ignore")
        for func in run_early_list:
            func(early_validated_config)

    plugin_loader = PluginLoader(
        typer_app=app,
        internal_plugins_panel_name=TyperRichPanelNames.internal_plugins,
        external_plugins_panel_name=TyperRichPanelNames.external_plugins,
    )
    load_plugins(
        plugin_loader,
        cli_startup_for_plugins,
        cli_cleanup_for_external_plugins,
    )
    # Must be run after all plugins are loaded as they are given
    # a chance to modify ResultCallbackHandler.is_store_okay
    check_result_callback_log_container()
