from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Literal, Optional, Type

import click
import typer
from typer.core import TyperGroup
from typer.models import CommandFunctionType

from ...configuration import APP_NAME
from ...loggers import get_logger
from ...utils import check_reserved_keyword

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


class Typer(typer.Typer):
    def __init__(
        self,
        rich_markup_mode: Literal["markdown", "rich"] = "markdown",
        cls_: Optional[Type[TyperGroup]] = OrderedCommands,
        **kwargs,
    ):
        try:
            super().__init__(
                pretty_exceptions_show_locals=False,
                rich_markup_mode=rich_markup_mode,
                cls=cls_,
                **kwargs,
            )
        except TypeError as e:
            check_reserved_keyword(
                e,
                what=f"{APP_NAME} overloaded class '{__package__}.{Typer.__name__}'",
                against=f"{typer.Typer.__name__} class",
            )
            raise e

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
        self, *args, **kwargs
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        original_decorator = super().command(*args, **kwargs)

        def custom_decorator(func):
            @wraps(func)
            def wrapper(*wrapper_args, **wrapper_kwargs):
                ctx = click.get_current_context()
                self._preload_ctx_feedback(ctx)
                return func(*wrapper_args, **wrapper_kwargs)

            return original_decorator(wrapper)

        return custom_decorator
