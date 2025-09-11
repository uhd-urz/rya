import os
from pathlib import Path

# variables with leading underscores here indicate that they are to be overwritten by config.py
# In which case, import their counterparts from src/config.py
# name definitions
APP_NAME: str = "pj"
APP_BRAND_NAME: str = "pj"
LOG_FILE_NAME: str = f"{APP_NAME}.log"
CONFIG_FILE_EXTENSION: str = "yaml"
CONFIG_FILE_NAME: str = f"{APP_NAME}.{CONFIG_FILE_EXTENSION}"
DEFAULT_EXPORT_DATA_FORMAT: str = "json"
VERSION_FILE_NAME: str = "VERSION"
user_home: Path = Path.home()
cur_dir: Path = Path.cwd()

# XDG and other convention variable definitions
ENV_XDG_DATA_HOME: str = "XDG_DATA_HOME"
ENV_XDG_DOWNLOAD_DIR: str = "XDG_DOWNLOAD_DIR"
ENV_XDG_CONFIG_HOME: str = "XDG_CONFIG_HOME"

# Fallback definitions
FALLBACK_DIR: Path = user_home / ".local/share" / APP_NAME
FALLBACK_EXPORT_DIR: Path = user_home / "Downloads"
FALLBACK_CONFIG_DIR: Path = user_home / ".config"

# Configuration path definitions
SYSTEM_CONFIG_LOC: Path = Path("/etc") / CONFIG_FILE_NAME
LOCAL_CONFIG_LOC: Path = (
    Path(os.getenv(ENV_XDG_CONFIG_HOME, FALLBACK_CONFIG_DIR)) / CONFIG_FILE_NAME
)
# In case $XDG_CONFIG_HOME isn't defined in the machine, it falls back to $HOME/.config/pj.yml
PROJECT_CONFIG_LOC: Path = cur_dir / CONFIG_FILE_NAME

# Configuration field definitions
KEY_DEVELOPMENT_MODE: str = "DEVELOPMENT_MODE"
KEY_PLUGIN_KEY_NAME: str = "PLUGINS"

# Log data directory with root permission
LOG_DIR_ROOT: Path = Path(f"/var/log/{APP_NAME}")
