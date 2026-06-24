import re
from collections import defaultdict
from typing import Annotated, Optional

import typer
from rich import box
from rich.table import Table

from ._meta import get_app_meta_info
from ._names import ConfigDisplayOptionDefaults, _ConfigInternalDisplayOptionDefaults
from ._parse_schema import (
    _add_include_options_to_display_values,
    _get_field_config_result,
    flatten_config_schema,
)
from .exceptions import ConfigDisplayFilterNotSupportedError
from .models import ConfigDisplayFilters, ConfigDisplayIncludes
from .utils import (
    _MultiOptionsParserParams,
    _parse_config_disp_user_multi_options,
)
from ..commons import Typer
from ...config import ConfigMaker
from ...kernel import Exit
from ...names import AppIdentity
from ...styles import print_typer_error, stdout_console

app = Typer(name="config", help="Manage configuration.", no_args_is_help=True)


@app.command(name="show", help="Display configuration values.")
def show(
    field_name: Annotated[
        Optional[str],
        typer.Argument(
            help="Configuration field name (a.k.a. the key). "
            "Dot notation is also supported. E.g.: [green]plugins.foo[/green]"
        ),
    ] = None,
    short_view: Annotated[
        bool,
        typer.Option(
            "--short",
            "-s",
            help="Shortcut flag to show only the configuration fild names and values.",
        ),
    ] = False,
    long_view: Annotated[
        bool,
        typer.Option(
            "--long",
            "-l",
            help="Shortcut flag to show all the available attributes of configuration fields.",
        ),
    ] = False,
    show_borders: Annotated[
        bool,
        typer.Option(
            "--border",
            "-B",
            help="Show borders around the table.",
        ),
    ] = False,
    include_options: Annotated[
        str,
        typer.Option(
            "--include",
            help="Specify which information to include. Configuration field names and values "
            "are always shown. Supported options: "
            f"{', '.join(ConfigDisplayIncludes.model_fields.keys())}. "
            "Multiple options are applied with an 'OR' relationship. "
            f"Options must be separated by {ConfigDisplayOptionDefaults.separator_desc}. "
            f"E.g., [green]--include 'key desc loc unit'[/green] will include the field "
            f"name, description, location, and unit.",
            show_default=False,
        ),
    ] = ConfigDisplayOptionDefaults.include_cli_default,
    user_filters: Annotated[
        str,
        typer.Option(
            "--filter",
            help=f"Filter display values. Supported options: "
            f"{', '.join(ConfigDisplayFilters.model_fields.keys())}. "
            f"Multiple options are applied with an 'AND' relationship. "
            f"Options must be separated by '{ConfigDisplayOptionDefaults.separator_desc}'. "
            f"E.g., [green]--filter 'env secret'[/green] will "
            f"filter all fields that are secrets and are loaded from environment variables.",
        ),
    ] = ConfigDisplayOptionDefaults.filter_cli_default,
):
    def _create_columns(table_: Table, column_names_: tuple[str, ...]):
        if len(table_.columns) != len(column_names_):
            for _ in column_names_:
                table_.add_column(
                    "",
                    overflow="fold",
                    no_wrap=False,
                )

    if short_view:
        include_options = "key val unit"
    if long_view:
        include_options = "key val desc loc unit"
    try:
        include_struct = _parse_config_disp_user_multi_options(
            include_options,
            _parser_params=_MultiOptionsParserParams[ConfigDisplayIncludes](
                separator=ConfigDisplayOptionDefaults.separator,
                default_dict=_ConfigInternalDisplayOptionDefaults.include_default,
                base_model_type=ConfigDisplayIncludes,
                identifier="include",
            ),
        )
        filters_struct = _parse_config_disp_user_multi_options(
            user_filters,
            _parser_params=_MultiOptionsParserParams(
                separator=ConfigDisplayOptionDefaults.separator,
                default_dict=_ConfigInternalDisplayOptionDefaults.filter_default,
                base_model_type=ConfigDisplayFilters,
                identifier="filter",
            ),
        )
    except ConfigDisplayFilterNotSupportedError as e:
        print_typer_error(str(e))
        raise Exit(1)

    unique_config_files: dict[str | None, int] = defaultdict(int)
    table = Table(
        box=box.HEAVY_HEAD if show_borders else None,
        show_header=True,
        show_lines=True,  # Doesn't show anyway when box=None
    )
    for key, val in flatten_config_schema(ConfigMaker.get_all_models()).items():
        match field_name:
            case None:
                result = _get_field_config_result(key, val, filters=filters_struct)
                if result is not None:
                    unique_config_files[result.location] += 1
                    column_names, rows = _add_include_options_to_display_values(
                        include_options=include_struct, display_values=result
                    )
                    _create_columns(table, column_names)
                    for _i, _c in enumerate(column_names):
                        table.columns[_i].header = _c
                    table.add_row(*rows)
            case _:
                pattern_appr_key = (field_name or "").replace(".", r"\.")
                pattern = re.compile(
                    (
                        rf"^({pattern_appr_key}(?=\.))|"
                        rf"^{pattern_appr_key}$"
                    ),
                    re.IGNORECASE,
                )
                if re.match(pattern, key):
                    result = _get_field_config_result(key, val, filters=filters_struct)
                    if result is not None:
                        unique_config_files[result.location] += 1
                        column_names, rows = _add_include_options_to_display_values(
                            include_options=include_struct, display_values=result
                        )
                        _create_columns(table, column_names)
                        for _i, _c in enumerate(column_names):
                            table.columns[_i].header = _c
                        table.add_row(*rows)
    if table.row_count > 0:
        stdout_console.print(table)
    else:
        raise Exit(1)
    if unique_config_files:
        stdout_console.print("\n[bold]Unique Configuration Files:[/bold]")
        for k, v in unique_config_files.items():
            stdout_console.print(f"- {k}: {v} matched")


@app.command(name="meta", help=f"Show {AppIdentity.app_fancy_name} meta information.")
def meta(
    show_borders: Annotated[
        bool,
        typer.Option(
            "--border",
            "-B",
            help="Show borders around the table.",
        ),
    ] = False,
):
    table = Table(
        box=box.HEAVY_HEAD if show_borders else None,
        show_header=False,
        show_lines=True,  # Doesn't show anyway when box=None
    )
    table.add_column("", overflow="fold", no_wrap=False)
    table.add_column("", overflow="fold", no_wrap=False)
    stdout_console.print(f"[bold]{AppIdentity.app_fancy_name} meta information:[/bold]")
    for key, val in get_app_meta_info().items():
        table.add_row(f"[magenta]{key}[/magenta]", str(val))
    stdout_console.print(table)
