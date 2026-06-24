from enum import StrEnum

from properpath import P

from ..kernel import (
    AppLocations,
    ConfigFileModel,
    LayerLoader,
    LogFileModel,
    LoggerDefaults,
    PublicLayerNames,
    RunEarlyList,
    BaseCacheModel,
)


class AppIdentity(StrEnum):
    app_name = "rya"
    app_fancy_name = "rya"
    pypi_name = app_name
    log_file_name = f"{app_name}.log"
    config_file_extension = "toml"
    user_config_file_name = f"config.{config_file_extension}"
    project_config_file_name = f"{app_name}.{config_file_extension}"


if LayerLoader.is_bootstrap_mode():
    LayerLoader.load_layers(
        globals(),
        layer_names=(PublicLayerNames.names,),
    )

LoggerDefaults.logger_name = AppIdentity.app_name

_platform_dirs = P.platformdirs(
    appname=AppIdentity.app_name,
    appauthor=AppIdentity.app_name,
    ensure_exists=False,
    follow_unix=False,
)
app_locations = AppLocations(
    platform_dirs=_platform_dirs,
    config_files=[
        ConfigFileModel(
            path=_platform_dirs.user_config_dir / AppIdentity.user_config_file_name,
            name="user config",
        ),
        ConfigFileModel(
            path=P.cwd() / AppIdentity.project_config_file_name,
            name="project config",
        ),
    ],
    log_file=LogFileModel(
        path=_platform_dirs.user_log_dir / AppIdentity.log_file_name,
        name="user log",
    ),
    cache_path=_platform_dirs.user_cache_dir / f"{AppIdentity.app_name}.json",
)

run_early_list: RunEarlyList = RunEarlyList()


# Cache file definitions
class CacheModel(BaseCacheModel): ...


if LayerLoader.is_bootstrap_mode():
    LayerLoader.load_layers(
        globals(),
        layer_names=(PublicLayerNames.names,),
    )
