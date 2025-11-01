from typing import Callable, Iterable, Optional

import click
from click import Context, HelpFormatter
from rich.text import Text
from typer.core import MarkupMode
from typer.rich_utils import rich_format_help


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
