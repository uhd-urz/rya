from collections import namedtuple
from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Literal, NamedTuple, Optional, Type

import click
import typer
from typer.core import TyperGroup
from typer.models import CommandFunctionType

from ...configuration import APP_NAME, DEFAULT_EXPORT_DATA_FORMAT
from ...core_validators import Exit, PathValidationError, Validate
from ...loggers import get_logger
from ...path import ProperPath
from ...styles import FormatError, get_formatter
from ...utils import check_reserved_keyword
from .export import ExportPathValidator

logger = get_logger()


@dataclass
class _DetectedClickFeedback:
    context: Optional[typer.Context]
    commands: Optional[str]


detected_click_feedback: _DetectedClickFeedback = _DetectedClickFeedback(
    context=None, commands=None
)


def get_cli_exportable_params(
    data_format: Optional[str] = None,
    export_dest: Optional[str] = None,
    can_overwrite: bool = False,
) -> NamedTuple:
    try:
        validate_export = Validate(
            ExportPathValidator(export_dest, can_overwrite=can_overwrite)
        )
    except (ValueError, PathValidationError) as e:
        logger.error(e)
        raise Exit(1)
    validated_export_dest: ProperPath = validate_export.get()

    _export_file_ext: Optional[str] = (
        validated_export_dest.expanded.suffix.removeprefix(".")
        if validated_export_dest.kind == "file"
        else None
    )
    data_format = (
        data_format or _export_file_ext or DEFAULT_EXPORT_DATA_FORMAT
    )  # default data_format format
    ExportableParams = namedtuple(
        "ExportableParams", ["data_format", "destination", "extension"]
    )
    return ExportableParams(data_format, validated_export_dest, _export_file_ext)


def get_cli_formatter(
    data_format: str,
    package_identifier: str,
    export_file_ext: Optional[str] = None,
):
    try:
        format = get_formatter(data_format, package_identifier=package_identifier)
    except FormatError as e:
        logger.error(e)
        logger.info(
            f"{APP_NAME} will fallback to '{DEFAULT_EXPORT_DATA_FORMAT}' format."
        )
        format = get_formatter(
            DEFAULT_EXPORT_DATA_FORMAT, package_identifier=package_identifier
        )
    format_convention = format.convention
    if format_convention is not None:
        if isinstance(format_convention, str):
            ...
        elif isinstance(format_convention, Iterable):
            format.convention = next(
                iter(format_convention)
            )  # only accept the first item as convention and modify format.convention
        if export_file_ext is not None and export_file_ext != format_convention:
            logger.info(
                f"File extension is '{export_file_ext}' but data "
                f"format will be of format '{format.convention.upper()}'."
            )
        return format
    logger.warning(
        f"The formatter found {format!r} for format '{data_format}' "
        f"does not have a non-empty convention."
    )
    logger.info(
        f"{APP_NAME} will fallback to '{DEFAULT_EXPORT_DATA_FORMAT}' "
        f"format for exporting."
    )
    return get_formatter(
        DEFAULT_EXPORT_DATA_FORMAT, package_identifier=package_identifier
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
