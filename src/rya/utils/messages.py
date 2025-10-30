import logging
from typing import Optional

from ..pre_utils import DataObjectList
from ..loggers import LogMessageData


class MessagesList(DataObjectList[LogMessageData]): ...


messages_list = MessagesList()


def add_message(
    message: str,
    level: int = logging.INFO,
    logger: Optional[logging.Logger] = None,
    is_aggressive: bool = False,
) -> None:
    messages_list.append(
        LogMessageData(
            message=message, level=level, logger=logger, is_aggressive=is_aggressive
        )
    )
