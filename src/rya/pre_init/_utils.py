from pathlib import Path

from ..names import AppIdentity


class PatternNotFoundError(Exception): ...


def get_app_version() -> str:
    return (
        Path(f"{__file__}/../../{AppIdentity.version_file_name}")
        .resolve()
        .read_text()
        .strip()
    )
