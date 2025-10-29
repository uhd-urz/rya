import click
from colorama import Fore
from rich.padding import Padding
from rich.text import Text
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
    exception = click.ClickException(error_message)
    exception.ctx = click.get_current_context()
    rich_format_error(exception)
