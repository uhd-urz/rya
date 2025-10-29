import logging

from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from ..loggers import get_file_logger, get_logger
from ..names import AppIdentity
from ..styles import make_noted_text, stderr_console
from ..utils import messages_list

logger = get_logger()
file_logger = get_file_logger()


def messages_panel():
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
        grid.add_column(style="bold")
        grid.add_column()
        for i, log_tuple in enumerate(messages_list, start=1):
            message, level, logger_, is_aggressive = log_tuple.model_dump().values()
            file_logger.log(level, message) if logger_ is None else logger_.log(
                level, message
            )
            log_record.levelno = log_tuple.level
            log_record.levelname = logging.getLevelName(log_tuple.level)
            # The following is the only way that I could figure out for the log
            # message to show up in a rich panel without breaking the pretty rich formatting.
            message = rich_handler.render(
                record=log_record,
                traceback=None,
                message_renderable=rich_handler.render_message(
                    record=log_record,
                    message=log_tuple.message,
                ),
            )
            grid.add_row(f"{i}.", message)
        grid.add_row(
            "",
            make_noted_text(
                f"{AppIdentity.app_name} will continue to work despite "
                f"the above warnings. Pass [dim]--debug: c[/dim] "
                f"to debug these errors with Python traceback (if any).",
                stem="Note",
            ),
        )
        stderr_console.print(
            Panel(
                grid,
                title=f"[yellow]ⓘ Message{'s' if len(messages_list) > 1 else ''}[/yellow]",
                title_align="left",
            )
        )
