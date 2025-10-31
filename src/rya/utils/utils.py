import re
import subprocess
from pathlib import Path
from typing import Tuple

import rich_click.rich_click as rc
from pydantic import BaseModel
from rich_click.rich_click_theme import RichClickThemeNotFound

from ..loggers import get_logger
from ..names import AppIdentity
from ..utils import Missing

logger = get_logger()


class PreventiveWarning(RuntimeWarning): ...


class PythonVersionCheckFailed(Exception): ...


def check_reserved_keyword(
    error_instance: Exception, /, *, what: str, against: str
) -> None:
    if re.search(
        r"got multiple values for keyword argument",
        error_verbose := str(error_instance),
        re.IGNORECASE,
    ):
        match = re.match(r"^'\w+'", error_verbose[::-1], re.IGNORECASE)
        if match:
            _reserved_key_end = match.end()
            raise AttributeError(
                f"{what} reserves the keyword argument "
                f"'{error_verbose[-_reserved_key_end + 1 : -1]}' "
                f"for {against}."
            ) from error_instance


def get_sub_package_name(dunder_package: str, /) -> str:
    if not isinstance(dunder_package, str):
        raise TypeError(
            f"{get_sub_package_name.__name__} only accepts __package__ as string."
        )
    match = re.match(r"(^[a-z_]([a-z0-9_]+)?)\.", dunder_package[::-1], re.IGNORECASE)
    # Pattern almost follows: https://packaging.python.org/en/latest/specifications/name-normalization/
    if match is not None:
        return match.group(1)[::-1]
    raise ValueError("No matching sub-package name found.")


def update_kwargs_with_defaults(kwargs: dict, /, defaults: dict) -> None:
    key_arg_missing = Missing("Keyword argument missing")
    for default_key, default_val in defaults.items():
        if kwargs.get(default_key, key_arg_missing) is key_arg_missing:
            kwargs.update({default_key: default_val})


def _get_venv_relative_python_binary_path() -> Path:
    return Path("bin/python")


def get_external_python_version(venv_dir: Path) -> Tuple[str, str, str]:
    external_python_path: Path = (
        external_python_path_unresolved := (
            venv_dir / _get_venv_relative_python_binary_path()
        )
    ).resolve()
    if external_python_path.exists() is False:
        raise PythonVersionCheckFailed(
            f"Resolved Python binary path {external_python_path_unresolved} -> "
            f"{external_python_path} does not exist"
        )
    try:
        external_python_version_call = subprocess.run(
            [str(external_python_path), "--version"],
            check=True,
            encoding="utf-8",
            timeout=5,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise PythonVersionCheckFailed(e) from e
    except TimeoutError as e:
        raise PythonVersionCheckFailed(e) from e
    else:
        external_python_version_match = re.search(
            r"^Python (\d+)\.(\d+)\.(\d+)$",  # ensures 3 strings in match.groups()
            external_python_version_call.stdout,
            flags=re.IGNORECASE,
        )
        if external_python_version_match is not None:
            major, micro, patch = external_python_version_match.groups()
            return major, micro, patch
        raise PythonVersionCheckFailed(
            "Matching Python version not found in output string"
        )


def update_rich_click_cli_theme(config_model: BaseModel) -> None:
    rich_theme = getattr(config_model, "rich_theme", None)
    if rich_theme is None:
        return
    rich_theme_name = getattr(rich_theme, "name", None)
    if rich_theme_name is None:
        return
    try:
        rc.THEME = rich_theme_name
    except RichClickThemeNotFound as e:
        logger.warning(
            f"{AppIdentity.app_name} CLI theme could not be "
            f"changed. Exception details: {e}"
        )
