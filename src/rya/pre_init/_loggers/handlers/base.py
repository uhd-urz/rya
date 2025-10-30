from logging import LogRecord

from ....pre_utils import DataObjectList


class LogItemList(DataObjectList[LogRecord]): ...


global_log_record_container = LogItemList()
