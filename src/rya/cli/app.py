from time import sleep

import typer
from properpath.validators import PathWriteValidator

from ..pre_init import get_app_version
from ..core_validators import Exit, Validate, ValidationError
from ..loggers import get_logger
from ..names import AppIdentity, config_file_sources
from ..styles import stdout_console
from ._cli_handler import app

logger = get_logger()


@app.command(
    name="init",
    short_help=f"Initialize {AppIdentity.app_name} configuration file.",
    skip_cli_startup=True,
)
def init() -> None:
    """
    A quick and simple command to initialize the rya configuration file.
    rya supports multiple configuration files
    that follow a priority hierarchy. This command is meant to be user-friendly and
    only creates one configuration file in the user's home directory.
    See [README](https://pypi.org/project/rya-cli/) for use-cases of advanced configuration files.

    'rya init' can be run with or without any arguments. When it is run without arguments, a user prompt is shown
    asking for the required values.

    Without arguments: `rya init`

    With arguments: `rya init --development_mode <value>`
    """
    for config_file in config_file_sources:
        if config_file.init_cmd_default:
            init_config_file = config_file.path
            break
    else:
        logger.error(
            "No configuration file for initialization was "
            f"defined in config file sources: "
            f"{config_file_sources}"
        )
        raise Exit(1)
    with stdout_console.status(
        f"Creating configuration file {init_config_file}...",
        refresh_per_second=15,
    ) as status:
        sleep(0.5)
        typer.echo()  # mainly for a newline!
        try:
            validate_local_config_loc = Validate(PathWriteValidator(init_config_file))
            validate_local_config_loc()
        except ValidationError:
            logger.error(
                f"{AppIdentity.app_name} couldn't validate path '{init_config_file}' "
                f"for writing configuration! "
                f"Please make sure you have write and read access to "
                f"'{init_config_file}'. "
                "Configuration initialization has failed!"
            )
            raise Exit(1)
        else:
            path = init_config_file
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
            except path.PathException as path_exc:
                if isinstance(path_exc, FileNotFoundError):
                    path.create()
                else:
                    status.stop()
                    logger.error(path_exc)
                    logger.error("Configuration initialization has failed!")
                    raise Exit(1)
            try:
                with path.open(mode="w") as f:
                    _configuration_yaml_text = """
"""
                    f.write(_configuration_yaml_text)
            except path.PathException as path_exc:
                logger.error(path_exc)
                logger.error("Configuration initialization has failed!")
                raise Exit(1)
            else:
                stdout_console.print(
                    "Configuration file has been successfully created! "
                    f"Run '{AppIdentity.app_name} show-config' to see "
                    f"the configuration path "
                    "and more configuration details.",
                    style="green",
                )


@app.command(name="version", skip_cli_startup=True)
def version() -> str:
    """
    Show version number.
    """
    _version = get_app_version()
    stdout_console.print(f"{AppIdentity.app_name} {_version}", highlight=False)
    return _version
