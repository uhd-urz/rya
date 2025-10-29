from functools import lru_cache
from typing import Optional, Union, get_args, get_origin

from pydantic import BaseModel

# Pydantic doesn't recommend using FieldInfo directly, hence it's not added
# to pydantic.fields.__all__
# noinspection PyProtectedMember
from pydantic.fields import FieldInfo

from ..loggers import get_logger

logger = get_logger()
FieldConfigStructType = dict[str, dict[str, FieldInfo | list[str]]]
FieldsConfigStructType = dict[str, FieldConfigStructType]


@lru_cache(maxsize=128, typed=True)
def get_pydantic_nested_model_fields(
    model: type[BaseModel],
) -> FieldConfigStructType:
    main_fields: dict[str, dict[str, FieldInfo | list[str]]] = {}

    def read_model(
        current_model: type[BaseModel], current_parent: Optional[list[str]] = None
    ) -> None:
        for field_name, field_info in current_model.model_fields.items():
            current_parent: list[str] = current_parent or []
            new_parent: list[str] = current_parent + [field_name]
            if not is_pydantic_model(field_info.annotation, new_parent):
                main_fields[".".join(new_parent)] = {
                    "name": field_name,
                    "nested_relation": new_parent,
                    "field_info": field_info,
                }

    def is_pydantic_model(annotation, parent: list[str]) -> bool:
        type_origin, type_args = get_origin(annotation), get_args(annotation)
        model_found: bool = False
        if type_origin:
            if type_origin in (Union, list, tuple, set):
                for arg in type_args:
                    if is_pydantic_model(arg, parent):
                        model_found = True
            elif type_origin is dict:
                try:
                    hashable_key, val = type_args
                except ValueError as e:
                    raise TypeError(
                        f"A Pydantic model or field was expected, but a 'dict' "
                        f"annotation '{annotation}' (of origin '{''.join(parent)}') "
                        f"was found with no valid subscription."
                    ) from e
                else:
                    if is_pydantic_model(val, parent):
                        model_found = True
        elif isinstance(annotation, type):
            if issubclass(annotation, BaseModel):
                read_model(annotation, parent)
                model_found = True
            else:
                logger.debug(
                    f"Annotation '{annotation}' (of origin '{''.join(parent)}') "
                    f"is not a Pydantic model, and will not be considered as a model."
                )
        return model_found

    read_model(model)
    return main_fields
