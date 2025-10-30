from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Callable, Optional, Type

import click
from pydantic import BaseModel, ConfigDict
from typer.core import MarkupMode, TyperGroup

from ...names import AppIdentity
from ...pre_utils import LayerLoader


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


@dataclass
class TyperRichPanelNames:
    internal_plugins: str = "Built-in plugins"
    external_plugins: str = "External plugins"
    callback: str = f"{AppIdentity.app_fancy_name} global options"


@dataclass
class TyperGlobalOptions:
    config_file: tuple[str, str] = (
        "--config-file",
        "--C",
    )


if LayerLoader.is_bootstrap_mode():
    LayerLoader.load_layers(
        globals(),
        layer_names=("names",),
    )
