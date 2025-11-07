import sys
import tomllib
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import ClassVar

from properpath import P
from pydantic.types import PositiveInt

from ..names import AppIdentity
from ..pre_utils import PublicLayerNames, get_logger

logger = get_logger()


class AppVersionNotFound(Exception): ...


class PatternNotFoundError(Exception): ...


@dataclass
class _ProjectDistMetadata:
    file_name: ClassVar[str] = "pyproject.toml"
    version_key: ClassVar[str] = "version"
    package_key: ClassVar[str] = "name"


def _search_pyproject_file(root_dir: P | Path, depth: PositiveInt) -> P:
    if (path := root_dir / _ProjectDistMetadata.file_name).exists():
        return path
    if depth <= 1:
        raise FileNotFoundError(
            f"{_ProjectDistMetadata.file_name} not found in {root_dir} "
            f"up to level {depth}."
        )
    return _search_pyproject_file(root_dir.parent, depth - 1)


def get_app_version() -> str:
    try:
        return version(AppIdentity.app_name)
    except PackageNotFoundError:
        logger.debug(
            f"'{AppIdentity.app_name}' is not installed as a package. "
            f"So the project's 'pyproject.toml' file will be used to "
            f"get the version (if it exists)."
        )
        app_names_layer = f"{AppIdentity.app_name}.{PublicLayerNames.names}"
        module = sys.modules.get(app_names_layer)
        if module is None:
            raise AppVersionNotFound(
                f"Module layer '{app_names_layer}' is not found "
                f"in sys.modules. Try installing your app "
                f"'{AppIdentity.app_name}' as a development package. "
                f"E.g., uv add --dev {AppIdentity.app_name}. Alternatively, "
                f"add a {_ProjectDistMetadata.file_name} to your "
                f"project directory."
            )
        root_installation_dir = P(f"{module.__file__}/../../")
        try:
            pyproject_file = _search_pyproject_file(root_installation_dir, depth=3)
        except FileNotFoundError as e:
            raise AppVersionNotFound(
                f"No {_ProjectDistMetadata.file_name} is found and nor is "
                f"the app {AppIdentity.app_name} installed as a package."
            ) from e
        else:
            try:
                pyproject = tomllib.loads(pyproject_file.read_text())
            except tomllib.TOMLDecodeError as e:
                raise AppVersionNotFound(
                    f"{pyproject_file} file is found, but it could not parsed as "
                    f"a valid TOML. Exception details: {e}"
                ) from e
            else:
                if (
                    pyproject.get(_ProjectDistMetadata.package_key)
                    != AppIdentity.pypi_name
                ):
                    logger.warning(
                        f"The '{_ProjectDistMetadata.package_key}' from {pyproject_file} "
                        f"doesn't match app '{AppIdentity.app_name}' package "
                        f"name '{AppIdentity.pypi_name}'. The found version will be "
                        f"considered but it could be of a different package! "
                        f"Update your 'AppIdentity.py_package_name' value to match "
                        f"your {_ProjectDistMetadata.file_name}'s if it should."
                    )
                try:
                    return pyproject[_ProjectDistMetadata.version_key]
                except KeyError as e:
                    raise AppVersionNotFound(
                        f"{pyproject_file} doesn't have the "
                        f"'{_ProjectDistMetadata.version_key}' key!"
                    ) from e
