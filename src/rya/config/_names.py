from typing import ClassVar, Optional

from properpath import P
from pydantic import BaseModel

from ..names import AppIdentity, app_dirs, config_file_sources
from ..pre_utils import LayerLoader
from ..utils import get_dynaconf_core_loader


class DynaConfArgs(BaseModel, validate_assignment=True):
    apply_default_on_none: bool = False
    auto_cast: bool = True
    commentjson_enabled: bool = False
    core_loaders: list[str] = list(
        get_dynaconf_core_loader(AppIdentity.config_file_extension)
    )
    default_env: str = "default"  # Controlled by "environments"
    dotenv_override: bool = False  # Controlled by "load_dotenv"
    dotenv_path: str = "."
    dotenv_verbose: bool = False
    dotted_lookup: bool = True
    encoding: str = "utf-8"
    environments: bool = False  # Controls "env", "env_switcher", "default_env" only
    envvar: str = (
        ""  # Enables the setting file via an environment variable.
        # To have it turned on: f"SETTINGS_FILE_FOR_{AppIdentity.app_name.upper()}"
        # The setting file found with this environment variable has the lowest priority,
        # based on Dynaconf's source code (unless "settings_files" is disabled)
    )
    envvar_prefix: str = AppIdentity.app_name.upper()  # Has nothing to do with "envvar"
    env: str = "development"  # Controlled by "environments"
    env_switcher: str = (
        f"ENV_FOR_{AppIdentity.app_name.upper()}"  # Controlled by "environments"
    )
    force_env: Optional[str] = None
    fresh_vars: list[str] = []
    includes: list[str] | str = []
    loaders: list[str] = []  # Modified. Default: ['dynaconf.loaders.env_loader']
    load_dotenv: bool = False  # Controls "dotenv_override"
    lowercase_read: bool = True  # Modified
    merge_enabled: bool = True  # Modified
    nested_separator: str = "__"
    preload: list[str] | str = []
    redis_enabled: bool = False
    redis: dict = {}
    root_path: Optional[str] = None
    secrets: Optional[str] = None
    settings_files: Optional[str | list[str]] = [
        str(config_file.path) for config_file in config_file_sources
    ]  # Modified
    skip_files: Optional[list[str]] = None
    sysenv_fallback: bool | list[str] = False
    validate_on_update: bool | str = False
    validators: list = []
    validate_only_current_env: bool = False
    validate_only: Optional[str | list[str]] = None
    validate_exclude: Optional[str | list[str]] = None
    vault_enabled: bool = False
    vault: dict = {}
    yaml_loader: str = "safe_load"  # Modified


class InternalPluginLoaderDefinitions(BaseModel, validate_assignment=True):
    root_installation_dir: ClassVar[P] = P(__file__).parent.parent
    directory_name: ClassVar[str] = "plugins"
    typer_app_file_name_prefix: ClassVar[str] = "cli"
    typer_app_file_name: ClassVar[str] = f"{typer_app_file_name_prefix}.py"
    typer_app_var_name: ClassVar[str] = "app"


class ExternalPluginLoaderDefinitions(BaseModel, validate_assignment=True):
    directory_name: ClassVar[str] = InternalPluginLoaderDefinitions.directory_name
    dir: ClassVar[P] = app_dirs.user_data_dir / directory_name
    typer_app_file_name_prefix: ClassVar[str] = (
        InternalPluginLoaderDefinitions.typer_app_file_name_prefix
    )
    typer_app_file_name: ClassVar[str] = (
        InternalPluginLoaderDefinitions.typer_app_file_name
    )
    typer_app_var_name: ClassVar[str] = (
        InternalPluginLoaderDefinitions.typer_app_var_name
    )
    file_name_prefix: ClassVar[str] = "plugin_metadata"
    file_ext: ClassVar[str] = "toml"
    file_name: ClassVar[str] = f"{file_name_prefix}.{file_ext}"


class ExternalPluginMetadataDefinitions(BaseModel, validate_assignment=True):
    file_exists: ClassVar[str] = (
        f"{ExternalPluginLoaderDefinitions.file_name_prefix}_exists"
    )
    plugin_name: ClassVar[str] = "plugin_name"
    cli_script_path: ClassVar[str] = "cli_script"
    venv_path: ClassVar[str] = "venv_dir"
    project_path: ClassVar[str] = "project_dir"
    plugin_root_dir: ClassVar[str] = "plugin_root_dir"


if LayerLoader.is_bootstrap_mode():
    LayerLoader.load_layers(
        globals(),
        layer_names=("names",),
    )
