from typing import Any, Protocol, runtime_checkable

from pydantic import ValidationError


@runtime_checkable
class BasicValidationModel(Protocol):
    def validate(self, *args, **kwargs): ...


@runtime_checkable
class PyndanticBaseModel(Protocol):
    @classmethod
    def model_validate(cls, *args, **kwargs): ...
    def model_dump(self, *args, **kwargs): ...


class MultiValidator:
    def __init__(
        self,
        *_typ: BasicValidationModel | PyndanticBaseModel,
        validation_error_type: type[Exception]
        | tuple[type[Exception], ...] = ValidationError,
    ):
        self.typ = _typ
        self.validation_error_type = validation_error_type

    def validate_one(self, *args, **kwargs) -> Any:
        for typ in self.typ:
            # noinspection PyBroadException
            try:
                match typ:
                    case BasicValidationModel():
                        # noinspection PyNoneFunctionAssignment
                        validated = typ.validate(*args, **kwargs)
                    case PyndanticBaseModel():
                        # noinspection PyNoneFunctionAssignment
                        validated = type(typ).model_validate(
                            typ.model_dump(round_trip=True), *args, **kwargs
                        )
                    case _:
                        raise TypeError(
                            f"Unsupported validation instance {typ} of type {type(typ)}"
                        )
            except self.validation_error_type:
                continue
            else:
                return validated
        raise ValidationError("Validation failed for all provided models.")

    def validate_all(self, *args, **kwargs) -> Any:
        validated_results = []
        for typ in self.typ:
            # noinspection PyBroadException
            match typ:
                case BasicValidationModel():
                    # noinspection PyNoneFunctionAssignment
                    validated = typ.validate(*args, **kwargs)
                case PyndanticBaseModel():
                    # noinspection PyNoneFunctionAssignment
                    validated = type(typ).model_validate(
                        typ.model_dump(round_trip=True), *args, **kwargs
                    )
                case _:
                    raise TypeError(
                        f"Unsupported validation instance {typ} of type {type(typ)}"
                    )
            validated_results.append(validated)
        return validated_results
