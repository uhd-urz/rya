from abc import ABC, abstractmethod
from typing import Any

from properpath.validators import PathWriteValidator

from ..pre_utils import Exit


class ValidationError(Exception): ...


class RuntimeValidationError(Exit, ValidationError):
    def __init__(self, *args) -> None:
        super().__init__(*args or (1,))  # the default error code is always 1


class CriticalValidationError(Exit, ValidationError): ...


class Validator(ABC):
    @abstractmethod
    def validate(self, *args, **kwargs): ...


class Validate:
    def __init__(self, *_typ: Validator | PathWriteValidator):
        self.typ = _typ

    def __call__(self, *args, **kwargs) -> None:
        for typ in self.typ:
            typ.validate(*args, **kwargs)

    def get(self, *args, **kwargs) -> Any:
        for typ in self.typ:
            return typ.validate(*args, **kwargs)
        return None
