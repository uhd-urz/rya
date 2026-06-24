from properpath import P
from pydantic.experimental.missing_sentinel import MISSING

from ...config._names import (
    ExternalPluginLoaderDefinitions,
    InternalPluginLoaderDefinitions,
)
from ...kernel import PublicLayerNames
from ...loggers import get_log_file_path, LogFileNotGivenError
from ...names import app_locations
from ...pre_init import get_cached_data


def get_app_meta_info() -> dict:
    log_file_path: str | P
    try:
        log_file_path = get_log_file_path()
    except LogFileNotGivenError:
        log_file_path = "Not used"
    ext_plugin_defs = ExternalPluginLoaderDefinitions()
    int_plugin_defs = InternalPluginLoaderDefinitions()
    loaded_internal_plugins = getattr(
        get_cached_data().app_meta, "internal_plugins", None
    )
    loaded_external_plugins = getattr(
        get_cached_data().app_meta, "external_plugins", None
    )
    return {
        "Pre-defined configuration locations": ", ".join(
            str(_.path) for _ in app_locations.config_files
        ),
        "Log file path": log_file_path,
        "App data directory": app_locations.platform_dirs.user_data_dir,
        "Cache file path": app_locations.cache_path,
        f"{ext_plugin_defs.name.capitalize()} {PublicLayerNames.plugins} "
        f"directory": ext_plugin_defs.dir or "[red]Disabled[/red]",
        f"Loaded {int_plugin_defs.name} {PublicLayerNames.plugins}": f"{
            f'[blue]{", ".join(loaded_internal_plugins or [])}[/blue]'
            if loaded_internal_plugins is not MISSING
            else 'None'
        }",
        f"Loaded {ext_plugin_defs.name} {PublicLayerNames.plugins}": f"{
            f'[blue]{", ".join(loaded_external_plugins or [])}[/blue]'
            if loaded_external_plugins is not MISSING
            else 'None'
        }",
    }
