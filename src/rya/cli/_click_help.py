from collections.abc import Callable
from functools import partial

import rich_click
import typer

from ..loggers import get_logger
from ..plugins.commons import Typer
from ..styles import click_format_help_with_callback, rich_format_help_with_callback

logger = get_logger()


def apply_click_typer_help_patch(app: Typer, messages_panel: Callable) -> None:
    logger.debug("Patching Click-Typer 'help' page.")
    match app.rich_markup_mode:
        case "rich-click" | None:
            rich_click.rich_click.USE_RICH_MARKUP = True
            rich_click.rich_click.STYLE_EPILOG_TEXT = ""
            return_type = "plain" if app.rich_markup_mode is None else "rich"
            Typer.add_cli_help_result_callback(
                partial(messages_panel, return_type=return_type)
            )
            typer.main.TyperCommand.format_help = click_format_help_with_callback(
                typer.main.TyperCommand.format_help,
                callback=Typer.get_cli_help_callbacks(),
                result_callback=Typer.get_cli_help_result_callbacks(),
            )
            typer.core.TyperGroup.format_help = click_format_help_with_callback(
                typer.core.TyperGroup.format_help,
                callback=Typer.get_cli_help_callbacks(),
                result_callback=Typer.get_cli_help_result_callbacks(),
            )
        case _:
            Typer.add_cli_help_result_callback(messages_panel)
            typer.rich_utils.rich_format_help = partial(
                rich_format_help_with_callback,
                callback=Typer.get_cli_help_callbacks(),
                result_callback=Typer.get_cli_help_result_callbacks(),
            )
