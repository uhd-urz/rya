import logging
from pathlib import Path
from typing import Optional

from dynaconf import Dynaconf

from .._names import (
    APP_BRAND_NAME,
    APP_NAME,
    CONFIG_FILE_EXTENSION,
    CONFIG_FILE_NAME,
    DEFAULT_EXPORT_DATA_FORMAT,
    ENV_XDG_DOWNLOAD_DIR,
    FALLBACK_DIR,
    FALLBACK_EXPORT_DIR,
    KEY_DEVELOPMENT_MODE,
    KEY_PLUGIN_KEY_NAME,
    LOCAL_CONFIG_LOC,
    LOG_DIR_ROOT,
    PROJECT_CONFIG_LOC,
    SYSTEM_CONFIG_LOC,
    VERSION_FILE_NAME,
)
from ..core_validators import (
    CriticalValidationError,
    PathValidator,
    Validate,
    ValidationError,
)
from ..loggers import _XDG_DATA_HOME, LOG_FILE_PATH, Logger
from ..utils import Missing
from ..utils import add_message
from ._config_history import (
    AppliedConfigIdentity,
    ConfigHistory,
    InspectConfigHistory,
    MinimalActiveConfiguration,
)

__all__ = [
    "APP_BRAND_NAME",
    "APP_NAME",
    "CONFIG_FILE_EXTENSION",
    "CONFIG_FILE_NAME",
    "DEFAULT_EXPORT_DATA_FORMAT",
    "ENV_XDG_DOWNLOAD_DIR",
    "FALLBACK_DIR",
    "FALLBACK_EXPORT_DIR",
    "KEY_DEVELOPMENT_MODE",
    "KEY_PLUGIN_KEY_NAME",
    "LOCAL_CONFIG_LOC",
    "LOG_DIR_ROOT",
    "PROJECT_CONFIG_LOC",
    "SYSTEM_CONFIG_LOC",
    "settings",
    "history",
    "inspect",
    "minimal_active_configuration",
    "DEVELOPMENT_MODE_DEFAULT_VAL",
    "PLUGIN_DEFAULT_VALUE",
    "MinimalActiveConfiguration",
    "VERSION_FILE_NAME",
    "DEVELOPMENT_MODE",
    "EXTERNAL_LOCAL_PLUGIN_DIR",
    "EXTERNAL_LOCAL_PLUGIN_DIRECTORY_NAME",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX",
    "EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR",
    "EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME",
    "EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME",
    "FALLBACK_SOURCE_NAME",
    "PLUGIN",
    "NON_CANON_YAML_EXTENSION",
    "APP_DATA_DIR",
    "INTERNAL_PLUGIN_DIRECTORY_NAME",
    "INTERNAL_PLUGIN_TYPER_APP_FILE_NAME",
    "INTERNAL_PLUGIN_TYPER_APP_VAR_NAME",
    "ROOT_INSTALLATION_DIR",
    "_NON_CANON_CONFIG_FILE_NAME",
    "CONFIG_MIS_PATH"
]

logger = Logger()

SYSTEM_CONFIG_LOC: Path = SYSTEM_CONFIG_LOC
LOCAL_CONFIG_LOC: Path = LOCAL_CONFIG_LOC
PROJECT_CONFIG_LOC: Path = PROJECT_CONFIG_LOC

env_var_app_name = APP_NAME.upper().replace("-", "_")
FALLBACK_SOURCE_NAME: str = "DEFAULT"

NON_CANON_YAML_EXTENSION: str = "yml"
_NON_CANON_CONFIG_FILE_NAME: str = f"{APP_NAME}.{NON_CANON_YAML_EXTENSION}"
CONFIG_MIS_PATH: Optional[Path] = None
for path in [
    SYSTEM_CONFIG_LOC.parent / _NON_CANON_CONFIG_FILE_NAME,
    LOCAL_CONFIG_LOC.parent / _NON_CANON_CONFIG_FILE_NAME,
    PROJECT_CONFIG_LOC.parent / _NON_CANON_CONFIG_FILE_NAME,
]:
    if path.exists():
        CONFIG_MIS_PATH = path
        message = (
            f"You have a message marked as 'Attention' waiting for you. "
            f"Please run '{APP_NAME} show-config' to see it."
        )
        add_message(message, logging.INFO)
        break
