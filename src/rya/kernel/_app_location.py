import sys
from collections import UserList
from typing import Sequence

from properpath import P
from properpath.platformdirs_ import ProperPlatformDirs, ProperUnix
from pydantic import BaseModel, field_validator, ConfigDict

from ._loggers import get_logger
from ._name_containers import (
    ConfigFileModel,
    FileModelContainer,
    FallbackLogFileModel,
    LogFileModel,
)

logger = get_logger()


class AppLocations(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    platform_dirs: ProperPlatformDirs | ProperUnix
    config_files: list[ConfigFileModel]
    log_file: LogFileModel | None
    cache_path: P

    @staticmethod
    def _convert_list_to_file_model_container(
        value: Sequence[ConfigFileModel] | Sequence[FallbackLogFileModel],
    ):
        _models = []
        for file in value:
            if file.target_platforms is not None:
                if any(map(sys.platform.startswith, file.target_platforms)):
                    _models.append(file)
            else:
                _models.append(file)
        return FileModelContainer(_models)

    @field_validator("config_files", mode="after")
    @classmethod
    def _validate_config_file_models(
        cls, value: UserList[ConfigFileModel] | list[ConfigFileModel]
    ) -> FileModelContainer:
        _value = cls._convert_list_to_file_model_container(value)
        if not _value:
            logger.debug(
                f"{AppLocations} attribute config_file becomes empty after "
                f"validation. This could lead to incomplete or failed "
                f"configuration loading."
            )
        return _value

    @field_validator("log_file", mode="after")
    @classmethod
    def _validate_log_file_models(
        cls, value: LogFileModel | None
    ) -> LogFileModel | None:
        if value is not None:
            value.fallback_paths = cls._convert_list_to_file_model_container(
                value.fallback_paths
            )
        return value


# Without explicitly giving how to resolve ProperPath here, Pydantic gives:
# pydantic.errors.PydanticUserError: `AppLocations` is not fully defined; you
# should define `ProperPath`, then call `AppLocations.model_rebuild()`.
# For further information visit https://errors.pydantic.dev/2.13/u/class-not-fully-defined
# The main culprit is likely ProperPlatformDirs and ProperUnix.
# ProperPath supports Pydantic validation already.
AppLocations.model_rebuild(_types_namespace={"ProperPath": P})
