import time

from .ast import (
    ActionChoose,
    ActionDelay,
    ActionIf,
    ActionNotify,
    ActionService,
    ActionTimer,
    ActionTurn,
    ConditionAtom,
    Duration,
    EntityRef,
    ExprAnd,
    ExprNot,
    ExprOr,
    TriggerBetween,
    TriggerDevice,
    TriggerEvent,
    TriggerState,
    TriggerSun,
    TriggerTime,
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
    # Prepara o gerador com a tabela de simbolos.
    def __init__(self, symbols):
        self.symbols = symbols
        self._extra_conditions = []  # será resetado a cada automação

    # Gera o YAML de todas as automacoes.
    def generate(self, program):
        base_id = int(time.time() * 1000)
        items = [
            self._automation_to_dict(automation, base_id + idx)
            for idx, automation in enumerate(program.automations)
        ]
        return dump_yaml(items)

    # Converte uma automacao para dicionario.
    def _automation_to_dict(self, automation, id_value):
        # Reinicia a lista de condições extras para esta automação
        self._extra_conditions = []
        
        # Gera os triggers (e coleta condições extras no caminho)
        triggers = [self._trigger_to_yaml(t) for t in automation.triggers if t is not None]
        
        # Processa a condição principal, se existir
        conditions = []
        if automation.condition:
            conditions = self._as_condition_list(self._expr_to_yaml(automation.condition))
        
        # Adiciona quaisquer condições extras acumuladas (ex: de TriggerBetween)
        conditions.extend(self._extra_conditions)
        
        return {
            "id": str(id_value),
            "alias": automation.name,
            "description": "",
            "triggers": triggers,
            "conditions": conditions,
            "actions": [self._action_to_yaml(action) for action in automation.actions],
            "mode": automation.mode or "single",
        }

    # Converte um gatilho para YAML.
    def _trigger_to_yaml(self, trigger):
        if isinstance(trigger, TriggerState):
            return self._state_trigger_to_yaml(trigger)
        if isinstance(trigger, TriggerEvent):
            return {"trigger": "event", "event_type": trigger.event_name}
        if isinstance(trigger, TriggerTime):
            return {"trigger": "time", "at": self._normalize_time(trigger.time)}
        if isinstance(trigger, TriggerBetween):
            # Adiciona uma condição de tempo para restringir o horário
            self._extra_conditions.append({
                "condition": "time",
                "after": self._normalize_time(trigger.start),
                "before": self._normalize_time(trigger.end)
            })
            # Retorna um trigger que dispara a cada minuto
            return {"trigger": "time_pattern", "minutes": "/1"}
        if isinstance(trigger, TriggerSun):
            return self._sun_trigger_to_yaml(trigger)
        if isinstance(trigger, TriggerDevice):
            return self._device_trigger_to_yaml(trigger)
        return {"trigger": "state"}

    # Converte gatilho de estado para YAML.
    def _state_trigger_to_yaml(self, trigger):
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

    # Converte gatilho solar para YAML.
    def _sun_trigger_to_yaml(self, trigger):
        payload = {"trigger": "sun", "event": trigger.event}
        if trigger.offset and trigger.offset_sign:
            payload["offset"] = self._duration_to_offset(trigger.offset, trigger.offset_sign)
        return payload

    # Converte gatilho de dispositivo para YAML.
    def _device_trigger_to_yaml(self, trigger):
        payload = {
            "trigger": "state",
            "entity_id": self._resolve_entity(trigger.entity),
            "to": self._normalize_state(trigger.event),
        }
        if trigger.duration:
            payload["for"] = self._duration_to_dict(trigger.duration)
        return payload

    # Converte uma expressao para YAML.
    def _expr_to_yaml(self, expr):
        if isinstance(expr, ConditionAtom):
            return self._atom_to_yaml(expr)
        if isinstance(expr, ExprAnd):
            if all(isinstance(item, ConditionAtom) for item in expr.items):
                return [self._atom_to_yaml(item) for item in expr.items]
            return {"condition": "and", "conditions": [self._ensure_condition_block(item) for item in expr.items]}
        if isinstance(expr, ExprOr):
            return {"condition": "or", "conditions": [self._ensure_condition_block(item) for item in expr.items]}
        if isinstance(expr, ExprNot):
            return {"condition": "not", "conditions": [self._ensure_condition_block(expr.item)]}
        return {"condition": "state"}

    # Garante que uma expressao virou bloco de condicao.
    def _ensure_condition_block(self, expr):
        block = self._expr_to_yaml(expr)
        if isinstance(block, list):
            return {"condition": "and", "conditions": block}
        return block

    # Converte uma condicao simples para YAML.
    def _atom_to_yaml(self, atom):
        if atom.kind in {"state", "device"}:
            return self._state_condition_to_yaml(atom)
        if atom.kind == "time":
            return self._time_condition_to_yaml(atom)
        if atom.kind == "sun":
            return {"condition": "sun", "before": "sunrise", "after": "sunset"}
        return {"condition": "state"}

    # Converte condicao de estado para YAML.
    def _state_condition_to_yaml(self, atom):
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
        return payload

    # Converte condicao de tempo para YAML.
    def _time_condition_to_yaml(self, atom):
        payload = {"condition": "time"}
        if "after" in atom.data:
            payload["after"] = self._normalize_time(atom.data["after"])
        if "before" in atom.data:
            payload["before"] = self._normalize_time(atom.data["before"])
        return payload

    # Converte uma acao para YAML.
    def _action_to_yaml(self, action):
        if isinstance(action, ActionTurn):
            entity_id = self._resolve_entity(action.entity)
            return {"action": self._service_for_turn(entity_id, action.turn_on), "target": {"entity_id": entity_id}}
        if isinstance(action, ActionDelay):
            return {"delay": self._duration_to_dict(action.duration)}
        if isinstance(action, ActionNotify):
            return {"action": "notify.notify", "data": {"message": action.message}}
        if isinstance(action, ActionTimer):
            return self._timer_action_to_yaml(action)
        if isinstance(action, ActionService):
            return self._service_action_to_yaml(action)
        if isinstance(action, ActionIf):
            return self._if_action_to_yaml(action)
        if isinstance(action, ActionChoose):
            return self._choose_action_to_yaml(action)
        return {"action": "homeassistant.turn_on"}

    # Converte acao de timer para YAML.
    def _timer_action_to_yaml(self, action):
        services = {"parar": "timer.cancel", "finalizar": "timer.finish"}
        entity_id = self._resolve_entity(action.entity)
        return {"action": services.get(action.operation, "timer.start"), "target": {"entity_id": entity_id}}

    # Converte acao de servico para YAML.
    def _service_action_to_yaml(self, action):
        payload = {"action": f"{action.domain}.{action.service}"}
        data = {}
        target = {}

        for key, value in action.args.items():
            converted = self._value_to_python(value)
            if key in {"entity_id", "device_id"}:
                target[key] = converted
            else:
                data[key] = converted

        if target:
            payload["target"] = target
        if data:
            payload["data"] = data
        return payload

    # Converte acao se para YAML.
    def _if_action_to_yaml(self, action):
        payload = {
            "if": self._as_condition_list(self._expr_to_yaml(action.condition)),
            "then": [self._action_to_yaml(item) for item in action.then_actions],
        }
        if action.else_actions is not None:
            payload["else"] = [self._action_to_yaml(item) for item in action.else_actions]
        return payload

    # Converte acao escolha para YAML.
    def _choose_action_to_yaml(self, action):
        choices = []
        for case in action.cases:
            choices.append({
                "conditions": self._as_condition_list(self._expr_to_yaml(case.condition)),
                "sequence": [self._action_to_yaml(item) for item in case.actions],
            })

        payload = {"choose": choices}
        if action.default_actions is not None:
            payload["default"] = [self._action_to_yaml(item) for item in action.default_actions]
        return payload

    # Garante que condicoes estejam em lista.
    def _as_condition_list(self, value):
        return value if isinstance(value, list) else [value]

    # Resolve alias para entity_id.
    def _resolve_entity(self, ref):
        if ref.is_entity_id:
            return ref.name
        decl = self.symbols.get(ref.name)
        return decl.entity_id if decl else ref.name

    # Escolhe o servico para ligar ou desligar.
    def _service_for_turn(self, entity_id, turn_on):
        domain = entity_id.split(".", 1)[0] if "." in entity_id else "homeassistant"
        if domain == "cover":
            return "cover.open_cover" if turn_on else "cover.close_cover"
        return f"{domain}.turn_on" if turn_on else f"{domain}.turn_off"

    # Converte duracao para dicionario YAML.
    def _duration_to_dict(self, duration):
        unit_map = {"ms": "milliseconds", "s": "seconds", "min": "minutes", "h": "hours", "d": "days"}
        value = int(duration.value) if duration.value.is_integer() else duration.value
        return {unit_map.get(duration.unit, "seconds"): value}

    # Converte duracao para offset solar.
    def _duration_to_offset(self, duration, sign):
        seconds = self._duration_to_seconds(duration)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{sign}{hours:02d}:{minutes:02d}:{secs:02d}"

    # Converte duracao para segundos.
    def _duration_to_seconds(self, duration):
        if duration.unit == "ms":
            return int(duration.value / 1000)
        if duration.unit == "min":
            return int(duration.value * 60)
        if duration.unit == "h":
            return int(duration.value * 3600)
        if duration.unit == "d":
            return int(duration.value * 86400)
        return int(duration.value)

    # Monta payload de comparacao numerica.
    def _numeric_operator_payload(self, operator, value):
        if operator == ">":
            return {"above": value}
        if operator == ">=":
            return {"above": value - 0.000001 if isinstance(value, (int, float)) else value}
        if operator == "<":
            return {"below": value}
        if operator == "<=":
            return {"below": value + 0.000001 if isinstance(value, (int, float)) else value}
        return {}

    # Normaliza horario para HH:MM:SS.
    def _normalize_time(self, time_text):
        return f"{time_text}:00" if time_text.count(":") == 1 else time_text

    # Normaliza estados em portugues.
    def _normalize_state(self, value):
        return STATE_ALIASES.get(value, value) if isinstance(value, str) else value

    # Converte Value para valor Python.
    def _value_to_python(self, value):
        if value.kind in {"string", "number", "boolean"}:
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
            return [self._value_to_python(item) for item in value.value]
        if value.kind == "map":
            return {key: self._value_to_python(item) for key, item in value.value.items()}
        return value.value