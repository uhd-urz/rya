"""
This script includes CLI help documentation for the app.
"""

from dataclasses import dataclass
from typing import ClassVar

from ..names import AppIdentity


@dataclass
class MainAppCLIDoc:
    no_keys: ClassVar[str] = "Do not show the names of configuration keywords."
    cli_startup: ClassVar[str] = (
        f"Configuration file with the highest priority. E.g., `{AppIdentity.app_name} --C "
        f"./project_config.{AppIdentity.config_file_extension} <command>`."
    )
