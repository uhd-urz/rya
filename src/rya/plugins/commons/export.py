from datetime import datetime
from typing import Any, ClassVar, Optional, Self

from properpath import P
from pydantic import BaseModel, computed_field, model_validator

from ...loggers import get_logger

logger = get_logger()


class Export(BaseModel):
    file_name_date_format: ClassVar[str] = "%Y-%m-%d"
    file_name_time_format: ClassVar[str] = "%H%M%S"
    destination: P
    file_name_stub: str
    file_extension: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_name(self) -> str:
        date = datetime.now()
        file_name_prefix: str = (
            f"{date.strftime(Export.file_name_date_format)}_"
            f"{date.strftime(Export.file_name_time_format)}"
        )
        return f"{file_name_prefix}_{self.file_name_stub}.{self.file_extension}"

    @model_validator(mode="after")
    def fix_destination(self) -> Self:
        self.destination = self.destination / (
            self.file_name if self.destination.kind == "dir" else ""
        )
        return self

    def __call__(
        self,
        data: Any,
        encoding: Optional[str] = "utf-8",
        append_only: bool = False,
        verbose: bool = False,
    ) -> None:
        mode: str = "w" if not append_only else "a"
        if isinstance(data, bytes):
            mode += "b"
            encoding = None
        with self.destination.open(mode=mode, encoding=encoding) as file:
            file.write(data)
        if verbose:
            logger.info(
                f"{self.file_name_stub} data successfully exported to "
                f"{self.destination}."
            )
