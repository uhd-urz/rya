import logging
import platform
import sys
from dataclasses import astuple
from functools import partial
from sys import argv
from time import sleep
from typing import Optional

import click
import typer
from rich import pretty
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from typing_extensions import Annotated

from .. import APP_NAME
from .._names import KEY_DEVELOPMENT_MODE, config_files
from ..configuration import (
    CONFIG_FILE_NAME,
    KEY_PLUGIN_KEY_NAME,
    ConfigIdentity,
    DevelopmentState,
    get_development_mode,
    minimal_config_data,
    reinitiate_config,
    settings,
)
from ..core_validators import Exit, PathWriteValidator, Validate, ValidationError
from ..loggers import (
    GlobalLogRecordContainer,
    ResultCallbackHandler,
    get_file_logger,
    get_logger,
)
from ..plugins.commons.cli_helpers import Typer
from ..plugins.commons.parse_user_cli_input import get_structured_data
from ..styles import (
    NoteText,
    print_typer_error,
    rich_format_help_with_callback,
    stderr_console,
    stdout_console,
)
from ..utils import (
    GlobalCLIGracefulCallback,
    GlobalCLIResultCallback,
    GlobalCLISuperStartupCallback,
    MessagesList,
    PythonVersionCheckFailed,
    get_external_python_version,
)
from ._plugin_handler import (
    PluginInfo,
    external_local_plugin_typer_apps,
    internal_plugin_typer_apps,
)
from .doc import __PARAMETERS__doc__ as docs

logger = get_logger()
file_logger = get_file_logger()
pretty.install()

DevelopmentState.switch_state(get_development_mode(skip_validation=True))


def result_callback_wrapper(_, override_config):
    if (
        calling_sub_command_name := (
            ctx := click.get_current_context()
        ).invoked_subcommand
    ) not in SENSITIVE_PLUGIN_NAMES and ctx.command.name != calling_sub_command_name:
        if argv[-1] != (ARG_TO_SKIP := "--help") or ARG_TO_SKIP not in argv:
            global_result_callback = GlobalCLIResultCallback()
            if global_result_callback.get_callbacks():
                logger.debug(
                    f"Running {__package__} controlled callback with "
                    f"Typer result callback: "
                    f"{global_result_callback.singleton_subclass_name}"
                )
                global_result_callback.call_callbacks()


app = Typer(result_callback=result_callback_wrapper)


SENSITIVE_PLUGIN_NAMES: tuple[str, str, str] = (
    "init",
    "show-config",
    "version",
)  # version is no longer a plugin, but it used to be
SPECIAL_SENSITIVE_PLUGIN_NAMES: tuple[str] = ("show-config",)
COMMANDS_TO_SKIP_CLI_STARTUP: list = list(SENSITIVE_PLUGIN_NAMES)
CLI_STARTUP_CALLBACK_PANEL_NAME: str = f"{APP_NAME} global options"
RESERVED_PLUGIN_NAMES: tuple[str, ...] = (APP_NAME,)
INTERNAL_PLUGIN_NAME_REGISTRY: dict = {}
EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY: dict = {}

INTERNAL_PLUGIN_PANEL_NAME: str = "Built-in plugins"
THIRD_PARTY_PLUGIN_PANEL_NAME: str = "Third-party plugins"

OVERRIDE_CONFIG_OPTION_NAME_LONG: str = "--override-config"
OVERRIDE_CONFIG_OPTION_NAME_SHORT: str = "--OC"
OVERRIDE_CONFIG_OPTION_NAME: str = (
    f"{OVERRIDE_CONFIG_OPTION_NAME_LONG}/{OVERRIDE_CONFIG_OPTION_NAME_SHORT}"
)


def prettify() -> None:
    logger.debug(f"{APP_NAME} has started.")
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            stdout_console.print(line, end="")
    except KeyboardInterrupt:
        raise Exit(1)
    finally:
        stdout_console.print("\n[green]Command finished.[/green]")


