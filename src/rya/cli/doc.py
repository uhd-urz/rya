"""
This script includes CLI help documentation for the app.
"""

from dataclasses import dataclass
from typing import ClassVar

from ..names import AppIdentity

# noinspection PyProtectedMember
from ..plugins.commons._names import TyperArgs
from ..styles import get_rich_inline_code_text


@dataclass
class MainAppCLIDoc:
    no_keys: ClassVar[str] = "Do not show the names of configuration keywords."
    _config_file_cmd: ClassVar[str] = get_rich_inline_code_text(
        f"{AppIdentity.app_name} --C "
        f"./project_config.{AppIdentity.config_file_extension} <command>",
        typer_rich_markup_mode=TyperArgs().rich_markup_mode,
    )
    config_file: ClassVar[str] = (
        f"Configuration file with the highest priority. E.g., {_config_file_cmd}."
    )
