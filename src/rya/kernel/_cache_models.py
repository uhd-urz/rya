from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from properpath import P
from pydantic import BaseModel, ConfigDict, Field
from pydantic.experimental.missing_sentinel import MISSING


class AppMetaCacheModel(BaseModel):
    log_file_path: P | MISSING = MISSING
    internal_plugins: list[str] | MISSING = MISSING
    external_plugins: list[str] | MISSING = MISSING


class BaseCacheModel(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, validate_assignment=True)
    date: datetime = datetime.now()
    app_meta: AppMetaCacheModel | MISSING = Field(MISSING, alias="_app_meta")


@dataclass(frozen=True)
class CacheFileProperties:
    expires_in_days: ClassVar[int] = 30
    encoding: ClassVar[str] = "utf-8"
    indent: ClassVar[int] = 4
