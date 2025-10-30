import sys
from pathlib import Path

from ..names import AppIdentity
from ..pre_utils import PublicLayerNames


class PatternNotFoundError(Exception): ...


def get_app_version() -> str:
    app_names_layer = f"{AppIdentity.app_name}.{PublicLayerNames.names}"
    module = sys.modules.get(app_names_layer)
    if module is None:
        raise RuntimeError(
            f"Module layer '{app_names_layer}' is not found in sys.modules. "
            f"This is an unexpected error."
        )
    return (
        Path(f"{module.__file__}/../../{AppIdentity.version_file_name}")
        .resolve()
        .read_text()
        .strip()
    )
