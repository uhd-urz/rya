from logging import LogRecord

from ..._data_list import DataObjectList


class LogItemList(DataObjectList[LogRecord]): ...


global_log_record_container = LogItemList()
