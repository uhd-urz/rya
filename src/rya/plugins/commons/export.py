from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Iterable, Optional, Self, Union

from properpath import P
from pydantic import BaseModel, computed_field, model_validator

from ...core_validators import PathValidationError, PathWriteValidator, ValidationError
from ...loggers import get_logger

logger = get_logger()


class Export(BaseModel):
    file_name_date_format: ClassVar[str] = "%Y-%m-%d"
    file_name_time_format: ClassVar[str] = "%H%M%S"
    destination: Union[P, Path, str]
    file_name_stub: str
    file_extension: str

    @computed_field
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


class ExportPathWriteValidator(PathWriteValidator):
    def __init__(
        self,
        /,
        export_path: Iterable[str | P | Path] | str | P | Path,
        can_overwrite: bool = False,
    ):
        self.export_path = export_path
        self.can_overwrite = can_overwrite
        super().__init__(export_path)

    @property
    def can_overwrite(self) -> bool:
        return self._can_overwrite

    @can_overwrite.setter
    def can_overwrite(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("can_overwrite attribute must be a boolean!")
        self._can_overwrite = value

    def validate(self) -> P:
        try:
            path = P(super().validate(), err_logger=logger)
        except ValidationError as e:
            logger.warning(f"Export path '{self.export_path}' couldn't be validated!")
            raise PathValidationError from e
        else:
            if (
                path.kind == "file"
                and path.exists()
                and path not in super()._self_created_files
                and not self.can_overwrite
            ):
                logger.warning(
                    f"Export path '{self.export_path}' already exists! "
                    f"The file will not be overwritten unless explicitly specified."
                )
                raise PathValidationError
            return path
