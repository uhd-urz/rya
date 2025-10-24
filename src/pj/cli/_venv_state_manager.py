from pathlib import Path
from typing import Union

from properpath import P

VENV_INDICATOR_DIR_NAME: str = "site-packages"


def switch_venv_state(
    state: bool,
    /,
    venv_dir: Path,
    project_dir: Union[Path, P],
):
    import sys

    _project_dir: str = str(project_dir)
    site_packages = sorted(
        venv_dir.rglob(VENV_INDICATOR_DIR_NAME), key=lambda x: str(x).lower()
    )

    if not site_packages:
        raise ValueError(
            f"Could not find '{VENV_INDICATOR_DIR_NAME}' directory in "
            "virtual environment path."
        )
    for unique_dir in site_packages:
        _unique_dir = str(unique_dir)
        if state is True:
            sys.path.insert(1, _unique_dir)
            sys.path.insert(1, _project_dir)
            return
        else:
            if sys.path[1:3] == [_project_dir, _unique_dir]:
                sys.path.pop(1)
                sys.path.pop(1)
                return
            else:
                try:
                    sys.path.remove(_unique_dir)
                except ValueError as e:
                    raise RuntimeError(
                        f"Virtual environment directory "
                        f"{_unique_dir} couldn't be removed from sys.path!"
                    ) from e
                else:
                    try:
                        sys.path.remove(_project_dir)
                    except ValueError as e:
                        raise RuntimeError(
                            f"Project directory {_project_dir} "
                            f"couldn't be removed from sys.path!"
                        ) from e
                    return