@app.callback(invoke_without_command=True)
def cli_startup(
    override_config: Annotated[
        str,
        typer.Option(
            OVERRIDE_CONFIG_OPTION_NAME_LONG,
            OVERRIDE_CONFIG_OPTION_NAME_SHORT,
            help=docs["cli_startup"],
            show_default=False,
            rich_help_panel=CLI_STARTUP_CALLBACK_PANEL_NAME,
        ),
    ] = "{}",
) -> None:
    # Notice GlobalCLICallback is run before configuration validation (reinitiate_config)
    # However, PluginConfigurationValidator is always run
    # first when development_mode is enabled
    global_init_callbacks = GlobalCLISuperStartupCallback()
    if global_init_callbacks.get_callbacks():
        logger.debug(
            f"Running {__package__} controlled callback before anything else: "
            f"{global_init_callbacks.singleton_subclass_name}"
        )
        global_init_callbacks.call_callbacks()

    def show_aggressive_log_message():
        messages = MessagesList()

        for log_tuple in messages:
            message, level, logger_, is_aggressive = log_tuple.items()
            if is_aggressive is True:
                logger.log(level, message) if logger_ is None else logger_.log(
                    level, message
                )

    try:
        struct_override_config: dict = get_structured_data(
            override_config, option_name=OVERRIDE_CONFIG_OPTION_NAME
        )
    except ValueError:
        raise Exit(1)
    else:
        OVERRIDABLE_FIELDS_SOURCE: str = "CLI"
        for key, value in struct_override_config.items():
            if key.lower() == KEY_DEVELOPMENT_MODE.lower():
                DevelopmentState.switch_state(value)
            if key.lower() == KEY_PLUGIN_KEY_NAME.lower():
                plugins = minimal_config_data[key].value
                if not isinstance(value, dict):
                    # I.e., invalid type for plugin value. --override-config will simply comply.
                    minimal_config_data[key] = ConfigIdentity(
                        value, OVERRIDABLE_FIELDS_SOURCE
                    )
                else:
                    for plugin_name, plugin_config in value.items():
                        if not isinstance(plugin_config, dict):
                            # I.e., invalid type for plugin value. --override-config will simply comply.
                            continue
                        try:
                            plugins[plugin_name].update(plugin_config)
                        except KeyError:
                            if getattr(
                                settings.get(KEY_PLUGIN_KEY_NAME), "get", dict().get
                            )(plugin_name):
                                logger.warning(
                                    f"Plugin configuration in {CONFIG_FILE_NAME} for '{plugin_name}' plugin "
                                    f"was ignored due to type violation, but '{OVERRIDE_CONFIG_OPTION_NAME}' was "
                                    f"passed configuration value for the same plugin, which will be considered. "
                                    f"This might still lead to unexpected errors for the '{plugin_name}' plugin. "
                                    f"It is strongly recommended to fix the type error first "
                                    f"in {CONFIG_FILE_NAME}."
                                )
                            plugins[plugin_name] = {}
                            plugins[plugin_name].update(plugin_config)
                    minimal_config_data[key] = ConfigIdentity(
                        plugins, OVERRIDABLE_FIELDS_SOURCE
                    )
            else:
                minimal_config_data[key] = ConfigIdentity(
                    value, OVERRIDABLE_FIELDS_SOURCE
                )
        if (
            (
                calling_sub_command_name := (
                    ctx := click.get_current_context()
                ).invoked_subcommand
            )
            not in COMMANDS_TO_SKIP_CLI_STARTUP
            and ctx.command.name != calling_sub_command_name
        ):
            if argv[-1] != (ARG_TO_SKIP := "--help") or ARG_TO_SKIP not in argv:
                reinitiate_config()
                show_aggressive_log_message()
                global_graceful_callbacks = GlobalCLIGracefulCallback()
                if global_graceful_callbacks.get_callbacks():
                    logger.debug(
                        f"Running {__package__} controlled callback "
                        f"after configuration validation: "
                        f"{global_graceful_callbacks.singleton_subclass_name}"
                    )
                    global_graceful_callbacks.call_callbacks()
        else:
            if calling_sub_command_name in SENSITIVE_PLUGIN_NAMES:
                if struct_override_config:
                    print_typer_error(
                        f"{APP_NAME} command '{calling_sub_command_name}' does not support "
                        f"the override argument {OVERRIDE_CONFIG_OPTION_NAME}."
                    )
                    raise Exit(1)
                if calling_sub_command_name in SPECIAL_SENSITIVE_PLUGIN_NAMES:
                    reinitiate_config(ignore_essential_validation=True)
                return
    if calling_sub_command_name is None:
        # This is where we know that pj is run as is
        prettify()


