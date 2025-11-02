import click

from ..loggers import get_logger
from ..plugins.commons import Typer

# noinspection PyProtectedMember
from ..plugins.commons._names import (
    TyperArgs,
)
from ..pre_utils import global_cli_result_callback
from ._cli_handler_utils import is_run_with_help_arg, should_skip_cli_startup

logger = get_logger()


def result_callback_wrapper(_, **kwargs):
    # **kwargs is passed because the arguments from @app.callback
    # are automatically passed here as well
    ctx = click.get_current_context()
    should_skip, _ = should_skip_cli_startup(app, ctx)
    if is_run_with_help_arg(ctx) or should_skip:
        return
    user_result_callback(**{"global_options": kwargs})
    if global_cli_result_callback.get_callbacks():
        logger.debug(
            f"Running {__package__} controlled callback with "
            f"Typer result callback: "
            f"{global_cli_result_callback.instance_name}"
        )
        global_cli_result_callback.call_callbacks()


typer_args = TyperArgs()
user_callback = typer_args.callback or (lambda *args, **kwargs: None)
user_result_callback = typer_args.result_callback or (lambda *args, **kwargs: None)
typer_args.result_callback = result_callback_wrapper
app = Typer(**typer_args.model_dump())
