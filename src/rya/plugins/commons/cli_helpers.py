from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional

import click
import typer
from rich_click.patch import patch_typer
from typer.models import CommandFunctionType

from ...loggers import get_logger
from ._names import TyperArgs

if TyperArgs().rich_markup_mode == "rich-click":
    patch_typer()

logger = get_logger()


@dataclass
class _DetectedClickFeedback:
    context: Optional[typer.Context]
    command_names: Optional[str]


detected_click_feedback: _DetectedClickFeedback = _DetectedClickFeedback(
    context=None, command_names=None
)


class Typer(typer.Typer):
    _cli_help_callbacks: Optional[list[Callable]] = None
    _cli_help_result_callbacks: Optional[list[Callable]] = None

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
        detected_click_feedback.command_names = " ".join(commands)
        detected_click_feedback.context = ctx

    @classmethod
    def add_cli_help_callback(cls, callback: Callable) -> None:
        if not callable(callback):
            raise TypeError(f"Given callback '{callback}' must be a callable.")
        if cls._cli_help_callbacks is None:
            cls._cli_help_callbacks = []
        cls._cli_help_callbacks.append(callback)

    @classmethod
    def add_cli_help_result_callback(cls, callback: Callable) -> None:
        if not callable(callback):
            raise TypeError(f"Given callback '{callback}' must be a callable.")
        if cls._cli_help_result_callbacks is None:
            cls._cli_help_result_callbacks = []
        cls._cli_help_result_callbacks.append(callback)

    @classmethod
    def get_cli_help_callbacks(cls) -> list[Callable]:
        return cls._cli_help_callbacks or []

    @classmethod
    def get_cli_help_result_callbacks(cls) -> list[Callable]:
        return cls._cli_help_result_callbacks or []

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
