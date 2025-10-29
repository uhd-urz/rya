"""
This script includes CLI help documentation for rya.
"""

from dataclasses import dataclass

from ..names import AppIdentity


@dataclass
class MainAppCLIDoc:
    no_keys: str = "Do not show the names of configuration keywords."
    cli_startup: str = (
        f"Configuration file with the highest priority. E.g., `{AppIdentity.app_name} --C "
        f"./project_config.{AppIdentity.config_file_extension} <command>`."
    )