def check_result_callback_log_container():
    if (
        ResultCallbackHandler.is_store_okay()
        and ResultCallbackHandler.get_client_count() == 0
    ):
        GlobalLogRecordContainer().data.clear()
        ResultCallbackHandler.is_store_okay = False


def cli_switch_venv_state(state: bool, /) -> None:
    import click

    from ._venv_state_manager import switch_venv_state

    try:
        venv_dir = EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY[
            click.get_current_context().command.name
        ].venv
        project_dir = EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY[
            click.get_current_context().command.name
        ].project_dir
    except KeyError:
        ...
    else:
        if venv_dir is not None:
            switch_venv_state(state, venv_dir, project_dir)


def cli_startup_for_plugins(
    override_config: Annotated[
        Optional[str],
        typer.Option(
            "--override-config",
            "--OC",
            help=docs["cli_startup"],
            show_default=False,
            rich_help_panel=CLI_STARTUP_CALLBACK_PANEL_NAME,
        ),
    ] = None,
) -> None:
    from ..styles import print_typer_error

    cli_switch_venv_state(True)
    if override_config is not None:
        print_typer_error(
            f"--override-config/--OC can only be passed after "
            f"the main program name '{APP_NAME}', "
            f"and not after a plugin name."
        )
        raise Exit(1)
    # Calling cli_startup again here would call cli_startup
    # again before loading each plugin. This is necessary because
    # whatever modifications/additions a plugin made,
    # cli_startup would need to consider them again. E.g., adding a
    # callback to GlobalGlobalCLIGracefulCallback.
    cli_startup()


def cli_cleanup_for_third_party_plugins(*args, override_config=None):
    cli_switch_venv_state(False)


logger.debug(f"{APP_NAME} will load internal plugins.")
for inter_app_obj in internal_plugin_typer_apps:
    if inter_app_obj is not None:
        app_name = inter_app_obj.info.name
        INTERNAL_PLUGIN_NAME_REGISTRY[app_name] = inter_app_obj
        COMMANDS_TO_SKIP_CLI_STARTUP.append(inter_app_obj.info.name)
        app.add_typer(
            inter_app_obj,
            rich_help_panel=INTERNAL_PLUGIN_PANEL_NAME,
            callback=cli_startup_for_plugins,
        )


def disable_plugin(
    main_app: Typer,
    /,
    *,
    plugin_name: str,
    err_msg: str,
    panel_name: str,
    short_reason: Optional[str] = None,
):
    import logging

    from ..utils import add_message

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


