import logging
from typing import Optional

from .._names import KEY_DEVELOPMENT_MODE
from ..core_validators import Exit
from ..loggers import LoggerMaker, get_logger

logger = get_logger()


class DevelopmentState:
    _last_state: Optional[bool] = None

    @staticmethod
    def modify_logger_level(level: int) -> None:
        for _, loggers in LoggerMaker.registered_logger_items():
            for logger_name, logger_obj in loggers.items():
                for handler in logger_obj.handlers:
                    handler.setLevel(level)

    @classmethod
    def switch_state(cls, development_mode: bool) -> None:
        if development_mode != DevelopmentState._last_state:
            if development_mode is True:
                Exit.SYSTEM_EXIT = False
                cls.modify_logger_level(logging.DEBUG)
            else:
                Exit.SYSTEM_EXIT = True
                cls.modify_logger_level(logging.INFO)
            if cls._last_state is not None:
                logger.info(
                    f"'{KEY_DEVELOPMENT_MODE.lower()}' value is set to {development_mode}. "
                    f"The new value will be respected from this point on. "
                    f"Some internal layers might have escaped this modification "
                    f"already."
                )
            cls._last_state = development_mode
