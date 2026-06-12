from dataclasses import dataclass
from typing import ClassVar

from ...pre_utils import LayerLoader, PublicLayerNames


@dataclass
class ConfDescDefinition:
    conf_desc_key: ClassVar[str] = "__conf_desc__"
    max_reveal_masked_secret: ClassVar[int] = 0


if LayerLoader.is_bootstrap_mode():
    LayerLoader.load_layers(
        globals(),
        layer_names=(PublicLayerNames.names,),
    )
