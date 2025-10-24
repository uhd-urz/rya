from logging import LogRecord

from ...._core_utils import DataObjectList


class LogItemList(DataObjectList[LogRecord]): ...


global_log_record_container = LogItemList()
