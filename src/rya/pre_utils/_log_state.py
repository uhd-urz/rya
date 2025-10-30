from typing import Optional

from ._loggers import LoggerMaker, get_logger

logger = get_logger()


class LogState:
    _last_state: Optional[int] = None

    @staticmethod
    def modify_logger_level(level: int) -> None:
        for _, loggers in LoggerMaker.registered_logger_items():
            for logger_name, logger_obj in loggers.items():
                for handler in logger_obj.handlers:
                    handler.setLevel(level)

    @classmethod
    def switch_state(cls, level: int) -> None:
        if level != LogState._last_state:
            cls.modify_logger_level(level)
            if cls._last_state is not None:
                logger.info(
                    f"Logging level is set to {level}. "
                    f"The new value will be respected from this point on."
                )
            cls._last_state = level
