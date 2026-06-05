from colorama import Fore
from rich.padding import Padding
from rich.text import Text
from typer._click import ClickException
from typer._click.globals import get_current_context
from typer.rich_utils import rich_format_error


def make_noted_text(
    text: str, /, stem: str = "P.S.", color: str = "yellow", indent: int = 3
) -> Padding:
    return Padding(
        f"{Text(f'[b {color}]{stem}:[/b {color}]')} {text}",
        pad=(1, 0, 0, indent),
    )


def color_text(text: str, /, ansi_color: str) -> str:
    return f"{ansi_color}{text}{Fore.RESET}"


def print_typer_error(error_message: str) -> None:
    exception = ClickException(error_message)
    # This extra ctx attribute is added so we can inspect the context later.
    exception.ctx = get_current_context()  # type: ignore[attr-defined]
    rich_format_error(exception)
