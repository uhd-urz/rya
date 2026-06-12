from dataclasses import dataclass
from typing import Any, ClassVar

from ...pre_utils import LayerLoader, PublicLayerNames


@dataclass
class ConfDescDefinition:
    conf_desc_key: ClassVar[str] = "__conf_desc__"
    max_reveal_masked_secret: ClassVar[int] = 0


@dataclass
class _ConfigInternalDisplayOptionDefaults:
    filter_default: ClassVar[dict[str, bool]] = {"all": True}
    include_default: ClassVar[dict[str, bool]] = {"key": True, "val": True}


@dataclass
class ConfigDisplayOptionDefaults:
    separator: ClassVar[str] = " "
    separator_desc: ClassVar[str] = "a single space"
    filter_cli_default: ClassVar[str] = "all"
    include_cli_default: ClassVar[str] = "key desc unit val"


if LayerLoader.is_bootstrap_mode():
    LayerLoader.load_layers(
        globals(),
        layer_names=(PublicLayerNames.names,),
    )
