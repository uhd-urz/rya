from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional

import click
import typer
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