settings = Dynaconf(
    envar_prefix=env_var_app_name,
    env_switcher=f"{env_var_app_name}_ENV",
    # environment variable to apply mode of environment (e.g., dev, production)
    core_loaders=["YAML"],  # will not read any file extensions except YAML
    # loaders=['conf'], # will not work without properly defining a custom loader for .conf first
    yaml_loader="safe_load",  # safe load doesn't execute arbitrary Python code in YAML files
    settings_files=[SYSTEM_CONFIG_LOC, LOCAL_CONFIG_LOC, PROJECT_CONFIG_LOC],
    # Order of the "settings_files" list is the overwrite priority order.
    # PROJECT_CONFIG_LOC has the highest priority.
)

history = ConfigHistory(settings)
minimal_active_configuration: MinimalActiveConfiguration = MinimalActiveConfiguration()


# App internal data location
if LOG_FILE_PATH.parent != LOG_DIR_ROOT:
    APP_DATA_DIR = LOG_FILE_PATH.parent
else:
    validate_app_dir = Validate(
        PathValidator([_XDG_DATA_HOME / APP_NAME, FALLBACK_DIR / APP_NAME])
    )
    try:
        APP_DATA_DIR = validate_app_dir.get()
    except ValidationError:
        logger.critical(
            f"{APP_NAME} couldn't validate {FALLBACK_DIR} to store {APP_NAME} internal application data. "
            f"{APP_NAME} will not run!"
        )
        raise CriticalValidationError

# The history is ready to be inspected
inspect = InspectConfigHistory(history)

# DEVELOPMENT_MODE falls back to false if not defined in the configuration
DEVELOPMENT_MODE_DEFAULT_VAL: bool = False
DEVELOPMENT_MODE = settings.get(KEY_DEVELOPMENT_MODE, None)

# Plugins
PLUGIN = settings.get(KEY_PLUGIN_KEY_NAME, None)
PLUGIN_DEFAULT_VALUE: dict = {}


for key_name, key_val in [
    (KEY_DEVELOPMENT_MODE, DEVELOPMENT_MODE),
    (KEY_PLUGIN_KEY_NAME, PLUGIN),
]:
    try:
        history.patch(key_name, key_val)
    except KeyError:
        minimal_active_configuration[key_name] = AppliedConfigIdentity(Missing(), None)
    else:
        minimal_active_configuration[key_name] = InspectConfigHistory(
            history
        ).applied_config[key_name]


# Plugin file definitions and locations
ROOT_INSTALLATION_DIR: Path = Path(__file__).parent.parent
INTERNAL_PLUGIN_DIRECTORY_NAME: str = KEY_PLUGIN_KEY_NAME.lower()
INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX: str = "cli"
INTERNAL_PLUGIN_TYPER_APP_FILE_NAME: str = (
    f"{INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX}.py"
)
INTERNAL_PLUGIN_TYPER_APP_VAR_NAME: str = "app"
# Local external/3rd-party plugin definitions
EXTERNAL_LOCAL_PLUGIN_DIRECTORY_NAME: str = INTERNAL_PLUGIN_DIRECTORY_NAME
EXTERNAL_LOCAL_PLUGIN_DIR: Path = APP_DATA_DIR / EXTERNAL_LOCAL_PLUGIN_DIRECTORY_NAME
EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX: str = (
    INTERNAL_PLUGIN_TYPER_APP_FILE_NAME_PREFIX
)
EXTERNAL_LOCAL_PLUGIN_TYPER_APP_FILE_NAME: str = INTERNAL_PLUGIN_TYPER_APP_FILE_NAME
EXTERNAL_LOCAL_PLUGIN_TYPER_APP_VAR_NAME: str = INTERNAL_PLUGIN_TYPER_APP_VAR_NAME
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX: str = f"{APP_NAME}_plugin_metadata"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_EXT: str = CONFIG_FILE_EXTENSION
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME: str = (
    f"{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX}."
    f"{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_EXT}"
)

EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_FILE_EXISTS = (
    f"{EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_NAME_PREFIX}_exists"
)
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PLUGIN_NAME: str = "plugin_name"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_CLI_SCRIPT_PATH: str = "cli_script"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_VENV_PATH: str = "venv_dir"
EXTERNAL_LOCAL_PLUGIN_METADATA_FILE_KEY_PROJECT_PATH: str = "project_dir"
EXTERNAL_LOCAL_PLUGIN_METADATA_KEY_PLUGIN_ROOT_DIR: str = "plugin_root_dir"
