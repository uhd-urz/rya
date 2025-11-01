import logging
from typing import Literal

from rich.highlighter import ReprHighlighter
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..loggers import get_file_logger, get_logger
from ..names import AppIdentity

# noinspection PyProtectedMember
from ..plugins.commons._names import TyperRichPanelNames
from ..pre_utils import LoggerDefaults
from ..styles import (
    make_noted_text,
    stderr_console,
)
from ..utils import messages_list

logger = get_logger()
try:
    file_logger = get_file_logger()
except RuntimeError as e:
    logger.debug(f"File logger could not be instantiated. Exception: {e}")
    file_logger = logger


def messages_panel(
    return_type: Literal["plain", "rich"] | None = None,
) -> str | Text | None:
    if return_type not in (None, "plain", "rich"):
        raise ValueError(f"Invalid return type: {return_type}")
    if messages_list:
        rich_handler = RichHandler(show_path=False, show_time=False)
        log_record = logging.LogRecord(
            logger.name,
            level=logging.NOTSET,
            pathname="",
            lineno=0,
            msg="",
            args=None,
            exc_info=None,
        )
        grid = Table.grid(expand=True, padding=1)
        title = TyperRichPanelNames.messages
        plain_messages: list[str] = [f"{title}:"]
        grid.add_column(style="bold")
        grid.add_column()
        for i, log_tuple in enumerate(messages_list, start=1):
            message, level, logger_, is_aggressive = log_tuple.model_dump().values()
            file_logger.log(level, message) if logger_ is None else logger_.log(
                level, message
            )
            # The following is the only way that I could figure out for the log
            # message to show up in a rich panel without breaking
            # the pretty rich formatting.
            match return_type:
                case None:
                    log_record.levelno = log_tuple.level
                    log_record.levelname = logging.getLevelName(log_tuple.level)
                    message = rich_handler.render(
                        record=log_record,
                        traceback=None,
                        message_renderable=rich_handler.render_message(
                            record=log_record,
                            message=log_tuple.message,
                        ),
                    )
                    grid.add_row(f"{i}.", message)
                case _:
                    plain_messages.append(f"{i}. {log_tuple.message}")
        note_envvar: str = (
            f"{AppIdentity.app_name.upper()}_"
            f"{LoggerDefaults.debug_envvar_suffix.upper()}: f"
        )
        note_text = (
            f"{AppIdentity.app_name} will continue to work despite "
            f"the above warnings. Enable environment variable "
            f"'{note_envvar}' to debug these errors with "
            f"Python traceback (if any)."
        )
        match return_type:
            case "rich":
                plain_messages.append(note_text)
                return ReprHighlighter()("\n\n".join(plain_messages))
            case "plain":
                plain_messages.append(note_text)
                return "\n\n".join(plain_messages)
            case None:
                note_text = note_text.replace(
                    f"'{note_envvar}'", f"[dim]{note_envvar}[/dim]"
                )
                grid.add_row(
                    "",
                    make_noted_text(note_text, stem="Note"),
                )
                stderr_console.print(
                    Panel(
                        grid,
                        title=f"[yellow]{title}[/yellow]",
                        title_align="left",
                    ),
                )
                return None
    return None
