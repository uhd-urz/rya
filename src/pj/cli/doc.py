"""
This script includes CLI help documentation for pj.
"""

from .._names import CONFIG_FILE_NAME
from ..configuration import DEFAULT_EXPORT_DATA_FORMAT
from ..styles import BaseFormat, __PACKAGE_IDENTIFIER__ as styles_package_identifier

supported_highlighting_formats = ", ".join(
    f"**{_.upper()}**"
    for _ in BaseFormat.supported_formatter_names(styles_package_identifier)
)

__PARAMETERS__doc__ = {
    "data_format": f"Format style for the output. Supported values are: {supported_highlighting_formats}. "
              f"The values are case insensitive. The default format is `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`. "
              "If an unsupported format value is provided then the output format "
              f"falls back to `{DEFAULT_EXPORT_DATA_FORMAT.upper()}`.",
    "no_keys": "Do not show the names of configuration keywords.",
    "cli_startup": f"⚡️Force override detected configuration from '{CONFIG_FILE_NAME}'. "
                     "The value can be in **JSON** format as a string, or a JSON or YAML **file path**. "
                     "This option can only be passed **before** passing any other "
                     "argument/option/command. E.g., "
                     '`pj --OC \'{"timeout": "10", "verify_ssl": "false"}\' get info -F yml`, '
                     'or `pj --OC "~/.quick-config.yml" get info -F yml`.',
}
