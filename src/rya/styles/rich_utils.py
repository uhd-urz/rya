import operator
from typing import Callable, Iterable, Optional

import click
import rich_click.rich_click as rc
from click import Context, HelpFormatter
from pydantic import BaseModel
from rich.text import Text
from rich_click.rich_click_theme import RichClickThemeNotFound
from typer.core import MarkupMode
from typer.rich_utils import rich_format_help

from ..pre_utils import get_logger

logger = get_logger()


def rich_format_help_with_callback(
    *,
    obj: click.Command | click.Group,
    ctx: Context,
    markup_mode: MarkupMode,
    callback: Optional[Iterable[Callable]] = None,
    result_callback: Optional[Iterable[Callable]] = None,
) -> None:
    if callback is not None:
        for func in callback:
            func()
    rich_format_help(obj=obj, ctx=ctx, markup_mode=markup_mode)
    if result_callback is not None:
        for func in result_callback:
            func()


def click_format_help_with_callback(
    original_format_help: Callable,
    callback: Optional[Iterable[Callable]] = None,
    result_callback: Optional[Iterable[Callable]] = None,
) -> Callable:
    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:
        epilog_string = None
        if callback is not None:
            for func in callback:
                func()
        if result_callback is not None:
            for func in result_callback:
                val = func()
                if isinstance(val, (str, Text)):
                    epilog_string = val
            if epilog_string:
                ctx.command.epilog = epilog_string
        original_format_help(self, ctx, formatter)

    return format_help


def update_rich_click_cli_theme(
    config_model: BaseModel, /, config_field_loc: str, default_theme: str
) -> None:
    try:
        theme = operator.attrgetter(config_field_loc)(config_model)
    except AttributeError:
        theme = default_theme
        logger.debug(
            f"Possible incomplete detected configuration model "
            f"{config_model.__class__} was received. Default theme "
            f"'{default_theme}' will be used."
        )
    try:
        rc.THEME = theme
        logger.debug(f"CLI theme is changed to '{theme}'.")
    except RichClickThemeNotFound as e:
        logger.warning(
            f"CLI theme could not be changed. Exception details: {e}. "
            f"Default theme '{default_theme}' will be used."
        )
        rc.THEME = default_theme


def get_rich_inline_code_text(
    text: str,
    *,
    typer_rich_markup_mode: Optional[str],
    default_rich_tag: str = "green",
) -> str:
    match typer_rich_markup_mode:
        case "markdown":
            return f"`{text}`"
        case "rich-click" | "rich":
            return f"[{default_rich_tag}]{text}[/{default_rich_tag}]"
        case None:
            return text
        case _:
            raise ValueError(
                f"Invalid Typer rich_markup_mode '{typer_rich_markup_mode}'."
            )
