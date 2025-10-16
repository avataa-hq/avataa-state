from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PreferenceInstances(_message.Message):
    __slots__ = ("preference_instances",)
    PREFERENCE_INSTANCES_FIELD_NUMBER: _ClassVar[int]
    preference_instances: _containers.RepeatedCompositeFieldContainer[PreferenceInstance]
    def __init__(self, preference_instances: _Optional[_Iterable[_Union[PreferenceInstance, _Mapping]]] = ...) -> None: ...

class RequestObjectForPalette(_message.Message):
    __slots__ = ("tmo_id_preference",)
    class TmoIdPreferenceEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: PreferenceInstances
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[PreferenceInstances, _Mapping]] = ...) -> None: ...
    TMO_ID_PREFERENCE_FIELD_NUMBER: _ClassVar[int]
    tmo_id_preference: _containers.MessageMap[int, PreferenceInstances]
    def __init__(self, tmo_id_preference: _Optional[_Mapping[int, PreferenceInstances]] = ...) -> None: ...

class PreferenceInstance(_message.Message):
    __slots__ = ("preference_name", "val_type", "kpi_id")
    PREFERENCE_NAME_FIELD_NUMBER: _ClassVar[int]
    VAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    KPI_ID_FIELD_NUMBER: _ClassVar[int]
    preference_name: str
    val_type: str
    kpi_id: int
    def __init__(self, preference_name: _Optional[str] = ..., val_type: _Optional[str] = ..., kpi_id: _Optional[int] = ...) -> None: ...

class WrongKpiIds(_message.Message):
    __slots__ = ("wrong_kpi_ids",)
    WRONG_KPI_IDS_FIELD_NUMBER: _ClassVar[int]
    wrong_kpi_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, wrong_kpi_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class PreferenceInstanceForWithPalette(_message.Message):
    __slots__ = ("preference_name", "val_type", "kpi_id", "palette", "object_type_id")
    PREFERENCE_NAME_FIELD_NUMBER: _ClassVar[int]
    VAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    KPI_ID_FIELD_NUMBER: _ClassVar[int]
    PALETTE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    preference_name: str
    val_type: str
    kpi_id: int
    palette: str
    object_type_id: int
    def __init__(self, preference_name: _Optional[str] = ..., val_type: _Optional[str] = ..., kpi_id: _Optional[int] = ..., palette: _Optional[str] = ..., object_type_id: _Optional[int] = ...) -> None: ...

class RequestToSetCustomPalette(_message.Message):
    __slots__ = ("preference_instances",)
    PREFERENCE_INSTANCES_FIELD_NUMBER: _ClassVar[int]
    preference_instances: _containers.RepeatedCompositeFieldContainer[PreferenceInstanceForWithPalette]
    def __init__(self, preference_instances: _Optional[_Iterable[_Union[PreferenceInstanceForWithPalette, _Mapping]]] = ...) -> None: ...
