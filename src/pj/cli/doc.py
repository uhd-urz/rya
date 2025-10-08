"""
This script includes CLI help documentation for pj.
"""

from .._names import CONFIG_FILE_NAME

__PARAMETERS__doc__ = {
    "no_keys": "Do not show the names of configuration keywords.",
    "cli_startup": f"⚡️Force override detected configuration from '{CONFIG_FILE_NAME}'. "
                     "The value can be in **JSON** format as a string, or a JSON or YAML **file path**. "
                     "This option can only be passed **before** passing any other "
                     "argument/option/command. E.g., "
                     '`pj --OC \'{"timeout": "10", "verify_ssl": "false"}\' get info -F yml`, '
                     'or `pj --OC "~/.quick-config.yml" get info -F yml`.',
}
