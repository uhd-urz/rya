from typing import Any, Optional, Self

from pydantic import BaseModel, model_validator


class ConfigDescriptionModel(BaseModel):
    include: bool = True
    description: Optional[str] = None
    unit: Optional[str] = None
    contains_secrets: bool = False


class ConfigDisplayValues(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None

    @model_validator(mode="after")
    def _check_value_type(self) -> Self:
        self.value = str(self.value)
        return self


class ConfigDisplayIncludes(BaseModel):
    key: bool = True
    val: bool = True
    desc: bool = False
    loc: bool = False
    unit: bool = False


class ConfigDisplayFilters(BaseModel):
    all: bool = True
    nondef: bool = False
    secret: bool = False
    env: bool = False
