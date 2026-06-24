import logging
from logging import Handler

from .base import global_log_record_container


class ResultCallbackHandler(Handler):
    _store_okay: bool = True
    _client_count: int = 0

    def __init__(self):
        super().__init__()
        self.setLevel(logging.INFO)

    @classmethod
    def enable_store_okay(cls) -> None:
        cls._store_okay = True
        cls._client_count += 1

    @classmethod
    def disable_store_okay(cls) -> None:
        cls._store_okay = False

    @classmethod
    def is_store_okay(cls) -> bool:
        return cls._store_okay

    @classmethod
    def get_client_count(cls) -> int:
        return cls._client_count

    def emit(self, record):
        if ResultCallbackHandler._store_okay:
            if record.levelno >= self.level:
                global_log_record_container.append(record)
