from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Program:
    entities: List["EntityDecl"] = field(default_factory=list)
    automations: List["Automation"] = field(default_factory=list)


@dataclass
class EntityDecl:
    type_name: str
    alias: str
    entity_id: str
    line: int


@dataclass
class EntityRef:
    name: str
    is_entity_id: bool
    line: int


@dataclass
class Duration:
    value: float
    unit: str
    line: int


@dataclass
class Value:
    kind: str
    value: Any
    line: int


@dataclass
class Automation:
    name: str
    triggers: List[Any]
    condition: Optional[Any]
    actions: List[Any]
    mode: Optional[str]
    line: int


@dataclass
class TriggerState:
    entity: EntityRef
    to_state: Any
    duration: Optional[Duration]
    line: int
    kind: str = "state"


@dataclass
class TriggerEvent:
    event_name: str
    line: int
    kind: str = "event"


@dataclass
class TriggerTime:
    time: str
    line: int
    kind: str = "time"


@dataclass
class TriggerBetween:
    start: str
    end: str
    line: int
    kind: str = "between"


@dataclass
class TriggerSun:
    event: str
    offset: Optional[Duration]
    offset_sign: Optional[str]
    line: int
    kind: str = "sun"


@dataclass
class TriggerDevice:
    entity: EntityRef
    event: str
    duration: Optional[Duration]
    line: int
    kind: str = "device"


@dataclass
class ConditionAtom:
    kind: str
    data: Dict[str, Any]
    line: int


@dataclass
class ExprAnd:
    items: List[Any]
    line: int


@dataclass
class ExprOr:
    items: List[Any]
    line: int


@dataclass
class ExprNot:
    item: Any
    line: int


@dataclass
class ActionTurn:
    turn_on: bool
    entity: EntityRef
    line: int
    kind: str = "turn"


@dataclass
class ActionDelay:
    duration: Duration
    line: int
    kind: str = "delay"


@dataclass
class ActionNotify:
    message: str
    line: int
    kind: str = "notify"


@dataclass
class ActionTimer:
    entity: EntityRef
    operation: str
    line: int
    kind: str = "timer"


@dataclass
class ActionService:
    domain: str
    service: str
    args: Dict[str, Value]
    line: int
    kind: str = "service"


@dataclass
class ActionIf:
    condition: Any
    then_actions: List[Any]
    else_actions: Optional[List[Any]]
    line: int
    kind: str = "if"


@dataclass
class ChooseCase:
    condition: Any
    actions: List[Any]
    line: int


@dataclass
class ActionChoose:
    cases: List[ChooseCase]
    default_actions: Optional[List[Any]]
    line: int
    kind: str = "choose"
