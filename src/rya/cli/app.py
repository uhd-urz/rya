

from ..kernel import Exit
from ..loggers import get_logger
from ..names import AppIdentity
from ..pre_init import AppVersionNotFound, get_app_version
from ..styles import stdout_console
from ._app_util import app

logger = get_logger()


@app.command(name="version", skip_cli_startup=True)
def version() -> str:
    """
    Show version number.
    """
    try:
        _version = get_app_version()
    except AppVersionNotFound as e:
        logger.critical(f"Version could not be fetched. Exception details: {e}")
        raise Exit(1) from e
    else:
        stdout_console.print(
            f"{AppIdentity.app_fancy_name} {_version}", highlight=False
        )
        return _version
