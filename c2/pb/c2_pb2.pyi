from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HelloReq(_message.Message):
    __slots__ = ("nonce",)
    NONCE_FIELD_NUMBER: _ClassVar[int]
    nonce: int
    def __init__(self, nonce: _Optional[int] = ...) -> None: ...

class HelloRes(_message.Message):
    __slots__ = ("nonce",)
    NONCE_FIELD_NUMBER: _ClassVar[int]
    nonce: int
    def __init__(self, nonce: _Optional[int] = ...) -> None: ...

class EradicateReq(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EradicateRes(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PushActionsReq(_message.Message):
    __slots__ = ("actions",)
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    actions: _containers.RepeatedCompositeFieldContainer[Action]
    def __init__(self, actions: _Optional[_Iterable[_Union[Action, _Mapping]]] = ...) -> None: ...

class PushActionsRes(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetPositionsReq(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetPositionsRes(_message.Message):
    __slots__ = ("positions",)
    POSITIONS_FIELD_NUMBER: _ClassVar[int]
    positions: _containers.RepeatedCompositeFieldContainer[Position]
    def __init__(self, positions: _Optional[_Iterable[_Union[Position, _Mapping]]] = ...) -> None: ...

class Position(_message.Message):
    __slots__ = ("position", "time", "state")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    position: str
    time: float
    state: str
    def __init__(self, position: _Optional[str] = ..., time: _Optional[float] = ..., state: _Optional[str] = ...) -> None: ...

class Action(_message.Message):
    __slots__ = ("cowrie", "suid", "fake_data")
    COWRIE_FIELD_NUMBER: _ClassVar[int]
    SUID_FIELD_NUMBER: _ClassVar[int]
    FAKE_DATA_FIELD_NUMBER: _ClassVar[int]
    cowrie: CowrieAction
    suid: SUIDAction
    fake_data: FakeDataAction
    def __init__(self, cowrie: _Optional[_Union[CowrieAction, _Mapping]] = ..., suid: _Optional[_Union[SUIDAction, _Mapping]] = ..., fake_data: _Optional[_Union[FakeDataAction, _Mapping]] = ...) -> None: ...

class CowrieAction(_message.Message):
    __slots__ = ("start",)
    START_FIELD_NUMBER: _ClassVar[int]
    start: bool
    def __init__(self, start: bool = ...) -> None: ...

class SUIDAction(_message.Message):
    __slots__ = ("start", "old_path", "new_path")
    START_FIELD_NUMBER: _ClassVar[int]
    OLD_PATH_FIELD_NUMBER: _ClassVar[int]
    NEW_PATH_FIELD_NUMBER: _ClassVar[int]
    start: bool
    old_path: str
    new_path: str
    def __init__(self, start: bool = ..., old_path: _Optional[str] = ..., new_path: _Optional[str] = ...) -> None: ...

class FakeDataAction(_message.Message):
    __slots__ = ("start", "old_path", "new_path")
    START_FIELD_NUMBER: _ClassVar[int]
    OLD_PATH_FIELD_NUMBER: _ClassVar[int]
    NEW_PATH_FIELD_NUMBER: _ClassVar[int]
    start: bool
    old_path: str
    new_path: str
    def __init__(self, start: bool = ..., old_path: _Optional[str] = ..., new_path: _Optional[str] = ...) -> None: ...
