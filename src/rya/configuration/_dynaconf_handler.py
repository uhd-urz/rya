from dynaconf import Dynaconf

from .names import DynaConfArgs, SupportedDynaconfCoreLoaders


def get_dynaconf_core_loader(
    config_file_extension: str | SupportedDynaconfCoreLoaders,
) -> tuple[str]:
    supported_core_loaders = SupportedDynaconfCoreLoaders.__members__
    for e in supported_core_loaders:
        if e == config_file_extension.upper():
            return (str(supported_core_loaders[e]),)
    raise ValueError(
        f"Unsupported config file extension: '{config_file_extension}'. "
        f"Supported configuration extensions are: "
        f"{', '.join(supported_core_loaders)}."
    )


def get_dynaconf_settings(dynaconf_args: DynaConfArgs, /) -> Dynaconf:
    return Dynaconf(**dynaconf_args.model_dump())
