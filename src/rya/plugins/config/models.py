from enum import StrEnum
from typing import Any, Optional, Self

from pydantic import BaseModel, model_validator


class ConfigDescriptionModel(BaseModel):
    title: Optional[str]
    unit: Optional[str] = None
    description: Optional[str] = None
    contains_secrets: bool = False


class ConfigDisplayValues(BaseModel):
    key: str
    title: Optional[str] = None
    value: Any
    description: Optional[str] = None

    @model_validator(mode="after")
    def _check_value_type(self) -> Self:
        self.value = str(self.value)
        return self


class ConfigDisplayFilters(BaseModel):
    all: bool = True
    mod: bool = False
    secret: bool = False
    env: bool = False
