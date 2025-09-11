from ..configuration import (
    APP_BRAND_NAME,
    APP_DATA_DIR,
    APP_NAME,
    EXTERNAL_LOCAL_PLUGIN_DIR,
    FALLBACK_SOURCE_NAME,
    KEY_DEVELOPMENT_MODE,
    get_development_mode,
    inspect,
    minimal_active_configuration,
)

from ..configuration.config import (
    _NON_CANON_CONFIG_FILE_NAME,
    NON_CANON_YAML_EXTENSION,
    CONFIG_FILE_EXTENSION,
    CONFIG_MIS_PATH,
)
from ..loggers import LOG_FILE_PATH
from ..styles import ColorText
from ..utils import Missing
from ..styles.colors import BLUE, LIGHTCYAN, LIGHTGREEN, RED, YELLOW

detected_config = minimal_active_configuration
detected_config_files = inspect.applied_config_files
missing = ColorText(Missing())


try:
    development_mode_source = detected_config[KEY_DEVELOPMENT_MODE].source
    development_mode_source = detected_config_files[development_mode_source]
except KeyError:
    development_mode_source = FALLBACK_SOURCE_NAME
finally:
    development_mode_value = (
        "True" if get_development_mode(skip_validation=True) else "False"
    )


detected_config_files_formatted = "\n- " + "\n- ".join(
    f"`{v}`: {k}" for k, v in detected_config_files.items()
)

wrong_ext_warning = (
    f"File '{_NON_CANON_CONFIG_FILE_NAME}' detected in location '{CONFIG_MIS_PATH}'. "
    f"If it is meant to be an {APP_NAME} configuration file, "
    f"please rename the file extension from '{NON_CANON_YAML_EXTENSION}' "
    f"to '{CONFIG_FILE_EXTENSION}'. {APP_NAME} only supports '{CONFIG_FILE_EXTENSION}' "
    f"as file extension for configuration files."
)


def show(no_keys: bool) -> str:
    _info = (
        f"""
## {APP_BRAND_NAME} configuration information
The following information includes configuration values and their sources as detected by {APP_NAME}. 
> Name [Key]: Value ← Source

- {ColorText("Log file path").colorize(LIGHTGREEN)}: {LOG_FILE_PATH}
"""
        + f"""
- {ColorText("App data directory").colorize(LIGHTGREEN)}: {APP_DATA_DIR}
- {ColorText("Third-party plugins directory").colorize(LIGHTCYAN)}: {
            EXTERNAL_LOCAL_PLUGIN_DIR
        }
"""
        + "\n"
        + f"- {ColorText('Development mode').colorize(LIGHTGREEN)}"
        + (
            f" **[{ColorText(KEY_DEVELOPMENT_MODE.lower()).colorize(YELLOW)}]**"
            if not no_keys
            else ""
        )
        + f": {development_mode_value} ← `{development_mode_source}`"
        + f"""


{ColorText("Detected configuration sources that are in use:").colorize(BLUE)}
{detected_config_files_formatted}
"""
        + (
            f"""
- `{FALLBACK_SOURCE_NAME}`: Fallback value for when no user configuration is found or found to be invalid.
"""
            if FALLBACK_SOURCE_NAME in (development_mode_source,)
            else ""
        )
        + (
            f"""


**{ColorText("Attention:").colorize(RED)}**
    {wrong_ext_warning}
    """
            if CONFIG_MIS_PATH is not None
            else ""
        )
    )

    return _info