def messages_panel():
    messages = MessagesList()

    if messages:
        rich_handler = RichHandler(show_path=False, show_time=False)
        log_record = logging.LogRecord(
            logger.name,
            level=logging.NOTSET,
            pathname="",
            lineno=0,
            msg="",
            args=None,
            exc_info=None,
        )
        grid = Table.grid(expand=True, padding=1)
        grid.add_column(style="bold")
        grid.add_column()
        for i, log_tuple in enumerate(messages, start=1):
            message, level, logger_, is_aggressive = astuple(log_tuple)
            file_logger.log(level, message) if logger_ is None else logger_.log(
                level, message
            )
            log_record.levelno = log_tuple.level
            log_record.levelname = logging.getLevelName(log_tuple.level)
            # The following is the only way that I could figure out for the log
            # message to show up in a rich panel without breaking the pretty rich formatting.
            message = rich_handler.render(
                record=log_record,
                traceback=None,
                message_renderable=rich_handler.render_message(
                    record=log_record,
                    message=log_tuple.message,
                ),
            )
            grid.add_row(f"{i}.", message)
        grid.add_row(
            "",
            NoteText(
                f"{APP_NAME} will continue to work despite "
                f"the above warnings. Set [dim]development_mode: True[/dim] "
                f"in {CONFIG_FILE_NAME} configuration "
                "file to debug these errors with Python "
                "traceback (if any).",
                stem="Note",
            ),
        )
        stderr_console.print(
            Panel(
                grid,
                title=f"[yellow]ⓘ Message{'s' if len(messages) > 1 else ''}[/yellow]",
                title_align="left",
            )
        )


typer.rich_utils.rich_format_help = partial(
    rich_format_help_with_callback, result_callback=messages_panel
)


@app.command(short_help=f"Initialize {APP_NAME} configuration file.")
def init() -> None:
    """
    A quick and simple command to initialize the pj configuration file.
    pj supports multiple configuration files
    that follow a priority hierarchy. This command is meant to be user-friendly and
    only creates one configuration file in the user's home directory.
    See [README](https://pypi.org/project/pj-cli/) for use-cases of advanced configuration files.

    'pj init' can be run with or without any arguments. When it is run without arguments, a user prompt is shown
    asking for the required values.

    Without arguments: `pj init`

    With arguments: `pj init --development_mode <value>`
    """
    with stdout_console.status(
        f"Creating configuration file {CONFIG_FILE_NAME}...", refresh_per_second=15
    ) as status:
        sleep(0.5)
        typer.echo()  # mainly for a newline!
        try:
            validate_local_config_loc = Validate(PathWriteValidator(config_files.user.file))
            validate_local_config_loc()
        except ValidationError:
            logger.error(
                f"{APP_NAME} couldn't validate path '{config_files.user.file}' "
                f"for writing configuration! "
                f"Please make sure you have write and read access to "
                f"'{config_files.user.file}'. "
                "Configuration initialization has failed!"
            )
            raise Exit(1)
        else:
            path = config_files.user.file
            try:
                with path.open(mode="r") as f:
                    if f.read():
                        status.stop()
                        logger.error(
                            f"A configuration file '{path}' already exists "
                            f"and it's not empty! "
                            f"It's ambiguous what to do in this situation."
                        )
                        logger.error("Configuration initialization has failed!")
                        raise Exit(1)
            except path.PathException as e:
                if isinstance(e, FileNotFoundError):
                    path.create()
                else:
                    status.stop()
                    logger.error(e)
                    logger.error("Configuration initialization has failed!")
                    raise Exit(1)
            try:
                with path.open(mode="w") as f:
                    _configuration_yaml_text = """development_mode: false
"""
                    f.write(_configuration_yaml_text)
            except path.PathException as e:
                logger.error(e)
                logger.error("Configuration initialization has failed!")
                raise Exit(1)
            else:
                stdout_console.print(
                    "Configuration file has been successfully created! "
                    f"Run '{APP_NAME} show-config' to see "
                    f"the configuration path "
                    "and more configuration details.",
                    style="green",
                )


@app.command(name="show-config")
def show_config(
    no_keys: Annotated[
        bool,
        typer.Option("--no-keys", help=docs["no_keys"], show_default=True),
    ] = False,
) -> None:
    """
    Get information about detected configuration values.
    """
    from ..plugins.show_config import show

    md = Markdown(show(no_keys))
    stdout_console.print(md)


