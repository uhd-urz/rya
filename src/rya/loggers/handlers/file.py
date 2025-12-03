import logging
from typing import Literal, Optional

from properpath import P
from pydantic import BaseModel, ConfigDict, Field


class AppFileHandlerArgs(BaseModel, validate_assignment=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    filename: P
    mode: str = "a"
    encoding: Optional[str] = None
    delay: bool = False
    errors: Optional[str] = None
    os_errors: Literal["raise", "ignore"] = "ignore"
    level: int = logging.INFO
    formatter: logging.Formatter = Field(
        default=logging.Formatter(
            "%(asctime)s:%(levelname)s:%(name)s:%(filename)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ),
    )


class AppFileHandler(logging.FileHandler):
    def __init__(self, args: AppFileHandlerArgs):
        self.args = args
        self.file = args.filename
        super().__init__(
            str(args.filename),
            args.mode,
            args.encoding,
            args.delay,
            args.errors,
        )
        self.setFormatter(args.formatter)
        self.setLevel(args.level)

    def _open(self):
        try:
            return self.file.open(
                mode=self.mode,
                encoding=self.encoding,
            )
        except self.file.PathException as e:
            match self.args.os_errors:
                case "raise":
                    raise e
                case "ignore":
                    pass
