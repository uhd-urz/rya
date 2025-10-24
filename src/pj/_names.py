from collections import namedtuple
from dataclasses import dataclass
from enum import StrEnum

from properpath import P

# variables with leading underscores here indicate that they are to be overwritten by config.py
# In which case, import their counterparts from src/config.py
# name definitions
APP_NAME: str = "pj"
APP_BRAND_NAME: str = "pj"
LOG_FILE_NAME: str = f"{APP_NAME}.log"
CONFIG_FILE_EXTENSION: str = "yml"
CONFIG_FILE_NAME: str = f"{APP_NAME}.{CONFIG_FILE_EXTENSION}"
DEFAULT_EXPORT_DATA_FORMAT: str = "json"
VERSION_FILE_NAME: str = "VERSION"

ConfigFileTuple = namedtuple("ConfigFileTuple", ("file", "level"))
LogFileTuple = namedtuple("LogFileTuple", ("file", "level"))


class AppIdentity(StrEnum):
    app_name = "pj"
    app_brand_name = "pj"
    log_file_name = f"{app_name}.log"
    config_file_extension = "yml"
    user_config_file_name = f"config.{config_file_extension}"
    project_config_file_name = f"{app_name}.{config_file_extension}"
    version_file_name = "VERSION"


app_dirs = P.platformdirs(
    appname=AppIdentity.app_name,
    appauthor=AppIdentity.app_name,
    ensure_exists=True,
    follow_unix=True,
)


@dataclass(frozen=True, slots=True)
class ConfigPaths:
    system_config_file: P = (
        P("/etc") / AppIdentity.app_name / AppIdentity.user_config_file_name
    )
    user_config_dir: P = app_dirs.user_config_dir
    user_config_file: P = app_dirs.user_config_dir / AppIdentity.user_config_file_name
    project_config_file: P = P.cwd() / AppIdentity.project_config_file_name


@dataclass(frozen=True, slots=True)
class LogPaths:
    system_log_file: P = (
        P("/var/log") / AppIdentity.app_name / AppIdentity.log_file_name
    )
    user_log_dir: P = app_dirs.user_log_dir
    user_log_file: P = app_dirs.user_log_dir / AppIdentity.log_file_name


config_paths = ConfigPaths()
log_paths = LogPaths()


@dataclass(frozen=True, slots=True)
class LogFiles:
    root: LogFileTuple = LogFileTuple(log_paths.system_log_file, "SYSTEM LOG")
    user: LogFileTuple = LogFileTuple(log_paths.user_log_file, "USER LOG")


@dataclass()
class ConfigFiles:
    root: ConfigFileTuple = ConfigFileTuple(
        config_paths.system_config_file, "SYSTEM CONFIG"
    )
    user: ConfigFileTuple = ConfigFileTuple(
        config_paths.user_config_file, "USER CONFIG"
    )
    project: ConfigFileTuple = ConfigFileTuple(
        config_paths.project_config_file, "PROJECT CONFIG"
    )


config_files = ConfigFiles()
log_files = LogFiles()

# Configuration field definitions
KEY_DEVELOPMENT_MODE: str = "DEVELOPMENT_MODE"
KEY_PLUGIN_KEY_NAME: str = "PLUGINS"
