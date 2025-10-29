from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Type

import click
import typer
from pydantic import BaseModel, ConfigDict
from typer.core import MarkupMode, TyperGroup
from typer.models import CommandFunctionType

from ...loggers import get_logger

logger = get_logger()


@dataclass
class _DetectedClickFeedback:
    context: Optional[typer.Context]
    commands: Optional[str]


detected_click_feedback: _DetectedClickFeedback = _DetectedClickFeedback(
    context=None, commands=None
)


class OrderedCommands(TyperGroup):
    """
    OrderedCommands is passed to typer.Typer app so that the list of the commands on the terminal
    is shown in the order they are defined on the script instead of being shown alphabetically.
    See: https://github.com/tiangolo/typer/issues/428#issuecomment-1238866548
    """

    def list_commands(self, ctx: click.Context) -> Iterable[str]:
        return self.commands.keys()


class TyperArgs(BaseModel, validate_assignment=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: Optional[str] = None
    cls: Optional[Type[TyperGroup]] = OrderedCommands  # Modified
    invoke_without_command: bool = False
    no_args_is_help: bool = True  # Modified
    subcommand_metavar: Optional[str] = None
    chain: bool = False
    result_callback: Optional[Callable[..., Any]] = None
    # Command
    context_settings: Optional[dict[Any, Any]] = None
    callback: Optional[Callable[..., Any]] = None
    help: Optional[str] = None
    epilog: Optional[str] = None
    short_help: Optional[str] = None
    options_metavar: str = "[OPTIONS]"
    add_help_option: bool = True
    hidden: bool = False
    deprecated: bool = False
    add_completion: bool = True
    # Rich settings
    rich_markup_mode: MarkupMode = "markdown"  # Modified
    rich_help_panel: str | None = None
    suggest_commands: bool = True
    pretty_exceptions_enable: bool = True
    pretty_exceptions_show_locals: bool = False
    pretty_exceptions_short: bool = True


class Typer(typer.Typer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.commands_skip_cli_startup: list[str] = []
        self.no_arg_command: Optional[Callable] = None

    @staticmethod
    def _preload_ctx_feedback(ctx: typer.Context) -> None:
        commands: list[str] = []
        if ctx.command.name:
            while ctx.parent:
                commands.insert(0, ctx.command.name)
                ctx = ctx.parent
        detected_click_feedback.commands = " ".join(commands)
        detected_click_feedback.context = ctx

    def command(
        self, *args, skip_cli_startup: bool = False, **kwargs
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        if skip_cli_startup is True:
            try:
                self.commands_skip_cli_startup.append(kwargs["name"])
            except KeyError as e:
                raise ValueError(
                    "If 'skip_cli_startup' is True, 'name' must be provided."
                ) from e
        original_decorator = super().command(*args, **kwargs)

        def custom_decorator(func):
            @wraps(func)
            def wrapper(*wrapper_args, **wrapper_kwargs):
                ctx = click.get_current_context()
                self._preload_ctx_feedback(ctx)
                return func(*wrapper_args, **wrapper_kwargs)

            return original_decorator(wrapper)

        return custom_decorator
