from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
current: States
historical: States
planned: States

class KPI(_message.Message):
    __slots__ = ["granularity_id", "kpi_id", "object_id", "record_time", "state", "value"]
    GRANULARITY_ID_FIELD_NUMBER: _ClassVar[int]
    KPI_ID_FIELD_NUMBER: _ClassVar[int]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    RECORD_TIME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    granularity_id: int
    kpi_id: int
    object_id: int
    record_time: _timestamp_pb2.Timestamp
    state: States
    value: str
    def __init__(self, kpi_id: _Optional[int] = ..., object_id: _Optional[int] = ..., granularity_id: _Optional[int] = ..., value: _Optional[str] = ..., record_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., state: _Optional[_Union[States, str]] = ...) -> None: ...

class RequestBatchImport(_message.Message):
    __slots__ = ["kpi_data"]
    KPI_DATA_FIELD_NUMBER: _ClassVar[int]
    kpi_data: _containers.RepeatedCompositeFieldContainer[KPI]
    def __init__(self, kpi_data: _Optional[_Iterable[_Union[KPI, _Mapping]]] = ...) -> None: ...

class ResponseBatchImport(_message.Message):
    __slots__ = ["message", "status"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    message: str
    status: str
    def __init__(self, status: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class States(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
