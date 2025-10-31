from dataclasses import dataclass
from typing import ClassVar

from ...pre_utils import LayerLoader, PublicLayerNames


@dataclass
class RichClickOptions:
    enable_themes: ClassVar[bool] = False


if LayerLoader.is_bootstrap_mode():
    LayerLoader.load_layers(
        globals(),
        layer_names=(PublicLayerNames.names,),
    )
