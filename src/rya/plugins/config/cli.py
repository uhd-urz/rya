import re
from typing import Annotated, Optional

import typer
from rich.table import Table

from ...config import ConfigMaker
from ...styles import stdout_console
from ..commons import Typer
from ._parse_schema import _get_field_config_result, flatten_config_schema
from .models import ConfigDisplayFilters
from .utils import ConfigDisplayFilterDefaults, _parse_config_disp_user_multi_options

app = Typer(name="config", short_help="Manage configuration.", no_args_is_help=True)


@app.command(name="show", short_help="Display all configuration values.")
def show(
    key_name: Annotated[
        Optional[str], typer.Argument(help="Configuration key name.")
    ] = None,
    filter_: Annotated[
        str,
        typer.Option(
            "--filter",
            help=f"Filter display values. Supported options: "
            f"{', '.join(ConfigDisplayFilters.model_fields.keys())}. "
            f"Multiple options are applied with an 'AND' relationship. "
            f"Options must be separated by a single space. E.g., [green]--filter "
            f"'env secret'[/green] will "
            f"filter all fields that are secrets and are loaded from environment variables.",
        ),
    ] = ConfigDisplayFilterDefaults.default_key,  # all, mod, secrets, env
):
    filters = _parse_config_disp_user_multi_options(filter_)
    table = Table(box=None, show_header=True)
    table.add_column("", style="green", overflow="fold", no_wrap=False)
    table.add_column("", overflow="fold", no_wrap=False)
    for key, val in flatten_config_schema(ConfigMaker.get_all_models()).items():
        match key_name:
            case None:
                result = _get_field_config_result(key, val, filters=filters)
                if result is not None:
                    table.add_row(result.key, result.value)
            case _:
                pattern_appr_key = (key_name or "").replace(".", r"\.")
                pattern = re.compile(
                    (
                        rf"^({pattern_appr_key}(?=\.))|"
                        rf"^{pattern_appr_key}$"
                    ),
                    re.IGNORECASE,
                )
                if re.match(pattern, key):
                    result = _get_field_config_result(key, val, filters=filters)
                    if result is not None:
                        table.add_row(result.key, result.value)
    stdout_console.print(table)