@app.command()
def version() -> str:
    """
    Show version number.
    """
    from .. import APP_NAME
    from ..utils import get_app_version

    _version = get_app_version()
    stdout_console.print(f"{APP_NAME} {_version}", highlight=False)
    return _version


logger.debug(f"{APP_NAME} will load external plugins.")
# Load external plugins
for plugin_info in external_local_plugin_typer_apps:
    if plugin_info is not None:
        ext_app_obj, _path, _venv, _proj_dir = plugin_info
    else:
        continue
    if ext_app_obj is not None:
        original_name: str = ext_app_obj.info.name
        ext_app_name: str = original_name.lower()
        if ext_app_name in EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY:
            error_message = (
                f"Plugin name '{original_name}' from {_path} conflicts with an "
                f"existing third-party plugin from "
                f"{EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY[ext_app_name].path}. "
                f"Please rename the plugin."
            )
            error_message += (
                " Note, plugin names are case-insensitive."
                if original_name != ext_app_name
                else ""
            )
            disable_plugin(
                app,
                plugin_name=ext_app_name,
                err_msg=error_message,
                panel_name=THIRD_PARTY_PLUGIN_PANEL_NAME,
                short_reason="naming conflict",
            )
        elif ext_app_name in INTERNAL_PLUGIN_NAME_REGISTRY:
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
                app,
                plugin_name=ext_app_name,
                err_msg=error_message,
                panel_name=INTERNAL_PLUGIN_PANEL_NAME,
                short_reason="naming conflict",
            )
        elif ext_app_name in RESERVED_PLUGIN_NAMES:
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
                app,
                plugin_name=ext_app_name,
                err_msg=error_message,
                panel_name=THIRD_PARTY_PLUGIN_PANEL_NAME,
                short_reason="naming conflict",
            )
        else:
            if _venv is not None:
                try:
                    external_plugin_python_version = get_external_python_version(
                        venv_dir=_venv
                    )[:2]
                except PythonVersionCheckFailed as e:
                    error_message = (
                        f"Plugin name '{original_name}' from {_path} uses "
                        f"virtual environment "
                        f"{_venv} whose own Python version could not "
                        f"be determined for the following reason: "
                        f"{e}. Plugin will be disabled."
                    )
                    disable_plugin(
                        app,
                        plugin_name=ext_app_name,
                        err_msg=error_message,
                        panel_name=THIRD_PARTY_PLUGIN_PANEL_NAME,
                        short_reason="undetermined .venv Python version",
                    )
                    continue
                else:
                    if external_plugin_python_version != (
                        own_python_version := platform.python_version_tuple()[:2]
                    ):
                        error_message = (
                            f"Plugin name '{original_name}' from {_path} "
                            f"uses virtual environment "
                            f"{_venv} whose Python version (major and minor) "
                            f"'{'.'.join(external_plugin_python_version)}' "
                            f"does not match {APP_NAME}'s own Python version "
                            f"'{'.'.join(own_python_version)}'. "
                            f"Plugin will be disabled."
                        )
                        disable_plugin(
                            app,
                            plugin_name=ext_app_name,
                            err_msg=error_message,
                            panel_name=THIRD_PARTY_PLUGIN_PANEL_NAME,
                            short_reason=".venv Python version conflict",
                        )
                        continue
            EXTERNAL_LOCAL_PLUGIN_NAME_REGISTRY[ext_app_name] = PluginInfo(
                ext_app_obj, _path, _venv, _proj_dir
            )
            COMMANDS_TO_SKIP_CLI_STARTUP.append(ext_app_name)
            app.add_typer(
                ext_app_obj,
                rich_help_panel=THIRD_PARTY_PLUGIN_PANEL_NAME,
                callback=cli_startup_for_plugins,
                result_callback=cli_cleanup_for_third_party_plugins,
            )
# Must be run after all plugins are loaded as they are given
# a chance to modify ResultCallbackHandler.is_store_okay
check_result_callback_log_container()
