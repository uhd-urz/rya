import logging
from types import ModuleType
from typing import List, Optional, Self

from pydantic import BaseModel, ConfigDict, model_validator

# noinspection PyProtectedMember
from rich._log_render import FormatTimeCallable
from rich.console import Console
from rich.highlighter import Highlighter
from rich.logging import RichHandler
from rich.theme import Theme


class AppRichHandlerArgs(BaseModel, validate_assignment=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    level: int | str = logging.INFO  # Modified
    console: Optional[Console] = None
    show_time: bool = False  # Modified
    omit_repeated_times: bool = True
    show_level: bool = True
    show_path: bool = True
    enable_link_path: bool = False  # Modified
    highlighter: Optional[Highlighter] = None
    markup: bool = False
    rich_tracebacks: bool = False
    tracebacks_width: Optional[int] = None
    tracebacks_code_width: Optional[int] = 88
    tracebacks_extra_lines: int = 3
    tracebacks_theme: Optional[str] = None
    tracebacks_word_wrap: bool = True
    tracebacks_show_locals: bool = False
    tracebacks_suppress: tuple[str | ModuleType] = ()
    tracebacks_max_frames: int = 100
    locals_max_length: int = 10
    locals_max_string: int = 80
    log_time_format: str | FormatTimeCallable = "[%x %X]"
    keywords: Optional[List[str]] = None
    level_colors: Optional[dict] = None  # New

    @model_validator(mode="after")
    def console_with_level_colors(self) -> Self:
        if self.level_colors is None:
            self.__dict__["console"] = self.console
            return self
        rich_level_colors: dict = {}
        for level_name, color_name in self.level_colors.items():
            rich_level_colors[f"logging.level.{level_name}"] = color_name
        # Rich handler with colored level support:
        # https://github.com/Textualize/rich/issues/1161#issuecomment-813882224
        self.__dict__["console"] = Console(theme=Theme(rich_level_colors), stderr=True)
        return self


class AppRichHandler(RichHandler):
    def __init__(self, args: AppRichHandlerArgs):
        super().__init__(**args.model_dump(exclude={"level_colors"}))
        self.setFormatter(logging.Formatter("%(name)s: %(message)s"))
