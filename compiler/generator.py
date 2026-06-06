import time
from typing import Any, Dict, List, Optional

from .ast import (
    ActionChoose,
    ActionDelay,
    ActionIf,
    ActionNotify,
    ActionService,
    ActionTimer,
    ActionTurn,
    Automation,
    ChooseCase,
    ConditionAtom,
    Duration,
    EntityDecl,
    EntityRef,
    ExprAnd,
    ExprNot,
    ExprOr,
    Program,
    TriggerBetween,
    TriggerDevice,
    TriggerEvent,
    TriggerState,
    TriggerSun,
    TriggerTime,
    Value,
)
from .yaml_writer import dump_yaml


STATE_ALIASES = {
    "ligado": "on",
    "desligado": "off",
    "desarmado": "disarmed",
    "armado": "armed",
    "aberto": "on",
    "fechado": "off",
}


class YamlGenerator:
    def __init__(self, symbols: Dict[str, EntityDecl]) -> None:
        self.symbols = symbols

    def generate(self, program: Program) -> str:
        items: List[Dict[str, Any]] = []
        base_id = int(time.time() * 1000)
        for idx, automation in enumerate(program.automations):
            items.append(self._automation_to_dict(automation, base_id + idx))
        return dump_yaml(items)

    def _automation_to_dict(self, automation: Automation, id_value: int) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data["id"] = str(id_value)
        data["alias"] = automation.name
        data["description"] = ""
        data["triggers"] = [self._trigger_to_yaml(t) for t in automation.triggers]

        if automation.condition:
            cond_yaml = self._expr_to_yaml(automation.condition)
            if isinstance(cond_yaml, list):
                data["conditions"] = cond_yaml
            else:
                data["conditions"] = [cond_yaml]
        else:
            data["conditions"] = []

        data["actions"] = [self._action_to_yaml(a) for a in automation.actions]
        data["mode"] = automation.mode or "single"
        return data

    def _trigger_to_yaml(self, trigger: Any) -> Dict[str, Any]:
        if isinstance(trigger, TriggerState):
            entity_id = self._resolve_entity(trigger.entity)
            if trigger.operator in {">", "<", ">=", "<="}:
                payload = {
                    "trigger": "numeric_state",
                    "entity_id": entity_id,
                    **self._numeric_operator_payload(trigger.operator, trigger.to_state),
                }
            else:
                payload = {
                    "trigger": "state",
                    "entity_id": entity_id,
                    "to": self._normalize_state(trigger.to_state),
                }
                if trigger.operator == "!=":
                    payload["not_to"] = payload.pop("to")
            if trigger.duration:
                payload["for"] = self._duration_to_dict(trigger.duration)
            return payload
        if isinstance(trigger, TriggerEvent):
            return {"trigger": "event", "event_type": trigger.event_name}
        if isinstance(trigger, TriggerTime):
            return {"trigger": "time", "at": self._normalize_time(trigger.time)}
        if isinstance(trigger, TriggerBetween):
            return {"trigger": "time", "at": self._normalize_time(trigger.start)}
        if isinstance(trigger, TriggerSun):
            payload = {"trigger": "sun", "event": trigger.event}
            if trigger.offset and trigger.offset_sign:
                payload["offset"] = self._duration_to_offset(trigger.offset, trigger.offset_sign)
            return payload
        if isinstance(trigger, TriggerDevice):
            entity_id = self._resolve_entity(trigger.entity)
            payload = {
                "trigger": "state",
                "entity_id": entity_id,
                "to": self._normalize_state(trigger.event),
            }
            if trigger.duration:
                payload["for"] = self._duration_to_dict(trigger.duration)
            return payload
        return {"trigger": "state"}

    def _expr_to_yaml(self, expr: Any) -> Any:
        if isinstance(expr, ConditionAtom):
            return self._atom_to_yaml(expr)
        if isinstance(expr, ExprAnd):
            if all(isinstance(item, ConditionAtom) for item in expr.items):
                return [self._atom_to_yaml(item) for item in expr.items]
            return {
                "condition": "and",
                "conditions": [self._ensure_condition_block(i) for i in expr.items],
            }
        if isinstance(expr, ExprOr):
            return {
                "condition": "or",
                "conditions": [self._ensure_condition_block(i) for i in expr.items],
            }
        if isinstance(expr, ExprNot):
            return {
                "condition": "not",
                "conditions": [self._ensure_condition_block(expr.item)],
            }
        return {"condition": "state"}

    def _ensure_condition_block(self, expr: Any) -> Dict[str, Any]:
        block = self._expr_to_yaml(expr)
        if isinstance(block, list):
            return {"condition": "and", "conditions": block}
        return block

    def _atom_to_yaml(self, atom: ConditionAtom) -> Dict[str, Any]:
        if atom.kind in {"state", "device"}:
            entity = atom.data.get("entity")
            state = atom.data.get("state")
            operator = atom.data.get("operator", "esta")
            entity_id = self._resolve_entity(entity) if isinstance(entity, EntityRef) else ""
            if operator in {">", "<", ">=", "<="}:
                return {
                    "condition": "numeric_state",
                    "entity_id": entity_id,
                    **self._numeric_operator_payload(operator, state),
                }
            payload = {
                "condition": "state",
                "entity_id": entity_id,
                "state": self._normalize_state(state),
            }
            if operator == "!=":
                return {"condition": "not", "conditions": [payload]}
            return {
                **payload,
            }
        if atom.kind == "time":
            payload: Dict[str, Any] = {"condition": "time"}
            if "after" in atom.data:
                payload["after"] = self._normalize_time(atom.data["after"])
            if "before" in atom.data:
                payload["before"] = self._normalize_time(atom.data["before"])
            return payload
        if atom.kind == "sun":
            return {"condition": "sun", "before": "sunrise", "after": "sunset"}
        return {"condition": "state"}

    def _action_to_yaml(self, action: Any) -> Dict[str, Any]:
        if isinstance(action, ActionTurn):
            entity_id = self._resolve_entity(action.entity)
            service = self._service_for_turn(entity_id, action.turn_on)
            return {"action": service, "target": {"entity_id": entity_id}}
        if isinstance(action, ActionDelay):
            return {"delay": self._duration_to_dict(action.duration)}
        if isinstance(action, ActionNotify):
            return {"action": "notify.notify", "data": {"message": action.message}}
        if isinstance(action, ActionTimer):
            entity_id = self._resolve_entity(action.entity)
            service = "timer.start"
            if action.operation == "parar":
                service = "timer.cancel"
            elif action.operation == "finalizar":
                service = "timer.finish"
            return {"action": service, "target": {"entity_id": entity_id}}
        if isinstance(action, ActionService):
            payload: Dict[str, Any] = {"action": f"{action.domain}.{action.service}"}
            data = {}
            target = {}
            for key, val in action.args.items():
                if key in {"entity_id", "device_id"}:
                    target[key] = self._value_to_python(val)
                else:
                    data[key] = self._value_to_python(val)
            if target:
                payload["target"] = target
            if data:
                payload["data"] = data
            return payload
        if isinstance(action, ActionIf):
            cond_yaml = self._expr_to_yaml(action.condition)
            if isinstance(cond_yaml, list):
                conditions = cond_yaml
            else:
                conditions = [cond_yaml]
            payload: Dict[str, Any] = {
                "if": conditions,
                "then": [self._action_to_yaml(a) for a in action.then_actions],
            }
            if action.else_actions is not None:
                payload["else"] = [self._action_to_yaml(a) for a in action.else_actions]
            return payload
        if isinstance(action, ActionChoose):
            choices = []
            for case in action.cases:
                cond_yaml = self._expr_to_yaml(case.condition)
                if isinstance(cond_yaml, list):
                    conditions = cond_yaml
                else:
                    conditions = [cond_yaml]
                choices.append(
                    {
                        "conditions": conditions,
                        "sequence": [self._action_to_yaml(a) for a in case.actions],
                    }
                )
            payload = {"choose": choices}
            if action.default_actions is not None:
                payload["default"] = [self._action_to_yaml(a) for a in action.default_actions]
            return payload
        return {"action": "homeassistant.turn_on"}

    def _resolve_entity(self, ref: EntityRef) -> str:
        if ref.is_entity_id:
            return ref.name
        decl = self.symbols.get(ref.name)
        if decl:
            return decl.entity_id
        return ref.name

    def _service_for_turn(self, entity_id: str, turn_on: bool) -> str:
        domain = entity_id.split(".", 1)[0] if "." in entity_id else "homeassistant"
        if domain == "cover":
            return "cover.open_cover" if turn_on else "cover.close_cover"
        return f"{domain}.turn_on" if turn_on else f"{domain}.turn_off"

    def _duration_to_dict(self, duration: Duration) -> Dict[str, Any]:
        unit_map = {
            "ms": "milliseconds",
            "s": "seconds",
            "min": "minutes",
            "h": "hours",
            "d": "days",
        }
        key = unit_map.get(duration.unit, "seconds")
        value = int(duration.value) if duration.value.is_integer() else duration.value
        return {key: value}

    def _duration_to_offset(self, duration: Duration, sign: str) -> str:
        seconds = self._duration_to_seconds(duration)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{sign}{hours:02d}:{minutes:02d}:{secs:02d}"

    def _duration_to_seconds(self, duration: Duration) -> int:
        value = duration.value
        if duration.unit == "ms":
            return int(value / 1000)
        if duration.unit == "s":
            return int(value)
        if duration.unit == "min":
            return int(value * 60)
        if duration.unit == "h":
            return int(value * 3600)
        if duration.unit == "d":
            return int(value * 86400)
        return int(value)

    def _numeric_operator_payload(self, operator: str, value: Any) -> Dict[str, Any]:
        if operator == ">":
            return {"above": value}
        if operator == ">=":
            return {"above": value - 0.000001 if isinstance(value, (int, float)) else value}
        if operator == "<":
            return {"below": value}
        if operator == "<=":
            return {"below": value + 0.000001 if isinstance(value, (int, float)) else value}
        return {}

    def _normalize_time(self, time_text: str) -> str:
        if time_text.count(":") == 1:
            return f"{time_text}:00"
        return time_text

    def _normalize_state(self, value: Any) -> Any:
        if isinstance(value, str):
            return STATE_ALIASES.get(value, value)
        return value

    def _value_to_python(self, value: Value) -> Any:
        if value.kind == "string":
            return value.value
        if value.kind == "number":
            return value.value
        if value.kind == "boolean":
            return value.value
        if value.kind == "time":
            return self._normalize_time(value.value)
        if value.kind == "duration" and isinstance(value.value, Duration):
            return self._duration_to_dict(value.value)
        if value.kind == "entity" and isinstance(value.value, EntityRef):
            return self._resolve_entity(value.value)
        if value.kind == "ident":
            return value.value
        if value.kind == "list":
            return [self._value_to_python(v) for v in value.value]
        if value.kind == "map":
            return {k: self._value_to_python(v) for k, v in value.value.items()}
        return value.value
