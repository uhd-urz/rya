"""
This script includes CLI help documentation for pj.
"""

from dataclasses import dataclass

from ..names import AppIdentity


@dataclass
class MainAppCLIDoc:
    no_keys: str = "Do not show the names of configuration keywords."
    cli_startup: str = (
        f"⚡️Force override detected configuration from '{AppIdentity.user_config_file_name}'. "
        "The value can be in **JSON** format as a string, or a JSON or YAML **file path**. "
        "This option can only be passed **before** passing any other "
        "argument/option/command. E.g., "
        '`pj --OC \'{"timeout": "10", "verify_ssl": "false"}\' get info -F yml`, '
        'or `pj --OC "~/.quick-config.yml" get info -F yml`.'
    )
